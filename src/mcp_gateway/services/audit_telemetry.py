"""
Audit / Telemetry Service Client
Fire-and-forget — never blocks the request path.
"""

import asyncio
import httpx
from mcp_gateway.config import settings
from mcp_gateway.models import AuditEvent
from mcp_gateway.utils.logger import logger


class AuditTelemetryClient:
    def __init__(self) -> None:
        self._base_url = settings.audit_telemetry_url

    def emit(self, event: AuditEvent) -> None:
        """Non-blocking emit — schedules as a background task."""
        asyncio.create_task(self._send(event))

    async def _send(self, event: AuditEvent) -> None:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                await client.post(
                    f"{self._base_url}/v1/audit/events",
                    json=event.model_dump(),
                )
        except Exception as exc:
            logger.warning("Failed to emit audit event — non-fatal", event_id=event.event_id, error=str(exc))
