from pathlib import Path


def test_render_blueprint_exists():
    assert Path("render.yaml").exists()


def test_github_pages_artifacts_exist():
    assert Path("docs/index.html").exists()
    assert Path("docs/site-config.example.js").exists()
    assert Path("docs/site-config.js").exists()
