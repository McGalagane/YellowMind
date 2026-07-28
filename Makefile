.PHONY: up down logs migrate test lint typecheck

up:
	@./scripts/dev.sh up

down:
	@./scripts/dev.sh down

logs:
	@./scripts/dev.sh logs $(filter-out $@,$(MAKECMDGOALS))

migrate:
	@echo "Migrations not yet configured — see issue #7"
	@exit 1

test:
	poetry run pytest -v

lint:
	poetry run ruff check .

typecheck:
	poetry run pyright
