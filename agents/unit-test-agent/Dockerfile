FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY agents/unit-test-agent/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy shared libraries
COPY shared /app/shared

# Copy agent application
COPY agents/unit-test-agent/agent.py /app/agent.py

# Run agent
CMD ["python", "agent.py"]
