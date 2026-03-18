from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


# ─── Agent Identity ───────────────────────────────────────────────────────────

class AgentIdentity(BaseModel):
    agent_id: str
    user_id: str | None = None
    roles: list[str] = []
    scopes: list[str] = []
    token: str


# ─── Tool Registry ────────────────────────────────────────────────────────────

class ToolCategory(str, Enum):
    SOURCE_CONTROL = "source-control"
    TICKETING = "ticketing"
    CI_CD = "ci-cd"
    DEPLOYMENT = "deployment"
    KNOWLEDGE = "knowledge"
    OBSERVABILITY = "observability"
    SERVICE_CATALOG = "service-catalog"
    TESTING = "testing"
    APPROVAL_WORKFLOW = "approval-workflow"


class ToolDefinition(BaseModel):
    name: str
    description: str
    category: ToolCategory
    input_schema: dict[str, Any]
    connector: str
    requires_approval: bool = False
    policy_tags: list[str] = []


# ─── Policy ───────────────────────────────────────────────────────────────────

class PolicyDecision(BaseModel):
    allowed: bool
    requires_approval: bool = False
    reason: str | None = None
    applied_policies: list[str] = []


# ─── Tool Execution ───────────────────────────────────────────────────────────

class ToolCallStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    PENDING_APPROVAL = "pending_approval"


class ToolCallRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tool_name: str
    arguments: dict[str, Any] = {}
    agent: AgentIdentity
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ToolCallResult(BaseModel):
    request_id: str
    tool_name: str
    status: ToolCallStatus
    result: Any | None = None
    error: str | None = None
    approval_ticket_id: str | None = None
    duration_ms: int = 0


# ─── Audit ────────────────────────────────────────────────────────────────────

class AuditEventType(str, Enum):
    TOOL_CALL = "tool_call"
    AUTH_CHECK = "auth_check"
    POLICY_CHECK = "policy_check"
    TOOL_DISCOVERY = "tool_discovery"
    APPROVAL_REQUESTED = "approval_requested"


class AuditOutcome(str, Enum):
    ALLOWED = "allowed"
    DENIED = "denied"
    PENDING = "pending"
    ERROR = "error"


class AuditEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: AuditEventType
    request_id: str
    agent_id: str
    user_id: str | None = None
    tool_name: str | None = None
    outcome: AuditOutcome
    metadata: dict[str, Any] = {}
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ─── MCP Protocol Shapes ──────────────────────────────────────────────────────

class MCPToolSchema(BaseModel):
    name: str
    description: str
    inputSchema: dict[str, Any]


class MCPToolListResponse(BaseModel):
    tools: list[MCPToolSchema]


class MCPToolCallRequest(BaseModel):
    name: str
    arguments: dict[str, Any] = {}


class MCPContent(BaseModel):
    type: str = "text"
    text: str


class MCPToolCallResponse(BaseModel):
    content: list[MCPContent]
    request_id: str | None = None
    status: str | None = None
    isError: bool = False
