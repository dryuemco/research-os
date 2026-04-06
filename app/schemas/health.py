from pydantic import BaseModel, Field


class ComponentHealth(BaseModel):
    status: str
    detail: str | None = None


class HealthResponse(BaseModel):
    status: str
    app_env: str
    database: ComponentHealth
    dependencies: dict[str, dict] = Field(default_factory=dict)
