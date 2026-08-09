.PHONY: install format lint typecheck imports test coverage check assets build interface types play

install:
	uv sync --all-extras
	npm install

format:
	uv run isort src tests scripts
	uv run black src tests scripts
	npm run format --workspace frontend

lint:
	uv run isort --check-only src tests scripts
	uv run black --check src tests scripts
	uv run pylint src scripts
	npm run lint --workspace frontend

typecheck:
	uv run mypy
	npm run typecheck --workspace frontend

imports:
	uv run lint-imports

test:
	uv run pytest -n auto
	npm run test --workspace frontend

coverage:
	uv run pytest --cov --cov-report=term-missing

check: lint typecheck imports coverage
	npm run test --workspace frontend

assets:
	uv run python -m scripts.assets

build:
	npm run build --workspace frontend

interface:
	npm install
	npm run test --workspace frontend
	npm run build --workspace frontend

types:
	uv run python -m scripts.openapi
	npm run types --workspace frontend

TABLE_ARGUMENTS = \
	$(if $(GAME),--game $(GAME)) \
	$(if $(CODE),--code $(CODE)) \
	$(if $(PLAYERS),--players $(PLAYERS)) \
	$(if $(DECKS),--decks $(DECKS)) \
	$(if $(ROUNDS),--rounds $(ROUNDS)) \
	$(if $(SEED),--seed $(SEED)) \
	$(if $(GRACE),--grace-seconds $(GRACE)) \
	$(if $(PACK),--pack $(PACK)) \
	$(if $(BACK),--back $(BACK)) \
	$(if $(HOST),--host $(HOST)) \
	$(if $(PORT),--port $(PORT)) \
	$(if $(ADVERTISE),--advertise $(ADVERTISE))

play: build
	uv run cardtable $(TABLE_ARGUMENTS) $(ARGS)
