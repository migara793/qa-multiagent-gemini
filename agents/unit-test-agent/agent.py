"""
Unit Test Agent
Executes unit tests and generates coverage reports

Reference:
- Redis: https://redis.readthedocs.io/en/stable/examples/asyncio_examples.html
- Pika: https://pika.readthedocs.io/
"""
import asyncio
import os
import sys
import json
from datetime import datetime

import redis.asyncio as redis

# Configure Python path
sys.path.append('/app')

# Simple logger for agent
class Logger:
    def info(self, msg):
        print(f"[INFO] {datetime.utcnow().isoformat()} - {msg}")

    def error(self, msg):
        print(f"[ERROR] {datetime.utcnow().isoformat()} - {msg}")

    def debug(self, msg):
        print(f"[DEBUG] {datetime.utcnow().isoformat()} - {msg}")


logger = Logger()


class UnitTestAgent:
    """
    Unit test execution agent

    Simulates unit test execution for MVP
    In production, this would:
    - Clone the repository
    - Run Jest/Pytest via MCP servers
    - Collect coverage data
    - Report results
    """

    def __init__(self):
        self.redis_client = None
        self.redis_url = f"redis://:{os.getenv('REDIS_PASSWORD')}@{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}"

    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("✅ Connected to Redis")

        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            raise

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.aclose()
            logger.info("Disconnected from Redis")

    async def execute(self, execution_id: str):
        """
        Execute unit tests

        Args:
            execution_id: Execution ID from orchestrator

        Returns:
            Test results dictionary
        """
        logger.info(f"🧪 [Unit Test Agent] Starting execution for {execution_id}")

        try:
            # Get state from Redis
            state_key = f"execution:{execution_id}"
            state_json = await self.redis_client.get(state_key)

            if not state_json:
                logger.error(f"Execution {execution_id} not found in Redis")
                return

            state = json.loads(state_json)

            # Simulate unit test execution
            logger.info("Running unit tests...")
            await asyncio.sleep(2)  # Simulate test execution time

            # Generate mock results
            # In production, this would call Jest/Pytest MCP servers
            results = {
                "total": 45,
                "passed": 43,
                "failed": 2,
                "skipped": 0,
                "duration": 12.5,
                "coverage": {
                    "line": 82.5,
                    "branch": 68.0,
                    "function": 85.0,
                    "statement": 81.0
                },
                "failed_tests": [
                    {
                        "name": "UserAPI.createUser should validate email",
                        "file": "tests/unit/api/users.test.ts",
                        "line": 45,
                        "error": "Expected 400, got 500"
                    },
                    {
                        "name": "UserAPI.updateUser should require authentication",
                        "file": "tests/unit/api/users.test.ts",
                        "line": 67,
                        "error": "Expected 401, got 200"
                    }
                ]
            }

            # Update state
            state["unit_test_results"] = results

            # Save back to Redis
            await self.redis_client.setex(
                state_key,
                86400,  # 24 hours TTL
                json.dumps(state)
            )

            logger.info(
                f"✅ [Unit Test Agent] Completed: {results['passed']}/{results['total']} passed "
                f"({results['coverage']['line']:.1f}% coverage)"
            )

            # Update agent status
            await self.redis_client.hset(
                "agent_status",
                "unit-test-agent",
                json.dumps({
                    "status": "completed",
                    "execution_id": execution_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
            )

            return results

        except Exception as e:
            logger.error(f"❌ [Unit Test Agent] Error: {e}")

            # Update agent status with error
            await self.redis_client.hset(
                "agent_status",
                "unit-test-agent",
                json.dumps({
                    "status": "failed",
                    "execution_id": execution_id,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })
            )

            raise

    async def run_forever(self):
        """
        Run agent in continuous mode (listening to queue)

        For MVP, we'll just run once for testing
        In production, this would listen to RabbitMQ queue
        """
        await self.connect()

        logger.info("🎧 [Unit Test Agent] Listening for tasks...")

        # For MVP: Check Redis every 5 seconds for new executions
        while True:
            try:
                # Get all execution keys
                keys = []
                async for key in self.redis_client.scan_iter("execution:*"):
                    keys.append(key)

                # Process each execution (simplified for MVP)
                for key in keys:
                    execution_id = key.replace("execution:", "")

                    # Check if unit test already ran
                    state_json = await self.redis_client.get(key)
                    if state_json:
                        state = json.loads(state_json)

                        # Only run if strategy says to run unit tests and no results yet
                        if (state.get("test_strategy", {}).get("test_types") and
                            "unit" in state.get("test_strategy", {}).get("test_types", []) and
                            not state.get("unit_test_results")):

                            await self.execute(execution_id)

                # Wait before checking again
                await asyncio.sleep(5)

            except KeyboardInterrupt:
                logger.info("Shutting down...")
                break

            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(5)

        await self.disconnect()


async def main():
    """Main entry point"""
    agent = UnitTestAgent()

    try:
        await agent.run_forever()
    except KeyboardInterrupt:
        logger.info("Agent stopped by user")
    except Exception as e:
        logger.error(f"Agent crashed: {e}")
    finally:
        await agent.disconnect()


if __name__ == "__main__":
    logger.info("🚀 Starting Unit Test Agent")
    asyncio.run(main())
