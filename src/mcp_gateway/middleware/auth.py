from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from mcp_gateway.config import settings
from mcp_gateway.models import AgentIdentity
from mcp_gateway.services.auth_broker import AuthBrokerClient
from mcp_gateway.utils.logger import logger

_auth_client = AuthBrokerClient()

# Routes that do not require authentication
_PUBLIC_PATHS = {"/health", "/docs", "/openapi.json"}

# Dev stub identity used when AUTH_DISABLED=true
_DEV_IDENTITY = AgentIdentity(
    agent_id="dev-agent",
    user_id="dev-user",
    roles=["admin"],
    scopes=["*"],
    token="dev-token",
)


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in _PUBLIC_PATHS:
            return await call_next(request)

        # Dev bypass — set AUTH_DISABLED=true in .env to skip auth
        if settings.auth_disabled:
            logger.warning("Auth disabled — using dev identity (not for production)")
            request.state.agent = _DEV_IDENTITY
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"error": "Missing or invalid Authorization header"},
            )

        token = auth_header[7:]

        try:
            identity = await _auth_client.validate_token(token)
            request.state.agent = identity
            logger.debug("Agent authenticated", agent_id=identity.agent_id)
        except Exception as exc:
            logger.warning("Token validation failed", error=str(exc))
            return JSONResponse(
                status_code=401,
                content={"error": "Unauthorized — token validation failed"},
            )

        return await call_next(request)
