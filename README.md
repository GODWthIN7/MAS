# MAS

MAS is a FastAPI-based backend scaffold for the Multi Agent Development Team project. The repository is organized to keep API routes thin, configuration centralized, and project setup predictable for local development, Docker workflows, and CI.

## Project structure

```text
app/
  api/         # Route registration and HTTP endpoints
  core/        # Centralized settings and shared application wiring
  models/      # Domain models
  services/    # Business logic
tests/         # API and service tests
```

## Getting started

1. Create a virtual environment.
2. Copy the example environment file.
3. Install the project with development dependencies.

```bash
python -m venv .venv
source .venv/bin/activate
cp .env.example .env
pip install --upgrade pip
pip install .[dev]
```

## Run locally

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`, with the health endpoint at `/health`.

## Run with Docker

```bash
cp .env.example .env
docker compose up --build
```

To run the test stage inside Docker:

```bash
docker build --target test .
```

## Configuration

Application configuration is environment-variable based. Keep real secrets in your local `.env`, deployment platform settings, or a secret manager. Do not commit secrets to the repository.

Current variables:

- `APP_NAME`
- `APP_ENV`
- `DEBUG`
- `HOST`
- `PORT`

## Quality checks

```bash
ruff check .
pytest
```

## CI

GitHub Actions installs the project, runs Ruff, and executes the test suite on pushes and pull requests.
