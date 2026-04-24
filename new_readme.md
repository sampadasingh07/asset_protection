
FROM python:3.11-slim

# ── System dependencies ───────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        # Playwright / Chromium runtime deps
        libnss3 libnspr4 libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 \
        libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
        libxfixes3 libxrandr2 libgbm1 libasound2 libpango-1.0-0 \
        libpangocairo-1.0-0 libx11-xcb1 libxcb-dri3-0 \
        # General build / network utilities
        curl ca-certificates gcc \
    && rm -rf /var/lib/apt/lists/*

# ── Python dependencies ───────────────────────────────────────────────────────
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Playwright: install Chromium browser + its own OS deps ────────────────────
RUN playwright install chromium \
    && playwright install-deps chromium

# ── Application code ──────────────────────────────────────────────────────────
COPY . /app/workers/

# ── Runtime environment ───────────────────────────────────────────────────────
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    # Playwright uses this to locate the Chromium binary it downloaded
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Unprivileged user for security
RUN useradd --create-home --shell /bin/bash worker
USER worker

# ── Entrypoint ────────────────────────────────────────────────────────────────
CMD ["celery", "-A", "workers.tasks.celery_tasks", "worker", \
     "--loglevel=info", \
     "--queues=crawling,scoring,enforcement"]
