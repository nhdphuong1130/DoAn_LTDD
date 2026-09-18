FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .

COPY docker/entrypoint.sh /usr/local/bin/english7-entrypoint
RUN chmod +x /usr/local/bin/english7-entrypoint

ENTRYPOINT ["english7-entrypoint"]
CMD ["uvicorn", "english7.main:app", "--host", "0.0.0.0", "--port", "8000"]
