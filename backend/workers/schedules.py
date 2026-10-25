from __future__ import annotations

from celery.schedules import crontab

CELERYBEAT_SCHEDULE = {
    # Lightweight feed rebuild — every 30 minutes (no DB writes, just JSON/ICS regen)
    "rebuild-feeds-every-30min": {
        "task": "workers.tasks.feeds.rebuild_all_feeds",
        "schedule": crontab(minute="*/30"),
    },
    # Expire events that ended >48h ago — runs daily at 3 AM IST
    "expire-past-events-daily": {
        "task": "workers.tasks.crawl.expire_past_events",
        "schedule": crontab(hour=3, minute=0),
    },
}
