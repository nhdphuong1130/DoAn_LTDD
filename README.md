# English 7 GraphRAG

API-first learning application grounded exclusively in verified content from
*Tiếng Anh 7 – Global Success* Unit 1 and Unit 2.

## Current development command

```bash
docker run --rm -v "$PWD/backend:/app" -w /app python:3.12-slim \
  sh -c "pip install -e '.[test]' && pytest -q"
```

Infrastructure and Android Studio instructions are added incrementally as the
corresponding components become executable.

## Docker configuration

Copy `.env.example` to `.env`, replace every local example credential, then run:

```bash
docker compose config --quiet
docker compose up --build
```

Do not commit `.env`. All ports, image tags, credentials, bucket names, and
service-facing settings are supplied through environment variables.
