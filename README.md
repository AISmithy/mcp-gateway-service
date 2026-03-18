# MCP Gateway Service

A unified orchestration gateway that serves as the single entry point for agents and tools. It implements the **Model Context Protocol (MCP)** to enable GitHub Copilot agents, VS Code, and IntelliJ clients to discover and execute tools through a controlled, policy-governed pipeline.

## Architecture

```
Client (Copilot Agent / VS Code / IntelliJ)
               │
               ▼
       ┌───────────────┐
       │  MCP Gateway   │  ← FastAPI on port 3000
       │   Service      │
       └──────┬────────┘
              │
   ┌──────────┼──────────────────────────────┐
   │          │          │          │         │
   ▼          ▼          ▼          ▼         ▼
Auth       Tool       Policy     Tool      Audit &
Broker    Registry   Guardrail  Orchestrator Telemetry
(:8001)   (:8002)    (:8003)    (:8004)    (:8005)
```

Every tool call follows the pipeline: **Auth → Discover → Policy → Execute → Audit**.

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check with service status and upstream URLs |
| `/mcp/tools` | GET | List available tools filtered by agent scopes |
| `/mcp/tools/call` | POST | Execute a tool with arguments |
| `/mcp/tools/status/{request_id}` | GET | Query execution status of a tool call |

## Services

| Service | Port | Responsibility |
|---------|------|----------------|
| **Auth Broker** | 8001 | Token validation, agent identity resolution, token exchange |
| **Tool Registry** | 8002 | Tool catalog and schema discovery, scope-based filtering |
| **Policy Guardrail** | 8003 | Policy evaluation, approval routing, deny/allow decisions |
| **Tool Orchestrator** | 8004 | Dispatches execution to downstream connectors (Jira, GitHub, ArgoCD, etc.) |
| **Audit & Telemetry** | 8005 | Fire-and-forget event logging for compliance and debugging |

## Prerequisites

- Python 3.11+

## Getting Started

**1. Clone and install dependencies:**

```bash
git clone https://github.com/AISmithy/mcp-gateway-service.git
cd mcp-gateway-service
pip install -r requirements.txt
```

**2. Configure environment:**

```bash
cp .env.example .env
# Edit .env with your settings
```

**3. Run the server:**

```bash
# Development (hot reload enabled)
python src/mcp_gateway/main.py

# Or via Uvicorn directly
uvicorn mcp_gateway.app:app --host 0.0.0.0 --port 3000 --reload
```

**4. Verify:**

```bash
curl http://localhost:3000/health
```

## Configuration

All settings are managed via environment variables (`.env` file supported):

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `3000` | Server port |
| `ENV` | `development` | Environment (`development` / `production`) |
| `AUTH_BROKER_URL` | `http://auth-broker-service:8001` | Auth Broker service URL |
| `TOOL_REGISTRY_URL` | `http://tool-registry-service:8002` | Tool Registry service URL |
| `POLICY_GUARDRAIL_URL` | `http://policy-guardrail-service:8003` | Policy Guardrail service URL |
| `TOOL_ORCHESTRATOR_URL` | `http://tool-orchestrator-service:8004` | Tool Orchestrator service URL |
| `AUDIT_TELEMETRY_URL` | `http://audit-telemetry-service:8005` | Audit & Telemetry service URL |
| `JWT_SECRET` | — | JWT signing secret |
| `JWT_ISSUER` | `mcp-gateway` | JWT issuer identifier |
| `RATE_LIMIT_REQUESTS` | `100` | Max requests per rate-limit window |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | Rate-limit window duration |
| `LOG_LEVEL` | `INFO` | Logging level |
| `AUTH_DISABLED` | `true` | Disable auth for local development |

## Authentication

- Bearer token authentication via `Authorization: Bearer <token>` header
- Tokens are validated through the Auth Broker service
- Returns `AgentIdentity` with agent ID, roles, and scopes
- Set `AUTH_DISABLED=true` for local development (bypasses auth with a dev identity)
- Paths `/health`, `/docs`, and `/openapi.json` are exempt from auth

## Project Structure

```
src/mcp_gateway/
├── app.py                  # FastAPI application factory
├── main.py                 # Uvicorn entrypoint
├── config.py               # Pydantic settings (env vars)
├── models.py               # Shared data models
├── gateway/
│   └── gateway.py          # Core orchestration pipeline
├── middleware/
│   ├── auth.py             # Bearer token auth middleware
│   └── request_id.py       # Request ID tracing middleware
├── routes/
│   ├── health.py           # Health check endpoint
│   └── mcp.py              # MCP protocol endpoints
├── services/
│   ├── auth_broker.py      # Auth Broker client
│   ├── tool_registry.py    # Tool Registry client
│   ├── policy_guardrail.py # Policy Guardrail client
│   ├── tool_orchestrator.py# Tool Orchestrator client
│   └── audit_telemetry.py  # Audit & Telemetry client
└── utils/
    └── logger.py           # Structured logging (structlog)
```

## Supported Tool Categories

Source Control · Ticketing · CI/CD · Deployment · Knowledge Search · Observability · Service Catalog · Testing · Approval Workflow

## License

Private — All rights reserved.
