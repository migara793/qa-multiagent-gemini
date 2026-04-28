# QA Multi-Agent System

A production-ready Quality Assurance system using Google ADK, Gemini AI, and Model Context Protocol (MCP) for intelligent, automated software testing.

## 🚀 Features

- **Multi-Agent Architecture**: 10+ specialized AI agents working in parallel
- **Comprehensive Testing**: Unit, Integration, E2E, Performance, Security testing
- **AI-Powered**: Gemini AI for intelligent test generation and bug detection
- **MCP Integration**: Standardized protocol for AI tool integration (test-strategy-server)
- **Code Change Extraction**: Dedicated REST microservice (`code-analyzer`) pre-processes git diffs to reduce AI token usage by ~70%
- **Docker Compose**: Easy deployment with microservices
- **Real-time Monitoring**: Prometheus & Grafana dashboards
- **Quality Gates**: Automated pass/fail decisions
- **GitHub Integration**: Automatic PR status updates

## 📋 Prerequisites

- Docker & Docker Compose (v2.20.0+)
- Python 3.10+
- Node.js 18+ (for Jest MCP server)
- Git
- Gemini API Key ([Get it here](https://makersuite.google.com/app/apikey))

## 🛠️ Quick Start

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd qa-multiagent-gemini
```

### 2. Set up environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
nano .env
```

### 3. Run setup script

```bash
chmod +x scripts/*.sh
./scripts/setup.sh
```

### 4. Start the system

```bash
./scripts/start.sh
```

### 5. Access the services

- **Runner API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)

## 📚 Documentation

- [Implementation Guide](IMPLEMENTATION_GUIDE.md) - Complete setup and implementation
- [System Workflow](SYSTEM_WORKFLOW.md) - How the system works
- [Architecture](architecture.md) - System architecture details

## 🏗️ Architecture

```
Developer Push → GitHub Webhook → Runner → Orchestrator Agent
  → code-analyzer (REST) → structured summary → Gemini AI (MCP)
  → Parallel Test Agents (6) → Sequential Analysis (3)
  → Quality Gate → GitHub Status Update
```

> **Note on code-analyzer:** This is a direct HTTP REST microservice (port 8001), not an MCP server.
> It extracts structured change data from git commits before sending to Gemini, keeping AI token usage minimal.

## 🧪 Testing the System

```bash
# Trigger a test run
./scripts/test.sh

# Check logs
docker compose logs -f runner

# View specific service
docker compose logs -f test-strategy-server
```

## 📦 Project Structure

```
qa-multiagent-gemini/
├── runner/                 # Main orchestrator service (FastAPI, port 8080)
├── agents/                 # Test agent services (10 agents)
├── mcp-servers/           # MCP server implementations (test-strategy-server, port 3005)
├── services/
│   └── code-analyzer/     # REST microservice — git diff extraction & token optimization (port 8001)
├── infrastructure/        # Database, monitoring configs
├── shared/                # Shared libraries
├── scripts/               # Utility scripts
└── docker-compose.yml     # Service orchestration
```

## 🔧 Development

### Install Python dependencies

```bash
cd runner
pip install -r requirements.txt
```

### Run tests

```bash
pytest tests/
```

### Build Docker images

```bash
docker compose build
```

## 🚦 Quality Gates

The system evaluates:
- ✅ Code coverage ≥ 80%
- ✅ Test pass rate ≥ 95%
- ✅ Zero critical security vulnerabilities
- ✅ Performance within acceptable range

## 📊 Technologies Used

- **Google ADK** - Multi-agent orchestration
- **Gemini AI** - Intelligent testing
- **MCP** - Tool integration protocol
- **FastAPI** - Web framework
- **Docker Compose** - Container orchestration
- **PostgreSQL** - Database
- **Redis** - Caching & state management
- **RabbitMQ** - Message queue
- **Playwright** - E2E testing
- **Jest/Pytest** - Unit testing
- **Prometheus/Grafana** - Monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

MIT License

## 🙏 Acknowledgments

- Google ADK Team
- Model Context Protocol
- Gemini AI
- All open-source contributors

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Built for University Research Project**
*Advancing AI-powered software testing*
