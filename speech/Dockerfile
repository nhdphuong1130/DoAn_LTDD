FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY . /app/speech
ENV SPEECH_CACHE_DIR=/app/speech/.cache SPEECH_BIND_HOST=0.0.0.0
CMD ["python", "-m", "speech"]
