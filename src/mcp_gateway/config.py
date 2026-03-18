from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Server
    port: int = 3000
    env: str = "development"

    # Downstream services
    auth_broker_url: str = "http://auth-broker-service:8001"
    tool_registry_url: str = "http://tool-registry-service:8002"
    policy_guardrail_url: str = "http://policy-guardrail-service:8003"
    tool_orchestrator_url: str = "http://tool-orchestrator-service:8004"
    audit_telemetry_url: str = "http://audit-telemetry-service:8005"

    # Auth
    jwt_secret: str = "dev-secret-change-in-prod"
    jwt_issuer: str = "mcp-gateway"

    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    # Logging
    log_level: str = "INFO"

    # Development
    auth_disabled: bool = True


settings = Settings()
