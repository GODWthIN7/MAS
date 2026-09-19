.PHONY: install lint format format-check test run health check

VENV ?= .venv
PYTHON ?= python3.12
VENV_BIN := $(VENV)/bin

install:
	$(PYTHON) --version
	$(PYTHON) -m venv $(VENV)
	$(VENV_BIN)/pip install --upgrade pip
	$(VENV_BIN)/pip install -e ".[dev]"

lint:
	$(VENV_BIN)/ruff check .

format:
	$(VENV_BIN)/ruff format .

format-check:
	$(VENV_BIN)/ruff format --check .

test:
	$(VENV_BIN)/pytest

run:
	$(VENV_BIN)/uvicorn app.main:create_app --factory --host "$${HOST:-127.0.0.1}" --port "$${PORT:-8000}" --reload

health:
	curl -fsS "http://$${HOST:-127.0.0.1}:$${PORT:-8000}/health"

check: lint format-check test
