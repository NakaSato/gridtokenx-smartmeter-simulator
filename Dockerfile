# Stage 1: Build frontend assets
FROM node:20-slim AS frontend-builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy frontend source code
COPY vite.config.js postcss.config.js tailwind.config.js ./
COPY src/static ./src/static

# Build frontend
RUN npm run build

# Stage 2: Python runtime
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
COPY pyproject.toml .
RUN touch README.md

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir jinja2>=3.1.0

# Copy source code
COPY src/ ./src/

# Install the package in editable mode (requires source)
RUN pip install --no-cache-dir -e .

# Copy built frontend assets from builder stage
# The build output goes to ../../dist/static relative to src/static, so it's at /app/dist/static in the builder
# We need to copy it to /app/src/static in the final image
COPY --from=frontend-builder /app/dist/static/ ./src/static/

# Create directories for data and logs
RUN mkdir -p data logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set PYTHONPATH to include src directory
ENV PYTHONPATH=/app/src:$PYTHONPATH

# Run the application with uvicorn
CMD ["python", "-m", "uvicorn", "smart_meter_simulator.app:app", "--host", "0.0.0.0", "--port", "8000"]
