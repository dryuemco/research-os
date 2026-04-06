from pathlib import Path

DASHBOARD_PAGE_KEYS = [
    "overview",
    "health",
    "opportunities",
    "matches",
    "notifications",
    "operations",
    "proposals",
    "exports",
    "intelligence",
]


def test_dashboard_index_contains_expected_page_shell_ids():
    content = Path("docs/index.html").read_text(encoding="utf-8")
    for key in DASHBOARD_PAGE_KEYS:
        assert f'data-page="{key}"' in content
        assert f'id="page-{key}"' in content


def test_dashboard_app_uses_modular_frontend_files():
    content = Path("docs/app.js").read_text(encoding="utf-8")
    assert "./js/config.js" in content
    assert "./js/api-client.js" in content
    assert "./js/pages.js" in content


def test_pages_js_calls_live_backend_endpoints():
    content = Path("docs/js/pages.js").read_text(encoding="utf-8")
    assert "/dashboard/summary" in content
    assert "/dashboard/opportunities" in content
    assert "/dashboard/matches" in content
    assert "/dashboard/operations/jobs" in content
    assert "/memory/exports" in content
    assert "/intelligence/retrieval/preview" in content
