"""
QA Multi-Agent System - Main Entry Point
FastAPI Reference: https://fastapi.tiangolo.com/
"""
import asyncio
import uuid
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

import sys
sys.path.append('/app')

from shared.config import settings
from shared.logger import setup_logger
from shared.state_manager import StateManager
from shared.models import TriggerPayload, ExecutionState, QualityGate, QualityGateCriteria, QualityGateActual, QualityGateStatus
from orchestrator.orchestrator_agent import OrchestratorAgent

# Setup logging
logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Reference: https://fastapi.tiangolo.com/advanced/events/
    """
    # Startup
    logger.info("🚀 Starting QA Multi-Agent System")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    # Initialize state manager
    app.state.state_manager = StateManager()
    await app.state.state_manager.connect()

    # Initialize orchestrator
    app.state.orchestrator = OrchestratorAgent(app.state.state_manager)
    await app.state.orchestrator.initialize()

    logger.info("✅ System initialized successfully")

    yield

    # Shutdown
    logger.info("🛑 Shutting down QA Multi-Agent System")
    await app.state.state_manager.disconnect()
    await app.state.orchestrator.shutdown()
    logger.info("✅ Shutdown complete")


# Create FastAPI app
# Reference: https://fastapi.tiangolo.com/tutorial/first-steps/
app = FastAPI(
    title="QA Multi-Agent System",
    description="Production-ready automated testing system with AI-powered multi-agent architecture",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "QA Multi-Agent System",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    Used by Docker HEALTHCHECK
    """
    return {
        "status": "healthy",
        "service": "qa-runner",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/trigger")
async def trigger_qa_pipeline(
    payload: TriggerPayload,
    background_tasks: BackgroundTasks
):
    """
    Trigger QA pipeline

    This endpoint is called by GitHub webhooks or CI/CD systems

    Args:
        payload: Trigger information (commit, branch, PR, etc.)
        background_tasks: FastAPI background tasks

    Returns:
        Execution ID and status

    Example payload:
    ```json
    {
        "trigger_type": "pull_request",
        "repo_url": "https://github.com/org/repo",
        "branch": "feature/new-api",
        "commit_sha": "a1b2c3d4",
        "pull_request_id": "42",
        "author": "john_doe"
    }
    ```

    Reference: https://fastapi.tiangolo.com/tutorial/background-tasks/
    """
    try:
        execution_id = str(uuid.uuid4())

        logger.info(
            f"📬 Received trigger: {payload.trigger_type} for {payload.repo_url}",
            extra={"execution_id": execution_id}
        )

        # Create initial execution state
        initial_state = ExecutionState(
            execution_id=execution_id,
            commit_sha=payload.commit_sha,
            branch=payload.branch,
            pull_request_id=payload.pull_request_id,
            repo_url=payload.repo_url,
            trigger_type=payload.trigger_type,
            author=payload.author,
            quality_gate=QualityGate(
                criteria=QualityGateCriteria(
                    min_coverage=settings.MIN_CODE_COVERAGE,
                    max_failed_tests=settings.MAX_FAILED_TESTS,
                    max_critical_vulnerabilities=settings.MAX_CRITICAL_VULNERABILITIES,
                    min_pass_rate=settings.MIN_PASS_RATE
                ),
                actual=QualityGateActual()
            )
        )

        # Store initial state
        await app.state.state_manager.set(
            f"execution:{execution_id}",
            initial_state.model_dump()
        )

        # Start pipeline in background
        background_tasks.add_task(
            run_qa_pipeline,
            execution_id,
            app.state.orchestrator,
            app.state.state_manager
        )

        return JSONResponse(
            status_code=202,
            content={
                "status": "accepted",
                "execution_id": execution_id,
                "message": "QA pipeline started",
                "trigger": payload.trigger_type
            }
        )

    except Exception as e:
        logger.error(f"❌ Error triggering pipeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def run_qa_pipeline(
    execution_id: str,
    orchestrator: OrchestratorAgent,
    state_manager: StateManager
):
    """
    Execute the complete QA pipeline

    This runs in the background and orchestrates all agents

    Args:
        execution_id: Unique execution ID
        orchestrator: Orchestrator agent instance
        state_manager: State manager instance
    """
    try:
        logger.info(f"🎬 Starting pipeline execution: {execution_id}")

        # Run orchestrator
        result = await orchestrator.execute(execution_id)

        # Store final result
        await state_manager.set(f"execution:{execution_id}", result)

        logger.info(
            f"✅ Pipeline completed: {execution_id} - "
            f"Status: {result.get('quality_gate', {}).get('status')}"
        )

    except Exception as e:
        logger.error(
            f"❌ Pipeline execution error: {execution_id} - {e}",
            exc_info=True
        )

        # Update state with error
        try:
            state = await state_manager.get(f"execution:{execution_id}")
            if state:
                state["quality_gate"]["status"] = QualityGateStatus.ERROR
                state["error"] = str(e)
                await state_manager.set(f"execution:{execution_id}", state)
        except Exception as state_error:
            logger.error(f"Failed to update error state: {state_error}")


@app.get("/status/{execution_id}")
async def get_execution_status(execution_id: str):
    """
    Get execution status and results

    Args:
        execution_id: Execution ID from /trigger response

    Returns:
        Execution state with results

    Example:
        GET /status/abc123-def456
    """
    try:
        result = await app.state.state_manager.get(f"execution:{execution_id}")

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Execution {execution_id} not found"
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching status for {execution_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status/commit/{commit_sha}")
async def get_status_by_commit(commit_sha: str):
    """
    Get execution status by commit SHA

    Args:
        commit_sha: Git commit SHA

    Returns:
        Execution state for the commit
    """
    # In a real implementation, you'd query a database
    # For now, we'll return a placeholder
    raise HTTPException(
        status_code=501,
        detail="Query by commit SHA not yet implemented. Please use /status/{execution_id}"
    )


@app.get("/agents/status")
async def get_all_agent_status():
    """
    Get status of all agents

    Returns:
        Dictionary of agent statuses
    """
    try:
        statuses = await app.state.state_manager.get_all_agent_status()
        return statuses

    except Exception as e:
        logger.error(f"Error fetching agent statuses: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/webhook/github")
async def github_webhook(
    payload: dict,
    background_tasks: BackgroundTasks
):
    """
    GitHub webhook endpoint

    Handles push and pull_request events

    Reference: https://docs.github.com/en/webhooks
    """
    try:
        event_type = payload.get("action", "push")

        # Extract relevant data from GitHub webhook
        trigger_payload = TriggerPayload(
            trigger_type="pull_request" if "pull_request" in payload else "push",
            repo_url=payload["repository"]["clone_url"],
            branch=payload.get("ref", "").replace("refs/heads/", ""),
            commit_sha=payload.get("after", payload.get("head_commit", {}).get("id")),
            pull_request_id=str(payload.get("pull_request", {}).get("number")) if "pull_request" in payload else None,
            author=payload.get("pusher", {}).get("name") or payload.get("sender", {}).get("login")
        )

        # Trigger the pipeline
        return await trigger_qa_pipeline(trigger_payload, background_tasks)

    except Exception as e:
        logger.error(f"Error processing GitHub webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # Run with uvicorn
    # Reference: https://www.uvicorn.org/
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
