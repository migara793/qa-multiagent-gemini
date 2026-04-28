FROM python:3.11-slim

WORKDIR /app

# Install git (required for analysis)
RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY analyzer.py .
COPY api.py .

# Expose port
EXPOSE 8001

# Run the API server
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8001"]
