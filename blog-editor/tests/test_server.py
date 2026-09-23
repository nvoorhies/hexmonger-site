import io

import pytest

from blog_editor.server import create_app

from conftest import make_png


@pytest.fixture
def client(site):
    app = create_app(site)
    return app.test_client()


def test_write_preview_and_publish_a_post(client, site, tmp_path):
    r = client.post("/_api/posts", json={"title": "Hello tide"})
    assert r.status_code == 201
    slug = r.json["slug"]
    assert r.json["status"] == "draft"

    png = make_png(tmp_path / "shot.png", (2000, 1000))
    r = client.post(f"/_api/posts/{slug}/media",
                    data={"file": (io.BytesIO(png.read_bytes()), "Shot.png"), "web_size": "1"})
    assert r.json["names"] == ["shot.webp"]

    doc = {"meta": {"title": "Hello tide", "date": "2026-09-23", "summary": "Hi."},
           "body": "![The beach](shot.webp)\n\n$x$"}
    assert client.put(f"/_api/posts/{slug}/draft", json=doc).json["status"] == "draft"

    r = client.post(f"/_api/preview/{slug}", json=doc)
    assert r.json["errors"] == [] and 'data-line="0"' in r.json["html"]
    assert client.get(f"/_preview/{slug}/").status_code == 200
    assert client.get(f"/_preview/{slug}/shot.webp").status_code == 200
    assert client.get(f"/_preview/{slug}/draft.md").status_code == 400

    r = client.post(f"/_api/posts/{slug}/publish", json=doc)
    assert r.json["published"] and r.json["status"] == "published", r.json
    assert "blog/hello-tide/index.html" in r.json["changed"]
    assert client.get("/blog/hello-tide/").status_code == 200
    assert client.get("/blog/hello-tide").headers["Location"] == "/blog/hello-tide/"


def test_serves_the_site_but_not_the_editor_folder(client):
    assert client.get("/").status_code == 200
    assert client.get("/assets/site.css").status_code == 200
    assert client.get("/nowhere/").status_code == 404
    assert client.get("/blog-editor/pyproject.toml").status_code == 404
    assert client.get("/.git/config").status_code == 404


def test_refuses_other_sites_and_hosts(client):
    r = client.post("/_api/posts", json={"title": "x"}, headers={"Origin": "https://evil.example"})
    assert r.status_code == 403
    assert client.get("/_api/posts", headers={"Host": "evil.example"}).status_code == 403
