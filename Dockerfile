FROM python:3.9.6-slim-buster as vocabulary
LABEL maintainer="<kolobov.kirill@list.ru>"

ENV PYTHONUNBUFFERED 1

RUN apt-get update \
    && pip install poetry --no-cache-dir \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml /app
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev -n

COPY . /app
