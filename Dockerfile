FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /code

COPY pyproject.toml /code/
COPY .env.example /code/
COPY README.md /code/

FROM base AS test

COPY app /code/app
COPY tests /code/tests

RUN pip install --no-cache-dir ".[dev]"

CMD ["pytest"]

FROM base AS runtime

COPY app /code/app

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
