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

