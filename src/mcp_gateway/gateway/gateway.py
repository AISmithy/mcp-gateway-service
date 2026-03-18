"""
MCP Gateway — Core Orchestration

Flow for every tool call:
  1. Auth     → Validate token via Auth Broker
  2. Discover → Resolve tool definition from Tool Registry
  3. Policy   → Evaluate guardrails (allow / deny / require approval)
  4. Execute  → Dispatch to Tool Orchestrator
  5. Audit    → Emit event to Audit/Telemetry Service (non-blocking)
"""

import time
import uuid
from typing import Any

from mcp_gateway.models import (
    AgentIdentity,
    AuditEvent,
    AuditEventType,
    AuditOutcome,
    ToolCallRequest,
    ToolCallResult,
    ToolCallStatus,
    ToolDefinition,
)
from mcp_gateway.services.audit_telemetry import AuditTelemetryClient
from mcp_gateway.services.policy_guardrail import PolicyGuardrailClient
from mcp_gateway.services.tool_orchestrator import ToolOrchestratorClient
from mcp_gateway.services.tool_registry import ToolRegistryClient
from mcp_gateway.utils.logger import logger


class MCPGateway:
    def __init__(self) -> None:
        self._registry = ToolRegistryClient()
        self._policy = PolicyGuardrailClient()
        self._orchestrator = ToolOrchestratorClient()
        self._audit = AuditTelemetryClient()

    # ─── Tool Discovery ───────────────────────────────────────────────────────

    async def list_available_tools(self, agent: AgentIdentity) -> list[ToolDefinition]:
        tools = await self._registry.list_tools(agent.scopes)

        self._audit.emit(self._build_audit(
            event_type=AuditEventType.TOOL_DISCOVERY,
            request_id=str(uuid.uuid4()),
            agent=agent,
            outcome=AuditOutcome.ALLOWED,
            metadata={"tool_count": len(tools)},
        ))

        return tools

    # ─── Tool Execution ───────────────────────────────────────────────────────

    async def execute_tool(
        self,
        agent: AgentIdentity,
        tool_name: str,
        tool_args: dict[str, Any],
    ) -> ToolCallResult:
        request_id = str(uuid.uuid4())
        start = time.monotonic()

        logger.info("Gateway: processing tool call", request_id=request_id, tool_name=tool_name, agent_id=agent.agent_id)

        # 1. Resolve tool definition
        tool_def = await self._registry.get_tool(tool_name)
        if tool_def is None:
            self._emit_denied(request_id, agent, tool_name, "Tool not found in registry")
            return self._error_result(request_id, tool_name, "Tool not found", start)

        # 2. Policy evaluation
        decision = await self._policy.evaluate(agent, tool_name, tool_args)

        if not decision.allowed:
            logger.warning("Policy denied tool call", request_id=request_id, tool_name=tool_name, reason=decision.reason)
            self._emit_denied(request_id, agent, tool_name, decision.reason or "Policy denied")
            return self._error_result(request_id, tool_name, f"Denied: {decision.reason}", start)

        # 3. Requires approval → route to Approval Workflow (ServiceNow / Change Mgmt)
        if decision.requires_approval:
            logger.info("Tool call requires approval", request_id=request_id, tool_name=tool_name)

            request = ToolCallRequest(request_id=request_id, tool_name=tool_name, arguments=tool_args, agent=agent)
            pending = await self._orchestrator.execute_tool(request)

            self._audit.emit(self._build_audit(
                event_type=AuditEventType.APPROVAL_REQUESTED,
                request_id=request_id,
                agent=agent,
                tool_name=tool_name,
                outcome=AuditOutcome.PENDING,
                metadata={"approval_ticket_id": pending.approval_ticket_id},
            ))
            return pending

        # 4. Execute via Orchestrator
        request = ToolCallRequest(request_id=request_id, tool_name=tool_name, arguments=tool_args, agent=agent)
        result = await self._orchestrator.execute_tool(request)

        # 5. Emit audit event
        self._audit.emit(self._build_audit(
            event_type=AuditEventType.TOOL_CALL,
            request_id=request_id,
            agent=agent,
            tool_name=tool_name,
            outcome=AuditOutcome.ERROR if result.status == ToolCallStatus.ERROR else AuditOutcome.ALLOWED,
            metadata={"duration_ms": result.duration_ms, "status": result.status},
        ))

        return result

    # ─── Helpers ─────────────────────────────────────────────────────────────

    def _emit_denied(self, request_id: str, agent: AgentIdentity, tool_name: str, reason: str) -> None:
        self._audit.emit(self._build_audit(
            event_type=AuditEventType.POLICY_CHECK,
            request_id=request_id,
            agent=agent,
            tool_name=tool_name,
            outcome=AuditOutcome.DENIED,
            metadata={"reason": reason},
        ))

    def _error_result(self, request_id: str, tool_name: str, error: str, start: float) -> ToolCallResult:
        return ToolCallResult(
            request_id=request_id,
            tool_name=tool_name,
            status=ToolCallStatus.ERROR,
            error=error,
            duration_ms=int((time.monotonic() - start) * 1000),
        )

    def _build_audit(
        self,
        *,
        event_type: AuditEventType,
        request_id: str,
        agent: AgentIdentity,
        outcome: AuditOutcome,
        metadata: dict[str, Any],
        tool_name: str | None = None,
    ) -> AuditEvent:
        return AuditEvent(
            event_type=event_type,
            request_id=request_id,
            agent_id=agent.agent_id,
            user_id=agent.user_id,
            tool_name=tool_name,
            outcome=outcome,
            metadata=metadata,
        )
