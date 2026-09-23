"""The editor's local web server.

- ``/_editor/`` — the editor itself.
- ``/_api/…`` — JSON for the editor: posts, drafts, media, preview, publish.
- ``/_preview/<slug>/`` — the post as it will look, from the editor's latest
  text; the post's media are served next to it, as they will be once live.
- everything else is the site folder, served as GitHub Pages would, so the
  preview's stylesheets, fonts and links are the real ones.

It listens on localhost only, and refuses requests that come from another
site in the same browser.
"""

from __future__ import annotations

import threading
from pathlib import Path

from flask import Flask, abort, jsonify, redirect, request, send_file, send_from_directory
from werkzeug.exceptions import HTTPException

from .content import TOOL_DIRNAME, ContentError, Meta, Post
from .site import Site

STATIC = Path(__file__).parent / "static"


def create_app(site: Site) -> Flask:
    app = Flask(__name__, static_folder=None)
    app.config["MAX_CONTENT_LENGTH"] = 512 * 1024 * 1024
    store = site.store
    previews: dict[str, Post] = {}  # the editor's unsaved text, per post
    lock = threading.Lock()  # one publish or build at a time

    @app.before_request
    def same_origin_only():
        host = request.host or ""
        host = host[: host.index("]") + 1] if host.startswith("[") else host.split(":")[0]
        if host not in ("127.0.0.1", "localhost", "[::1]"):
            abort(403, "the editor only answers on localhost")
        origin = request.headers.get("Origin")
        if request.method not in ("GET", "HEAD") and origin and origin != request.host_url.rstrip("/"):
            abort(403, "cross-site request refused")

    @app.after_request
    def no_cache(resp):
        resp.headers["Cache-Control"] = "no-store"
        return resp

    @app.errorhandler(ContentError)
    def content_error(e):
        return jsonify(error=str(e)), 400

    @app.errorhandler(HTTPException)
    def http_error(e):
        if request.path.startswith("/_api/"):
            return jsonify(error=e.description), e.code
        return e

    def body_json() -> tuple[Meta, str]:
        data = request.get_json(force=True) or {}
        return Meta.from_dict(data.get("meta")), str(data.get("body") or "")

    def post_json(slug: str) -> dict:
        post = store.load(slug)
        return {"slug": slug, "meta": post.meta.to_dict(), "body": post.body,
                "status": store.status(slug), "media": store.media(slug),
                "url": f"/blog/{slug}/" if store.status(slug) != "draft" else None}

    # ---------- editor ----------

    @app.get("/_editor/")
    def editor():
        return send_file(STATIC / "editor.html")

    @app.get("/_editor/<path:name>")
    def editor_static(name):
        return send_from_directory(STATIC, name)

    # ---------- posts ----------

    @app.get("/_api/posts")
    def list_posts():
        return jsonify(posts=store.summaries())

    @app.post("/_api/posts")
    def new_post():
        title = str((request.get_json(force=True) or {}).get("title") or "").strip()
        post = store.create(title or "Untitled")
        return jsonify(post_json(post.slug)), 201

    @app.get("/_api/posts/<slug>")
    def get_post(slug):
        return jsonify(post_json(slug))

    @app.put("/_api/posts/<slug>/draft")
    def save_draft(slug):
        store.existing(slug)
        meta, body = body_json()
        store.save_draft(slug, meta, body)
        return jsonify(status=store.status(slug))

    @app.delete("/_api/posts/<slug>/draft")
    def discard_draft(slug):
        store.discard_draft(slug)
        previews.pop(slug, None)
        return jsonify(post_json(slug))

    @app.post("/_api/posts/<slug>/rename")
    def rename(slug):
        new = str((request.get_json(force=True) or {}).get("slug") or "")
        store.rename(slug, new)
        previews.pop(slug, None)
        return jsonify(post_json(new))

    @app.post("/_api/posts/<slug>/publish")
    def publish(slug):
        meta, body = body_json()
        with lock:
            report = site.publish(slug, meta, body)
        out = report.to_dict()
        out["published"] = not report.errors
        if not report.errors:
            out.update(post_json(slug))
        return jsonify(out)

    @app.post("/_api/posts/<slug>/unpublish")
    def unpublish(slug):
        with lock:
            report = site.unpublish(slug)
        return jsonify({**report.to_dict(), **post_json(slug)})

    # ---------- media ----------

    @app.get("/_api/posts/<slug>/media")
    def list_media(slug):
        return jsonify(media=store.media(slug))

    @app.post("/_api/posts/<slug>/media")
    def upload(slug):
        web_size = request.form.get("web_size", "1") == "1"
        names = []
        for f in request.files.getlist("file"):
            names.append(store.add_media(slug, f.filename or "file", f.read(), web_size))
        if not names:
            abort(400, "no file was sent")
        return jsonify(names=names, media=store.media(slug))

    # ---------- preview ----------

    @app.post("/_api/preview/<slug>")
    def update_preview(slug):
        store.existing(slug)
        meta, body = body_json()
        post = Post(slug, meta, body)
        previews[slug] = post
        report, page, _ = site.check_post(post, preview=True)
        return jsonify(html=page, errors=report.errors, warnings=report.warnings)

    @app.get("/_preview/<slug>/")
    def preview_page(slug):
        post = previews.get(slug) or store.load(slug)
        page, _ = site.render_post(post, store.published(), preview=True)
        return page

    @app.get("/_preview/<slug>/<name>")
    def preview_media(slug, name):
        path = store.media_path(slug, name)
        if not path.is_file():
            abort(404)
        return send_file(path, conditional=True)

    # ---------- the site ----------

    @app.get("/")
    @app.get("/<path:path>")
    def site_file(path=""):
        parts = Path(path).parts
        if any(p.startswith(".") or p == ".." for p in parts) or (parts and parts[0] == TOOL_DIRNAME):
            abort(404)
        f = site.root / path
        if f.is_dir():
            if path and not path.endswith("/"):
                return redirect(f"/{path}/")
            f = f / "index.html"
        if f.is_file():
            return send_file(f, conditional=True)
        return send_file(site.root / "404.html"), 404

    return app

