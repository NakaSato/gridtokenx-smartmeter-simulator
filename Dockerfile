# syntax=docker/dockerfile:1
# Stage 1: Build UI
FROM oven/bun:1 AS ui-builder

WORKDIR /app/ui

# Copy package files
COPY frontend/package.json frontend/bun.lock* ./

# Install dependencies with cache mount
RUN --mount=type=cache,target=/root/.bun/install/cache \
    bun install --frozen-lockfile

# Copy UI source
COPY frontend/ .

# Build UI (Next.js build)
RUN bun x next build

# Stage 2: Python Backend
FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install system dependencies with cache mount
RUN <<EOT
    apt-get update
    apt-get install -y --no-install-recommends gcc curl
EOT

# Set working directory
WORKDIR /app

# Copy project files from backend
COPY backend/pyproject.toml backend/uv.lock ./

# Install Python dependencies with uv cache mount
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

# Copy application source from backend
COPY backend/src/ ./src/

# Copy built UI from builder
COPY --from=ui-builder /app/ui/.next ./ui/.next
COPY --from=ui-builder /app/ui/public ./ui/public

# Copy other backend files
COPY backend/ .

# Install the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# InfluxDB run persistence (powers the /run plots). Off by default — enable at
# runtime and point at an InfluxDB 2.x instance, e.g.
#   docker run -e INFLUX_ENABLED=true -e INFLUX_URL=http://host.docker.internal:8086 \
#     -e INFLUX_TOKEN=<token> ...
# INFLUX_TOKEN is a secret and is intentionally NOT baked into the image; supply
# it at runtime. Standalone sim bucket — not the parent monorepo's InfluxDB.
ENV INFLUX_ENABLED=false \
    INFLUX_URL=http://localhost:8086 \
    INFLUX_ORG=gridtokenx \
    INFLUX_BUCKET=smartmeter_sim \
    INFLUX_MEASUREMENT=meter_reading \
    INFLUX_PERSIST_EVERY=1

# Create non-root user for security
RUN <<EOT
    useradd -m -u 1000 appuser
    chown -R appuser:appuser /app
EOT

USER appuser

# Expose port (app reads PORT, default 8082)
EXPOSE 8082

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f "http://localhost:${PORT:-8082}/api/v1/quality/health" || exit 1

# Run the application.
#
# `--no-sync` is load-bearing for the dev loop: deps + the project are already
# installed into the image's venv at build time (the `uv sync` layers above), so
# a plain `uv run` would needlessly re-sync on every boot. With the source
# bind-mounted at runtime (compose), that re-sync rebuilds the editable package
# (`Failed to build smart-meter-simulator @ file:///app`), which fetches build
# deps from PyPI — slow, and a flaky network leaves the container restart-looping.
# `--no-sync` skips that: the venv is used as-is and bind-mounted code edits are
# still picked up on restart (no rebuild, no network).
ENV UV_NO_SYNC=1
ENTRYPOINT ["uv", "run", "--no-sync", "start"]
