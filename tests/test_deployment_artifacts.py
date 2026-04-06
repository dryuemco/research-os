from pathlib import Path


def test_render_blueprint_exists():
    assert Path("render.yaml").exists()


def test_github_pages_artifacts_exist():
    assert Path("docs/index.html").exists()
    assert Path("docs/app.js").exists()
    assert Path("docs/js/config.js").exists()
    assert Path("docs/js/api-client.js").exists()
    assert Path("docs/js/ui.js").exists()
    assert Path("docs/js/pages.js").exists()
    assert Path("docs/styles.css").exists()
    assert Path("docs/site-config.example.js").exists()
    assert Path("docs/site-config.js").exists()
    assert Path("docs/.nojekyll").exists()
    assert not Path(".github/workflows/deploy-pages.yml").exists()
