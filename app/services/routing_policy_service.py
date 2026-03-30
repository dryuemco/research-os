import json
from pathlib import Path

from app.core.config import get_settings
from app.schemas.routing import ModelRoutingPolicy, TaskRoutingPolicy


class RoutingPolicyService:
    def __init__(self, policy: ModelRoutingPolicy) -> None:
        self.policy = policy

    @classmethod
    def from_config(cls) -> "RoutingPolicyService":
        settings = get_settings()
        policy_data = json.loads(Path(settings.model_routing_policy_path).read_text())
        return cls(ModelRoutingPolicy.model_validate(policy_data))

    def get_policy_for_task(self, task_type: str) -> TaskRoutingPolicy | None:
        return self.policy.task_policies.get(task_type)
