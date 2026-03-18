from datetime import datetime
from fastapi import APIRouter
from mcp_gateway.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "mcp-gateway-service",
        "version": "1.0.0",
        "environment": settings.env,
        "timestamp": datetime.utcnow().isoformat(),
        "upstream_services": {
            "auth_broker": settings.auth_broker_url,
            "tool_registry": settings.tool_registry_url,
            "policy_guardrail": settings.policy_guardrail_url,
            "tool_orchestrator": settings.tool_orchestrator_url,
            "audit_telemetry": settings.audit_telemetry_url,
        },
    }
