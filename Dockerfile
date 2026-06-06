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

# Create non-root user for security
RUN <<EOT
    useradd -m -u 1000 appuser
    chown -R appuser:appuser /app
EOT

USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
ENTRYPOINT ["uv", "run", "start"]
