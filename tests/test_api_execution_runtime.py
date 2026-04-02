from app.schemas.provider import BudgetPolicySchema


def test_execution_runtime_endpoints(client):
    payload = {
        "task_type": "section_draft",
        "purpose": "draft section",
        "prompt": "Write section draft.",
        "approved_providers": ["mock-local"],
        "preferred_provider": "mock-local",
        "fallback_chain": ["mock-local"],
        "budget_policy": BudgetPolicySchema(run_budget_limit=10.0).model_dump(mode="json"),
    }
    create = client.post("/execution-runtime/tasks", json=payload)
    assert create.status_code == 200
    run_id = create.json()["id"]

    process = client.post("/execution-runtime/jobs/process-next")
    assert process.status_code == 200

    get_run = client.get(f"/execution-runtime/runs/{run_id}")
    assert get_run.status_code == 200
    assert get_run.json()["status"] in {"succeeded", "waiting_retry", "queued", "failed", "paused"}

    traces = client.get("/execution-runtime/traces")
    assert traces.status_code == 200

    preview = client.post(
        "/execution-runtime/routing-quota-preview",
        json={
            "task_type": "section_draft",
            "purpose": "preview",
            "approved_providers": ["mock-local"],
            "preferred_provider": "mock-local",
            "projected_spend": 0.1,
            "budget_policy": BudgetPolicySchema(run_budget_limit=10.0).model_dump(mode="json"),
        },
    )
    assert preview.status_code == 200
