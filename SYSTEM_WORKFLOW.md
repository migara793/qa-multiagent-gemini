# QA Multi-Agent System - Complete Workflow Guide

## How The System Works When Code is Pushed to Repository

This document explains the **complete end-to-end workflow** of the QA Multi-Agent System from the moment a developer pushes code to the repository until the final quality gate decision.

### Key Design Decision: Token Optimization via code-analyzer

The `code-analyzer` microservice exists specifically to **reduce AI token consumption**.

Instead of sending raw git diffs and full file contents directly to Gemini (which can be thousands of tokens per file), the code-analyzer pre-processes the repository changes into a compact structured summary — only the essential facts (files changed, functions modified, risk score, affected modules) reach the AI. This keeps Gemini prompts lean and costs low regardless of how large the actual code change is.

```
WITHOUT code-analyzer (high token cost):
  Raw diff → Gemini  ❌ 10,000+ tokens per PR

WITH code-analyzer (optimized):
  Raw diff → code-analyzer → structured summary → Gemini  ✅ ~200 tokens per PR
```

---

## Table of Contents
1. [Workflow Overview](#workflow-overview)
2. [Trigger Mechanisms](#trigger-mechanisms)
3. [Detailed Step-by-Step Flow](#detailed-step-by-step-flow)
4. [Data Flow & State Management](#data-flow--state-management)
5. [Agent Communication](#agent-communication)
6. [Error Handling & Retry Logic](#error-handling--retry-logic)
7. [Timeline & Performance](#timeline--performance)
8. [Real-World Example](#real-world-example)
9. [Code Analyzer — Accuracy & Reliability](#code-analyzer--accuracy--reliability)

---

## Workflow Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DEVELOPER PUSHES CODE                             │
│                    git push origin feature/new-api                   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   GITHUB WEBHOOK TRIGGERED                           │
│              POST /trigger with payload (commit, branch, etc)        │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   RUNNER RECEIVES TRIGGER                            │
│              Creates execution ID, initializes shared state          │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│         PHASE 1: ORCHESTRATOR AGENT (30-60 seconds)                  │
│                                                                       │
│  Step 1: Fetch code changes from GitHub                             │
│  Step 2: Analyze diff (MCP: git-server)                             │
│  Step 3: Extract code changes (REST API: code-analyzer :8001)       │
│  Step 4: Generate test strategy (MCP: test-strategy-server + Gemini)│
│                                                                       │
│  Output: Test strategy → which tests to run, priority, resources    │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│      PHASE 2: PARALLEL TEST EXECUTION (5-15 minutes)                 │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ Unit Test    │  │ Integration  │  │ E2E Test     │              │
│  │ Agent        │  │ Test Agent   │  │ Agent        │              │
│  │              │  │              │  │              │              │
│  │ Jest/Pytest  │  │ API Testing  │  │ Playwright   │              │
│  │ Coverage     │  │ Contract     │  │ Screenshots  │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                  │                  │                      │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐              │
│  │ Performance  │  │ Security     │  │ Code Review  │              │
│  │ Test Agent   │  │ Test Agent   │  │ Agent        │              │
│  │              │  │              │  │              │              │
│  │ K6/JMeter    │  │ SonarQube    │  │ ESLint       │              │
│  │ Lighthouse   │  │ OWASP ZAP    │  │ Prettier     │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                       │
│  All agents write results to shared Redis state                     │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│      PHASE 3: SEQUENTIAL ANALYSIS (2-5 minutes)                      │
│                                                                       │
│  Step 1: Test Analyzer Agent                                        │
│    → Aggregates all test results                                    │
│    → Identifies flaky tests                                         │
│    → Compares against baseline                                      │
│    → Calculates metrics (pass rate, coverage, duration)             │
│                                                                       │
│  Step 2: Bug Detector Agent                                         │
│    → AI-powered bug pattern detection (Gemini)                      │
│    → Severity classification (critical, high, medium, low)          │
│    → Root cause analysis                                            │
│    → Creates GitHub Issues / JIRA tickets                           │
│                                                                       │
│  Step 3: Report Generator Agent                                     │
│    → Generates HTML report (Allure)                                 │
│    → Creates visualizations                                         │
│    → Sends Slack notifications                                      │
│    → Updates GitHub PR status                                       │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│             QUALITY GATE EVALUATION                                  │
│                                                                       │
│  Criteria:                                                           │
│  ✅ Code coverage ≥ 80%                                             │
│  ✅ Test pass rate ≥ 95%                                            │
│  ✅ Zero critical/high security vulnerabilities                     │
│  ✅ Performance within acceptable range                             │
│                                                                       │
│  Decision: PASS / FAIL / WARN                                       │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ├─── PASS ───┐
                             │            │
                             │            ▼
                             │    ┌────────────────────┐
                             │    │ ✅ Update PR       │
                             │    │ Status: APPROVED   │
                             │    │ Allow merge        │
                             │    └────────────────────┘
                             │
                             ├─── FAIL ───┐
                             │            │
                             │            ▼
                             │    ┌────────────────────┐
                             │    │ ❌ Block PR merge  │
                             │    │ Post review        │
                             │    │ comments           │
                             │    │ Notify team        │
                             │    └────────────────────┘
                             │
                             └─── WARN (with failures) ───┐
                                          │
                                          ▼
                             ┌────────────────────────────────────┐
                             │ PHASE 4: REGRESSION LOOP           │
                             │ (if pass rate < 95%)               │
                             │                                    │
                             │ Iteration 1: Retry flaky tests     │
                             │ Iteration 2: Auto-fix (Gemini)     │
                             │ Iteration 3: Final retry           │
                             │                                    │
                             │ Max 3 iterations                   │
                             └────────────┬───────────────────────┘
                                          │
                                          ▼
                             ┌────────────────────────────────────┐
                             │ Re-evaluate Quality Gate           │
                             └────────────────────────────────────┘
```

---

## Trigger Mechanisms

### 1. GitHub Webhook Integration

When code is pushed or PR is created, GitHub sends a webhook to your system:

**GitHub Webhook Configuration:**
```yaml
# In GitHub repository settings
Webhook URL: https://your-domain.com/trigger
Events:
  - push
  - pull_request
  - pull_request_review
Content type: application/json
Secret: your_webhook_secret
```

**Webhook Payload Example:**
```json
{
  "ref": "refs/heads/feature/new-api",
  "after": "a1b2c3d4e5f6",
  "repository": {
    "name": "my-app",
    "full_name": "org/my-app",
    "clone_url": "https://github.com/org/my-app.git"
  },
  "pusher": {
    "name": "john_doe",
    "email": "john@example.com"
  },
  "commits": [
    {
      "id": "a1b2c3d4e5f6",
      "message": "Add new API endpoint",
      "added": ["src/api/users.ts"],
      "modified": ["src/routes.ts"],
      "removed": []
    }
  ],
  "pull_request": {
    "number": 42,
    "title": "Add user management API",
    "state": "open"
  }
}
```

### 2. GitHub Actions Integration

**Alternative: Trigger from GitHub Actions**

`.github/workflows/qa-testing.yml`:
```yaml
name: QA Multi-Agent Testing

on:
  pull_request:
    types: [opened, synchronize, reopened]
  push:
    branches: [main, develop, release/*]

jobs:
  trigger-qa-system:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
        with:
          fetch-depth: 0  # Full history for diff

      - name: Trigger QA Multi-Agent System
        run: |
          curl -X POST https://your-qa-system.com/trigger \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer ${{ secrets.QA_SYSTEM_TOKEN }}" \
            -d '{
              "trigger_type": "pull_request",
              "repo_url": "${{ github.repositoryUrl }}",
              "branch": "${{ github.ref_name }}",
              "commit_sha": "${{ github.sha }}",
              "pull_request_id": "${{ github.event.pull_request.number }}",
              "author": "${{ github.actor }}",
              "commits": ${{ toJson(github.event.commits) }}
            }'

      - name: Wait for QA Results
        id: qa-status
        run: |
          execution_id=$(curl -s "https://your-qa-system.com/status?commit=${{ github.sha }}" | jq -r '.execution_id')

          # Poll for completion
          for i in {1..60}; do
            status=$(curl -s "https://your-qa-system.com/status/$execution_id" | jq -r '.quality_gate.status')

            if [ "$status" == "PASS" ]; then
              echo "QA passed!"
              exit 0
            elif [ "$status" == "FAIL" ]; then
              echo "QA failed!"
              exit 1
            fi

            echo "Waiting for QA completion... ($i/60)"
            sleep 30
          done

      - name: Post Results to PR
        if: always()
        uses: actions/github-script@v6
        with:
          script: |
            const result = await fetch('https://your-qa-system.com/status/${{ github.sha }}');
            const data = await result.json();

            const comment = `## 🤖 QA Multi-Agent Test Results

            **Status:** ${data.quality_gate.status}

            ### Test Results
            - **Unit Tests:** ${data.unit_test_results.passed}/${data.unit_test_results.total} passed
            - **Integration Tests:** ${data.integration_test_results.passed}/${data.integration_test_results.total} passed
            - **E2E Tests:** ${data.e2e_test_results.passed}/${data.e2e_test_results.total} passed

            ### Metrics
            - **Code Coverage:** ${data.quality_gate.actual.coverage}%
            - **Pass Rate:** ${data.quality_gate.actual.pass_rate}%
            - **Critical Vulnerabilities:** ${data.quality_gate.actual.critical_vulnerabilities}

            **Report:** [View Full Report](${data.report_url})
            `;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            });
```

---

## Detailed Step-by-Step Flow

### STEP 1: Code Push Event (T+0s)

```bash
# Developer pushes code
$ git add src/api/users.ts
$ git commit -m "Add user management API"
$ git push origin feature/user-api
```

**What happens:**
1. Git push triggers GitHub webhook
2. GitHub sends POST request to Runner
3. Runner validates webhook signature
4. Runner creates execution ID: `exec_a1b2c3d4`

---

### STEP 2: Runner Initialization (T+1s)

**Runner receives trigger:**

```python
# runner/main.py - Trigger handler

@app.post("/trigger")
async def trigger_qa_pipeline(payload: dict, background_tasks: BackgroundTasks):
    # Extract webhook data
    repo_url = payload["repository"]["clone_url"]
    commit_sha = payload["after"]
    branch = payload["ref"].replace("refs/heads/", "")
    pr_id = payload.get("pull_request", {}).get("number")

    # Create execution context
    execution_context = {
        "execution_id": str(uuid.uuid4()),
        "trigger_type": "pull_request" if pr_id else "push",
        "repo_url": repo_url,
        "commit_sha": commit_sha,
        "branch": branch,
        "pull_request_id": str(pr_id) if pr_id else None,
        "author": payload["pusher"]["name"],
        "timestamp": datetime.utcnow().isoformat()
    }

    # Store in database
    await db.executions.insert(execution_context)

    # Start pipeline in background
    background_tasks.add_task(
        run_qa_pipeline,
        execution_context,
        app.state.orchestrator,
        app.state.state_manager
    )

    # Update GitHub PR status to "pending"
    await github_client.create_status(
        repo_url,
        commit_sha,
        state="pending",
        description="QA Multi-Agent System started",
        context="qa-multiagent/tests"
    )

    return {
        "status": "accepted",
        "execution_id": execution_context["execution_id"]
    }
```

---

### STEP 3: Orchestrator - Code Analysis (T+5s)

**Orchestrator Agent analyzes code changes:**

```python
# runner/orchestrator/orchestrator_agent.py

async def _analyze_and_strategize(self, state: Dict[str, Any]):
    """Phase 1: Analyze code and generate test strategy"""

    # Step 1: Clone repository and fetch changes
    repo_path = await self._clone_repository(state["repo_url"], state["commit_sha"])

    # Step 2: Get git diff
    git_diff = await self.mcp_clients["git"].call_tool(
        "get_diff",
        {
            "repo_path": repo_path,
            "base": "main",
            "head": state["commit_sha"]
        }
    )
    # Output:
    # {
    #   "changed_files": ["src/api/users.ts", "src/routes.ts"],
    #   "lines_added": 150,
    #   "lines_removed": 20,
    #   "diff_content": "diff --git a/src/api/users.ts..."
    # }

    # Step 3: Extract code changes via REST API (code-analyzer microservice)
    # WHY REST and not MCP: code-analyzer is a pre-processing layer whose sole job is
    # to reduce AI token usage. Raw diffs can be 10,000+ tokens; the structured summary
    # output is ~200 tokens. Only the summary is ever sent to Gemini, keeping costs low.
    # It is a direct HTTP REST microservice, NOT an MCP server.
    code_analysis = await self.http_client.post(
        "http://code-analyzer:8001/analyze/commit",
        json={
            "repo_path": repo_path,
            "commit_ref": state["commit_sha"]
        }
    )
    # Output:
    # {
    #   "success": true,
    #   "data": {
    #     "commit_sha": "a1b2c3d4...",
    #     "commit_message": "Add user management API",
    #     "author": "john_doe",
    #     "files_changed": [
    #       {
    #         "file_path": "src/api/users.ts",
    #         "change_type": "added",
    #         "lines_added": 150,
    #         "lines_removed": 0,
    #         "language": "typescript",
    #         "functions_changed": ["createUser", "updateUser"],
    #         "complexity_delta": 8
    #       }
    #     ],
    #     "total_lines_added": 150,
    #     "total_lines_removed": 20,
    #     "risk_score": 7.0,
    #     "affected_modules": ["api"],
    #     "test_files_modified": false,
    #     "suggested_test_areas": ["Integration tests for api module"]
    #   }
    # }
    #
    # For PR diff analysis (base branch → PR head), use /analyze/diff:
    # POST http://code-analyzer:8001/analyze/diff
    # { "repo_path": ..., "base_ref": "main", "head_ref": "HEAD" }

    # Step 4: Generate test strategy using Gemini AI
    strategy_prompt = f"""
    Analyze this code change and generate a comprehensive test strategy:

    Changed Files: {git_diff['changed_files']}
    Lines Changed: +{git_diff['lines_added']} -{git_diff['lines_removed']}
    Complexity: {code_analysis['complexity']}
    Risk Level: {code_analysis['risk_level']}
    Trigger: {state['trigger_type']}

    Determine:
    1. Which test types to run (unit, integration, e2e, performance, security)
    2. Priority level (critical, high, medium, low)
    3. Affected components and modules
    4. Estimated test duration
    5. Resource requirements
    6. Whether full regression is needed

    Return as JSON with keys: test_types, priority, affected_components,
    estimated_duration, parallel_execution, regression_required
    """

    gemini_response = await self.model.generate_content(strategy_prompt)
    test_strategy = json.loads(gemini_response.text)

    # Output:
    # {
    #   "test_types": ["unit", "integration", "e2e", "security"],
    #   "priority": "high",
    #   "affected_components": ["auth", "api", "database"],
    #   "estimated_duration": 420,  # seconds
    #   "parallel_execution": true,
    #   "regression_required": false
    # }

    # Update shared state
    state["test_strategy"] = test_strategy
    state["code_diff"] = git_diff
    state["code_analysis"] = code_analysis

    # Store in Redis for agents to access
    await self.state_manager.set(f"execution:{state['execution_id']}", state)

    logger.info(f"Strategy: Run {len(test_strategy['test_types'])} test types")
```

---

### STEP 4: Parallel Test Execution (T+1min)

**Orchestrator dispatches tasks to agents via RabbitMQ:**

```python
async def _execute_parallel_tests(self, state: Dict[str, Any]):
    """Phase 2: Execute all test agents in parallel"""

    test_types = state["test_strategy"]["test_types"]

    # Publish messages to RabbitMQ queues
    tasks = []

    if "unit" in test_types:
        await self.rabbitmq.publish(
            queue="unit-test-queue",
            message={
                "execution_id": state["execution_id"],
                "repo_url": state["repo_url"],
                "commit_sha": state["commit_sha"],
                "files_to_test": state["code_analysis"]["changed_files"]
            }
        )
        tasks.append("unit-test")

    if "integration" in test_types:
        await self.rabbitmq.publish(
            queue="integration-test-queue",
            message={
                "execution_id": state["execution_id"],
                "repo_url": state["repo_url"],
                "affected_apis": state["code_analysis"]["affected_apis"]
            }
        )
        tasks.append("integration-test")

    # ... similar for other test types

    # Always run security and code review
    await self.rabbitmq.publish(queue="security-test-queue", ...)
    await self.rabbitmq.publish(queue="code-review-queue", ...)

    # Wait for all agents to complete (with timeout)
    completion_timeout = state["test_strategy"]["estimated_duration"] + 300

    await self._wait_for_agents(
        state["execution_id"],
        expected_agents=tasks,
        timeout=completion_timeout
    )
```

#### Unit Test Agent Execution

```python
# agents/unit-test-agent/agent.py

class UnitTestAgent:
    async def run(self):
        """Listen to RabbitMQ queue and process test requests"""

        async for message in self.rabbitmq_consumer("unit-test-queue"):
            execution_id = message["execution_id"]

            # Get shared state from Redis
            state = await self.redis.get(f"execution:{execution_id}")

            # Clone repository
            repo_path = await self.clone_repo(message["repo_url"], message["commit_sha"])

            # Step 1: Generate unit tests (if needed) using Gemini
            if state["test_strategy"].get("generate_tests", False):
                new_tests = await self.generate_tests(
                    files=message["files_to_test"],
                    repo_path=repo_path
                )
                await self.write_test_files(new_tests)

            # Step 2: Run Jest tests via MCP server
            jest_result = await self.jest_client.call_tool(
                "run_tests",
                {
                    "repo_path": repo_path,
                    "test_path": "tests/unit",
                    "config": "jest.config.js"
                }
            )
            # Output:
            # {
            #   "total": 45,
            #   "passed": 42,
            #   "failed": 3,
            #   "skipped": 0,
            #   "duration": 12.5,
            #   "failed_tests": [
            #     {
            #       "name": "UserAPI.createUser should validate email",
            #       "error": "Expected 400, got 500",
            #       "file": "tests/unit/api/users.test.ts",
            #       "line": 45
            #     }
            #   ]
            # }

            # Step 3: Generate coverage report
            coverage = await self.jest_client.call_tool(
                "generate_coverage",
                {"repo_path": repo_path}
            )
            # Output:
            # {
            #   "line": 78.5,
            #   "branch": 65.2,
            #   "function": 82.0,
            #   "statement": 77.8
            # }

            # Step 4: Update shared state
            state["unit_test_results"] = {
                **jest_result,
                "coverage": coverage
            }
            await self.redis.set(f"execution:{execution_id}", state)

            # Step 5: Notify completion
            await self.rabbitmq.publish(
                queue="agent-completion",
                message={
                    "execution_id": execution_id,
                    "agent": "unit-test",
                    "status": "completed",
                    "results": jest_result
                }
            )
```

#### E2E Test Agent Execution (Playwright)

```python
# agents/e2e-test-agent/agent.py

class E2ETestAgent:
    async def execute_tests(self, message):
        execution_id = message["execution_id"]
        state = await self.redis.get(f"execution:{execution_id}")

        # Run Playwright tests via MCP server
        playwright_result = await self.playwright_client.call_tool(
            "run_e2e_tests",
            {
                "base_url": state.get("staging_url", "http://localhost:3000"),
                "test_suite": "tests/e2e",
                "browsers": ["chromium", "firefox", "webkit"],
                "headless": True,
                "video": True,
                "screenshot_on_failure": True
            }
        )
        # Output:
        # {
        #   "total": 15,
        #   "passed": 14,
        #   "failed": 1,
        #   "duration": 145.8,
        #   "screenshots": [
        #     "results/screenshots/login-failure-chromium.png"
        #   ],
        #   "videos": [
        #     "results/videos/login-flow-chromium.webm"
        #   ],
        #   "failed_tests": [
        #     {
        #       "name": "User login flow",
        #       "error": "Timeout waiting for #submit-button",
        #       "screenshot": "results/screenshots/login-failure.png"
        #     }
        #   ]
        # }

        # Upload artifacts to S3
        await self.upload_artifacts(playwright_result["screenshots"])
        await self.upload_artifacts(playwright_result["videos"])

        # Update state
        state["e2e_test_results"] = playwright_result
        await self.redis.set(f"execution:{execution_id}", state)
```

#### Security Test Agent Execution

```python
# agents/security-test-agent/agent.py

class SecurityTestAgent:
    async def execute_tests(self, message):
        execution_id = message["execution_id"]
        repo_path = message["repo_path"]

        # Step 1: SAST with SonarQube
        sonar_result = await self.sonarqube_client.scan(
            project_key=message["repo_url"].split("/")[-1],
            sources=repo_path
        )
        # Output:
        # {
        #   "vulnerabilities": 3,
        #   "bugs": 5,
        #   "code_smells": 12,
        #   "security_hotspots": 2,
        #   "issues": [
        #     {
        #       "severity": "CRITICAL",
        #       "type": "VULNERABILITY",
        #       "message": "SQL injection vulnerability",
        #       "file": "src/api/users.ts",
        #       "line": 67
        #     }
        #   ]
        # }

        # Step 2: Dependency scanning with Snyk
        snyk_result = await self.snyk_client.test(repo_path)
        # Output:
        # {
        #   "vulnerabilities": [
        #     {
        #       "id": "SNYK-JS-JSONWEBTOKEN-1234567",
        #       "title": "JWT algorithm confusion",
        #       "severity": "high",
        #       "package": "jsonwebtoken@8.5.1",
        #       "fixed_in": "9.0.0"
        #     }
        #   ],
        #   "severity_counts": {
        #     "critical": 1,
        #     "high": 2,
        #     "medium": 5,
        #     "low": 8
        #   }
        # }

        # Step 3: DAST with OWASP ZAP (if app is deployed)
        if message.get("staging_url"):
            zap_result = await self.zap_client.active_scan(
                target=message["staging_url"]
            )

        # Aggregate results
        security_results = {
            "sast": sonar_result,
            "dependency_scan": snyk_result,
            "dast": zap_result if message.get("staging_url") else None,
            "severity_counts": {
                "critical": 1,
                "high": 4,
                "medium": 8,
                "low": 15
            },
            "total_vulnerabilities": 28
        }

        # Update state
        state = await self.redis.get(f"execution:{execution_id}")
        state["security_test_results"] = security_results
        await self.redis.set(f"execution:{execution_id}", state)
```

---

### STEP 5: Test Analysis (T+8min)

**Sequential analysis pipeline starts:**

```python
# agents/test-analyzer-agent/agent.py

class TestAnalyzerAgent:
    async def analyze(self, execution_id: str):
        # Get all test results from shared state
        state = await self.redis.get(f"execution:{execution_id}")

        # Aggregate results
        all_results = {
            "unit": state["unit_test_results"],
            "integration": state["integration_test_results"],
            "e2e": state["e2e_test_results"],
            "performance": state["performance_test_results"],
            "security": state["security_test_results"]
        }

        # Calculate metrics
        total_tests = sum(r.get("total", 0) for r in all_results.values())
        total_passed = sum(r.get("passed", 0) for r in all_results.values())
        total_failed = sum(r.get("failed", 0) for r in all_results.values())

        pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

        # Detect flaky tests (tests that failed in current run but passed before)
        flaky_tests = await self._detect_flaky_tests(state["commit_sha"])

        # Compare with baseline (previous runs on main branch)
        baseline = await self.db.get_baseline_metrics(state["branch"])
        coverage_delta = state["unit_test_results"]["coverage"]["line"] - baseline["coverage"]

        # Identify failure patterns using Gemini
        failure_analysis = await self._analyze_failures(all_results)

        # Update state
        state["test_analysis"] = {
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "pass_rate": pass_rate,
            "flaky_tests": flaky_tests,
            "coverage_delta": coverage_delta,
            "failure_patterns": failure_analysis,
            "regression_detected": coverage_delta < -5.0  # 5% drop
        }

        await self.redis.set(f"execution:{execution_id}", state)

        # Trigger next agent in pipeline
        await self.rabbitmq.publish("bug-detector-queue", {"execution_id": execution_id})
```

---

### STEP 6: Bug Detection (T+10min)

```python
# agents/bug-detector-agent/agent.py

class BugDetectorAgent:
    async def detect_bugs(self, execution_id: str):
        state = await self.redis.get(f"execution:{execution_id}")

        # Collect all failures
        all_failures = []
        all_failures.extend(state["unit_test_results"].get("failed_tests", []))
        all_failures.extend(state["integration_test_results"].get("failed_tests", []))
        all_failures.extend(state["e2e_test_results"].get("failed_tests", []))

        # AI-powered bug detection using Gemini
        detected_bugs = []

        for failure in all_failures:
            bug_analysis = await self.analyze_failure_with_ai(failure, state["code_diff"])

            if bug_analysis["is_real_bug"]:
                bug = {
                    "title": bug_analysis["title"],
                    "severity": bug_analysis["severity"],  # critical, high, medium, low
                    "description": bug_analysis["description"],
                    "root_cause": bug_analysis["root_cause"],
                    "file": failure["file"],
                    "line": failure.get("line"),
                    "suggested_fix": bug_analysis["suggested_fix"]
                }
                detected_bugs.append(bug)

                # Create GitHub issue for critical/high bugs
                if bug["severity"] in ["critical", "high"]:
                    await self.create_github_issue(state["repo_url"], bug)

        # Update state
        state["detected_bugs"] = detected_bugs
        await self.redis.set(f"execution:{execution_id}", state)

        # Trigger report generator
        await self.rabbitmq.publish("report-generator-queue", {"execution_id": execution_id})

    async def analyze_failure_with_ai(self, failure, code_diff):
        """Use Gemini to analyze if test failure indicates a real bug"""

        prompt = f"""
        Analyze this test failure and determine if it's a real bug:

        Test: {failure['name']}
        Error: {failure['error']}
        File: {failure['file']}

        Code changes:
        {code_diff['diff_content']}

        Determine:
        1. Is this a real bug or test flakiness?
        2. What is the severity? (critical, high, medium, low)
        3. What is the root cause?
        4. What is a suggested fix?

        Return JSON with: is_real_bug, severity, title, description, root_cause, suggested_fix
        """

        response = await self.gemini_model.generate_content(prompt)
        return json.loads(response.text)
```

---

### STEP 7: Report Generation (T+12min)

```python
# agents/report-generator-agent/agent.py

class ReportGeneratorAgent:
    async def generate_report(self, execution_id: str):
        state = await self.redis.get(f"execution:{execution_id}")

        # Generate HTML report using Allure
        report_path = await self._generate_allure_report(state)

        # Upload to S3/storage
        report_url = await self.upload_report(report_path)
        state["report_url"] = report_url

        # Create summary for Slack/GitHub
        summary = self._create_summary(state)

        # Send Slack notification
        await self.send_slack_notification(summary)

        # Post comment on GitHub PR
        if state["pull_request_id"]:
            await self.post_github_pr_comment(
                state["repo_url"],
                state["pull_request_id"],
                summary
            )

        await self.redis.set(f"execution:{execution_id}", state)

    def _create_summary(self, state):
        """Create human-readable summary"""

        quality_gate = state["quality_gate"]

        status_emoji = {
            "PASS": "✅",
            "FAIL": "❌",
            "WARN": "⚠️"
        }[quality_gate["status"]]

        summary = f"""
## {status_emoji} QA Multi-Agent Test Results

**Execution ID:** `{state['execution_id']}`
**Commit:** `{state['commit_sha'][:8]}`
**Branch:** `{state['branch']}`
**Duration:** {state['execution_time']:.1f}s

### 📊 Test Results

| Type | Passed | Failed | Total | Duration |
|------|--------|--------|-------|----------|
| Unit | {state['unit_test_results']['passed']} | {state['unit_test_results']['failed']} | {state['unit_test_results']['total']} | {state['unit_test_results']['duration']:.1f}s |
| Integration | {state['integration_test_results']['passed']} | {state['integration_test_results']['failed']} | {state['integration_test_results']['total']} | - |
| E2E | {state['e2e_test_results']['passed']} | {state['e2e_test_results']['failed']} | {state['e2e_test_results']['total']} | {state['e2e_test_results']['duration']:.1f}s |

### 📈 Quality Metrics

- **Code Coverage:** {quality_gate['actual']['coverage']:.1f}% (threshold: {quality_gate['criteria']['min_coverage']}%)
- **Pass Rate:** {quality_gate['actual']['pass_rate']:.1f}% (threshold: {quality_gate['criteria']['min_pass_rate']}%)
- **Critical Vulnerabilities:** {quality_gate['actual']['critical_vulnerabilities']} (max: {quality_gate['criteria']['max_critical_vulnerabilities']})

### 🐛 Detected Bugs

{len(state['detected_bugs'])} bugs detected:
""" + "\n".join([f"- [{b['severity'].upper()}] {b['title']}" for b in state['detected_bugs'][:5]])

        summary += f"""

### 📄 Full Report
[View Detailed Report]({state['report_url']})

---
*Generated by QA Multi-Agent System powered by Gemini AI*
        """

        return summary
```

---

### STEP 8: Quality Gate Evaluation (T+13min)

```python
# runner/orchestrator/orchestrator_agent.py

def _evaluate_quality_gate(self, state: Dict[str, Any]):
    """Final quality gate decision"""

    criteria = state["quality_gate"]["criteria"]

    # Calculate actual metrics
    unit_cov = state["unit_test_results"]["coverage"]["line"]

    total_tests = sum([
        state["unit_test_results"]["total"],
        state["integration_test_results"]["total"],
        state["e2e_test_results"]["total"]
    ])

    failed_tests = sum([
        state["unit_test_results"]["failed"],
        state["integration_test_results"]["failed"],
        state["e2e_test_results"]["failed"]
    ])

    critical_vulns = state["security_test_results"]["severity_counts"]["critical"]
    high_vulns = state["security_test_results"]["severity_counts"]["high"]

    passed_tests = total_tests - failed_tests
    pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

    # Store actual values
    state["quality_gate"]["actual"] = {
        "coverage": unit_cov,
        "pass_rate": pass_rate,
        "failed_tests": failed_tests,
        "critical_vulnerabilities": critical_vulns + high_vulns
    }

    # Evaluate each criterion
    checks = {
        "coverage": unit_cov >= criteria["min_coverage"],
        "pass_rate": pass_rate >= criteria["min_pass_rate"],
        "failed_tests": failed_tests <= criteria["max_failed_tests"],
        "security": (critical_vulns + high_vulns) <= criteria["max_critical_vulnerabilities"]
    }

    # Determine status
    if all(checks.values()):
        state["quality_gate"]["status"] = "PASS"
        state["quality_gate"]["passed"] = True
    elif pass_rate >= 90 and unit_cov >= 70:
        state["quality_gate"]["status"] = "WARN"
        state["quality_gate"]["passed"] = False
    else:
        state["quality_gate"]["status"] = "FAIL"
        state["quality_gate"]["passed"] = False

    # Generate recommendations
    state["recommendations"] = self._generate_recommendations(checks, state)

    return state

def _generate_recommendations(self, checks, state):
    """AI-powered recommendations using Gemini"""

    recommendations = []

    if not checks["coverage"]:
        recommendations.append(
            f"Increase code coverage from {state['quality_gate']['actual']['coverage']:.1f}% "
            f"to {state['quality_gate']['criteria']['min_coverage']}%"
        )

    if not checks["pass_rate"]:
        recommendations.append(
            f"Fix {state['quality_gate']['actual']['failed_tests']} failing tests"
        )

    if not checks["security"]:
        recommendations.append(
            f"Address {state['quality_gate']['actual']['critical_vulnerabilities']} "
            "critical/high security vulnerabilities"
        )

    return recommendations
```

---

### STEP 9: GitHub Status Update (T+14min)

```python
# Final step: Update GitHub PR status

async def update_github_status(state):
    """Update GitHub commit/PR status"""

    status = state["quality_gate"]["status"]

    # Map to GitHub status states
    github_state = {
        "PASS": "success",
        "WARN": "success",  # or "neutral" if using Checks API
        "FAIL": "failure"
    }[status]

    description = {
        "PASS": f"All tests passed! Coverage: {state['quality_gate']['actual']['coverage']:.1f}%",
        "WARN": f"Tests passed with warnings. Pass rate: {state['quality_gate']['actual']['pass_rate']:.1f}%",
        "FAIL": f"Quality gate failed. {state['quality_gate']['actual']['failed_tests']} tests failed"
    }[status]

    # Update commit status
    await github_client.create_status(
        repo=state["repo_url"],
        sha=state["commit_sha"],
        state=github_state,
        target_url=state["report_url"],
        description=description,
        context="qa-multiagent/tests"
    )

    # If PR exists, update checks
    if state["pull_request_id"]:
        await github_client.create_check_run(
            repo=state["repo_url"],
            name="QA Multi-Agent Tests",
            head_sha=state["commit_sha"],
            status="completed",
            conclusion=github_state,
            output={
                "title": f"QA Tests {status}",
                "summary": description,
                "text": state["recommendations"]
            }
        )
```

---

## Data Flow & State Management

### Redis Shared State Structure

```python
# Key: execution:{execution_id}
# Value: JSON

{
    "execution_id": "exec_a1b2c3d4",
    "commit_sha": "a1b2c3d4e5f6",
    "branch": "feature/user-api",
    "pull_request_id": "42",

    # Updated by Orchestrator (Phase 1)
    "test_strategy": {
        "test_types": ["unit", "integration", "e2e", "security"],
        "priority": "high",
        "estimated_duration": 420
    },

    # Updated by Unit Test Agent (Phase 2)
    "unit_test_results": {
        "total": 45,
        "passed": 42,
        "failed": 3,
        "coverage": {"line": 78.5, "branch": 65.2}
    },

    # Updated by Integration Test Agent (Phase 2)
    "integration_test_results": {...},

    # Updated by E2E Test Agent (Phase 2)
    "e2e_test_results": {...},

    # Updated by Security Test Agent (Phase 2)
    "security_test_results": {
        "severity_counts": {"critical": 1, "high": 2}
    },

    # Updated by Test Analyzer (Phase 3)
    "test_analysis": {
        "pass_rate": 93.3,
        "flaky_tests": ["UserAPI.login"],
        "coverage_delta": +2.5
    },

    # Updated by Bug Detector (Phase 3)
    "detected_bugs": [
        {
            "severity": "high",
            "title": "SQL injection in user search",
            "file": "src/api/users.ts",
            "line": 67
        }
    ],

    # Updated by Orchestrator (Final)
    "quality_gate": {
        "status": "WARN",
        "passed": false,
        "actual": {
            "coverage": 78.5,
            "pass_rate": 93.3,
            "failed_tests": 3,
            "critical_vulnerabilities": 3
        }
    },

    "report_url": "https://reports.qa-system.com/exec_a1b2c3d4",
    "execution_time": 840.5,
    "timestamp": "2026-04-14T10:30:00Z"
}
```

---

## Timeline & Performance

### Typical Execution Timeline

| Time | Phase | Activity | Duration |
|------|-------|----------|----------|
| T+0s | Trigger | GitHub webhook received | <1s |
| T+1s | Initialize | Runner creates execution context | <2s |
| T+5s | Phase 1 | Orchestrator analyzes code | 30-60s |
| T+1m | Phase 2 | Parallel test execution starts | 5-15min |
| - | - | Unit tests (Jest/Pytest) | 2-5min |
| - | - | Integration tests (API) | 3-7min |
| - | - | E2E tests (Playwright) | 5-15min |
| - | - | Performance tests (K6) | 3-10min |
| - | - | Security scan (SonarQube) | 2-8min |
| T+8m | Phase 3 | Sequential analysis starts | 2-5min |
| - | - | Test analyzer | 30s-1min |
| - | - | Bug detector (Gemini AI) | 1-2min |
| - | - | Report generator | 30s-1min |
| T+12m | Phase 4 | Quality gate evaluation | <10s |
| T+13m | Final | GitHub status update | <5s |
| **T+14m** | **Complete** | **Total execution time** | **~14min** |

### Performance Optimization

**Parallel execution** reduces total time from 30+ minutes (sequential) to ~14 minutes (parallel).

---

## Real-World Example

### Scenario: Developer adds new API endpoint

```javascript
// Developer adds this file: src/api/users.ts

export async function createUser(req, res) {
    const { email, password } = req.body;

    // Bug: No email validation!
    const user = await db.users.create({
        email,
        password: bcrypt.hash(password)
    });

    return res.json({ id: user.id });
}
```

### System Response:

**1. Code Change Extraction (code-analyzer REST API → `POST /analyze/commit`):**
- Detects new file `src/api/users.ts` was added
- Identifies functions changed: `createUser`
- Calculates risk score: 7.0 (new backend code, no tests modified)
- Flags `test_files_modified: false` → triggers test coverage warning
- Suggests: integration tests for `api` module

**2. Test Strategy (Gemini via test-strategy-server MCP):**
- Recommends: unit + integration + security tests

**2. Test Execution:**
- **Unit tests:** Generate tests for email validation, password hashing
- **Integration tests:** Test API endpoint with various payloads
- **Security scan:** Detects missing input validation (OWASP A03:2021)

**3. Bug Detection (Gemini):**
```json
{
  "severity": "high",
  "title": "Missing email validation in createUser",
  "description": "User input not validated, allows invalid emails",
  "suggested_fix": "Add email validation: if (!isValidEmail(email)) return 400"
}
```

**4. GitHub PR Comment:**
```markdown
## ⚠️ QA Multi-Agent Test Results

**Status:** WARN

### 🐛 Detected Issues
- [HIGH] Missing email validation in createUser (src/api/users.ts:5)
- [MEDIUM] Password hashing should be async

### 📊 Metrics
- Code Coverage: 65% (threshold: 80%)
- Security Vulnerabilities: 2 high

**Recommendation:** Add input validation before merging

[View Full Report](https://reports.qa-system.com/exec_abc123)
```

---

## Summary

The system provides **comprehensive, automated QA** that:

1. ✅ **Triggers automatically** on code push/PR
2. ✅ **Extracts code changes** via code-analyzer REST microservice (`POST /analyze/commit`, `/analyze/diff`)
3. ✅ **Generates test strategy** using Gemini AI via test-strategy-server (MCP)
4. ✅ **Runs tests in parallel** for speed
5. ✅ **Detects bugs proactively** using Gemini
6. ✅ **Generates detailed reports** with visualizations
7. ✅ **Updates GitHub automatically** with results
8. ✅ **Blocks merges** if quality gates fail
9. ✅ **Provides actionable recommendations**

**Result:** Faster feedback, higher code quality, fewer production bugs!

---

## Service Architecture Reference

| Service | Type | Protocol | Port | Purpose |
|---------|------|----------|------|---------|
| `runner` | Core | HTTP REST | 8080 | Pipeline trigger & orchestration |
| `test-strategy-server` | MCP Server | MCP over HTTP | 3005 | AI test strategy generation (Gemini) |
| `code-analyzer` | REST Microservice | HTTP REST | 8001 | Code change extraction — pre-processes diffs to reduce AI token usage |
| `postgres` | Infrastructure | TCP | 5433 | Execution state persistence |
| `redis` | Infrastructure | TCP | 6380 | Shared agent state |
| `rabbitmq` | Infrastructure | AMQP | 5672 | Agent task queue |

> **Important:** `code-analyzer` is a **direct REST API microservice**, not an MCP server.
> It is called with standard HTTP POST requests — not via the MCP protocol.
> Use `/analyze/commit` for single commits and `/analyze/diff` for PR branch comparisons.
>
> **Why not MCP?** The code-analyzer is a token optimization layer — it converts large raw diffs
> into compact structured summaries before they reach Gemini. There is no reason to route this
> through MCP since the AI never calls it directly; the orchestrator calls it first, then feeds
> the small structured output into the AI prompt.

---

## Code Analyzer — Accuracy & Reliability

### Attribute Accuracy Summary

Every attribute the code-analyzer extracts was tested and verified against raw git commands during research validation. Results below are based on live tests against the `online-store` JavaScript repository.

| # | Attribute | Computation Method | Verified Against | Accuracy |
|---|---|---|---|---|
| 1 | `files_changed` | `git diff-tree --name-status` | `git diff-tree` raw output | **100%** — exact match |
| 2 | `change_type` | Git status codes (A/M/D/R) | `git diff-tree` raw output | **100%** — exact match |
| 3 | `lines_added` | `git show --numstat` | `git show --numstat` raw output | **100%** — exact match |
| 4 | `lines_removed` | `git show --numstat` | `git show --numstat` raw output | **100%** — exact match |
| 5 | `language` | File extension lookup table | Manual file inspection | **~95%** — fails only on uncommon/no extension |
| 6 | `functions_changed` | Regex scan on diff `+` lines | Manual diff inspection | **~75%** — named functions; some arrow patterns missed |
| 7 | `classes_changed` | Regex scan on diff `+` lines | Manual diff inspection | **~75%** — same method as functions |
| 8 | `complexity_delta` | Decision-point counting (AST for Python, regex for JS/TS) | Manual counting of if/for/while/&&/\|\| | **~80%** — regex is accurate, full AST would be 95%+ |
| 9 | `risk_score` | 4-factor formula (files + lines + complexity + core files) | Manual formula calculation | **~85%** — formula verified, depends on upstream inputs |
| 10 | `test_files_modified` | Regex pattern match on file path | Manual file path check | **~95%** — covers all common test naming conventions |
| 11 | `affected_modules` | First directory component of file path | `git diff --name-only \| awk -F'/' '{print $1}'` | **~90%** — fails for flat repos with no subdirectory |
| 12 | `suggested_test_areas` | Rule-based on language + functions changed | Manual code review | **~80%** — deterministic rules, improves with function names |

---

### Bugs Found and Fixed During Research

Three bugs were discovered and fixed through live testing and cross-validation:

#### Bug 1: `lines_added` and `lines_removed` always returned 0
**Root cause:** The numstat parser used `output.split('\t')` on the full `git show` output, which includes a multi-line commit header before the numbers. Splitting the entire string by tab meant `parts[0]` contained the whole header text, not the number — causing `int()` to fail silently and return 0.

**Fix:** Added `_parse_numstat_line()` which iterates line-by-line and finds the correct data line where both first and second tab-separated values are digits.

**Impact:** All line count data was wrong for every commit before this fix.

---

#### Bug 2: `functions_changed` always returned `[]` for JavaScript/TypeScript files
**Root cause:** Hard-coded guard `if language != 'python': return [], []` at the top of `_get_changed_symbols()` — the function exited immediately for any non-Python file without attempting any extraction.

**Fix:** Added `_get_js_symbols_commit()` and `_parse_js_symbols()` methods that scan diff `+` lines using JS/TS-specific regex patterns for function definitions, arrow functions, and Express route handlers.

**Impact:** The AI received no information about which functions changed in JS/TS projects (the majority of web projects).

---

#### Bug 3: `complexity_delta` always returned `0` for JavaScript/TypeScript files
**Root cause:** Same hard-coded guard `if language != 'python': return 0` in `_calculate_complexity_delta()`.

**Fix:** Added `_calculate_js_complexity()` which counts cyclomatic decision points (`if`, `else if`, `for`, `while`, `case`, `catch`, `&&`, `||`, ternary `?`) after stripping comments and strings to avoid false matches.

**Impact:** `risk_score` was always underreported for JS/TS projects because the complexity factor (worth up to 25 points) was always 0, meaning genuinely risky changes appeared safer than they were.

---

### Risk Score Formula (Verified)

```
risk_score = Factor1 + Factor2 + Factor3 + Factor4   (max: 100)

Factor 1 (files scope):   min(num_files × 2,            25)
Factor 2 (lines changed): min((lines_added+removed) ÷ 10, 25)
Factor 3 (complexity):    min(complexity_delta × 5,      25)
Factor 4 (core files):    min(core_files_touched × 5,    25)

core_files = files whose path contains: main, core, config, server, app
```

**Live verification result (online-store, `backend/server.js` change):**
```
Factor 1: min(1×2, 25)   =  2.0
Factor 2: min(15÷10, 25) =  1.5
Factor 3: min(1×5, 25)   =  5.0   ← only accurate after Bug 3 fix
Factor 4: min(1×5, 25)   =  5.0   (server.js matches "server")
─────────────────────────────────
risk_score               = 13.5   ✅ matches API output exactly
```

---

### Manual Reliability Verification Commands

Run these at any time to confirm the service is accurate:

```bash
# 1. Health check
curl http://localhost:8001/health

# 2. Cross-check files_changed count
API_FILES=$(curl -s -X POST http://localhost:8001/analyze/commit \
  -H "Content-Type: application/json" \
  -d '{"repo_path":"/git-repos/online-store","commit_ref":"HEAD"}' \
  | python3 -c "import sys,json; print(len(json.load(sys.stdin)['data']['files_changed']))")
GIT_FILES=$(git -C /home/migara/Desktop/online-store diff-tree --no-commit-id --name-only -r HEAD | wc -l)
echo "API=$API_FILES  GIT=$GIT_FILES  MATCH=$([ "$API_FILES" = "$GIT_FILES" ] && echo YES || echo NO)"

# 3. Cross-check lines_added
API_ADDED=$(curl -s -X POST http://localhost:8001/analyze/commit \
  -H "Content-Type: application/json" \
  -d '{"repo_path":"/git-repos/online-store","commit_ref":"HEAD"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['total_lines_added'])")
GIT_ADDED=$(git -C /home/migara/Desktop/online-store show --numstat HEAD \
  | awk 'NF==3 && $1~/^[0-9]+$/{sum+=$1} END{print sum+0}')
echo "API=$API_ADDED  GIT=$GIT_ADDED  MATCH=$([ "$API_ADDED" = "$GIT_ADDED" ] && echo YES || echo NO)"

# 4. Verify risk_score is in valid range 0-100
RISK=$(curl -s -X POST http://localhost:8001/analyze/commit \
  -H "Content-Type: application/json" \
  -d '{"repo_path":"/git-repos/online-store","commit_ref":"HEAD"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['risk_score'])")
python3 -c "print('risk_score', $RISK, '→ VALID' if 0 <= $RISK <= 100 else '→ INVALID')"
```
