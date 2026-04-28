"""
Shared state management using Redis
Based on: https://redis.readthedocs.io/en/stable/examples/asyncio_examples.html
"""
import json
from typing import Dict, Any, Optional
import redis.asyncio as redis

from .logger import setup_logger
from .config import settings

logger = setup_logger(__name__)


class StateManager:
    """
    Manages shared state across agents using Redis

    Reference: https://redis.io/docs/latest/integrate/redis-py/
    """

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None

    async def connect(self):
        """
        Connect to Redis server

        Uses redis.asyncio for async/await support
        Reference: https://redis.readthedocs.io/en/stable/examples/asyncio_examples.html
        """
        try:
            self.redis_client = await redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )

            # Test connection
            await self.redis_client.ping()

            logger.info(f"Connected to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}")

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.aclose()
            logger.info("Disconnected from Redis")

    async def set(self, key: str, value: Dict[str, Any], ttl: int = 86400):
        """
        Store data in Redis with TTL

        Args:
            key: Redis key
            value: Dictionary to store (will be JSON serialized)
            ttl: Time to live in seconds (default 24 hours)
        """
        try:
            await self.redis_client.setex(
                key,
                ttl,
                json.dumps(value, default=str)
            )
            logger.debug(f"Stored key: {key}")

        except Exception as e:
            logger.error(f"Failed to set key {key}: {e}")
            raise

    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve data from Redis

        Args:
            key: Redis key

        Returns:
            Dictionary if key exists, None otherwise
        """
        try:
            data = await self.redis_client.get(key)

            if data:
                return json.loads(data)

            return None

        except Exception as e:
            logger.error(f"Failed to get key {key}: {e}")
            return None

    async def delete(self, key: str):
        """Delete a key from Redis"""
        try:
            await self.redis_client.delete(key)
            logger.debug(f"Deleted key: {key}")

        except Exception as e:
            logger.error(f"Failed to delete key {key}: {e}")

    async def exists(self, key: str) -> bool:
        """Check if a key exists"""
        try:
            return await self.redis_client.exists(key) > 0

        except Exception as e:
            logger.error(f"Failed to check key {key}: {e}")
            return False

    async def hset(self, name: str, key: str, value: Any):
        """
        Set hash field

        Args:
            name: Hash name
            key: Field name
            value: Value (will be JSON serialized if dict)
        """
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value, default=str)

            await self.redis_client.hset(name, key, value)
            logger.debug(f"Set hash field: {name}.{key}")

        except Exception as e:
            logger.error(f"Failed to set hash field {name}.{key}: {e}")
            raise

    async def hget(self, name: str, key: str) -> Optional[Any]:
        """Get hash field"""
        try:
            value = await self.redis_client.hget(name, key)

            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value

            return None

        except Exception as e:
            logger.error(f"Failed to get hash field {name}.{key}: {e}")
            return None

    async def hgetall(self, name: str) -> Dict[str, Any]:
        """Get all hash fields"""
        try:
            data = await self.redis_client.hgetall(name)

            result = {}
            for key, value in data.items():
                try:
                    result[key] = json.loads(value)
                except json.JSONDecodeError:
                    result[key] = value

            return result

        except Exception as e:
            logger.error(f"Failed to get hash {name}: {e}")
            return {}

    async def update_agent_status(self, agent_name: str, status: Dict[str, Any]):
        """
        Update agent execution status

        Args:
            agent_name: Name of the agent
            status: Status dictionary
        """
        await self.hset("agent_status", agent_name, status)

    async def get_agent_status(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get agent status"""
        return await self.hget("agent_status", agent_name)

    async def get_all_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        return await self.hgetall("agent_status")


# Example usage
if __name__ == "__main__":
    import asyncio

    async def main():
        manager = StateManager()
        await manager.connect()

        # Test operations
        await manager.set("test:key", {"hello": "world"})
        data = await manager.get("test:key")
        print(f"Retrieved: {data}")

        await manager.disconnect()

    asyncio.run(main())
