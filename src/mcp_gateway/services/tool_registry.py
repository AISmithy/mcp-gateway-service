"""
Tool Registry Service Client
Discovers available tools and their schemas for a given agent/scope.
"""

import httpx
from mcp_gateway.config import settings
from mcp_gateway.models import ToolDefinition
from mcp_gateway.utils.logger import logger


class ToolRegistryClient:
    def __init__(self) -> None:
        self._base_url = settings.tool_registry_url

    async def list_tools(self, scopes: list[str]) -> list[ToolDefinition]:
        logger.debug("Fetching available tools from Tool Registry", scopes=scopes)

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{self._base_url}/v1/tools",
                params={"scopes": ",".join(scopes)},
            )
            response.raise_for_status()
            return [ToolDefinition(**t) for t in response.json()["tools"]]

    async def get_tool(self, tool_name: str) -> ToolDefinition | None:
        logger.debug("Fetching tool definition", tool_name=tool_name)

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{self._base_url}/v1/tools/{tool_name}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return ToolDefinition(**response.json())
