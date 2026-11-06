from __future__ import annotations

from datetime import datetime, timedelta, timezone

import structlog
from celery import shared_task
from sqlalchemy import delete, update

from api.core.database import SessionLocal
from api.models.event import Event
from workers.utils import run_async

log = structlog.get_logger(__name__)

# Events with start_at beyond this year are considered junk-date sentinels
_JUNK_DATE_YEAR = 2050


@shared_task(name="workers.tasks.crawl.expire_past_events")
def expire_past_events() -> dict:
    """Three-pass cleanup:
    Pass A: Expire events with explicit end_at older than 48h.
    Pass B: Expire events with no end_at but start_at older than 7 days.
    Pass C: Hard-delete junk-date events (start_at > 2050) older than 1 day.
    """
    now = datetime.now(timezone.utc)
    results: dict[str, int] = {"pass_a": 0, "pass_b": 0, "pass_c_deleted": 0}

    async def _run() -> dict:
        async with SessionLocal() as db:
            # Pass A: has end_at and it's > 48h in the past
            cutoff_48h = now - timedelta(hours=48)
            stmt_a = (
                update(Event)
                .where(
                    (Event.expires_at.is_(None))
                    & (Event.end_at.is_not(None))
                    & (Event.end_at < cutoff_48h)
                )
                .values(expires_at=now)
            )
            res_a = await db.execute(stmt_a)
            results["pass_a"] = int(res_a.rowcount or 0)

            # Pass B: no end_at, but start_at was > 7 days ago (event definitely over)
            cutoff_7d = now - timedelta(days=7)
            stmt_b = (
                update(Event)
                .where(
                    (Event.expires_at.is_(None))
                    & (Event.end_at.is_(None))
                    & (Event.start_at < cutoff_7d)
                )
                .values(expires_at=now)
            )
            res_b = await db.execute(stmt_b)
            results["pass_b"] = int(res_b.rowcount or 0)

            # Pass C: hard-delete junk-date events (sentinel 2099/2050+)
            # Grace period: only delete if created > 24h ago (avoids mid-pipeline events)
            junk_sentinel = datetime(year=_JUNK_DATE_YEAR, month=1, day=1, tzinfo=timezone.utc)
            grace_cutoff = now - timedelta(hours=24)
            stmt_c = delete(Event).where(
                (Event.start_at > junk_sentinel)
                & (Event.created_at < grace_cutoff)
            )
            res_c = await db.execute(stmt_c)
            results["pass_c_deleted"] = int(res_c.rowcount or 0)

            await db.commit()
            return results

    final = run_async(_run())
    log.info("expire_past_events.done", **final)
    return {"ok": True, **final}
