# Lucknow Tech Events

> A living aggregator of tech events happening in **Lucknow, UP, India**.

> **Rebuild in progress.** The project is being rebuilt from AI-based discovery to small per-platform adapters (Luma, Unstop, GDG/Bevy) that read public event data once a day. No AI is used in the new core flow. Track the work in the [`v1 core flow` milestone](https://github.com/LucknowAI/lucknow-live-events/milestone/).

> The legacy AI code has been removed. The older architecture and pipeline descriptions below are historical pending the README rewrite (#23). Use the engine command in Local Development; no model-provider key is required.

[![Next.js](https://img.shields.io/badge/Next.js-15-black?logo=next.js)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql)](https://postgresql.org)

---

## What is this?

Lucknow Tech Events is an automated events aggregation platform. An AI agent continuously searches the web for tech events — hackathons, workshops, conferences, meetups — in Lucknow and surfaces them in a clean, filterable UI.

**No manual curation.** Events are discovered by a Gemini-powered search agent, validated by an extraction agent that normalises raw page content into structured data, and published automatically when confidence is high enough.

The platform is built and maintained by the Lucknow tech community, for the Lucknow tech community.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Discovery Agent                         │
│  Gemini 3 Flash + Google Search Grounding                   │
│  Runs every 3 hours via Celery Beat                         │
└───────────────────────────┬─────────────────────────────────┘
                            │ individual event URLs
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Ingestion Pipeline                        │
│  1. Scrape page (httpx + BeautifulSoup)                     │
│  2. Pre-filter garbage (JS soup / 404 / no event signal)    │
│  3. Extraction Agent — Gemini extracts structured JSON      │
│  4. Confidence scoring (0.0 – 1.0)                          │
│  5. Publish (≥0.5) or flag for Date TBA / Moderation        │
└───────────────────────────┬─────────────────────────────────┘
                            │ structured Event record
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              PostgreSQL  ←→  FastAPI  ←→  Next.js           │
│         (events, raw_events, sources, submissions)          │
└─────────────────────────────────────────────────────────────┘
```

### Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15 (App Router), TypeScript, Tailwind CSS |
| Backend API | FastAPI, Python 3.12, SQLAlchemy 2.0 (async) |
| Scheduler | system cron (daily at 06:00 IST) |
| Database | PostgreSQL 16 |
| AI | Google Gemini 3.0 Flash via `google-genai` SDK |
| Containerisation | Docker / Podman Compose |
| Migrations | Alembic |

---

## Monorepo Structure

```
lucknow-events/
├── apps/
│   └── web/                  # Next.js 15 frontend
│       ├── app/              # App Router pages
│       ├── components/       # Shared UI components
│       └── lib/              # API client, utilities
├── backend/
│   ├── ai/                   # Gemini agents (extraction, classification)
│   ├── api/                  # FastAPI app
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── routers/          # Route handlers (events, admin, submissions)
│   │   ├── schemas/          # Pydantic schemas
│   │   └── services/         # Business logic
│   ├── ingestion/            # Scraping + pipeline orchestration
│   │   └── adapters/         # Platform-specific scrapers (WIP)
│   └── alembic/              # Database migrations
├── docker/
│   └── docker-compose.dev.yml
├── data/                     # Local storage for scraped snapshots
└── .env                      # Environment variables (see below)
```

---

## Local Development

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) or [Podman](https://podman.io/) with the Compose plugin
- [Node.js 20+](https://nodejs.org/) and [pnpm](https://pnpm.io/) (`npm i -g pnpm`)

### 1. Clone and configure

```bash
git clone https://github.com/ItsPriyamSri/Lucknow-events.git
cd Lucknow-events
cp .env.example.dev .env.dev   # then fill in your values (see Environment Variables below)
```

### 2. Start all services

```bash
docker compose --env-file .env.dev -f docker/docker-compose.dev.yml up --build
```

This starts:
| Service | URL |
|---|---|
| **Frontend** (Next.js) | http://localhost:3000 |
| **Backend API** (FastAPI) | http://localhost:8000 |
| **API Docs** (Swagger) | http://localhost:8000/docs |
| **PostgreSQL** | localhost:5432 |

### 3. Run database migrations

```bash
docker compose --env-file .env.dev -f docker/docker-compose.dev.yml exec api alembic upgrade head
```

### Backend tests

Create an empty, dedicated test database on the development Docker Postgres:

```bash
docker compose -f docker/docker-compose.dev.yml up -d postgres
docker compose -f docker/docker-compose.dev.yml exec postgres createdb -U user lucknow_events_test
export TEST_DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/lucknow_events_test
make test
```

Requires Python 3.12+ and `uv`; `make test` installs the locked development dependencies.
`TEST_DATABASE_URL` is required and must use `postgresql+asyncpg` with a database name
ending in `_test`. Alembic runs once per test session; each test uses a rolled-back
transaction, including when application code calls `commit()`. Never use a live database.
Pass pytest arguments with `make test TEST_ARGS='-v'`.

### 4. Run the event engine

Run `make seed` once to add the initial source rows, then preview the configured platform sources without saving events:

```bash
docker compose --env-file .env.dev -f docker/docker-compose.dev.yml exec api python -m engine.run --dry-run
```

Run `make crawl-all` to fetch and save events with the engine. In production a
system cron job runs the same command once a day; see [Deployment](#deployment).

---

## Environment Variables

Use separate, ignored files for each environment:

- Development: copy `.env.example.dev` to `.env.dev` and pass `--env-file .env.dev` with `docker/docker-compose.dev.yml` (also used by `make dev`).
- Production: copy `.env.example.prod` to `.env.prod` and pass `--env-file .env.prod` with `docker/docker-compose.prod.yml`. This Compose file runs the backend services; configure the separately hosted frontend with the public URL settings below before building it.
- Without Compose: copy `.env.example` to `backend/.env` or export the backend variables in your shell. Use a localhost database URL. Put only frontend URL/site settings in `apps/web/.env.local`; Next.js does not read the repository-root env file.

Run Compose commands from the repository root. `--env-file` supplies Compose interpolation; each Compose file also loads its matching file into the backend services. Shell variables take precedence, so avoid mixing exported production values with development commands. Both templates intentionally leave credentials and database URLs blank. Fill them privately before starting services. Compose rejects a missing database password/URL, and production also requires the admin hash and signing key.

| Variable | Purpose |
|---|---|
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Container database settings; the password has no default |
| `DATABASE_URL` | Async PostgreSQL URL with matching credentials (`postgresql+asyncpg://…`) |
| `ALEMBIC_DATABASE_URL` | Sync URL for offline migrations (`postgresql+psycopg2://…`); online migrations use `DATABASE_URL` |
| `HEALTHCHECK_URL` | healthchecks.io ping URL used by the daily engine run; blank disables the ping |
| `JWT_SECRET` | Private backend signing key; use a long random value supplied securely, never `NEXT_PUBLIC_*` |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD_HASH` | Backend login identity and bcrypt password hash |
| `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` | Optional future text-completion helper; leave blank for normal operation. The base URL includes the provider's API prefix (such as `/v1`). |
| `CORS_ORIGINS` | Comma-separated frontend origins |
| `DEBUG`, `LOG_LEVEL` | Development/production diagnostics; production Compose forces debug off |
| `STORAGE_TYPE`, `LOCAL_STORAGE_PATH` | Snapshot storage configuration |
| `NEXT_PUBLIC_API_URL`, `INTERNAL_API_URL` | Public API endpoint and server-side/proxy endpoint, including `/api/v1`; available when building and running the frontend |
| `NEXT_PUBLIC_SITE_NAME`, `NEXT_PUBLIC_SITE_URL` | Public site metadata |

Percent-encode reserved password characters in database URLs. Single-quote bcrypt hash values in env files to preserve their literal `$` characters; do not double the dollar signs. Never copy backend secrets into frontend variables or commit filled env files.

`await llm.complete(prompt, system=None)` is available for future features through an OpenAI-compatible `/chat/completions` endpoint. No API route or engine code calls it. It raises `LLMDisabled` without a key; explicitly configure all three `LLM_*` settings before calling it. Provider errors propagate, with no automatic retries or fabricated fallback text.

Open `/mission-control/login` to sign in. There is no query-string key: a key bundled in browser JavaScript cannot protect admin access. The backend still verifies the admin password and requires a valid admin JWT on protected endpoints. With a missing/blank `JWT_SECRET`, login returns 503 and token verification rejects requests; public endpoints remain available. Missing `ADMIN_PASSWORD_HASH` also disables login.

These files describe source configuration only. Applying new database credentials to an existing PostgreSQL volume does not change its password. Existing deployments must retain their configured credentials; changing live settings or rotating credentials is a separate operator action.

---

## Running Services Individually

```bash
# API only
docker compose --env-file .env.dev -f docker/docker-compose.dev.yml up api postgres

# Frontend only (after installing deps)
cd apps/web && pnpm install && pnpm dev

# Engine only (manual run; production uses system cron)
docker compose --env-file .env.dev -f docker/docker-compose.dev.yml exec api python -m engine.run
```

---

## Database Migrations

```bash
# Apply all pending migrations
docker compose --env-file .env.dev -f docker/docker-compose.dev.yml exec api alembic upgrade head

# Create a new migration
docker compose --env-file .env.dev -f docker/docker-compose.dev.yml exec api alembic revision --autogenerate -m "your_description"

# Downgrade one step
docker compose --env-file .env.dev -f docker/docker-compose.dev.yml exec api alembic downgrade -1
```

---

## Deployment

| Piece | Runs on |
|---|---|
| Frontend | Vercel (`apps/web`) |
| API | Render (`render.yaml`) or the Compose backend |
| PostgreSQL | Neon or Compose Postgres |
| Daily engine | system cron on a VPS or another long-lived host |

The engine is a plain command, not a queue worker. Cron runs
`python -m engine.run` once a day at 06:00 IST. The command pings
healthchecks.io when the run finishes, so a failed or missed run alerts you.

### VPS setup for the engine

Use a dedicated `lucknow` user and keep the checkout at
`/opt/lucknow-live-events`.

1. Install `git`, Python 3.12 and `uv` (on the service user's `PATH`, for
   example `/usr/local/bin/uv`), then create the service user and the
   checkout directory:

   ```bash
   sudo useradd --system --user-group --create-home \
     --home-dir /var/lib/lucknow --shell /bin/sh lucknow
   sudo install -d -o lucknow -g lucknow /opt/lucknow-live-events
   sudo timedatectl set-timezone UTC
   ```

   Keep the server clock on UTC. The crontab entry below uses `00:30 UTC`,
   which is `06:00 Asia/Kolkata`; Debian and Ubuntu cron do not reliably
   support `CRON_TZ`.

2. Clone the repository and install the locked dependencies:

   ```bash
   sudo -u lucknow git clone \
     https://github.com/LucknowAI/lucknow-live-events.git \
     /opt/lucknow-live-events
   cd /opt/lucknow-live-events/backend
   sudo -u lucknow uv sync --frozen --no-dev
   ```

3. Create the private env file at `/etc/lucknow-live-events/engine.env`.
   Root owns it; the `lucknow` user reads it through the group:

   ```bash
   sudo install -d -m 0755 /etc/lucknow-live-events
   sudo install -m 0640 -o root -g lucknow /dev/null /etc/lucknow-live-events/engine.env
   sudo "${EDITOR:-vi}" /etc/lucknow-live-events/engine.env
   ```

   It needs at least:

   ```dotenv
   DATABASE_URL=postgresql+asyncpg://…
   ALEMBIC_DATABASE_URL=postgresql+psycopg2://…
   HEALTHCHECK_URL=https://hc-ping.com/…
   ```

   `HEALTHCHECK_URL` is a bearer token; keep the file private. Quote values
   that contain characters your shell treats specially.

4. Apply migrations and seed the source rows once:

   ```bash
   sudo -u lucknow sh -c '
     set -a; . /etc/lucknow-live-events/engine.env; set +a
     cd /opt/lucknow-live-events/backend
     .venv/bin/alembic upgrade head
     .venv/bin/python ../scripts/seed_sources.py
   '
   ```

   The runner only reads rows whose platform has an adapter (`bevy`, `luma`,
   `unstop`); the rest of the seed rows stay dormant until their adapter
   lands. Keep the ones you want enabled.

5. Create the log directory, then test the engine without saving events:

   ```bash
   sudo install -d -o lucknow -g lucknow /var/log/lucknow-live-events
   sudo -u lucknow /opt/lucknow-live-events/deploy/run-engine.sh --dry-run
   sudo tail -n 20 /var/log/lucknow-live-events/engine.log
   ```

6. Create a healthchecks.io check with a period of **1 day** and a grace of
   **1 hour**, then put its ping URL in `HEALTHCHECK_URL`. A run that never
   starts is caught by the grace period, so create the check before scheduling
   cron.

7. Run the engine once and confirm the check turns green:

   ```bash
   sudo -u lucknow /opt/lucknow-live-events/deploy/run-engine.sh
   ```

8. Install the cron and log rotation files:

   ```bash
   sudo install -m 0644 /opt/lucknow-live-events/deploy/crontab /etc/cron.d/lucknow-live-events
   sudo install -m 0644 /opt/lucknow-live-events/deploy/logrotate /etc/logrotate.d/lucknow-live-events
   ```

   Cron calls `/opt/lucknow-live-events/deploy/run-engine.sh` as the `lucknow`
   user at `00:30 UTC`. The script loads the env file, appends to
   `/var/log/lucknow-live-events/engine.log`, and exits with the engine's
   status. Logrotate keeps 14 daily files.

9. Failure drill. In your database console (Neon SQL editor or `psql`), add a
   temporary Bevy source with a bad chapter id:

   ```sql
   INSERT INTO sources (name, platform, base_url, config_json)
   VALUES (
     'Broken Bevy (drill)',
     'bevy',
     'https://gdg.community.dev',
     '{"chapter_id": "not-a-number"}'
   );
   ```

   Run only Bevy sources and confirm the command exits `1` and the check turns
   red:

   ```bash
   sudo -u lucknow /opt/lucknow-live-events/deploy/run-engine.sh --source bevy
   echo "exit=$?"
   ```

   Remove the drill row, then run the engine again to return the check to green:

   ```sql
   DELETE FROM sources WHERE name = 'Broken Bevy (drill)';
   ```

   A source that fails never marks its events as missing.

---

## Pipeline Internals

### Sources

The `sources` table is a **living accumulation log** — not a static seed. New entries arrive when:
- The discovery agent finds a new event URL
- A user submits an event via the submission form

The extraction agent periodically re-scrapes known sources to catch updates (e.g. a date being announced for a previously Date TBA event).

### Discovery Agent

Runs every 3 hours. Uses Gemini 2.0 Flash with Google Search Grounding to find individual event page URLs. It designs its own search strategy based on known Lucknow communities and platforms, then filters out listing/browse pages before feeding URLs into the pipeline.

### Extraction Agent

For each URL, the pipeline:
1. **Pre-filters garbage** — skips pages that are too short, pure JS/CSS soup, error pages, or have no event vocabulary
2. **Extracts structured data** — Gemini reads the cleaned page text and returns a structured JSON event record
3. **Grounded date fallback** — if the page is a JS-heavy SPA with no date, fires a targeted Google Search grounding call to find the date
4. **Scores confidence** (0.0–1.0) based on how many fields were successfully extracted

### Confidence Thresholds

| Score | Outcome |
|---|---|
| ≥ 0.50 with date | Published immediately |
| ≥ 0.30 without date | Published as **Date TBA** |
| < 0.30 | Sent to moderation queue |
| `not_an_event=true` | Rejected |

### Date TBA Events

Events without a confirmed date are published with `date_tba=true`. They appear at the bottom of the events list and are excluded from the calendar view. The extraction agent will re-check the source page on subsequent crawl runs — if a date is found, the event is updated.

---

## Contributing

Contributions are welcome! Here's how to get started:

1. Fork the repository and create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes following the patterns in existing code
3. Test locally using Docker Compose
4. Submit a pull request with a clear description of what you changed and why

### Code Conventions

- **Backend**: Follow PEP 8, use `async/await` throughout, type-hint everything
- **Frontend**: TypeScript strict mode, functional components with hooks
- **Commits**: Conventional commits format (`feat:`, `fix:`, `chore:`, etc.)
- **No secrets in code**: All credentials go in `.env`, never committed

---

## Future Scope

The following features are planned but not yet implemented:

### Platform-Specific Source Adapters *(High Priority)*

Dedicated crawlers for each major platform used by Lucknow communities:
- **GDG Community** (`gdg.community.dev`) — scrape chapter event listings, extract individual event links
- **Commudle** (`commudle.com`) — community-specific event pages
- **lu.ma**, **Meetup**, **Unstop**, **Devfolio**, **Townscript** — platform-specific parsers

These adapters would run in parallel with the AI discovery agent, scraping the Lucknow-specific event sections of each platform and feeding individual event URLs directly into the validation pipeline.

**Online events rule**: Online events listed on Lucknow community pages (even if not Lucknow-specific in scope) should count as valid and be included.

### Self-Improving Discovery Agent

Give the discovery agent persistent memory of which search strategies worked (returned valid events) vs. which failed (returned listing pages or empty results). Over time it improves its own queries without manual intervention.

### Batch Extraction

Currently each event URL is extracted individually (one LLM call per URL). Batch extraction would group multiple similar URLs into a single LLM call, dramatically reducing Gemini API quota usage.

### Community Submission → Live Listing Flow

Full end-to-end flow for the community link submission form: submitted links enter a moderation queue, approved links get validated by the extraction agent, and valid events go live automatically.

### Auto-Verification of Community Submissions

Trusted community sources (e.g. GDG Lucknow) could be whitelisted to bypass moderation and publish directly.

---

## License

MIT — see [LICENSE](LICENSE) for details.

---

*Built with ❤️ in Lucknow*
