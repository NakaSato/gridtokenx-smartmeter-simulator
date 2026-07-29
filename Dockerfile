# syntax=docker/dockerfile:1
#
# Backend-only image. This built the Next.js UI and copied `.next`/`public` in
# until 2026-07-29, but nothing ever served them: `create_app()` mounts no
# StaticFiles and the image carries no Node runtime, so the Next.js server could
# not have run here anyway. The dashboard is its own image, built from
# `frontend/Dockerfile` (compose service `smartmeter-ui`).

# Stage 1: Build the Python venv.
#
# gcc is needed to compile wheels that ship no manylinux build, but it is ~150 MB
# and is dead weight at runtime — so it lives in this stage, which is discarded.
# Only the finished /app/.venv crosses into the runtime image.
FROM python:3.11-slim AS py-builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

RUN <<EOT
    apt-get update
    apt-get install -y --no-install-recommends gcc
    rm -rf /var/lib/apt/lists/*
EOT

WORKDIR /app

# Dependencies first, so a source-only change does not re-resolve them.
COPY backend/pyproject.toml backend/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

# Then the project itself. `readme` in pyproject points at README.md, so
# hatchling needs it present to build the wheel.
COPY backend/README.md ./
COPY backend/src/ ./src/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# Stage 2: Runtime.
FROM python:3.11-slim

# curl is for the HEALTHCHECK below; no compiler here.
#
# The appuser is created *before* anything lands in /app so that every COPY can
# use --chown. A trailing `chown -R /app` would instead rewrite ownership across
# the whole tree — venv included — and Docker stores that as a second full copy
# of every file it touches (~760 MB on this image).
RUN <<EOT
    apt-get update
    apt-get install -y --no-install-recommends curl
    rm -rf /var/lib/apt/lists/*
    useradd -m -u 1000 appuser
EOT

# uv only — uvx is a separate ~22 MB binary and the entrypoint never calls it.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

WORKDIR /app

COPY --from=py-builder --chown=appuser:appuser /app/.venv ./.venv

# Backend source. The venv's editable install resolves to /app/src, so this must
# land at the same path the builder used.
COPY --chown=appuser:appuser backend/ .

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
