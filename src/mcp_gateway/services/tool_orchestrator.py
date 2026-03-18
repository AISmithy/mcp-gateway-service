"""
Tool Orchestrator Service Client
Dispatches tool execution to the appropriate downstream connector:
  - Knowledge Search  → Confluence / Wiki / ADRs
  - Ticketing         → Jira / Azure Boards
  - Source Control    → GitHub Enterprise
  - CI/CD             → GitHub Actions / Jenkins
  - Deployment        → ArgoCD / Spinnaker
  - Service Catalog   → Backstage / CMDB
  - Observability     → Splunk / Datadog / Prometheus
  - Test Execution    → Non-prod Test Environments
  - Approval Workflow → ServiceNow / Change Mgmt
"""

import time
import httpx
from mcp_gateway.config import settings
from mcp_gateway.models import ToolCallRequest, ToolCallResult
from mcp_gateway.utils.logger import logger


class ToolOrchestratorClient:
    def __init__(self) -> None:
        self._base_url = settings.tool_orchestrator_url

    async def execute_tool(self, request: ToolCallRequest) -> ToolCallResult:
        logger.info(
            "Dispatching tool call to orchestrator",
            request_id=request.request_id,
            tool_name=request.tool_name,
        )

        start = time.monotonic()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self._base_url}/v1/tools/execute",
                json=request.model_dump(),
            )
            response.raise_for_status()

        result = ToolCallResult(**response.json())
        result.duration_ms = int((time.monotonic() - start) * 1000)

        logger.info(
            "Tool call completed",
            request_id=request.request_id,
            tool_name=request.tool_name,
            status=result.status,
        )
        return result

    async def get_execution_status(self, request_id: str) -> ToolCallResult:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{self._base_url}/v1/tools/status/{request_id}"
            )
            response.raise_for_status()
            return ToolCallResult(**response.json())
