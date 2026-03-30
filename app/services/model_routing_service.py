import json
from pathlib import Path

from app.core.config import get_settings
from app.schemas.routing import ModelRoutingDecision, ModelRoutingPolicy, ModelRoutingRequest


class ModelRoutingService:
    def __init__(self, policy: ModelRoutingPolicy) -> None:
        self.policy = policy

    @classmethod
    def from_config(cls) -> "ModelRoutingService":
        settings = get_settings()
        policy_data = json.loads(Path(settings.model_routing_policy_path).read_text())
        return cls(ModelRoutingPolicy.model_validate(policy_data))

    def decide(self, request: ModelRoutingRequest) -> ModelRoutingDecision:
        task_policy = self.policy.task_policies.get(request.task_type.value)
        if task_policy is None:
            selected_provider = (
                request.preferred_provider
                or self.policy.default_fallback_provider
                or "unconfigured-provider"
            )
            return ModelRoutingDecision(
                policy_version=self.policy.policy_version,
                selected_provider=selected_provider,
                selected_model=request.preferred_model_family or "general",
                fallback_chain=[self.policy.default_fallback_provider],
                rationale=["task_policy_missing_default_used"],
            )

        candidates = list(task_policy.preferred_providers)
        if request.preferred_provider and request.preferred_provider in candidates:
            candidates.remove(request.preferred_provider)
            candidates.insert(0, request.preferred_provider)

        if request.approved_providers:
            candidates = [
                provider for provider in candidates if provider in request.approved_providers
            ]

        if request.local_only:
            candidates = [provider for provider in candidates if provider.startswith("local")]

        if not candidates:
            selected_provider = self.policy.default_fallback_provider
            rationale = ["no_candidate_after_constraints", "fallback_selected"]
        else:
            selected_provider = candidates[0]
            rationale = ["selected_first_eligible_provider"]

        if request.sensitivity not in task_policy.sensitivity_levels:
            rationale.append("sensitivity_outside_policy_range")

        return ModelRoutingDecision(
            policy_version=self.policy.policy_version,
            selected_provider=selected_provider,
            selected_model=request.preferred_model_family or task_policy.model_family,
            fallback_chain=task_policy.fallback_chain or [self.policy.default_fallback_provider],
            rationale=rationale,
        )
