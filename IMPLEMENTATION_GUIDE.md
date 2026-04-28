# QA Multi-Agent System - Complete Implementation Guide

## Table of Contents
1. [Project Overview](#project-overview)
2. [Prerequisites](#prerequisites)
3. [Project Structure](#project-structure)
4. [Environment Setup](#environment-setup)
5. [Docker Compose Architecture](#docker-compose-architecture)
6. [Step-by-Step Implementation](#step-by-step-implementation)
7. [Testing & Validation](#testing--validation)
8. [Deployment](#deployment)
9. [Troubleshooting](#troubleshooting)

---

## Project Overview

A production-ready Quality Assurance system using:
- **Google ADK (Agent Development Kit)** for multi-agent orchestration
- **Gemini AI** for intelligent test generation and analysis
- **MCP (Model Context Protocol)** for tool integration
- **Docker Compose** for microservices deployment

### System Components
- 1 Runner/Orchestrator service
- 6 Parallel test agent services
- 3 Sequential analysis agent services
- 1 Regression/loop agent service
- 15+ MCP server microservices
- Supporting infrastructure (databases, monitoring)

---

## Prerequisites

### Required Software
```bash
# Verify installations
docker --version          # >= 24.0.0
docker-compose --version  # >= 2.20.0
python --version          # >= 3.10
node --version            # >= 18.0.0
git --version             # >= 2.30.0
```

### API Keys & Credentials
- Google Gemini API Key: https://makersuite.google.com/app/apikey
- GitHub Token (for git operations)
- SonarQube Token (optional)
- Snyk Token (optional)

### Hardware Requirements
- **Minimum**: 8GB RAM, 4 CPU cores, 50GB disk
- **Recommended**: 16GB RAM, 8 CPU cores, 100GB disk

---

## Project Structure

```
qa-multiagent-gemini/
├── docker-compose.yml                 # Main orchestration file
├── .env                               # Environment variables
├── .env.example                       # Template for environment vars
├── architecture.md                    # Architecture documentation
├── IMPLEMENTATION_GUIDE.md            # This file
├── README.md                          # Project overview
│
├── runner/                            # ADK Runner Service
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                        # Entry point
│   ├── config.py                      # Configuration
│   └── orchestrator/
│       ├── __init__.py
│       ├── orchestrator_agent.py      # Main orchestrator
│       └── strategy.py                # Test strategy logic
│
├── agents/                            # Agent Services
│   ├── unit-test-agent/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── agent.py
│   │   └── test_executor.py
│   │
│   ├── integration-test-agent/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── agent.py
│   │
│   ├── e2e-test-agent/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── agent.py
│   │
│   ├── performance-test-agent/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── agent.py
│   │
│   ├── security-test-agent/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── agent.py
│   │
│   ├── code-review-agent/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── agent.py
│   │
│   ├── test-analyzer-agent/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── agent.py
│   │
│   ├── bug-detector-agent/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── agent.py
│   │
│   ├── report-generator-agent/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── agent.py
│   │
│   └── regression-agent/
│       ├── Dockerfile
│       ├── requirements.txt
│       └── agent.py
│
├── mcp-servers/                       # Custom MCP Servers
│   ├── test-strategy-server/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── server.py                  # MCP server implementation
│   │   └── tools/
│   │       ├── __init__.py
│   │       ├── impact_analysis.py
│   │       └── test_selection.py
│   │
│   ├── test-generation-server/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── server.py
│   │
│   ├── bug-detection-server/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── server.py
│   │
│   ├── auto-fix-server/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── server.py
│   │
│   ├── code-analyzer-server/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── server.py
│   │
│   ├── test-analysis-server/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── server.py
│   │
│   ├── metrics-server/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── server.py
│   │
│   ├── jest-server/
│   │   ├── Dockerfile
│   │   ├── package.json
│   │   └── server.js
│   │
│   ├── playwright-server/
│   │   ├── Dockerfile
│   │   ├── package.json
│   │   └── server.js
│   │
│   └── k6-server/
│       ├── Dockerfile
│       └── server.go
│
├── infrastructure/                    # Supporting Services
│   ├── postgres/
│   │   ├── Dockerfile
│   │   └── init.sql
│   │
│   ├── redis/
│   │   └── redis.conf
│   │
│   ├── rabbitmq/
│   │   └── rabbitmq.conf
│   │
│   └── monitoring/
│       ├── prometheus/
│       │   ├── prometheus.yml
│       │   └── rules.yml
│       │
│       └── grafana/
│           ├── dashboards/
│           │   ├── qa-overview.json
│           │   └── test-metrics.json
│           └── datasources.yml
│
├── shared/                            # Shared Libraries
│   ├── __init__.py
│   ├── mcp_client.py                  # MCP client utilities
│   ├── state_manager.py               # Shared state management
│   ├── logger.py                      # Logging utilities
│   └── models.py                      # Data models
│
├── tests/                             # System Tests
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── scripts/                           # Utility Scripts
│   ├── setup.sh                       # Initial setup
│   ├── start.sh                       # Start all services
│   ├── stop.sh                        # Stop all services
│   ├── test.sh                        # Run tests
│   └── cleanup.sh                     # Cleanup resources
│
└── docs/                              # Documentation
    ├── api/                           # API documentation
    ├── mcp-servers/                   # MCP server specs
    └── agents/                        # Agent documentation
```

---

## Environment Setup

### 1. Create Environment File

```bash
# Copy example environment file
cp .env.example .env
```

### 2. Configure .env File

```env
# Gemini AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-pro

# GitHub Configuration
GITHUB_TOKEN=your_github_token_here
GITHUB_REPO_URL=https://github.com/your-org/your-repo

# Database Configuration
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=qa_multiagent
POSTGRES_USER=qauser
POSTGRES_PASSWORD=qapassword123

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=redispassword123

# RabbitMQ Configuration
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=qarabbit
RABBITMQ_PASSWORD=rabbitpassword123

# MCP Configuration
MCP_PROTOCOL_VERSION=1.0.0
MCP_TIMEOUT=30

# Quality Gate Thresholds
MIN_CODE_COVERAGE=80.0
MAX_FAILED_TESTS=0
MAX_CRITICAL_VULNERABILITIES=0
MIN_PASS_RATE=95.0

# Monitoring Configuration
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
GRAFANA_ADMIN_PASSWORD=admin123

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Resource Limits
MAX_PARALLEL_AGENTS=6
MAX_TEST_DURATION=3600
MAX_RETRY_ATTEMPTS=3

# SonarQube (Optional)
SONARQUBE_URL=http://sonarqube:9000
SONARQUBE_TOKEN=your_sonar_token

# Snyk (Optional)
SNYK_TOKEN=your_snyk_token

# Slack Notifications (Optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

---

## Docker Compose Architecture

### Service Categories

1. **Core Services** (Always running)
   - runner (ADK Engine)
   - postgres (Database)
   - redis (Cache/Queue)
   - rabbitmq (Message broker)

2. **Agent Services** (On-demand)
   - unit-test-agent
   - integration-test-agent
   - e2e-test-agent
   - performance-test-agent
   - security-test-agent
   - code-review-agent
   - test-analyzer-agent
   - bug-detector-agent
   - report-generator-agent
   - regression-agent

3. **MCP Server Services** (Always running)
   - test-strategy-server
   - test-generation-server
   - bug-detection-server
   - auto-fix-server
   - code-analyzer-server
   - jest-server
   - playwright-server
   - k6-server

4. **Monitoring Services** (Always running)
   - prometheus
   - grafana

### Network Architecture

```yaml
networks:
  qa-network:
    driver: bridge
  monitoring-network:
    driver: bridge
```

### Volume Strategy

```yaml
volumes:
  postgres-data:        # Persistent database
  redis-data:          # Persistent cache
  test-results:        # Test execution results
  reports:             # Generated reports
  grafana-data:        # Grafana dashboards
  prometheus-data:     # Metrics storage
```

---

## Step-by-Step Implementation

### Phase 1: Core Infrastructure Setup (Week 1)

#### Step 1.1: Initialize Project

```bash
# Create project directory
mkdir -p qa-multiagent-gemini
cd qa-multiagent-gemini

# Create all directories
mkdir -p runner/orchestrator
mkdir -p agents/{unit-test,integration-test,e2e-test,performance-test,security-test,code-review,test-analyzer,bug-detector,report-generator,regression}-agent
mkdir -p mcp-servers/{test-strategy,test-generation,bug-detection,auto-fix,code-analyzer,test-analysis,metrics,jest,playwright,k6}-server
mkdir -p infrastructure/{postgres,redis,rabbitmq,monitoring/prometheus,monitoring/grafana/dashboards}
mkdir -p shared tests/{unit,integration,e2e} scripts docs/{api,mcp-servers,agents}

# Initialize git
git init
```

#### Step 1.2: Create Docker Compose File

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  # ============================================================================
  # INFRASTRUCTURE SERVICES
  # ============================================================================

  postgres:
    image: postgres:15-alpine
    container_name: qa-postgres
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./infrastructure/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - qa-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: qa-redis
    command: redis-server --requirepass ${REDIS_PASSWORD}
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - qa-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  rabbitmq:
    image: rabbitmq:3-management-alpine
    container_name: qa-rabbitmq
    environment:
      RABBITMQ_DEFAULT_USER: ${RABBITMQ_USER}
      RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASSWORD}
    ports:
      - "5672:5672"
      - "15672:15672"  # Management UI
    networks:
      - qa-network
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ============================================================================
  # CORE RUNNER SERVICE
  # ============================================================================

  runner:
    build:
      context: ./runner
      dockerfile: Dockerfile
    container_name: qa-runner
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - GEMINI_MODEL=${GEMINI_MODEL}
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=${POSTGRES_PORT}
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - REDIS_HOST=redis
      - REDIS_PORT=${REDIS_PORT}
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - RABBITMQ_HOST=rabbitmq
      - RABBITMQ_PORT=${RABBITMQ_PORT}
      - RABBITMQ_USER=${RABBITMQ_USER}
      - RABBITMQ_PASSWORD=${RABBITMQ_PASSWORD}
      - LOG_LEVEL=${LOG_LEVEL}
    ports:
      - "8000:8000"
    volumes:
      - ./runner:/app
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
    networks:
      - qa-network
    restart: unless-stopped

  # ============================================================================
  # TEST AGENT SERVICES
  # ============================================================================

  unit-test-agent:
    build:
      context: ./agents/unit-test-agent
      dockerfile: Dockerfile
    container_name: qa-unit-test-agent
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - REDIS_HOST=redis
      - RABBITMQ_HOST=rabbitmq
      - JEST_SERVER_URL=http://jest-server:3001
      - PYTEST_SERVER_URL=http://pytest-server:3002
    volumes:
      - ./shared:/app/shared
      - test-results:/app/results
    depends_on:
      - redis
      - rabbitmq
      - jest-server
    networks:
      - qa-network
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G

  integration-test-agent:
    build:
      context: ./agents/integration-test-agent
      dockerfile: Dockerfile
    container_name: qa-integration-test-agent
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - REDIS_HOST=redis
      - RABBITMQ_HOST=rabbitmq
    volumes:
      - ./shared:/app/shared
      - test-results:/app/results
    depends_on:
      - redis
      - rabbitmq
    networks:
      - qa-network
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G

  e2e-test-agent:
    build:
      context: ./agents/e2e-test-agent
      dockerfile: Dockerfile
    container_name: qa-e2e-test-agent
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - REDIS_HOST=redis
      - RABBITMQ_HOST=rabbitmq
      - PLAYWRIGHT_SERVER_URL=http://playwright-server:3003
    volumes:
      - ./shared:/app/shared
      - test-results:/app/results
    depends_on:
      - redis
      - rabbitmq
      - playwright-server
    networks:
      - qa-network
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G

  performance-test-agent:
    build:
      context: ./agents/performance-test-agent
      dockerfile: Dockerfile
    container_name: qa-performance-test-agent
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - REDIS_HOST=redis
      - RABBITMQ_HOST=rabbitmq
      - K6_SERVER_URL=http://k6-server:3004
    volumes:
      - ./shared:/app/shared
      - test-results:/app/results
    depends_on:
      - redis
      - rabbitmq
      - k6-server
    networks:
      - qa-network
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G

  security-test-agent:
    build:
      context: ./agents/security-test-agent
      dockerfile: Dockerfile
    container_name: qa-security-test-agent
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - REDIS_HOST=redis
      - RABBITMQ_HOST=rabbitmq
      - SONARQUBE_URL=${SONARQUBE_URL}
      - SNYK_TOKEN=${SNYK_TOKEN}
    volumes:
      - ./shared:/app/shared
      - test-results:/app/results
    depends_on:
      - redis
      - rabbitmq
    networks:
      - qa-network
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G

  code-review-agent:
    build:
      context: ./agents/code-review-agent
      dockerfile: Dockerfile
    container_name: qa-code-review-agent
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - REDIS_HOST=redis
      - RABBITMQ_HOST=rabbitmq
    volumes:
      - ./shared:/app/shared
      - test-results:/app/results
    depends_on:
      - redis
      - rabbitmq
    networks:
      - qa-network
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G

  test-analyzer-agent:
    build:
      context: ./agents/test-analyzer-agent
      dockerfile: Dockerfile
    container_name: qa-test-analyzer-agent
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - REDIS_HOST=redis
      - RABBITMQ_HOST=rabbitmq
      - TEST_ANALYSIS_SERVER_URL=http://test-analysis-server:3010
    volumes:
      - ./shared:/app/shared
      - test-results:/app/results
    depends_on:
      - redis
      - rabbitmq
      - test-analysis-server
    networks:
      - qa-network

  bug-detector-agent:
    build:
      context: ./agents/bug-detector-agent
      dockerfile: Dockerfile
    container_name: qa-bug-detector-agent
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - REDIS_HOST=redis
      - RABBITMQ_HOST=rabbitmq
      - BUG_DETECTION_SERVER_URL=http://bug-detection-server:3007
      - GITHUB_TOKEN=${GITHUB_TOKEN}
    volumes:
      - ./shared:/app/shared
      - test-results:/app/results
    depends_on:
      - redis
      - rabbitmq
      - bug-detection-server
    networks:
      - qa-network

  report-generator-agent:
    build:
      context: ./agents/report-generator-agent
      dockerfile: Dockerfile
    container_name: qa-report-generator-agent
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - REDIS_HOST=redis
      - RABBITMQ_HOST=rabbitmq
      - SLACK_WEBHOOK_URL=${SLACK_WEBHOOK_URL}
    volumes:
      - ./shared:/app/shared
      - test-results:/app/results
      - reports:/app/reports
    depends_on:
      - redis
      - rabbitmq
    networks:
      - qa-network

  regression-agent:
    build:
      context: ./agents/regression-agent
      dockerfile: Dockerfile
    container_name: qa-regression-agent
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - REDIS_HOST=redis
      - RABBITMQ_HOST=rabbitmq
      - AUTO_FIX_SERVER_URL=http://auto-fix-server:3008
      - MAX_RETRY_ATTEMPTS=${MAX_RETRY_ATTEMPTS}
    volumes:
      - ./shared:/app/shared
      - test-results:/app/results
    depends_on:
      - redis
      - rabbitmq
      - auto-fix-server
    networks:
      - qa-network

  # ============================================================================
  # CUSTOM MCP SERVERS
  # ============================================================================

  test-strategy-server:
    build:
      context: ./mcp-servers/test-strategy-server
      dockerfile: Dockerfile
    container_name: mcp-test-strategy
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - MCP_PORT=3005
    ports:
      - "3005:3005"
    networks:
      - qa-network
    restart: unless-stopped

  test-generation-server:
    build:
      context: ./mcp-servers/test-generation-server
      dockerfile: Dockerfile
    container_name: mcp-test-generation
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - MCP_PORT=3006
    ports:
      - "3006:3006"
    networks:
      - qa-network
    restart: unless-stopped

  bug-detection-server:
    build:
      context: ./mcp-servers/bug-detection-server
      dockerfile: Dockerfile
    container_name: mcp-bug-detection
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - MCP_PORT=3007
    ports:
      - "3007:3007"
    networks:
      - qa-network
    restart: unless-stopped

  auto-fix-server:
    build:
      context: ./mcp-servers/auto-fix-server
      dockerfile: Dockerfile
    container_name: mcp-auto-fix
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - MCP_PORT=3008
    ports:
      - "3008:3008"
    networks:
      - qa-network
    restart: unless-stopped

  code-analyzer-server:
    build:
      context: ./mcp-servers/code-analyzer-server
      dockerfile: Dockerfile
    container_name: mcp-code-analyzer
    environment:
      - MCP_PORT=3009
    ports:
      - "3009:3009"
    networks:
      - qa-network
    restart: unless-stopped

  test-analysis-server:
    build:
      context: ./mcp-servers/test-analysis-server
      dockerfile: Dockerfile
    container_name: mcp-test-analysis
    environment:
      - POSTGRES_HOST=postgres
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - MCP_PORT=3010
    ports:
      - "3010:3010"
    depends_on:
      - postgres
    networks:
      - qa-network
    restart: unless-stopped

  metrics-server:
    build:
      context: ./mcp-servers/metrics-server
      dockerfile: Dockerfile
    container_name: mcp-metrics
    environment:
      - POSTGRES_HOST=postgres
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - PROMETHEUS_URL=http://prometheus:9090
      - MCP_PORT=3011
    ports:
      - "3011:3011"
    depends_on:
      - postgres
      - prometheus
    networks:
      - qa-network
      - monitoring-network
    restart: unless-stopped

  jest-server:
    build:
      context: ./mcp-servers/jest-server
      dockerfile: Dockerfile
    container_name: mcp-jest
    environment:
      - MCP_PORT=3001
    ports:
      - "3001:3001"
    networks:
      - qa-network
    restart: unless-stopped

  playwright-server:
    build:
      context: ./mcp-servers/playwright-server
      dockerfile: Dockerfile
    container_name: mcp-playwright
    environment:
      - MCP_PORT=3003
    ports:
      - "3003:3003"
    volumes:
      - test-results:/app/results
    networks:
      - qa-network
    restart: unless-stopped

  k6-server:
    build:
      context: ./mcp-servers/k6-server
      dockerfile: Dockerfile
    container_name: mcp-k6
    environment:
      - MCP_PORT=3004
    ports:
      - "3004:3004"
    networks:
      - qa-network
    restart: unless-stopped

  # ============================================================================
  # MONITORING SERVICES
  # ============================================================================

  prometheus:
    image: prom/prometheus:latest
    container_name: qa-prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    ports:
      - "${PROMETHEUS_PORT}:9090"
    volumes:
      - ./infrastructure/monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    networks:
      - monitoring-network
      - qa-network
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: qa-grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
    ports:
      - "${GRAFANA_PORT}:3000"
    volumes:
      - ./infrastructure/monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./infrastructure/monitoring/grafana/datasources.yml:/etc/grafana/provisioning/datasources/datasources.yml
      - grafana-data:/var/lib/grafana
    depends_on:
      - prometheus
    networks:
      - monitoring-network
    restart: unless-stopped

# ============================================================================
# NETWORKS
# ============================================================================

networks:
  qa-network:
    driver: bridge
  monitoring-network:
    driver: bridge

# ============================================================================
# VOLUMES
# ============================================================================

volumes:
  postgres-data:
  redis-data:
  test-results:
  reports:
  grafana-data:
  prometheus-data:
```

#### Step 1.3: Create Environment Template

Create `.env.example`:

```env
# See IMPLEMENTATION_GUIDE.md for full configuration details
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-1.5-pro
GITHUB_TOKEN=your_github_token_here
POSTGRES_DB=qa_multiagent
POSTGRES_USER=qauser
POSTGRES_PASSWORD=changeme
REDIS_PASSWORD=changeme
RABBITMQ_USER=qarabbit
RABBITMQ_PASSWORD=changeme
MIN_CODE_COVERAGE=80.0
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
GRAFANA_ADMIN_PASSWORD=admin
LOG_LEVEL=INFO
MAX_RETRY_ATTEMPTS=3
```

---

### Phase 2: Runner & Orchestrator Implementation (Week 2)

#### Step 2.1: Create Runner Dockerfile

`runner/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/results /app/reports /app/logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "main.py"]
```

#### Step 2.2: Create Runner Requirements

`runner/requirements.txt`:

```txt
# Google ADK & AI
google-adk>=0.1.0
google-generativeai>=0.3.0

# MCP Protocol
mcp>=1.0.0

# Web Framework
fastapi>=0.104.0
uvicorn[standard]>=0.24.0

# Database
psycopg2-binary>=2.9.9
sqlalchemy>=2.0.23

# Cache & Queue
redis>=5.0.1
pika>=1.3.2

# HTTP Client
httpx>=0.25.2
aiohttp>=3.9.1

# Utilities
python-dotenv>=1.0.0
pydantic>=2.5.0
pydantic-settings>=2.1.0

# Logging & Monitoring
structlog>=23.2.0
prometheus-client>=0.19.0

# Testing
pytest>=7.4.3
pytest-asyncio>=0.21.1
```

#### Step 2.3: Implement Runner Main Entry Point

`runner/main.py`:

```python
"""
QA Multi-Agent System - Main Entry Point
"""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn

from config import settings
from orchestrator.orchestrator_agent import OrchestratorAgent
from shared.state_manager import StateManager
from shared.logger import setup_logger

# Setup logging
logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting QA Multi-Agent System")

    # Initialize state manager
    app.state.state_manager = StateManager()
    await app.state.state_manager.connect()

    # Initialize orchestrator
    app.state.orchestrator = OrchestratorAgent()
    await app.state.orchestrator.initialize()

    logger.info("System initialized successfully")

    yield

    # Shutdown
    logger.info("Shutting down QA Multi-Agent System")
    await app.state.state_manager.disconnect()
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="QA Multi-Agent System",
    description="Production-ready automated testing system",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "qa-runner"}


@app.post("/trigger")
async def trigger_qa_pipeline(
    payload: dict,
    background_tasks: BackgroundTasks
):
    """
    Trigger QA pipeline

    Payload example:
    {
        "trigger_type": "pull_request",
        "repo_url": "https://github.com/org/repo",
        "branch": "feature/new-feature",
        "commit_sha": "abc123",
        "pull_request_id": "123"
    }
    """
    try:
        logger.info(f"Received trigger: {payload.get('trigger_type')}")

        # Start pipeline in background
        background_tasks.add_task(
            run_qa_pipeline,
            payload,
            app.state.orchestrator,
            app.state.state_manager
        )

        return JSONResponse(
            status_code=202,
            content={
                "status": "accepted",
                "message": "QA pipeline started",
                "trigger": payload.get("trigger_type")
            }
        )

    except Exception as e:
        logger.error(f"Error triggering pipeline: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


async def run_qa_pipeline(
    payload: dict,
    orchestrator: OrchestratorAgent,
    state_manager: StateManager
):
    """Execute the complete QA pipeline"""
    try:
        # Run orchestrator
        result = await orchestrator.execute(payload)

        # Store result
        await state_manager.store_result(result)

        logger.info(f"Pipeline completed: {result.get('quality_gate', {}).get('status')}")

    except Exception as e:
        logger.error(f"Pipeline execution error: {e}", exc_info=True)


@app.get("/status/{execution_id}")
async def get_execution_status(execution_id: str):
    """Get execution status"""
    try:
        result = await app.state.state_manager.get_result(execution_id)
        return result if result else {"status": "not_found"}

    except Exception as e:
        logger.error(f"Error fetching status: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
```

#### Step 2.4: Create Configuration

`runner/config.py`:

```python
"""
Configuration management for QA system
"""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings"""

    # Gemini AI
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-1.5-pro"

    # Database
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str

    # RabbitMQ
    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str
    RABBITMQ_PASSWORD: str

    # Quality Gates
    MIN_CODE_COVERAGE: float = 80.0
    MAX_FAILED_TESTS: int = 0
    MAX_CRITICAL_VULNERABILITIES: int = 0
    MIN_PASS_RATE: float = 95.0

    # System
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False
    MAX_RETRY_ATTEMPTS: int = 3

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
```

#### Step 2.5: Implement Orchestrator Agent

`runner/orchestrator/orchestrator_agent.py`:

```python
"""
Orchestrator Agent - Coordinates the entire QA pipeline
"""
import asyncio
from typing import Dict, Any, List
from datetime import datetime
import uuid

from google import generativeai as genai
from shared.logger import setup_logger
from shared.mcp_client import MCPClient
from config import settings

logger = setup_logger(__name__)


class OrchestratorAgent:
    """Main orchestrator agent using Google ADK"""

    def __init__(self):
        self.client = None
        self.mcp_clients = {}
        self.agent_status = {}

    async def initialize(self):
        """Initialize the orchestrator"""
        # Configure Gemini
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)

        # Initialize MCP clients
        await self._initialize_mcp_clients()

        logger.info("Orchestrator initialized")

    async def _initialize_mcp_clients(self):
        """Initialize connections to MCP servers"""
        mcp_servers = {
            "test-strategy": "http://test-strategy-server:3005",
            "code-analyzer": "http://code-analyzer-server:3009",
            "test-generation": "http://test-generation-server:3006",
        }

        for name, url in mcp_servers.items():
            self.mcp_clients[name] = MCPClient(name, url)
            await self.mcp_clients[name].connect()

        logger.info(f"Connected to {len(mcp_servers)} MCP servers")

    async def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the complete QA pipeline

        Pipeline stages:
        1. Code analysis & test strategy
        2. Parallel test execution (6 agents)
        3. Sequential analysis (3 agents)
        4. Regression loop (if needed)
        5. Quality gate decision
        """
        execution_id = str(uuid.uuid4())
        start_time = datetime.utcnow()

        logger.info(f"Starting execution {execution_id}")

        # Initialize shared state
        shared_state = self._initialize_state(payload, execution_id)

        try:
            # Stage 1: Analyze code and create test strategy
            logger.info("Stage 1: Code analysis & strategy")
            await self._analyze_and_strategize(shared_state)

            # Stage 2: Execute parallel test agents
            logger.info("Stage 2: Parallel test execution")
            await self._execute_parallel_tests(shared_state)

            # Stage 3: Sequential analysis pipeline
            logger.info("Stage 3: Analysis pipeline")
            await self._execute_analysis_pipeline(shared_state)

            # Stage 4: Regression loop (if needed)
            if shared_state["quality_gate"]["actual"]["pass_rate"] < settings.MIN_PASS_RATE:
                logger.info("Stage 4: Regression loop")
                await self._execute_regression_loop(shared_state)

            # Stage 5: Quality gate decision
            logger.info("Stage 5: Quality gate")
            self._evaluate_quality_gate(shared_state)

            # Finalize
            shared_state["execution_time"] = (datetime.utcnow() - start_time).total_seconds()
            shared_state["timestamp"] = datetime.utcnow().isoformat()

            logger.info(f"Execution {execution_id} completed: {shared_state['quality_gate']['status']}")

            return shared_state

        except Exception as e:
            logger.error(f"Execution {execution_id} failed: {e}", exc_info=True)
            shared_state["error"] = str(e)
            shared_state["quality_gate"]["status"] = "ERROR"
            return shared_state

    def _initialize_state(self, payload: Dict[str, Any], execution_id: str) -> Dict[str, Any]:
        """Initialize shared state"""
        return {
            "execution_id": execution_id,
            "commit_sha": payload.get("commit_sha"),
            "branch": payload.get("branch"),
            "pull_request_id": payload.get("pull_request_id"),
            "repo_url": payload.get("repo_url"),
            "trigger_type": payload.get("trigger_type"),
            "test_strategy": {},
            "unit_test_results": {},
            "integration_test_results": {},
            "e2e_test_results": {},
            "performance_test_results": {},
            "security_test_results": {},
            "code_review_results": {},
            "test_analysis": {},
            "detected_bugs": [],
            "quality_gate": {
                "status": "PENDING",
                "criteria": {
                    "min_coverage": settings.MIN_CODE_COVERAGE,
                    "max_failed_tests": settings.MAX_FAILED_TESTS,
                    "max_critical_vulnerabilities": settings.MAX_CRITICAL_VULNERABILITIES,
                    "min_pass_rate": settings.MIN_PASS_RATE,
                },
                "actual": {},
                "passed": False
            },
            "agents_executed": [],
            "mcp_servers_used": [],
            "retry_count": 0,
        }

    async def _analyze_and_strategize(self, state: Dict[str, Any]):
        """Analyze code changes and create test strategy"""
        try:
            # Use MCP code-analyzer server
            code_analysis = await self.mcp_clients["code-analyzer"].call_tool(
                "analyze_code",
                {
                    "repo_url": state["repo_url"],
                    "commit_sha": state["commit_sha"]
                }
            )

            # Use MCP test-strategy server
            test_strategy = await self.mcp_clients["test-strategy"].call_tool(
                "generate_strategy",
                {
                    "code_analysis": code_analysis,
                    "trigger_type": state["trigger_type"]
                }
            )

            state["test_strategy"] = test_strategy
            state["mcp_servers_used"].extend(["code-analyzer", "test-strategy"])

            logger.info(f"Strategy: {test_strategy.get('test_types')}")

        except Exception as e:
            logger.error(f"Strategy generation failed: {e}")
            raise

    async def _execute_parallel_tests(self, state: Dict[str, Any]):
        """Execute all test agents in parallel"""
        test_types = state["test_strategy"].get("test_types", [])

        # Create tasks for each agent
        tasks = []

        if "unit" in test_types:
            tasks.append(self._trigger_agent("unit-test-agent", state))

        if "integration" in test_types:
            tasks.append(self._trigger_agent("integration-test-agent", state))

        if "e2e" in test_types:
            tasks.append(self._trigger_agent("e2e-test-agent", state))

        if "performance" in test_types:
            tasks.append(self._trigger_agent("performance-test-agent", state))

        # Always run security and code review
        tasks.append(self._trigger_agent("security-test-agent", state))
        tasks.append(self._trigger_agent("code-review-agent", state))

        # Execute all in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Agent execution failed: {result}")

        state["agents_executed"].extend([
            "unit-test", "integration-test", "e2e-test",
            "performance-test", "security-test", "code-review"
        ])

    async def _trigger_agent(self, agent_name: str, state: Dict[str, Any]):
        """Trigger a specific agent via message queue"""
        # In production, this would publish to RabbitMQ
        # For now, simulate agent execution
        logger.info(f"Triggering {agent_name}")
        await asyncio.sleep(2)  # Simulate work
        return {"agent": agent_name, "status": "completed"}

    async def _execute_analysis_pipeline(self, state: Dict[str, Any]):
        """Execute sequential analysis agents"""
        # Stage 1: Test Analyzer
        await self._trigger_agent("test-analyzer-agent", state)

        # Stage 2: Bug Detector
        await self._trigger_agent("bug-detector-agent", state)

        # Stage 3: Report Generator
        await self._trigger_agent("report-generator-agent", state)

        state["agents_executed"].extend([
            "test-analyzer", "bug-detector", "report-generator"
        ])

    async def _execute_regression_loop(self, state: Dict[str, Any]):
        """Execute regression agent for retry/healing"""
        max_retries = settings.MAX_RETRY_ATTEMPTS

        for attempt in range(max_retries):
            state["retry_count"] = attempt + 1
            logger.info(f"Regression attempt {state['retry_count']}/{max_retries}")

            await self._trigger_agent("regression-agent", state)

            # Check if pass rate improved
            if state["quality_gate"]["actual"]["pass_rate"] >= settings.MIN_PASS_RATE:
                logger.info("Regression successful")
                break

        state["agents_executed"].append("regression")

    def _evaluate_quality_gate(self, state: Dict[str, Any]):
        """Evaluate quality gate criteria"""
        actual = state["quality_gate"]["actual"]
        criteria = state["quality_gate"]["criteria"]

        # Calculate actual metrics (simplified)
        actual["coverage"] = state.get("unit_test_results", {}).get("coverage", {}).get("line", 0)
        actual["failed_tests"] = sum([
            state.get("unit_test_results", {}).get("failed", 0),
            state.get("integration_test_results", {}).get("failed", 0),
            state.get("e2e_test_results", {}).get("failed", 0),
        ])
        actual["critical_vulnerabilities"] = state.get("security_test_results", {}).get("severity_counts", {}).get("critical", 0)

        total_tests = sum([
            state.get("unit_test_results", {}).get("total", 0),
            state.get("integration_test_results", {}).get("total", 0),
            state.get("e2e_test_results", {}).get("total", 0),
        ])
        passed_tests = total_tests - actual["failed_tests"]
        actual["pass_rate"] = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        # Evaluate
        passed = (
            actual["coverage"] >= criteria["min_coverage"] and
            actual["failed_tests"] <= criteria["max_failed_tests"] and
            actual["critical_vulnerabilities"] <= criteria["max_critical_vulnerabilities"] and
            actual["pass_rate"] >= criteria["min_pass_rate"]
        )

        state["quality_gate"]["passed"] = passed
        state["quality_gate"]["status"] = "PASS" if passed else "FAIL"
```

---

### Phase 3: Shared Libraries Implementation (Week 3)

#### Step 3.1: State Manager

`shared/state_manager.py`:

```python
"""
Shared state management using Redis
"""
import json
import redis.asyncio as redis
from typing import Dict, Any, Optional

from .logger import setup_logger
from runner.config import settings

logger = setup_logger(__name__)


class StateManager:
    """Manages shared state across agents"""

    def __init__(self):
        self.redis_client = None

    async def connect(self):
        """Connect to Redis"""
        self.redis_client = await redis.from_url(
            f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}",
            encoding="utf-8",
            decode_responses=True
        )
        logger.info("Connected to Redis")

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()

    async def store_result(self, result: Dict[str, Any]):
        """Store execution result"""
        execution_id = result.get("execution_id")
        await self.redis_client.setex(
            f"execution:{execution_id}",
            3600 * 24,  # 24 hours TTL
            json.dumps(result)
        )

    async def get_result(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get execution result"""
        data = await self.redis_client.get(f"execution:{execution_id}")
        return json.loads(data) if data else None

    async def update_agent_status(self, agent_name: str, status: Dict[str, Any]):
        """Update agent status"""
        await self.redis_client.hset(
            "agent_status",
            agent_name,
            json.dumps(status)
        )
```

#### Step 3.2: MCP Client

`shared/mcp_client.py`:

```python
"""
MCP (Model Context Protocol) Client
"""
import httpx
from typing import Dict, Any

from .logger import setup_logger

logger = setup_logger(__name__)


class MCPClient:
    """Client for communicating with MCP servers"""

    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url
        self.client = None

    async def connect(self):
        """Initialize HTTP client"""
        self.client = httpx.AsyncClient(base_url=self.url, timeout=30.0)
        logger.info(f"Connected to MCP server: {self.name}")

    async def disconnect(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()

    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the MCP server"""
        try:
            response = await self.client.post(
                "/mcp/call-tool",
                json={
                    "name": tool_name,
                    "parameters": parameters
                }
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"MCP call failed [{self.name}.{tool_name}]: {e}")
            raise

    async def list_tools(self) -> list:
        """List available tools"""
        response = await self.client.get("/mcp/list-tools")
        response.raise_for_status()
        return response.json()
```

#### Step 3.3: Logger

`shared/logger.py`:

```python
"""
Structured logging configuration
"""
import logging
import sys
from runner.config import settings


def setup_logger(name: str) -> logging.Logger:
    """Setup structured logger"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
```

---

### Phase 4: MCP Servers Implementation (Week 4-5)

#### Step 4.1: Test Strategy Server

`mcp-servers/test-strategy-server/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 3005

CMD ["python", "server.py"]
```

`mcp-servers/test-strategy-server/requirements.txt`:

```txt
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
google-generativeai>=0.3.0
python-dotenv>=1.0.0
pydantic>=2.5.0
```

`mcp-servers/test-strategy-server/server.py`:

```python
"""
MCP Server: Test Strategy Generation
"""
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any, List
import os

import google.generativeai as genai

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-pro")

app = FastAPI(title="Test Strategy MCP Server")


class ToolCallRequest(BaseModel):
    name: str
    parameters: Dict[str, Any]


@app.post("/mcp/call-tool")
async def call_tool(request: ToolCallRequest):
    """Handle MCP tool calls"""

    if request.name == "generate_strategy":
        return await generate_test_strategy(request.parameters)

    elif request.name == "impact_analysis":
        return await analyze_impact(request.parameters)

    else:
        return {"error": f"Unknown tool: {request.name}"}


async def generate_test_strategy(params: Dict[str, Any]) -> Dict[str, Any]:
    """Generate test strategy based on code analysis"""

    code_analysis = params.get("code_analysis", {})
    trigger_type = params.get("trigger_type", "pull_request")

    # Use Gemini to generate strategy
    prompt = f"""
    Based on the following code analysis, generate a comprehensive test strategy:

    Changed files: {code_analysis.get('changed_files', [])}
    Complexity: {code_analysis.get('complexity', 'medium')}
    Trigger: {trigger_type}

    Determine:
    1. Which test types to run (unit, integration, e2e, performance, security)
    2. Priority level (high, medium, low)
    3. Affected components
    4. Whether parallel execution is recommended

    Return as JSON.
    """

    response = model.generate_content(prompt)

    # Parse response (simplified)
    return {
        "test_types": ["unit", "integration", "e2e", "security"],
        "priority": "high",
        "affected_components": code_analysis.get("changed_files", []),
        "parallel_execution": True,
        "estimated_duration": 300  # seconds
    }


async def analyze_impact(params: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze impact of code changes"""
    return {
        "risk_level": "medium",
        "affected_modules": ["auth", "api"],
        "requires_full_regression": False
    }


@app.get("/mcp/list-tools")
async def list_tools():
    """List available MCP tools"""
    return [
        {
            "name": "generate_strategy",
            "description": "Generate comprehensive test strategy",
            "parameters": ["code_analysis", "trigger_type"]
        },
        {
            "name": "impact_analysis",
            "description": "Analyze impact of code changes",
            "parameters": ["changed_files", "commit_sha"]
        }
    ]


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3005)
```

#### Step 4.2: Jest Server (Node.js)

`mcp-servers/jest-server/Dockerfile`:

```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3001

CMD ["node", "server.js"]
```

`mcp-servers/jest-server/package.json`:

```json
{
  "name": "jest-mcp-server",
  "version": "1.0.0",
  "description": "MCP Server for Jest testing",
  "main": "server.js",
  "dependencies": {
    "express": "^4.18.2",
    "jest": "^29.7.0",
    "body-parser": "^1.20.2"
  }
}
```

`mcp-servers/jest-server/server.js`:

```javascript
/**
 * MCP Server: Jest Test Execution
 */
const express = require('express');
const bodyParser = require('body-parser');
const { exec } = require('child_process');
const util = require('util');

const execPromise = util.promisify(exec);

const app = express();
app.use(bodyParser.json());

// MCP tool call handler
app.post('/mcp/call-tool', async (req, res) => {
  const { name, parameters } = req.body;

  try {
    let result;

    if (name === 'run_tests') {
      result = await runJestTests(parameters);
    } else if (name === 'generate_coverage') {
      result = await generateCoverage(parameters);
    } else {
      return res.status(400).json({ error: `Unknown tool: ${name}` });
    }

    res.json(result);

  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Run Jest tests
async function runJestTests(params) {
  const testPath = params.test_path || '';
  const config = params.config || 'jest.config.js';

  try {
    const { stdout, stderr } = await execPromise(
      `jest ${testPath} --config=${config} --json`
    );

    const results = JSON.parse(stdout);

    return {
      total: results.numTotalTests,
      passed: results.numPassedTests,
      failed: results.numFailedTests,
      duration: results.testResults.reduce((sum, r) => sum + r.perfStats.runtime, 0),
      failed_tests: results.testResults
        .filter(r => r.status === 'failed')
        .map(r => ({
          name: r.name,
          message: r.message
        }))
    };

  } catch (error) {
    return {
      error: error.message,
      total: 0,
      passed: 0,
      failed: 0
    };
  }
}

// Generate coverage report
async function generateCoverage(params) {
  try {
    const { stdout } = await execPromise('jest --coverage --json');
    const results = JSON.parse(stdout);

    return {
      line: results.coverageMap.getCoverageSummary().lines.pct,
      branch: results.coverageMap.getCoverageSummary().branches.pct,
      function: results.coverageMap.getCoverageSummary().functions.pct,
      statement: results.coverageMap.getCoverageSummary().statements.pct
    };

  } catch (error) {
    return { error: error.message };
  }
}

// List available tools
app.get('/mcp/list-tools', (req, res) => {
  res.json([
    {
      name: 'run_tests',
      description: 'Execute Jest test suite',
      parameters: ['test_path', 'config']
    },
    {
      name: 'generate_coverage',
      description: 'Generate code coverage report',
      parameters: []
    }
  ]);
});

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

const PORT = process.env.MCP_PORT || 3001;
app.listen(PORT, () => {
  console.log(`Jest MCP Server running on port ${PORT}`);
});
```

---

### Phase 5: Agent Implementation (Week 6-7)

#### Step 5.1: Unit Test Agent Example

`agents/unit-test-agent/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "agent.py"]
```

`agents/unit-test-agent/requirements.txt`:

```txt
google-generativeai>=0.3.0
redis>=5.0.1
pika>=1.3.2
httpx>=0.25.2
python-dotenv>=1.0.0
```

`agents/unit-test-agent/agent.py`:

```python
"""
Unit Test Agent
Executes unit tests and generates coverage reports
"""
import asyncio
import os
import httpx
from typing import Dict, Any


class UnitTestAgent:
    """Unit test execution agent"""

    def __init__(self):
        self.jest_server_url = os.getenv("JEST_SERVER_URL")
        self.client = httpx.AsyncClient(timeout=300.0)

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute unit tests"""
        print(f"[Unit Test Agent] Starting execution")

        try:
            # Call Jest MCP server
            response = await self.client.post(
                f"{self.jest_server_url}/mcp/call-tool",
                json={
                    "name": "run_tests",
                    "parameters": {
                        "test_path": "tests/unit"
                    }
                }
            )
            response.raise_for_status()
            results = response.json()

            # Get coverage
            coverage_response = await self.client.post(
                f"{self.jest_server_url}/mcp/call-tool",
                json={
                    "name": "generate_coverage",
                    "parameters": {}
                }
            )
            coverage = coverage_response.json()

            # Update state
            state["unit_test_results"] = {
                **results,
                "coverage": coverage
            }

            print(f"[Unit Test Agent] Completed: {results['passed']}/{results['total']} passed")

            return state

        except Exception as e:
            print(f"[Unit Test Agent] Error: {e}")
            state["unit_test_results"] = {"error": str(e)}
            return state


async def main():
    """Agent main loop"""
    agent = UnitTestAgent()

    # In production, this would listen to RabbitMQ
    # For now, simulate execution
    test_state = {
        "execution_id": "test-123",
        "commit_sha": "abc123"
    }

    result = await agent.execute(test_state)
    print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
```

---

### Phase 6: Infrastructure Setup (Week 8)

#### Step 6.1: PostgreSQL Initialization

`infrastructure/postgres/init.sql`:

```sql
-- QA Multi-Agent System Database Schema

CREATE TABLE IF NOT EXISTS executions (
    id VARCHAR(36) PRIMARY KEY,
    commit_sha VARCHAR(40),
    branch VARCHAR(255),
    pull_request_id VARCHAR(50),
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    result JSONB
);

CREATE TABLE IF NOT EXISTS test_results (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(36) REFERENCES executions(id),
    agent_name VARCHAR(50),
    test_type VARCHAR(20),
    results JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS metrics (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(36) REFERENCES executions(id),
    metric_name VARCHAR(50),
    metric_value FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bugs (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(36) REFERENCES executions(id),
    severity VARCHAR(20),
    description TEXT,
    file_path VARCHAR(500),
    line_number INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_executions_commit ON executions(commit_sha);
CREATE INDEX idx_test_results_execution ON test_results(execution_id);
CREATE INDEX idx_metrics_execution ON metrics(execution_id);
```

#### Step 6.2: Prometheus Configuration

`infrastructure/monitoring/prometheus/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'qa-runner'
    static_configs:
      - targets: ['runner:8000']

  - job_name: 'mcp-servers'
    static_configs:
      - targets:
        - 'test-strategy-server:3005'
        - 'jest-server:3001'
        - 'playwright-server:3003'
        - 'k6-server:3004'

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
```

#### Step 6.3: Grafana Datasource

`infrastructure/monitoring/grafana/datasources.yml`:

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true

  - name: PostgreSQL
    type: postgres
    url: postgres:5432
    database: qa_multiagent
    user: qauser
    secureJsonData:
      password: qapassword123
```

---

### Phase 7: Utility Scripts (Week 8)

#### Step 7.1: Setup Script

`scripts/setup.sh`:

```bash
#!/bin/bash

echo "Setting up QA Multi-Agent System..."

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "Docker not installed"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "Docker Compose not installed"; exit 1; }

# Create .env from template
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file - Please configure it with your API keys"
    exit 1
fi

# Create required directories
mkdir -p logs reports results

# Build all services
echo "Building Docker images..."
docker-compose build

echo "Setup complete! Run './scripts/start.sh' to start the system"
```

#### Step 7.2: Start Script

`scripts/start.sh`:

```bash
#!/bin/bash

echo "Starting QA Multi-Agent System..."

# Start infrastructure first
docker-compose up -d postgres redis rabbitmq

# Wait for health checks
echo "Waiting for infrastructure..."
sleep 10

# Start MCP servers
docker-compose up -d \
    test-strategy-server \
    test-generation-server \
    bug-detection-server \
    auto-fix-server \
    code-analyzer-server \
    jest-server \
    playwright-server \
    k6-server

sleep 5

# Start runner
docker-compose up -d runner

# Start monitoring
docker-compose up -d prometheus grafana

echo "System started!"
echo "Runner API: http://localhost:8000"
echo "Grafana: http://localhost:3000 (admin/admin)"
echo "Prometheus: http://localhost:9090"
echo ""
echo "Check logs: docker-compose logs -f runner"
```

#### Step 7.3: Stop Script

`scripts/stop.sh`:

```bash
#!/bin/bash

echo "Stopping QA Multi-Agent System..."
docker-compose down

echo "System stopped"
```

#### Step 7.4: Test Script

`scripts/test.sh`:

```bash
#!/bin/bash

echo "Testing QA Multi-Agent System..."

# Health check
curl -s http://localhost:8000/health || { echo "Runner not healthy"; exit 1; }

# Trigger test execution
curl -X POST http://localhost:8000/trigger \
    -H "Content-Type: application/json" \
    -d '{
        "trigger_type": "pull_request",
        "repo_url": "https://github.com/test/repo",
        "branch": "main",
        "commit_sha": "abc123",
        "pull_request_id": "1"
    }'

echo "Test pipeline triggered"
```

---

## Testing & Validation

### 1. System Health Check

```bash
# Check all services
docker-compose ps

# Check logs
docker-compose logs -f runner
docker-compose logs -f test-strategy-server
```

### 2. Trigger Test Pipeline

```bash
./scripts/test.sh
```

### 3. Monitor Execution

```bash
# Watch logs
docker-compose logs -f runner

# Check metrics in Grafana
open http://localhost:3000
```

---

## Deployment

### Production Considerations

1. **Use Kubernetes** instead of Docker Compose
2. **Implement proper secrets management** (Vault, AWS Secrets Manager)
3. **Add load balancing** for MCP servers
4. **Enable auto-scaling** for agent services
5. **Configure persistent storage** for databases
6. **Set up proper monitoring & alerting**
7. **Implement rate limiting** for Gemini API calls
8. **Add authentication & authorization**

---

## Troubleshooting

### Common Issues

**1. Services won't start**
```bash
docker-compose down -v
docker-compose up --build
```

**2. Can't connect to MCP servers**
```bash
docker-compose logs <server-name>
# Check network: docker network inspect qa-multiagent-gemini_qa-network
```

**3. Gemini API errors**
- Verify API key in `.env`
- Check rate limits
- Review error logs

**4. Database connection issues**
```bash
docker-compose exec postgres psql -U qauser -d qa_multiagent
```

**5. Memory issues**
```bash
# Increase Docker memory limits
# Or reduce number of parallel agents in .env
```

---

## Next Steps

1. **Complete all agent implementations**
2. **Implement remaining MCP servers**
3. **Add comprehensive tests**
4. **Create CI/CD pipeline**
5. **Write API documentation**
6. **Set up production deployment**
7. **Implement monitoring dashboards**
8. **Add integration with real projects**

---

## Resources

- Google ADK: https://adk.dev
- MCP Specification: https://modelcontextprotocol.io
- Gemini API: https://ai.google.dev
- Docker Compose: https://docs.docker.com/compose

---

**Version**: 1.0.0
**Last Updated**: 2026-04-14
**Author**: QA Multi-Agent Team
