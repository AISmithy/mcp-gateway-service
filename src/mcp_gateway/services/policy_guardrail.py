"""
Policy / Guardrail Service Client
Evaluates whether an agent is allowed to call a specific tool.
"""

from typing import Any
import httpx
from mcp_gateway.config import settings
from mcp_gateway.models import AgentIdentity, PolicyDecision
from mcp_gateway.utils.logger import logger


class PolicyGuardrailClient:
    def __init__(self) -> None:
        self._base_url = settings.policy_guardrail_url

    async def evaluate(
        self,
        agent: AgentIdentity,
        tool_name: str,
        tool_args: dict[str, Any],
    ) -> PolicyDecision:
        logger.debug("Evaluating policy", agent_id=agent.agent_id, tool_name=tool_name)

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{self._base_url}/v1/policy/evaluate",
                json={
                    "agent_id": agent.agent_id,
                    "roles": agent.roles,
                    "scopes": agent.scopes,
                    "tool_name": tool_name,
                    "tool_args": tool_args,
                },
            )
            response.raise_for_status()
            return PolicyDecision(**response.json())
