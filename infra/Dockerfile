FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md /app/
COPY apps /app/apps
COPY packages /app/packages
RUN pip install --no-cache-dir ".[dev]"

ENV PYTHONUNBUFFERED=1
