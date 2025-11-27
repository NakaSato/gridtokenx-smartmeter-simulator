# Use Python 3.11 slim image
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
COPY README.md .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir jinja2>=3.1.0
RUN pip install --no-cache-dir -e .

# Copy source code (only existing directories)
COPY src/ ./src/
COPY templates/ ./templates/

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
