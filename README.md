# Lucknow Tech Events

> A living aggregator of tech events happening in **Lucknow, UP, India** — powered by an AI discovery pipeline, not manual curation.

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
| Task Queue | Celery + Redis |
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
│   ├── workers/              # Celery tasks
│   │   └── tasks/
│   │       ├── discovery.py  # AI event discovery (runs every 3h)
│   │       └── crawl.py      # URL crawling + extraction
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
- A **Google Gemini API key** (get one at [aistudio.google.com](https://aistudio.google.com/app/apikey))

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
| **Task Monitor** (Flower) | http://localhost:5555 |
| **PostgreSQL** | localhost:5432 |
| **Redis** | localhost:6379 |

### 3. Run database migrations

```bash
docker compose --env-file .env.dev -f docker/docker-compose.dev.yml exec api alembic upgrade head
```

### 4. Trigger your first discovery run

The discovery agent runs automatically every 3 hours via Celery Beat. To trigger it immediately:

```bash
docker compose --env-file .env.dev -f docker/docker-compose.dev.yml exec api python -c "
from workers.tasks.discovery import auto_discover_events
auto_discover_events.delay()
print('Discovery queued.')
"
```

Or use the Mission Control dashboard (URL-only, not linked in the UI).

---

## Environment Variables

Use separate, ignored files for each environment:

- Development: copy `.env.example.dev` to `.env.dev` and pass `--env-file .env.dev` with `docker/docker-compose.dev.yml` (also used by `make dev`).
- Production: copy `.env.example.prod` to `.env.prod` and pass `--env-file .env.prod` with `docker/docker-compose.prod.yml`. This Compose file runs the backend services; configure the separately hosted frontend with the public URL settings below before building it.
- Without Compose: copy `.env.example` to `backend/.env` or export the backend variables in your shell. Use localhost database/Redis URLs. Put only frontend URL/site settings in `apps/web/.env.local`; Next.js does not read the repository-root env file.

Run Compose commands from the repository root. `--env-file` supplies Compose interpolation; each Compose file also loads its matching file into the backend services. Shell variables take precedence, so avoid mixing exported production values with development commands. Both templates intentionally leave credentials and database URLs blank. Fill them privately before starting services. Compose rejects a missing database password/URL, and production also requires the admin hash and signing key.

| Variable | Purpose |
|---|---|
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Container database settings; the password has no default |
| `DATABASE_URL` | Async PostgreSQL URL with matching credentials (`postgresql+asyncpg://…`) |
| `ALEMBIC_DATABASE_URL` | Sync URL for offline migrations (`postgresql+psycopg2://…`); online migrations use `DATABASE_URL` |
| `REDIS_URL` | Redis URL; use `redis://redis:6379/0` inside Compose |
| `JWT_SECRET` | Private backend signing key; use a long random value supplied securely, never `NEXT_PUBLIC_*` |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD_HASH` | Backend login identity and bcrypt password hash |
| `AI_MODE`, `GEMINI_API_KEY`, `GEMINI_MODEL` | Mock mode needs no provider key; supply a key only when opting into Gemini |
| `CORS_ORIGINS` | Comma-separated frontend origins |
| `DEBUG`, `LOG_LEVEL` | Development/production diagnostics; production Compose forces debug off |
| `STORAGE_TYPE`, `LOCAL_STORAGE_PATH` | Snapshot storage configuration |
| `NEXT_PUBLIC_API_URL`, `INTERNAL_API_URL` | Public API endpoint and server-side/proxy endpoint, including `/api/v1`; available when building and running the frontend |
| `NEXT_PUBLIC_SITE_NAME`, `NEXT_PUBLIC_SITE_URL` | Public site metadata |

Percent-encode reserved password characters in database URLs. Single-quote bcrypt hash values in env files to preserve their literal `$` characters; do not double the dollar signs. Never copy backend secrets into frontend variables or commit filled env files.

Open `/mission-control/login` to sign in. There is no query-string key: a key bundled in browser JavaScript cannot protect admin access. The backend still verifies the admin password and requires a valid admin JWT on protected endpoints. With a missing/blank `JWT_SECRET`, login returns 503 and token verification rejects requests; public endpoints remain available. Missing `ADMIN_PASSWORD_HASH` also disables login.

These files describe source configuration only. Applying new database credentials to an existing PostgreSQL volume does not change its password. Existing deployments must retain their configured credentials; changing live settings or rotating credentials is a separate operator action.

---

## Running Services Individually

```bash
# API only
docker compose --env-file .env.dev -f docker/docker-compose.dev.yml up api postgres redis

# Frontend only (after installing deps)
cd apps/web && pnpm install && pnpm dev

# Celery worker only
docker compose --env-file .env.dev -f docker/docker-compose.dev.yml up worker

# Celery beat (scheduler) only
docker compose --env-file .env.dev -f docker/docker-compose.dev.yml up beat
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
