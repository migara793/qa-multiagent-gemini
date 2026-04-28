"""
MCP (Model Context Protocol) Client
Based on: https://modelcontextprotocol.io/specification/2025-11-25
"""
import httpx
from typing import Dict, Any, List, Optional

from .logger import setup_logger
from .config import settings

logger = setup_logger(__name__)


class MCPClient:
    """
    Client for communicating with MCP servers

    MCP Specification: https://modelcontextprotocol.io/specification/2025-11-25
    """

    def __init__(self, name: str, url: str, timeout: int = None):
        """
        Initialize MCP client

        Args:
            name: Server name for logging
            url: Base URL of the MCP server
            timeout: Request timeout in seconds
        """
        self.name = name
        self.url = url.rstrip("/")
        self.timeout = timeout or settings.MCP_TIMEOUT
        self.client: Optional[httpx.AsyncClient] = None

    async def connect(self):
        """Initialize HTTP client"""
        self.client = httpx.AsyncClient(
            base_url=self.url,
            timeout=self.timeout,
            headers={
                "Content-Type": "application/json",
                "MCP-Protocol-Version": settings.MCP_PROTOCOL_VERSION
            }
        )

        # Health check
        try:
            response = await self.client.get("/health")
            response.raise_for_status()
            logger.info(f"Connected to MCP server: {self.name} at {self.url}")

        except Exception as e:
            logger.warning(f"Health check failed for {self.name}: {e}")

    async def disconnect(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()
            logger.info(f"Disconnected from MCP server: {self.name}")

    async def call_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call a tool on the MCP server

        Args:
            tool_name: Name of the tool to invoke
            parameters: Tool parameters

        Returns:
            Tool execution result

        Reference: MCP Specification - Tool Calling
        """
        try:
            logger.debug(f"Calling MCP tool: {self.name}.{tool_name}")

            response = await self.client.post(
                "/mcp/call-tool",
                json={
                    "name": tool_name,
                    "parameters": parameters
                }
            )

            response.raise_for_status()
            result = response.json()

            logger.debug(f"MCP tool {self.name}.{tool_name} completed")

            return result

        except httpx.HTTPStatusError as e:
            logger.error(
                f"MCP call failed [{self.name}.{tool_name}]: "
                f"HTTP {e.response.status_code} - {e.response.text}"
            )
            raise

        except Exception as e:
            logger.error(f"MCP call failed [{self.name}.{tool_name}]: {e}")
            raise

    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available tools from the MCP server

        Returns:
            List of tool descriptions

        Reference: MCP Specification - Tool Discovery
        """
        try:
            response = await self.client.get("/mcp/list-tools")
            response.raise_for_status()

            tools = response.json()
            logger.debug(f"Listed {len(tools)} tools from {self.name}")

            return tools

        except Exception as e:
            logger.error(f"Failed to list tools from {self.name}: {e}")
            return []

    async def list_resources(self) -> List[Dict[str, Any]]:
        """
        List available resources from the MCP server

        Returns:
            List of resource descriptions

        Reference: MCP Specification - Resource Discovery
        """
        try:
            response = await self.client.get("/mcp/list-resources")
            response.raise_for_status()

            resources = response.json()
            logger.debug(f"Listed {len(resources)} resources from {self.name}")

            return resources

        except Exception as e:
            logger.error(f"Failed to list resources from {self.name}: {e}")
            return []

    async def get_resource(self, resource_uri: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific resource

        Args:
            resource_uri: URI of the resource

        Returns:
            Resource data

        Reference: MCP Specification - Resource Access
        """
        try:
            response = await self.client.post(
                "/mcp/get-resource",
                json={"uri": resource_uri}
            )

            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Failed to get resource {resource_uri} from {self.name}: {e}")
            return None

    async def list_prompts(self) -> List[Dict[str, Any]]:
        """
        List available prompts from the MCP server

        Returns:
            List of prompt descriptions

        Reference: MCP Specification - Prompt Discovery
        """
        try:
            response = await self.client.get("/mcp/list-prompts")
            response.raise_for_status()

            prompts = response.json()
            logger.debug(f"Listed {len(prompts)} prompts from {self.name}")

            return prompts

        except Exception as e:
            logger.error(f"Failed to list prompts from {self.name}: {e}")
            return []


class MCPClientManager:
    """Manages multiple MCP client connections"""

    def __init__(self):
        self.clients: Dict[str, MCPClient] = {}

    async def add_client(self, name: str, url: str):
        """Add and connect to an MCP server"""
        client = MCPClient(name, url)
        await client.connect()
        self.clients[name] = client
        logger.info(f"Added MCP client: {name}")

    async def get_client(self, name: str) -> Optional[MCPClient]:
        """Get an MCP client by name"""
        return self.clients.get(name)

    async def disconnect_all(self):
        """Disconnect all MCP clients"""
        for name, client in self.clients.items():
            await client.disconnect()
        self.clients.clear()

    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Convenience method to call a tool"""
        client = self.clients.get(server_name)

        if not client:
            logger.error(f"MCP server not found: {server_name}")
            return None

        return await client.call_tool(tool_name, parameters)


# Example usage
if __name__ == "__main__":
    import asyncio

    async def main():
        # Example: Connect to test-strategy server
        client = MCPClient("test-strategy", "http://localhost:3005")
        await client.connect()

        # List available tools
        tools = await client.list_tools()
        print(f"Available tools: {tools}")

        # Call a tool
        result = await client.call_tool(
            "generate_strategy",
            {"trigger_type": "pull_request"}
        )
        print(f"Result: {result}")

        await client.disconnect()

    asyncio.run(main())
