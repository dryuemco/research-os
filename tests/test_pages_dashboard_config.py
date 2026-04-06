from pathlib import Path


def test_pages_site_config_targets_render_backend():
    content = Path("docs/site-config.js").read_text(encoding="utf-8")
    assert "https://rpos-api.onrender.com" in content
    assert "requestTimeoutMs" in content
    assert "notificationsUserId" in content


def test_pages_dashboard_entry_references_static_assets():
    content = Path("docs/index.html").read_text(encoding="utf-8")
    assert 'src="./site-config.js"' in content
    assert 'src="./app.js"' in content
    assert 'href="./styles.css"' in content
