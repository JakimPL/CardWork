.PHONY: install format lint typecheck imports test coverage check

install:
	uv sync --all-extras

format:
	uv run isort src tests
	uv run black src tests

lint:
	uv run isort --check-only src tests
	uv run black --check src tests
	uv run pylint src

typecheck:
	uv run mypy

imports:
	uv run lint-imports

test:
	uv run pytest -n auto

coverage:
	uv run pytest --cov --cov-report=term-missing

check: lint typecheck imports coverage
