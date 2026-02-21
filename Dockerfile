# ── Build stage ───────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install dependencies into an isolated prefix so they can be copied cheaply
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from the build stage
COPY --from=builder /install /usr/local

# Copy application source
COPY . .

# SQLite database lives in a dedicated directory so it can be bind-mounted as a
# named volume without overwriting the rest of the application files.
RUN mkdir -p /data
ENV DB_PATH=/data/cves.db

# Run as a non-root user for better security
RUN useradd --no-create-home --shell /bin/false botuser \
    && chown -R botuser:botuser /app /data
USER botuser

CMD ["python", "main.py"]
