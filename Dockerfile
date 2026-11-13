FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/

ENV PYTHONPATH=/app/src
CMD ["sh", "-c", "exec granian --interface asgi --host 0.0.0.0 --port \"${APP_PORT:-8080}\" energosbyt.main:app"]
