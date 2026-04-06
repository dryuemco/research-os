from pathlib import Path


def test_render_blueprint_exists():
    assert Path("render.yaml").exists()


def test_github_pages_artifacts_exist():
    assert Path("pages/index.html").exists()
    assert Path(".github/workflows/deploy-pages.yml").exists()
    assert Path("pages/site-config.example.js").exists()
