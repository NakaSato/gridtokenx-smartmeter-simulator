# Stage 1: Build UI
FROM oven/bun:1 AS ui-builder

WORKDIR /app/ui

# Copy package files
COPY frontend/package.json frontend/bun.lock* ./

# Install dependencies
RUN bun install --frozen-lockfile

# Copy UI source
COPY frontend/ .

# Build UI (Next.js build)
RUN bun x next build

# Stage 2: Rust Simulator Engine
FROM rust:1.83-slim AS rust-builder
WORKDIR /build
RUN apt-get update && apt-get install -y python3 python3-dev
COPY backend/src/rust_sim ./rust_sim
RUN cd rust_sim && cargo build --release

# Stage 3: Python Backend
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

# Copy project files from backend
COPY backend/pyproject.toml backend/uv.lock ./

# Install Python dependencies
RUN uv sync --frozen --no-install-project

# Copy application source from backend
COPY backend/src/ ./src/

# Copy built Rust engine from rust-builder
# Note: Rename from libgridtokenx_sim.so to gridtokenx_sim.so for Python import
COPY --from=rust-builder /build/rust_sim/target/release/libgridtokenx_sim.so ./src/gridtokenx_sim.so

# Copy built UI from builder
COPY --from=ui-builder /app/ui/.next ./ui/.next
COPY --from=ui-builder /app/ui/public ./ui/public

# Copy other backend files
COPY backend/ .

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
ENTRYPOINT ["uv", "run", "start"]
