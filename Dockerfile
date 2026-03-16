# Stage 1: Build UI
FROM oven/bun:1 AS ui-builder

WORKDIR /app/ui

# Copy package files
COPY ui/package.json ui/bun.lock* ./

# Install dependencies
RUN bun install --frozen-lockfile

# Copy UI source
COPY ui/ .

# Build UI
RUN bun run build

# Stage 2: Python Backend
FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock ./

# Install Python dependencies
RUN uv sync --frozen --no-install-project

# Copy application source
COPY src/ ./src/

# Copy built UI from builder
COPY --from=ui-builder /app/ui/dist ./ui/dist

# Copy project files
COPY . .

# Install the project
RUN uv sync --frozen

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
ENTRYPOINT ["uv", "run", "start-simulator"]
