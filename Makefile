.PHONY: install dev test lint typecheck build clean

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check agent_init tests

typecheck:
	mypy agent_init

build:
	python -m build

clean:
	rm -rf dist/ build/ *.egg-info/ .pytest_cache/ .ruff_cache/ .mypy_cache/
	find . -name __pycache__ -type d -exec rm -rf {} +
