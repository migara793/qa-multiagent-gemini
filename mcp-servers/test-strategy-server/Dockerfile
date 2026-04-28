FROM python:3.11-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY mcp-servers/test-strategy-server/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy shared libraries
COPY shared /app/shared

# Copy server application
COPY mcp-servers/test-strategy-server/server.py /app/server.py

# Expose MCP port
EXPOSE 3005

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
  CMD curl -f http://localhost:3005/health || exit 1

# Run server
CMD ["python", "server.py"]
