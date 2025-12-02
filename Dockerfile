# ==============================================================================
# IU Studiennavigator - Production Dockerfile
# ==============================================================================
# Multi-stage build für optimierte Image-Größe
# ==============================================================================

FROM python:3.12-slim as builder

# Build-Dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies installieren
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ==============================================================================
# Production Stage
# ==============================================================================

FROM python:3.12-slim

# Metadata
LABEL maintainer="teresa.ignatzek@iu-study.org"
LABEL description="IU Studiennavigator - Student Progress Management System"
LABEL version="1.0.0"

# Non-root user erstellen
RUN useradd -m -u 1000 appuser

# Arbeitsverzeichnis
WORKDIR /app

# Python dependencies von builder stage kopieren
COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH

# Application code kopieren
COPY --chown=appuser:appuser . .

# Data-Verzeichnis für SQLite DB
RUN mkdir -p /app/data && chown appuser:appuser /app/data

# Wechsel zu non-root user
USER appuser

# Port exposieren
EXPOSE 5000

# Health check endpoint (optional, aber empfohlen)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/')" || exit 1

# Produktions-Server (Gunicorn empfohlen statt Flask dev server)
# Falls Gunicorn nicht in requirements.txt: pip install gunicorn
# CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "app:app"]

# Für Demo/Development: Flask dev server
CMD ["python", "app.py"]