.PHONY: install format lint typecheck imports test coverage check assets play

install:
	uv sync --all-extras

format:
	uv run isort src tests scripts
	uv run black src tests scripts

lint:
	uv run isort --check-only src tests scripts
	uv run black --check src tests scripts
	uv run pylint src scripts

typecheck:
	uv run mypy

imports:
	uv run lint-imports

test:
	uv run pytest -n auto

coverage:
	uv run pytest --cov --cov-report=term-missing

check: lint typecheck imports coverage

assets:
	uv run python scripts/assets.py

play:
	uv run cardtable $(if $(GAME),--game $(GAME)) $(if $(PLAYERS),--players $(PLAYERS))
