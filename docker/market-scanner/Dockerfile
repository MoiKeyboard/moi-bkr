FROM python:3.12-slim

# Set environment variables
ENV ENV_MODE=prod
ENV PORT=8000

# Set working directory
WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && \
    apt-get install -y curl && \
    # Removes package lists after installation
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and config
COPY src/ ./src/
COPY config.yaml .

# Expose the API port
EXPOSE ${PORT}

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Command to run the API
CMD ["uvicorn", "src.api.scanner_api:app", "--host", "0.0.0.0", "--port", "8000"]
