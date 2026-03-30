from pydantic import BaseModel


class ComponentHealth(BaseModel):
    status: str
    detail: str | None = None


class HealthResponse(BaseModel):
    status: str
    app_env: str
    database: ComponentHealth
