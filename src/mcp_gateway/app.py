from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mcp_gateway.middleware.auth import AuthMiddleware
from mcp_gateway.middleware.request_id import RequestIdMiddleware
from mcp_gateway.routes import health, mcp
from mcp_gateway.utils.logger import logger, setup_logging

setup_logging()

app = FastAPI(
    title="MCP Gateway Service",
    description="Single entry point MCP Gateway for Agent/Tool orchestration",
    version="1.0.0",
)

# ─── Middleware (order matters — outermost added last) ────────────────────────
app.add_middleware(AuthMiddleware)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routes ───────────────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(mcp.router)


@app.on_event("startup")
async def on_startup():
    logger.info("MCP Gateway Service started")


@app.on_event("shutdown")
async def on_shutdown():
    logger.info("MCP Gateway Service shutting down")
