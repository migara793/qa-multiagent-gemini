# Manual Implementation Guide - QA Multi-Agent System

This guide will walk you through implementing the QA Multi-Agent System step-by-step from scratch.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Phase 1: Project Setup](#phase-1-project-setup)
3. [Phase 2: Infrastructure Setup](#phase-2-infrastructure-setup)
4. [Phase 3: Shared Libraries](#phase-3-shared-libraries)
5. [Phase 4: Runner Service](#phase-4-runner-service)
6. [Phase 5: MCP Servers](#phase-5-mcp-servers)
7. [Phase 6: Test Agents](#phase-6-test-agents)
8. [Phase 7: Testing](#phase-7-testing)
9. [Phase 8: Next Steps](#phase-8-next-steps)

---

## Prerequisites

### Required Software

Install the following on your system:

```bash
# 1. Docker & Docker Compose
# Visit: https://docs.docker.com/get-docker/
docker --version  # Should be 24.0.0+
docker compose version  # Should be 2.20.0+

# 2. Python 3.10+
python3 --version  # Should be 3.10+
pip3 --version

# 3. Node.js 18+ (for Jest MCP server later)
node --version  # Should be 18.0.0+
npm --version

# 4. Git
git --version

# 5. curl (for testing)
curl --version
```

### Get API Keys

1. **Gemini API Key** (Required)
   - Visit: https://makersuite.google.com/app/apikey
   - Sign in with Google account
   - Click "Create API Key"
   - Copy the key (you'll use it later)

2. **GitHub Token** (Optional, for later)
   - Visit: https://github.com/settings/tokens
   - Generate new token with `repo` scope

---

## Phase 1: Project Setup

### Step 1.1: Create Project Directory

```bash
# Create main project directory
mkdir qa-multiagent-gemini
cd qa-multiagent-gemini

# Create all subdirectories
mkdir -p runner/orchestrator
mkdir -p agents/{unit-test-agent,integration-test-agent,e2e-test-agent}
mkdir -p agents/{performance-test-agent,security-test-agent,code-review-agent}
mkdir -p agents/{test-analyzer-agent,bug-detector-agent,report-generator-agent,regression-agent}
mkdir -p mcp-servers/{test-strategy-server,test-generation-server,bug-detection-server}
mkdir -p mcp-servers/{auto-fix-server,code-analyzer-server,test-analysis-server}
mkdir -p mcp-servers/{metrics-server,jest-server,playwright-server,k6-server}/tools
mkdir -p infrastructure/{postgres,redis,rabbitmq,monitoring/prometheus,monitoring/grafana/dashboards}
mkdir -p shared tests/{unit,integration,e2e} scripts docs/{api,mcp-servers,agents}
mkdir -p logs reports results

# Verify structure
ls -la
```

### Step 1.2: Initialize Git

```bash
git init
```

### Step 1.3: Create .gitignore

Create `.gitignore` file:

```bash
cat > .gitignore << 'EOF'
# Environment variables
.env

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
venv/
ENV/
env/

# Testing
.pytest_cache/
.coverage
htmlcov/
*.log
test-results/
results/
reports/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Docker
*.pid
*.sock

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Logs
logs/
*.log

# Database
*.db
*.sqlite
*.sqlite3

# Temporary files
tmp/
temp/
*.tmp

# OS
Thumbs.db
EOF
```

### Step 1.4: Create Environment Template

Create `.env.example`:

```bash
cat > .env.example << 'EOF'
# QA Multi-Agent System Environment Configuration

# =============================================================================
# GEMINI AI CONFIGURATION
# Get your API key from: https://makersuite.google.com/app/apikey
# =============================================================================
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp

# =============================================================================
# GITHUB CONFIGURATION
# =============================================================================
GITHUB_TOKEN=your_github_token_here
GITHUB_REPO_URL=https://github.com/your-org/your-repo

# =============================================================================
# DATABASE CONFIGURATION (PostgreSQL)
# =============================================================================
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_EXTERNAL_PORT=5433
POSTGRES_DB=qa_multiagent
POSTGRES_USER=qauser
POSTGRES_PASSWORD=qapassword123

# =============================================================================
# REDIS CONFIGURATION
# =============================================================================
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_EXTERNAL_PORT=6380
REDIS_PASSWORD=redispassword123

# =============================================================================
# RABBITMQ CONFIGURATION
# =============================================================================
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=qarabbit
RABBITMQ_PASSWORD=rabbitpassword123

# =============================================================================
# RUNNER PORT
# =============================================================================
RUNNER_PORT=8080

# =============================================================================
# QUALITY GATE THRESHOLDS
# =============================================================================
MIN_CODE_COVERAGE=80.0
MAX_FAILED_TESTS=0
MAX_CRITICAL_VULNERABILITIES=0
MIN_PASS_RATE=95.0

# =============================================================================
# LOGGING
# =============================================================================
LOG_LEVEL=INFO
LOG_FORMAT=json

# =============================================================================
# SYSTEM CONFIGURATION
# =============================================================================
DEBUG=false
ENVIRONMENT=development
MAX_RETRY_ATTEMPTS=3
EOF
```

### Step 1.5: Create Your .env File

```bash
# Copy template
cp .env.example .env

# Edit with your actual API key
nano .env  # or use vim, code, etc.

# Make sure to replace:
# GEMINI_API_KEY=your_gemini_api_key_here
# with your actual key from Google
```

---

## Phase 2: Infrastructure Setup

### Step 2.1: Create PostgreSQL Initialization Script

Create `infrastructure/postgres/init.sql`:

```bash
cat > infrastructure/postgres/init.sql << 'EOF'
-- QA Multi-Agent System Database Schema

CREATE TABLE IF NOT EXISTS executions (
    id VARCHAR(36) PRIMARY KEY,
    commit_sha VARCHAR(40) NOT NULL,
    branch VARCHAR(255) NOT NULL,
    pull_request_id VARCHAR(50),
    repo_url VARCHAR(500) NOT NULL,
    trigger_type VARCHAR(20) NOT NULL,
    author VARCHAR(255),
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    execution_time FLOAT,
    result JSONB,
    error TEXT
);

CREATE TABLE IF NOT EXISTS test_results (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(36) REFERENCES executions(id) ON DELETE CASCADE,
    agent_name VARCHAR(50) NOT NULL,
    test_type VARCHAR(20) NOT NULL,
    total_tests INTEGER DEFAULT 0,
    passed_tests INTEGER DEFAULT 0,
    failed_tests INTEGER DEFAULT 0,
    duration FLOAT,
    results JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS metrics (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(36) REFERENCES executions(id) ON DELETE CASCADE,
    metric_name VARCHAR(50) NOT NULL,
    metric_value FLOAT NOT NULL,
    metric_unit VARCHAR(20),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bugs (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(36) REFERENCES executions(id) ON DELETE CASCADE,
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    file_path VARCHAR(500),
    line_number INTEGER,
    root_cause TEXT,
    suggested_fix TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS quality_gates (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(36) REFERENCES executions(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL,
    passed BOOLEAN DEFAULT FALSE,
    coverage FLOAT,
    pass_rate FLOAT,
    failed_tests INTEGER,
    critical_vulnerabilities INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_executions_commit ON executions(commit_sha);
CREATE INDEX IF NOT EXISTS idx_executions_branch ON executions(branch);
CREATE INDEX IF NOT EXISTS idx_executions_status ON executions(status);
CREATE INDEX IF NOT EXISTS idx_test_results_execution ON test_results(execution_id);
CREATE INDEX IF NOT EXISTS idx_metrics_execution ON metrics(execution_id);
CREATE INDEX IF NOT EXISTS idx_bugs_execution ON bugs(execution_id);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO qauser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO qauser;
EOF
```

### Step 2.2: Create Docker Compose File

Create `docker-compose.yml`:

```bash
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: qa-postgres
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-qa_multiagent}
      POSTGRES_USER: ${POSTGRES_USER:-qauser}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-qapassword123}
    ports:
      - "${POSTGRES_EXTERNAL_PORT:-5433}:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./infrastructure/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - qa-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-qauser}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: qa-redis
    command: redis-server --requirepass ${REDIS_PASSWORD:-redispassword123}
    ports:
      - "${REDIS_EXTERNAL_PORT:-6380}:6379"
    volumes:
      - redis-data:/data
    networks:
      - qa-network
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  rabbitmq:
    image: rabbitmq:3-management-alpine
    container_name: qa-rabbitmq
    environment:
      RABBITMQ_DEFAULT_USER: ${RABBITMQ_USER:-qarabbit}
      RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASSWORD:-rabbitpassword123}
    ports:
      - "5672:5672"
      - "15672:15672"
    networks:
      - qa-network
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  runner:
    build:
      context: .
      dockerfile: ./runner/Dockerfile
    container_name: qa-runner
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - GEMINI_MODEL=${GEMINI_MODEL:-gemini-2.0-flash-exp}
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - POSTGRES_DB=${POSTGRES_DB:-qa_multiagent}
      - POSTGRES_USER=${POSTGRES_USER:-qauser}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-qapassword123}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_PASSWORD=${REDIS_PASSWORD:-redispassword123}
      - RABBITMQ_HOST=rabbitmq
      - RABBITMQ_PORT=5672
      - RABBITMQ_USER=${RABBITMQ_USER:-qarabbit}
      - RABBITMQ_PASSWORD=${RABBITMQ_PASSWORD:-rabbitpassword123}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - LOG_FORMAT=${LOG_FORMAT:-json}
      - MIN_CODE_COVERAGE=${MIN_CODE_COVERAGE:-80.0}
      - MAX_FAILED_TESTS=${MAX_FAILED_TESTS:-0}
      - MAX_CRITICAL_VULNERABILITIES=${MAX_CRITICAL_VULNERABILITIES:-0}
      - MIN_PASS_RATE=${MIN_PASS_RATE:-95.0}
      - ENVIRONMENT=${ENVIRONMENT:-development}
      - DEBUG=${DEBUG:-false}
    ports:
      - "${RUNNER_PORT:-8080}:8000"
    volumes:
      - ./runner:/app/runner
      - ./shared:/app/shared
      - test-results:/app/results
      - reports:/app/reports
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy
      test-strategy-server:
        condition: service_started
    networks:
      - qa-network
    restart: unless-stopped

  test-strategy-server:
    build:
      context: .
      dockerfile: ./mcp-servers/test-strategy-server/Dockerfile
    container_name: mcp-test-strategy
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - GEMINI_MODEL=${GEMINI_MODEL:-gemini-2.0-flash-exp}
      - MCP_PORT=3005
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    ports:
      - "3005:3005"
    volumes:
      - ./mcp-servers/test-strategy-server:/app
      - ./shared:/app/shared
    networks:
      - qa-network
    restart: unless-stopped

  unit-test-agent:
    build:
      context: .
      dockerfile: ./agents/unit-test-agent/Dockerfile
    container_name: qa-unit-test-agent
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_PASSWORD=${REDIS_PASSWORD:-redispassword123}
      - RABBITMQ_HOST=rabbitmq
      - RABBITMQ_PORT=5672
      - RABBITMQ_USER=${RABBITMQ_USER:-qarabbit}
      - RABBITMQ_PASSWORD=${RABBITMQ_PASSWORD:-rabbitpassword123}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    volumes:
      - ./agents/unit-test-agent:/app
      - ./shared:/app/shared
      - test-results:/app/results
    depends_on:
      - redis
      - rabbitmq
    networks:
      - qa-network
    restart: unless-stopped

networks:
  qa-network:
    driver: bridge
    name: qa-network

volumes:
  postgres-data:
    name: qa-postgres-data
  redis-data:
    name: qa-redis-data
  test-results:
    name: qa-test-results
  reports:
    name: qa-reports
EOF
```

---

## Phase 3: Shared Libraries

### Step 3.1: Create Shared __init__.py

```bash
cat > shared/__init__.py << 'EOF'
"""
Shared libraries for QA Multi-Agent System
"""
__version__ = "1.0.0"
EOF
```

### Step 3.2: Create Logger

Create `shared/logger.py`:

```python
cat > shared/logger.py << 'EOF'
"""
Structured logging configuration
"""
import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict
import os


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logger(name: str, level: str = None) -> logging.Logger:
    """Setup structured logger"""
    logger = logging.getLogger(name)

    log_level = level or os.getenv("LOG_LEVEL", "INFO")
    logger.setLevel(getattr(logging, log_level.upper()))

    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)

    log_format = os.getenv("LOG_FORMAT", "standard")

    if log_format == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False

    return logger
EOF
```

### Step 3.3: Create Config Manager

Create `shared/config.py`:

```python
# This file is quite long - see the actual implementation in the repository
# Key points to implement:
# 1. Use pydantic-settings BaseSettings
# 2. Define all environment variables
# 3. Add validators for required fields
# 4. Create helper properties (database_url, redis_url, etc.)
```

**Note**: Copy the full `shared/config.py` from the generated files or refer to the complete codebase.

### Step 3.4: Create State Manager

Create `shared/state_manager.py`:

```python
# See the full implementation in the repository
# Key components:
# 1. Redis async client setup
# 2. get/set/delete methods
# 3. Hash operations for agent status
# 4. JSON serialization
```

### Step 3.5: Create MCP Client

Create `shared/mcp_client.py`:

```python
# See the full implementation
# Key features:
# 1. HTTP client for MCP servers
# 2. call_tool method
# 3. list_tools, list_resources methods
# 4. Error handling
```

### Step 3.6: Create Data Models

Create `shared/models.py`:

```python
# See the full implementation
# Define Pydantic models for:
# 1. TriggerPayload
# 2. ExecutionState
# 3. TestResults
# 4. QualityGate
# 5. AgentMessage
# etc.
```

---

## Phase 4: Runner Service

### Step 4.1: Create Runner Requirements

Create `runner/requirements.txt`:

```bash
cat > runner/requirements.txt << 'EOF'
# Core Framework
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
pydantic-settings>=2.1.0

# Google AI
google-generativeai>=0.3.0

# Database
psycopg2-binary>=2.9.9
sqlalchemy>=2.0.23

# Cache & Queue
redis>=5.0.1
pika>=1.3.2

# HTTP Client
httpx>=0.25.2

# Utilities
python-dotenv>=1.0.0
EOF
```

### Step 4.2: Create Runner Dockerfile

Create `runner/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY runner/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy shared libraries
COPY shared /app/shared

# Copy runner application
COPY runner /app/runner

# Set working directory
WORKDIR /app/runner

# Create directories
RUN mkdir -p /app/results /app/reports /app/logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run
CMD ["python", "main.py"]
```

### Step 4.3: Create Main Runner Application

Create `runner/main.py`:

**This is a large file - see the full implementation in the repository**

Key sections to implement:
1. FastAPI app setup with lifespan
2. `/trigger` endpoint
3. `/status/{execution_id}` endpoint
4. `/health` endpoint
5. Background task processing
6. State manager integration

### Step 4.4: Create Orchestrator Agent

Create `runner/orchestrator/orchestrator_agent.py`:

**See full implementation in repository**

Key methods:
1. `initialize()` - Setup Gemini and MCP clients
2. `execute()` - Main pipeline orchestration
3. `_analyze_and_strategize()` - Use Gemini for strategy
4. `_execute_parallel_tests()` - Trigger test agents
5. `_evaluate_quality_gate()` - Make pass/fail decision

---

## Phase 5: MCP Servers

### Step 5.1: Test Strategy Server

Create `mcp-servers/test-strategy-server/requirements.txt`:

```bash
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
google-generativeai>=0.3.0
pydantic>=2.5.0
python-dotenv>=1.0.0
```

Create `mcp-servers/test-strategy-server/Dockerfile`:

```dockerfile
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

# Copy server
COPY mcp-servers/test-strategy-server/server.py /app/server.py

EXPOSE 3005

CMD ["python", "server.py"]
```

Create `mcp-servers/test-strategy-server/server.py`:

**See full implementation - Key features:**
1. FastAPI app for MCP protocol
2. `/mcp/call-tool` endpoint
3. `generate_strategy` tool using Gemini
4. `/mcp/list-tools` endpoint
5. Health check endpoint

---

## Phase 6: Test Agents

### Step 6.1: Unit Test Agent

Create `agents/unit-test-agent/requirements.txt`:

```bash
redis>=5.0.1
pika>=1.3.2
httpx>=0.25.2
python-dotenv>=1.0.0
```

Create `agents/unit-test-agent/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY agents/unit-test-agent/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY shared /app/shared
COPY agents/unit-test-agent/agent.py /app/agent.py

CMD ["python", "agent.py"]
```

Create `agents/unit-test-agent/agent.py`:

**See full implementation - Key features:**
1. Redis connection for state
2. Main execution loop
3. Mock test execution
4. Update state with results

---

## Phase 7: Testing

### Step 7.1: Build and Start Infrastructure

```bash
# Start infrastructure services first
docker compose up -d postgres redis rabbitmq

# Wait for them to be healthy (check with)
docker compose ps

# You should see all 3 services as "healthy"
```

### Step 7.2: Build Application Services

```bash
# Build all services
docker compose build

# This will take 5-10 minutes
# It downloads Python packages, Gemini SDK, etc.
```

### Step 7.3: Start All Services

```bash
# Start everything
docker compose up -d

# Check status
docker compose ps

# All services should show "Up" or "Up (healthy)"
```

### Step 7.4: Test the System

```bash
# 1. Check health
curl http://localhost:8080/health

# 2. Trigger a pipeline
curl -X POST http://localhost:8080/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "trigger_type": "pull_request",
    "repo_url": "https://github.com/test/repo",
    "branch": "feature/test",
    "commit_sha": "abc123",
    "pull_request_id": "1",
    "author": "your_name"
  }'

# You'll get back an execution_id

# 3. Wait 15 seconds, then check status
curl http://localhost:8080/status/EXECUTION_ID | python3 -m json.tool

# Replace EXECUTION_ID with the actual ID from step 2
```

### Step 7.5: View Logs

```bash
# All services
docker compose logs -f

# Just runner
docker compose logs -f runner

# Just one agent
docker compose logs -f unit-test-agent

# Just MCP server
docker compose logs -f test-strategy-server
```

---

## Phase 8: Next Steps

### Add More Agents

To add Integration Test Agent:

1. Create directory: `agents/integration-test-agent/`
2. Copy structure from unit-test-agent
3. Modify logic for integration testing
4. Add to docker-compose.yml
5. Rebuild and restart

### Add More MCP Servers

To add Jest Server (Node.js):

1. Create `mcp-servers/jest-server/`
2. Create `package.json` with Jest dependencies
3. Create `server.js` with Express + Jest execution
4. Create Dockerfile (use `FROM node:18-alpine`)
5. Add to docker-compose.yml

### Add Monitoring

1. Add Prometheus service to docker-compose.yml
2. Add Grafana service
3. Configure Prometheus to scrape metrics
4. Create Grafana dashboards

### Connect to Real GitHub

1. Set up webhook in GitHub repo settings
2. Point webhook to your runner URL
3. Add GitHub token to .env
4. Implement GitHub PR status updates

---

## Troubleshooting

### Port Conflicts

If you get "port already in use" errors:

```bash
# Find what's using the port
sudo lsof -i :8080  # or whatever port

# Either stop that service, or change the port in .env
# For example:
RUNNER_PORT=8081
POSTGRES_EXTERNAL_PORT=5434
REDIS_EXTERNAL_PORT=6381
```

### Docker Build Fails

```bash
# Clean everything and rebuild
docker compose down -v
docker system prune -a
docker compose build --no-cache
```

### Services Won't Start

```bash
# Check logs
docker compose logs

# Restart specific service
docker compose restart runner

# Rebuild and restart
docker compose build runner
docker compose up -d runner
```

### Gemini API Errors

```bash
# Verify your API key is set
docker compose exec runner env | grep GEMINI

# Test API key manually
curl -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key=YOUR_API_KEY"
```

### Redis Connection Failed

```bash
# Check Redis is running
docker compose ps redis

# Test connection
docker compose exec redis redis-cli -a redispassword123 ping
# Should return: PONG

# Check password matches in .env
```

---

## Complete Implementation Checklist

- [ ] ✅ Phase 1: Project Setup (directories, .env, .gitignore)
- [ ] ✅ Phase 2: Infrastructure (docker-compose.yml, postgres init)
- [ ] ✅ Phase 3: Shared Libraries (logger, config, state manager, MCP client, models)
- [ ] ✅ Phase 4: Runner Service (FastAPI app, orchestrator agent)
- [ ] ✅ Phase 5: MCP Servers (test-strategy-server)
- [ ] ✅ Phase 6: Test Agents (unit-test-agent)
- [ ] ✅ Phase 7: Testing (build, start, test)
- [ ] ⬜ Phase 8: Add more agents (integration, e2e, etc.)
- [ ] ⬜ Phase 9: Add monitoring (Prometheus, Grafana)
- [ ] ⬜ Phase 10: GitHub integration

---

## Time Estimate

- **Phase 1-2**: 1-2 hours (setup and infrastructure)
- **Phase 3**: 2-3 hours (shared libraries)
- **Phase 4**: 3-4 hours (runner and orchestrator)
- **Phase 5**: 1-2 hours (MCP server)
- **Phase 6**: 1-2 hours (test agent)
- **Phase 7**: 1 hour (testing and debugging)

**Total**: 10-15 hours for MVP

**Full System** (all agents, monitoring, etc.): 40-60 hours

---

## Resources

### Official Documentation Used

1. **FastAPI**: https://fastapi.tiangolo.com/
2. **Gemini AI**: https://ai.google.dev/gemini-api/docs
3. **Docker Compose**: https://docs.docker.com/compose/
4. **Pydantic**: https://docs.pydantic.dev/
5. **Redis**: https://redis.io/docs/
6. **PostgreSQL**: https://www.postgresql.org/docs/
7. **MCP**: https://modelcontextprotocol.io/

### Learning Resources

1. **FastAPI Tutorial**: https://fastapi.tiangolo.com/tutorial/
2. **Docker Tutorial**: https://docs.docker.com/get-started/
3. **Gemini Quickstart**: https://ai.google.dev/gemini-api/docs/quickstart
4. **Multi-Agent Systems**: Research papers on AI agent orchestration

---

## Support

If you get stuck:

1. Check the logs: `docker compose logs -f`
2. Verify environment variables: `docker compose exec runner env`
3. Test individual components separately
4. Check official documentation
5. Review the complete working code in the repository

---

**Good luck with your implementation!** 🚀

This system demonstrates cutting-edge technologies and is perfect for your university research project.
