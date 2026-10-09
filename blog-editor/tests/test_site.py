from blog_editor.content import Meta

from conftest import make_png

BODY = """Intro with $e^{i\\pi} + 1 = 0$.

![A castle](castle.png "At low tide")

![](clip.mp4){.loop}

[Download the notes](notes.pdf) or go [home](/).
"""


def new_post(site, title="First light", body=BODY, date="2026-09-20", summary="Where it starts."):
    post = site.store.create(title)
    folder = site.store.folder(post.slug)
    make_png(folder / "castle.png")
    (folder / "clip.mp4").write_bytes(b"\x00\x00\x00\x18ftypmp42")
    (folder / "notes.pdf").write_bytes(b"%PDF-1.4")
    (folder / "unused.png").write_bytes(b"x")
    meta = Meta(title=title, date=date, summary=summary, cover="castle.png")
    return post.slug, meta, body


def test_publish_writes_the_blog_and_passes_the_site_check(site):
    slug, meta, body = new_post(site)
    report = site.publish(slug, meta, body)
    assert not report.errors, report.errors
    out = site.root / "blog" / slug
    assert sorted(f.name for f in out.iterdir()) == ["castle.png", "clip.mp4", "index.html", "notes.pdf"]
    page = (out / "index.html").read_text()
    assert "<title>First light — Hexmonger</title>" in page
    assert '<link rel="canonical" href="https://hexmonger.com/blog/first-light/">' in page
    assert 'content="https://hexmonger.com/blog/first-light/castle.png"' in page  # og:image from the cover
    assert "<math" in page and "data-line" not in page
    index = (site.root / "blog" / "index.html").read_text()
    assert 'href="/blog/first-light/"' in index and "September 20, 2026" in index
    feed = (site.root / "blog" / "feed.xml").read_text()
    assert "https://hexmonger.com/blog/first-light/castle.png" in feed  # absolute in the feed
    sitemap = (site.root / "sitemap.xml").read_text()
    assert "https://hexmonger.com/castles-in-the-sand/" in sitemap
    assert sitemap.index("<loc>https://hexmonger.com/blog/</loc>") < sitemap.index("</urlset>")
    assert report.check_ok, report.check
    assert site.store.status(slug) == "published"


def test_the_analytics_beacon_is_on_published_pages_but_not_the_preview(site):
    slug, meta, body = new_post(site)
    site.publish(slug, meta, body, run_check=False)
    for page in ("blog/index.html", f"blog/{slug}/index.html"):
        assert "c70e203b565e403fb495942f9dd584ec" in (site.root / page).read_text(), page
    preview, _ = site.render_post(site.store.load(slug), site.store.published(), preview=True)
    assert "cloudflareinsights" not in preview


def test_rebuilding_changes_nothing(site):
    slug, meta, body = new_post(site)
    site.publish(slug, meta, body, run_check=False)
    assert site.build(run_check=False).changed == []


def test_publish_refuses_a_broken_post_and_writes_nothing(site):
    slug, meta, _ = new_post(site)
    report = site.publish(slug, meta, "![gone](missing.webp)\n\n$\\frac{$", run_check=False)
    assert any("missing.webp" in e for e in report.errors)
    assert any("LaTeX" in e for e in report.errors)
    assert not (site.root / "blog").exists()
    assert site.store.status(slug) == "draft"
    meta.title = ""
    assert "the post needs a title" in site.publish(slug, meta, "ok", run_check=False).errors


def test_newer_and_older_links(site):
    a = new_post(site, "Older post", date="2026-01-01")
    b = new_post(site, "Newer post", date="2026-02-01")
    site.publish(*a, run_check=False)
    site.publish(*b, run_check=False)
    older = (site.root / "blog" / "older-post" / "index.html").read_text()
    newer = (site.root / "blog" / "newer-post" / "index.html").read_text()
    assert 'rel="next" href="/blog/newer-post/"' in older
    assert 'rel="prev" href="/blog/older-post/"' in newer
    index = (site.root / "blog" / "index.html").read_text()
    assert index.index("newer-post") < index.index("older-post")


def test_media_a_post_stops_using_is_removed(site):
    slug, meta, body = new_post(site)
    site.publish(slug, meta, body, run_check=False)
    site.publish(slug, meta, "Just words now.", run_check=False)
    assert sorted(f.name for f in (site.root / "blog" / slug).iterdir()) == ["castle.png", "index.html"]  # cover stays


def test_unpublishing_the_last_post_removes_the_blog(site):
    slug, meta, body = new_post(site)
    site.publish(slug, meta, body, run_check=False)
    report = site.unpublish(slug)
    assert not (site.root / "blog").exists()
    assert "/blog/" not in (site.root / "sitemap.xml").read_text()
    assert site.store.status(slug) == "draft"
    assert report.check_ok, report.check
