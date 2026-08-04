.PHONY: install format lint typecheck imports test coverage check assets interface types play

install:
	uv sync --all-extras
	npm --prefix frontend install

format:
	uv run isort src tests scripts
	uv run black src tests scripts
	npm --prefix frontend run format

lint:
	uv run isort --check-only src tests scripts
	uv run black --check src tests scripts
	uv run pylint src scripts
	npm --prefix frontend run lint

typecheck:
	uv run mypy
	npm --prefix frontend run typecheck

imports:
	uv run lint-imports

test:
	uv run pytest -n auto
	npm --prefix frontend run test

coverage:
	uv run pytest --cov --cov-report=term-missing

check: lint typecheck imports coverage
	npm --prefix frontend run test

assets:
	uv run python -m scripts.assets

interface:
	npm --prefix frontend install
	npm --prefix frontend run test
	npm --prefix frontend run build

types:
	uv run python -m scripts.openapi
	npm --prefix frontend run types

TABLE_ARGUMENTS = \
	$(if $(GAME),--game $(GAME)) \
	$(if $(PLAYERS),--players $(PLAYERS)) \
	$(if $(ROUNDS),--rounds $(ROUNDS)) \
	$(if $(SEED),--seed $(SEED)) \
	$(if $(GRACE),--grace-seconds $(GRACE)) \
	$(if $(PORT),--port $(PORT))

play:
	uv run cardtable $(TABLE_ARGUMENTS) $(ARGS)
