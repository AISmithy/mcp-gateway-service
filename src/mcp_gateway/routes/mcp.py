"""
MCP Protocol Routes
Implements tool listing and tool call endpoints.
Compatible with GitHub Copilot Agent Mode and VS Code / IntelliJ MCP clients.
"""

from fastapi import APIRouter, Request, HTTPException
from mcp_gateway.gateway.gateway import MCPGateway
from mcp_gateway.models import (
    MCPContent,
    MCPToolCallRequest,
    MCPToolCallResponse,
    MCPToolListResponse,
    MCPToolSchema,
    ToolCallStatus,
    ToolCallResult,
)
from mcp_gateway.services.tool_orchestrator import ToolOrchestratorClient
from mcp_gateway.utils.logger import logger
import json

router = APIRouter(prefix="/mcp")
gateway = MCPGateway()


# ─── List Tools ───────────────────────────────────────────────────────────────

@router.get("/tools", response_model=MCPToolListResponse)
async def list_tools(request: Request) -> MCPToolListResponse:
    agent = request.state.agent

    try:
        tools = await gateway.list_available_tools(agent)
        return MCPToolListResponse(
            tools=[
                MCPToolSchema(
                    name=t.name,
                    description=t.description,
                    inputSchema=t.input_schema,
                )
                for t in tools
            ]
        )
    except Exception as exc:
        logger.error("Failed to list tools", agent_id=agent.agent_id, error=str(exc))
        raise HTTPException(status_code=500, detail="Failed to retrieve tool list")


# ─── Call Tool ────────────────────────────────────────────────────────────────

@router.post("/tools/call")
async def call_tool(request: Request, body: MCPToolCallRequest):
    agent = request.state.agent

    try:
        result: ToolCallResult = await gateway.execute_tool(agent, body.name, body.arguments)

        if result.status == ToolCallStatus.ERROR:
            return MCPToolCallResponse(
                content=[MCPContent(text=result.error or "Unknown error")],
                request_id=result.request_id,
                isError=True,
            )

        if result.status == ToolCallStatus.PENDING_APPROVAL:
            return MCPToolCallResponse(
                content=[MCPContent(text=f"Approval required. Ticket: {result.approval_ticket_id}")],
                request_id=result.request_id,
                status="pending_approval",
            )

        return MCPToolCallResponse(
            content=[MCPContent(text=json.dumps(result.result, indent=2))],
            request_id=result.request_id,
        )

    except Exception as exc:
        logger.error("Tool call failed", agent_id=agent.agent_id, tool_name=body.name, error=str(exc))
        raise HTTPException(status_code=500, detail="Internal gateway error")


# ─── Execution Status ─────────────────────────────────────────────────────────

@router.get("/tools/status/{request_id}")
async def get_tool_status(request_id: str):
    try:
        orchestrator = ToolOrchestratorClient()
        result = await orchestrator.get_execution_status(request_id)
        return result
    except Exception as exc:
        logger.error("Failed to get execution status", request_id=request_id, error=str(exc))
        raise HTTPException(status_code=500, detail="Failed to retrieve status")
