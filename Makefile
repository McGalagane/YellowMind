.PHONY: up down logs migrate test lint typecheck

up:
	@./scripts/dev.sh up

down:
	@./scripts/dev.sh down

logs:
	@./scripts/dev.sh logs $(filter-out $@,$(MAKECMDGOALS))

migrate:
	DATABASE_URL=$${DATABASE_URL:-postgresql://yellowmind:yellowmind@localhost:5432/yellowmind} \
	poetry run alembic upgrade head

test:
	poetry run pytest -v

lint:
	poetry run ruff check .

typecheck:
	poetry run pyright
