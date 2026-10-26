.PHONY: dev down migrate seed crawl-all test lint format shell logs

dev:
	docker compose --env-file .env.dev -f docker/docker-compose.dev.yml up --build

down:
	docker compose --env-file .env.dev -f docker/docker-compose.dev.yml down -v

migrate:
	docker compose --env-file .env.dev -f docker/docker-compose.dev.yml exec api alembic upgrade head

seed:
	docker compose --env-file .env.dev -f docker/docker-compose.dev.yml exec api python scripts/seed_sources.py

crawl-all:
	docker compose --env-file .env.dev -f docker/docker-compose.dev.yml exec worker celery -A workers.celery_app call workers.tasks.crawl.crawl_all_sources

test:
	docker compose -f docker/docker-compose.dev.yml exec api pytest backend/tests/ -v

lint:
	docker compose --env-file .env.dev -f docker/docker-compose.dev.yml exec api ruff check backend/ && docker compose --env-file .env.dev -f docker/docker-compose.dev.yml exec api ruff format --check backend/

format:
	docker compose --env-file .env.dev -f docker/docker-compose.dev.yml exec api ruff format backend/

shell:
	docker compose --env-file .env.dev -f docker/docker-compose.dev.yml exec api bash

logs:
	docker compose --env-file .env.dev -f docker/docker-compose.dev.yml logs -f api worker

