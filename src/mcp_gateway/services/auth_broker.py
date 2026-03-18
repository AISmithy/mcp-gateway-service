"""
Auth / Token Broker Service Client
Validates bearer tokens and resolves agent identity + scopes.
"""

import httpx
from mcp_gateway.config import settings
from mcp_gateway.models import AgentIdentity
from mcp_gateway.utils.logger import logger


class AuthBrokerClient:
    def __init__(self) -> None:
        self._base_url = settings.auth_broker_url

    async def validate_token(self, bearer_token: str) -> AgentIdentity:
        logger.debug("Calling Auth Broker to validate token")

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{self._base_url}/v1/token/validate",
                headers={"Authorization": f"Bearer {bearer_token}"},
            )
            response.raise_for_status()
            return AgentIdentity(**response.json())

    async def exchange_token(self, agent_id: str, target_service: str) -> str:
        logger.debug("Requesting downstream token exchange", agent_id=agent_id, target=target_service)

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{self._base_url}/v1/token/exchange",
                json={"agent_id": agent_id, "target_service": target_service},
            )
            response.raise_for_status()
            return response.json()["token"]
