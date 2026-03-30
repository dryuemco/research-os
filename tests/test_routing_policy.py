from app.services.routing_policy_service import RoutingPolicyService


def test_routing_policy_loads_from_config() -> None:
    service = RoutingPolicyService.from_config()
    policy = service.get_policy_for_task("critical_review")

    assert policy is not None
    assert policy.privacy_level == "restricted"
    assert policy.preferred_providers[0] == "anthropic"
