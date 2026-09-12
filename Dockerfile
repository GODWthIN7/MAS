FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /code

COPY pyproject.toml /code/
COPY README.md /code/
COPY app /code/app

FROM base AS test

RUN pip install --no-cache-dir ".[dev]"

COPY tests /code/tests

CMD ["pytest"]

FROM base AS runtime

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
