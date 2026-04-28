# Getting Started - QA Multi-Agent System MVP

This guide will help you get the MVP (Minimum Viable Product) up and running.

## 🎯 What's in the MVP?

- ✅ **Runner Service** - FastAPI orchestrator with Gemini AI
- ✅ **Test Strategy MCP Server** - AI-powered test strategy generation
- ✅ **Unit Test Agent** - Simulated unit test execution
- ✅ **Infrastructure** - PostgreSQL, Redis, RabbitMQ
- ✅ **Docker Compose** - Easy deployment

## 📋 Prerequisites

1. **Docker & Docker Compose** (v2.20.0+)
   ```bash
   docker --version
   docker compose version
   ```

2. **Gemini API Key**
   - Get it from: https://makersuite.google.com/app/apikey
   - Free tier available!

3. **System Requirements**
   - 8GB RAM minimum
   - 4 CPU cores recommended
   - 10GB disk space

## 🚀 Quick Start (5 minutes)

### Step 1: Get Gemini API Key

1. Visit https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the key

### Step 2: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API key
nano .env  # or use your favorite editor

# Update this line:
GEMINI_API_KEY=your_actual_api_key_here
```

### Step 3: Run Setup

```bash
./scripts/setup.sh
```

This will:
- Check prerequisites
- Validate configuration
- Pull Docker images
- Build application images

### Step 4: Start the System

```bash
./scripts/start.sh
```

This will start all services in the correct order:
1. Infrastructure (PostgreSQL, Redis, RabbitMQ)
2. MCP servers
3. Agents
4. Runner service

Wait for the message: `✅ QA Multi-Agent System is running!`

### Step 5: Test the System

```bash
./scripts/test.sh
```

This will:
1. Trigger a QA pipeline
2. Wait for execution
3. Show results

## 📊 Access the Services

Once running, you can access:

- **Runner API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (Interactive Swagger UI)
- **Health Check**: http://localhost:8000/health
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)

## 🔍 Verify Everything Works

### 1. Check Service Status

```bash
docker compose ps
```

All services should show "Up" status.

### 2. Check Logs

```bash
# All services
docker compose logs -f

# Just runner
docker compose logs -f runner

# Just MCP server
docker compose logs -f test-strategy-server
```

### 3. Test API Manually

```bash
# Health check
curl http://localhost:8000/health

# Trigger pipeline
curl -X POST http://localhost:8000/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "trigger_type": "pull_request",
    "repo_url": "https://github.com/test/repo",
    "branch": "main",
    "commit_sha": "abc123",
    "pull_request_id": "1"
  }'

# Get status (replace EXECUTION_ID)
curl http://localhost:8000/status/EXECUTION_ID
```

### 4. Explore API Documentation

Visit http://localhost:8000/docs to see interactive API documentation powered by Swagger UI.

## 📖 Understanding the Flow

When you trigger a test:

1. **Trigger** → Runner receives webhook/API call
2. **Orchestrator** → Analyzes code with Gemini AI
3. **Strategy** → MCP server generates test strategy
4. **Execution** → Unit test agent runs (simulated)
5. **Quality Gate** → Evaluates pass/fail criteria
6. **Results** → Returns execution status

## 🔧 Common Commands

```bash
# Start system
./scripts/start.sh

# Stop system
./scripts/stop.sh

# View logs
docker compose logs -f

# View specific service
docker compose logs -f runner

# Restart a service
docker compose restart runner

# Rebuild after code changes
docker compose build runner
docker compose up -d runner

# Clean everything (including volumes)
docker compose down -v
```

## 🐛 Troubleshooting

### Problem: Services won't start

```bash
# Check Docker daemon is running
docker ps

# Check ports are not in use
lsof -i :8000
lsof -i :5432
lsof -i :6379

# Clean and restart
docker compose down -v
./scripts/start.sh
```

### Problem: Gemini API errors

```bash
# Check API key is set
cat .env | grep GEMINI_API_KEY

# Test API key manually
curl -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key=YOUR_API_KEY"
```

### Problem: Redis connection errors

```bash
# Check Redis is running
docker compose ps redis

# Test Redis connection
docker compose exec redis redis-cli -a redispassword123 ping
```

### Problem: Port already in use

```bash
# Find what's using the port
sudo lsof -i :8000

# Kill the process or change port in .env
```

## 📚 Next Steps

Now that MVP is working, you can:

1. **Add More Agents** - Implement integration, E2E, security agents
2. **Add Real Testing** - Connect to actual Jest/Pytest MCP servers
3. **Add Monitoring** - Set up Prometheus & Grafana
4. **GitHub Integration** - Connect to real repositories
5. **Customize Quality Gates** - Adjust thresholds in .env

## 🎓 For Your Research

### MVP Demonstrates:

✅ Multi-agent architecture
✅ AI-powered test orchestration (Gemini)
✅ MCP protocol integration
✅ Microservices with Docker Compose
✅ Event-driven workflow
✅ Quality gate evaluation

### Metrics to Collect:

- Pipeline execution time
- Test strategy accuracy
- Agent coordination efficiency
- Resource utilization
- API response times

### Documentation Available:

- `architecture.md` - Complete system architecture
- `IMPLEMENTATION_GUIDE.md` - Full implementation details
- `SYSTEM_WORKFLOW.md` - Detailed workflow explanation
- `README.md` - Project overview

## 💡 Tips

1. **Keep logs open** while testing to see what's happening
2. **Use API docs** at /docs for interactive testing
3. **Check Redis** to see stored state: `docker compose exec redis redis-cli -a redispassword123`
4. **Monitor resources**: `docker stats`

## 🆘 Getting Help

If you encounter issues:

1. Check logs: `docker compose logs -f`
2. Verify .env configuration
3. Ensure all prerequisites are met
4. Try clean restart: `docker compose down -v && ./scripts/start.sh`

## ✅ Success Criteria

You'll know MVP is working when:

- ✅ `./scripts/test.sh` completes successfully
- ✅ You see quality gate results (PASS/FAIL)
- ✅ Execution time is ~15 seconds
- ✅ API docs are accessible
- ✅ Unit test results appear in response

Congratulations! You now have a working QA Multi-Agent System MVP! 🎉
