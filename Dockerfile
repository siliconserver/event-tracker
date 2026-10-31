# Event-Tracker – schlankes Image für die Synology DS420+ (x86_64)
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/data \
    PHOTO_ROOT=/photos

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Läuft ohne Root. UID/GID lassen sich in docker-compose über "user:" an den NAS-Benutzer anpassen.
RUN useradd --uid 1000 --create-home tracker && mkdir -p /data /photos && chown tracker /data
USER tracker

VOLUME ["/data"]
EXPOSE 8000
HEALTHCHECK --interval=60s --timeout=5s --start-period=20s \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health').status==200 else 1)"

CMD ["uvicorn", "app.main:get_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
