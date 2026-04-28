"""
Orchestrator Agent - Coordinates the entire QA pipeline
Based on: https://google.github.io/adk-docs/agents/
Gemini API: https://ai.google.dev/gemini-api/docs
"""
import asyncio
import json
from typing import Dict, Any, List
from datetime import datetime

import google.generativeai as genai

import sys
sys.path.append('/app')

from shared.logger import setup_logger
from shared.config import settings
from shared.state_manager import StateManager
from shared.mcp_client import MCPClient, MCPClientManager
from shared.models import QualityGateStatus

logger = setup_logger(__name__)


class OrchestratorAgent:
    """
    Main orchestrator agent using Google Gemini

    Coordinates the entire QA pipeline:
    1. Analyzes code changes
    2. Generates test strategy
    3. Orchestrates parallel test execution
    4. Manages sequential analysis
    5. Evaluates quality gates

    Reference: https://googleapis.github.io/python-genai/
    """

    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager
        self.mcp_manager = MCPClientManager()
        self.model = None

    async def initialize(self):
        """Initialize the orchestrator"""
        try:
            # Configure Gemini
            # Reference: https://ai.google.dev/gemini-api/docs/quickstart
            genai.configure(api_key=settings.GEMINI_API_KEY)

            # Initialize Gemini model
            self.model = genai.GenerativeModel(settings.GEMINI_MODEL)

            logger.info(f"Initialized Gemini model: {settings.GEMINI_MODEL}")

            # Initialize MCP clients
            await self._initialize_mcp_clients()

            logger.info("✅ Orchestrator initialized")

        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}", exc_info=True)
            raise

    async def _initialize_mcp_clients(self):
        """
        Initialize connections to MCP servers

        Reference: https://modelcontextprotocol.io/specification/
        """
        # Define MCP servers
        # In production, these would be discovered dynamically
        mcp_servers = {
            "test-strategy": "http://test-strategy-server:3005",
            "code-analyzer": "http://code-analyzer-server:3009",
            "test-generation": "http://test-generation-server:3006",
        }

        for name, url in mcp_servers.items():
            try:
                await self.mcp_manager.add_client(name, url)
            except Exception as e:
                logger.warning(f"Failed to connect to {name} MCP server: {e}")

        logger.info(f"Connected to {len(self.mcp_manager.clients)} MCP servers")

    async def shutdown(self):
        """Shutdown the orchestrator"""
        await self.mcp_manager.disconnect_all()
        logger.info("Orchestrator shut down")

    async def execute(self, execution_id: str) -> Dict[str, Any]:
        """
        Execute the complete QA pipeline

        Pipeline stages:
        1. Code analysis & test strategy
        2. Parallel test execution (6 agents)
        3. Sequential analysis (3 agents)
        4. Regression loop (if needed)
        5. Quality gate decision

        Args:
            execution_id: Unique execution ID

        Returns:
            Final execution state
        """
        start_time = datetime.utcnow()

        logger.info(
            f"🎬 Starting execution {execution_id}",
            extra={"execution_id": execution_id}
        )

        # Get initial state
        state = await self.state_manager.get(f"execution:{execution_id}")

        if not state:
            raise ValueError(f"Execution {execution_id} not found")

        try:
            # Stage 1: Analyze code and create test strategy
            logger.info("📊 Stage 1: Code analysis & strategy", extra={"execution_id": execution_id})
            await self._analyze_and_strategize(state)
            await self.state_manager.set(f"execution:{execution_id}", state)

            # Stage 2: Execute parallel test agents
            logger.info("🔀 Stage 2: Parallel test execution", extra={"execution_id": execution_id})
            await self._execute_parallel_tests(state)
            await self.state_manager.set(f"execution:{execution_id}", state)

            # Stage 3: Sequential analysis pipeline
            logger.info("📈 Stage 3: Analysis pipeline", extra={"execution_id": execution_id})
            await self._execute_analysis_pipeline(state)
            await self.state_manager.set(f"execution:{execution_id}", state)

            # Stage 4: Regression loop (if needed)
            if state.get("quality_gate", {}).get("actual", {}).get("pass_rate", 100) < settings.MIN_PASS_RATE:
                logger.info("🔄 Stage 4: Regression loop", extra={"execution_id": execution_id})
                await self._execute_regression_loop(state)
                await self.state_manager.set(f"execution:{execution_id}", state)

            # Stage 5: Quality gate decision
            logger.info("🚦 Stage 5: Quality gate", extra={"execution_id": execution_id})
            self._evaluate_quality_gate(state)

            # Finalize
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            state["execution_time"] = execution_time
            state["timestamp"] = datetime.utcnow().isoformat()

            logger.info(
                f"✅ Execution {execution_id} completed: {state['quality_gate']['status']} "
                f"({execution_time:.1f}s)",
                extra={"execution_id": execution_id}
            )

            return state

        except Exception as e:
            logger.error(
                f"❌ Execution {execution_id} failed: {e}",
                exc_info=True,
                extra={"execution_id": execution_id}
            )
            state["error"] = str(e)
            state["quality_gate"]["status"] = QualityGateStatus.ERROR
            return state

    async def _analyze_and_strategize(self, state: Dict[str, Any]):
        """
        Analyze code changes and create test strategy using Gemini

        Uses MCP servers for code analysis and Gemini for strategy generation
        """
        try:
            # Simulate code analysis (in production, would call git-server MCP)
            code_analysis = {
                "changed_files": ["src/api/users.ts", "src/routes.ts"],
                "lines_added": 150,
                "lines_removed": 20,
                "complexity": {"cyclomatic": 12, "cognitive": 8},
                "risk_level": "medium"
            }

            # Generate test strategy using Gemini
            strategy_prompt = f"""
Analyze this code change and generate a comprehensive test strategy.

Changed Files: {code_analysis.get('changed_files', [])}
Lines Changed: +{code_analysis.get('lines_added')} -{code_analysis.get('lines_removed')}
Complexity: {code_analysis.get('complexity')}
Risk Level: {code_analysis.get('risk_level')}
Trigger: {state.get('trigger_type')}

Determine:
1. Which test types to run (unit, integration, e2e, performance, security)
2. Priority level (critical, high, medium, low)
3. Estimated test duration in seconds
4. Whether parallel execution is recommended

Return ONLY a valid JSON object with keys: test_types, priority, estimated_duration, parallel_execution
"""

            # Call Gemini API
            # Reference: https://ai.google.dev/gemini-api/docs
            response = self.model.generate_content(strategy_prompt)

            # Parse response
            response_text = response.text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            elif response_text.startswith("```"):
                response_text = response_text.replace("```", "").strip()

            try:
                test_strategy = json.loads(response_text)
            except json.JSONDecodeError:
                # Fallback strategy if Gemini response isn't valid JSON
                logger.warning("Gemini returned non-JSON, using fallback strategy")
                test_strategy = {
                    "test_types": ["unit", "integration", "security"],
                    "priority": "high",
                    "estimated_duration": 300,
                    "parallel_execution": True
                }

            state["test_strategy"] = test_strategy
            state["mcp_servers_used"] = state.get("mcp_servers_used", []) + ["code-analyzer"]

            logger.info(f"Strategy: Run {len(test_strategy.get('test_types', []))} test types")

        except Exception as e:
            logger.error(f"Strategy generation failed: {e}", exc_info=True)
            # Use fallback strategy
            state["test_strategy"] = {
                "test_types": ["unit"],
                "priority": "medium",
                "estimated_duration": 180,
                "parallel_execution": False
            }

    async def _execute_parallel_tests(self, state: Dict[str, Any]):
        """
        Execute all test agents in parallel (simulated)

        In production, this would publish to RabbitMQ queues
        """
        test_types = state.get("test_strategy", {}).get("test_types", [])

        # Simulate parallel test execution
        tasks = []

        if "unit" in test_types:
            tasks.append(self._simulate_test_agent("unit-test", state))

        if "integration" in test_types:
            tasks.append(self._simulate_test_agent("integration-test", state))

        if "e2e" in test_types:
            tasks.append(self._simulate_test_agent("e2e-test", state))

        # Always run security
        tasks.append(self._simulate_test_agent("security-test", state))

        # Execute all in parallel
        await asyncio.gather(*tasks)

        state["agents_executed"] = state.get("agents_executed", []) + [
            "unit-test", "integration-test", "e2e-test", "security-test"
        ]

    async def _simulate_test_agent(self, agent_name: str, state: Dict[str, Any]):
        """Simulate test agent execution (placeholder)"""
        logger.info(f"Simulating {agent_name} agent")

        # Simulate work
        await asyncio.sleep(1)

        # Mock results
        if agent_name == "unit-test":
            state["unit_test_results"] = {
                "total": 45,
                "passed": 43,
                "failed": 2,
                "duration": 12.5,
                "coverage": {"line": 82.5, "branch": 68.0, "function": 85.0}
            }
        elif agent_name == "security-test":
            state["security_test_results"] = {
                "vulnerabilities": 2,
                "severity_counts": {"critical": 0, "high": 1, "medium": 1, "low": 0}
            }

    async def _execute_analysis_pipeline(self, state: Dict[str, Any]):
        """Execute sequential analysis agents (simulated)"""
        # Mock analysis
        state["test_analysis"] = {
            "pass_rate": 95.6,
            "flaky_tests": [],
            "coverage_delta": 2.5
        }

        state["detected_bugs"] = []

        state["agents_executed"] = state.get("agents_executed", []) + [
            "test-analyzer", "bug-detector", "report-generator"
        ]

    async def _execute_regression_loop(self, state: Dict[str, Any]):
        """Execute regression agent (simulated)"""
        state["retry_count"] = state.get("retry_count", 0) + 1
        state["agents_executed"] = state.get("agents_executed", []) + ["regression"]

    def _evaluate_quality_gate(self, state: Dict[str, Any]):
        """
        Evaluate quality gate criteria

        Determines if the build should pass or fail
        """
        criteria = state["quality_gate"]["criteria"]

        # Calculate actual metrics
        unit_results = state.get("unit_test_results", {})
        coverage = unit_results.get("coverage", {}).get("line", 0)

        total_tests = unit_results.get("total", 0)
        failed_tests = unit_results.get("failed", 0)
        passed_tests = total_tests - failed_tests
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        security_results = state.get("security_test_results", {})
        critical_vulns = security_results.get("severity_counts", {}).get("critical", 0)
        high_vulns = security_results.get("severity_counts", {}).get("high", 0)

        # Store actual values
        state["quality_gate"]["actual"] = {
            "coverage": coverage,
            "failed_tests": failed_tests,
            "critical_vulnerabilities": critical_vulns + high_vulns,
            "pass_rate": pass_rate
        }

        # Evaluate
        checks = {
            "coverage": coverage >= criteria["min_coverage"],
            "pass_rate": pass_rate >= criteria["min_pass_rate"],
            "failed_tests": failed_tests <= criteria["max_failed_tests"],
            "security": (critical_vulns + high_vulns) <= criteria["max_critical_vulnerabilities"]
        }

        # Determine status
        if all(checks.values()):
            state["quality_gate"]["status"] = QualityGateStatus.PASS
            state["quality_gate"]["passed"] = True
        elif pass_rate >= 90 and coverage >= 70:
            state["quality_gate"]["status"] = QualityGateStatus.WARN
            state["quality_gate"]["passed"] = False
        else:
            state["quality_gate"]["status"] = QualityGateStatus.FAIL
            state["quality_gate"]["passed"] = False

        # Generate recommendations using Gemini
        state["recommendations"] = self._generate_recommendations(checks, state)

    def _generate_recommendations(self, checks: Dict[str, bool], state: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        actual = state["quality_gate"]["actual"]
        criteria = state["quality_gate"]["criteria"]

        if not checks["coverage"]:
            recommendations.append(
                f"Increase code coverage from {actual['coverage']:.1f}% to {criteria['min_coverage']}%"
            )

        if not checks["pass_rate"]:
            recommendations.append(
                f"Fix {actual['failed_tests']} failing tests to achieve {criteria['min_pass_rate']}% pass rate"
            )

        if not checks["security"]:
            recommendations.append(
                f"Address {actual['critical_vulnerabilities']} critical/high security vulnerabilities"
            )

        if not recommendations:
            recommendations.append("All quality gates passed! Ready to merge.")

        return recommendations
