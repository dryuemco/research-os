
def test_dashboard_and_memory_api_smoke(client):
    source_resp = client.post(
        "/memory/sources",
        json={"source_name": "internal", "source_uri": "internal://doc", "source_type": "internal"},
    )
    assert source_resp.status_code == 200
    source_id = source_resp.json()["source_id"]

    doc_resp = client.post(
        "/memory/documents",
        json={
            "title": "Org Profile",
            "category": "organization_profile",
            "source_id": source_id,
            "content_text": "Experienced team with large infrastructure.",
        },
    )
    assert doc_resp.status_code == 200

    block_resp = client.post(
        "/memory/blocks",
        json={
            "block_key": "org_profile_001",
            "category": "organization_profile",
            "title": "Institution Summary",
            "body_text": "Our organization has 20 years of project execution.",
            "tags": ["experience"],
        },
    )
    assert block_resp.status_code == 200
    block_id = block_resp.json()["id"]

    approve_resp = client.put(
        f"/memory/blocks/{block_id}",
        json={"approval_status": "approved", "approved_by": "operator-1"},
    )
    assert approve_resp.status_code == 200

    retrieval = client.post(
        "/memory/retrieval/preview?purpose=concept_note",
        json={"query_text": "project execution experience", "limit": 5},
    )
    assert retrieval.status_code == 200

    summary = client.get("/dashboard/summary")
    assert summary.status_code == 200
    assert "memory_blocks" in summary.json()

    audit = client.get("/dashboard/audit")
    assert audit.status_code == 200

    ui = client.get("/ui")
    assert ui.status_code == 200
    assert "RPOS Internal Operator Dashboard" in ui.text
