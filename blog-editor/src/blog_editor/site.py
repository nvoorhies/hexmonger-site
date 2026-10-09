"""Building the site's blog from the published posts.

Publishing writes, in the site repo:

- ``blog/<slug>/index.html`` for every published post, plus the images and
  videos it uses (and nothing else — files a post stops using are removed);
- ``blog/index.html``, the list of posts, and ``blog/feed.xml``, an Atom feed;
- the ``/blog/`` entries in ``sitemap.xml``, leaving the others alone.

Everything is rebuilt from ``post.md`` files on every publish, so the output
only depends on them and the templates. Nothing is committed.
"""

from __future__ import annotations

import datetime as dt
import html
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

from .content import IMAGE_EXTS, Meta, Post, Store, copy_if_changed
from .render import Rendered, is_local_ref, local_name, render_body

GENERATOR = "hexmonger blog-editor"
BIG_FILE = 25 * 1024 * 1024  # GitHub warns at 50 MB and refuses 100 MB
REF_RE = re.compile(r'\b(src|href|poster)="([^"]*)"')


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    changed: list[str] = field(default_factory=list)  # site paths written or removed
    check: str | None = None  # output of scripts/check-site.sh
    check_ok: bool | None = None

    def to_dict(self) -> dict:
        return self.__dict__.copy()


def find_site_root(*starts: Path) -> Path:
    for start in starts:
        for d in [start, *start.parents]:
            if (d / "CNAME").is_file() and (d / "assets" / "site.css").is_file():
                return d
    raise FileNotFoundError("can't find the site (a folder with CNAME and assets/site.css)")


def local_refs(page_html: str) -> set[str]:
    """File names the HTML refers to relative to its own folder."""
    return {local_name(html.unescape(v)) for _, v in REF_RE.findall(page_html) if is_local_ref(html.unescape(v))}


def long_date(iso: str) -> str:
    try:
        d = dt.date.fromisoformat(iso)
    except ValueError:
        return iso
    return f"{d:%B} {d.day}, {d.year}"


class Site:
    def __init__(self, root: Path):
        self.root = root
        self.store = Store(root)
        self.blog_dir = root / "blog"
        self.url = "https://" + (root / "CNAME").read_text().strip()
        self.jinja = Environment(
            loader=FileSystemLoader(Path(__file__).parent / "templates"),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True,
        )
        self.jinja.filters["longdate"] = long_date
        self.jinja.policies["json.dumps_kwargs"] = {"sort_keys": False, "ensure_ascii": False}

    # ---------- pages ----------

    def post_url(self, slug: str) -> str:
        return f"{self.url}/blog/{slug}/"

    def render_post(self, post: Post, published: list[Post], preview: bool = False) -> tuple[str, Rendered]:
        """The full page for a post, as it will be served at /blog/<slug>/.

        ``published`` is the other live posts; the newer/older links are
        worked out as if this post were live alongside them.
        """
        body = render_body(post.body, self.store.folder(post.slug), preview=preview)
        timeline = sorted([p for p in published if p.slug != post.slug] + [post],
                          key=lambda p: (p.meta.date, p.slug), reverse=True)
        i = next(n for n, p in enumerate(timeline) if p.slug == post.slug)
        cover = post.meta.cover
        page = self.jinja.get_template("post.html").render(
            site_url=self.url,
            page_url=self.post_url(post.slug),
            generator=GENERATOR,
            post=post,
            body=Markup(body.html),
            newer=timeline[i - 1] if i > 0 else None,
            older=timeline[i + 1] if i + 1 < len(timeline) else None,
            og_image=f"{self.post_url(post.slug)}{cover}" if cover else f"{self.url}/assets/img/og-image.jpg",
            preview=preview,
        )
        return page, body

    def check_post(self, post: Post, preview: bool = False) -> tuple[Report, str, set[str]]:
        """Render a post and list what is wrong with it.

        Errors stop it from being published; warnings don't. Returns the
        report, the page, and the files the page needs from the post folder.
        """
        page, body = self.render_post(post, self.store.published(), preview=preview)
        report = Report(errors=list(body.errors), warnings=list(body.warnings))
        m, folder = post.meta, self.store.folder(post.slug)
        if not m.title:
            report.errors.append("the post needs a title")
        try:
            dt.date.fromisoformat(m.date)
        except ValueError:
            report.errors.append(f"the date {m.date!r} isn't a YYYY-MM-DD date")
        if not m.summary:
            report.warnings.append("no summary: the blog index, the feed and link previews will show nothing under the title")
        files = local_refs(page)
        if m.cover:
            files.add(m.cover)
            if Path(m.cover).suffix.lower() not in IMAGE_EXTS - {".svg"}:
                report.errors.append(f"the cover {m.cover} needs to be a PNG, JPEG, GIF or WebP image")
        for name in sorted(files):
            f = folder / name
            if "/" in name or name.startswith("."):
                report.errors.append(f"{name}: media must sit directly in the post folder")
            elif not f.is_file():
                report.errors.append(f"{name} is used by the post but isn't in its folder")
            elif f.stat().st_size > BIG_FILE:
                report.warnings.append(f"{name} is {f.stat().st_size // 2**20} MB; GitHub refuses files over 100 MB")
        return report, page, files

    # ---------- publishing ----------

    def publish(self, slug: str, meta: Meta, body: str, run_check: bool = True) -> Report:
        post = Post(slug, meta, body)
        self.store.existing(slug)
        report, _, _ = self.check_post(post)
        if report.errors:
            return report
        self.store.save_published(slug, meta, body)
        built = self.build(run_check=run_check)
        built.warnings[:0] = report.warnings
        return built

    def unpublish(self, slug: str, run_check: bool = True) -> Report:
        self.store.unpublish(slug)
        return self.build(run_check=run_check)

    def build(self, run_check: bool = True) -> Report:
        """Write every published post, the index, the feed and the sitemap."""
        report = Report()
        posts = self.store.published()
        for post in posts:
            post_report, page, files = self.check_post(post)
            if post_report.errors:
                # A post.md edited by hand can break; keep its last good page.
                report.errors += [f"{post.slug}: {e}" for e in post_report.errors]
                continue
            out = self.blog_dir / post.slug
            out.mkdir(parents=True, exist_ok=True)
            self._write(out / "index.html", page, report)
            for name in sorted(files):
                if copy_if_changed(self.store.folder(post.slug) / name, out / name):
                    report.changed.append(self._rel(out / name))
            for f in sorted(out.iterdir()):
                if f.is_file() and f.name != "index.html" and f.name not in files:
                    f.unlink()
                    report.changed.append(self._rel(f) + " (removed)")

        live = {p.slug for p in posts}
        if self.blog_dir.is_dir():
            for d in sorted(self.blog_dir.iterdir()):
                if d.is_dir() and d.name not in live and self._generated(d / "index.html"):
                    shutil.rmtree(d)
                    report.changed.append(self._rel(d) + "/ (removed)")

        index, feed = self.blog_dir / "index.html", self.blog_dir / "feed.xml"
        if posts:
            ctx = {"site_url": self.url, "generator": GENERATOR, "posts": posts}
            self._write(index, self.jinja.get_template("index.html").render(**ctx, is_index=True), report)
            entries = [(p, self._absolute(self.render_post(p, posts)[1].html, p.slug)) for p in posts]
            self._write(feed, self.jinja.get_template("feed.xml").render(**ctx, entries=entries), report)
        else:
            for f in (index, feed):
                if f.is_file() and self._generated(f):
                    f.unlink()
                    report.changed.append(self._rel(f) + " (removed)")
            if self.blog_dir.is_dir() and not any(self.blog_dir.iterdir()):
                self.blog_dir.rmdir()
        self._update_sitemap(posts, report)

        if run_check:
            report.check_ok, report.check = self.check_site()
        return report

    def check_site(self) -> tuple[bool | None, str | None]:
        script = self.root / "scripts" / "check-site.sh"
        if not script.is_file():
            return None, None
        r = subprocess.run(["bash", str(script)], cwd=self.root, capture_output=True, text=True)
        return r.returncode == 0, (r.stdout + r.stderr).strip()

    # ---------- helpers ----------

    def _update_sitemap(self, posts: list[Post], report: Report) -> None:
        path = self.root / "sitemap.xml"
        if not path.is_file():
            return
        prefix = f"<loc>{self.url}/blog/"
        lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if prefix not in ln]
        close = next((i for i, ln in enumerate(lines) if "</urlset>" in ln), len(lines))
        urls = [f"{self.url}/blog/"] + [self.post_url(p.slug) for p in posts] if posts else []
        lines[close:close] = [f"  <url><loc>{u}</loc></url>" for u in urls]
        self._write(path, "\n".join(lines) + "\n", report)

    def _absolute(self, fragment: str, slug: str) -> str:
        """Make a post body's links absolute, for the feed."""
        base = self.post_url(slug)

        def fix(m: re.Match) -> str:
            attr, url = m.groups()
            if url.startswith("#") or is_local_ref(html.unescape(url)):
                url = base + url
            elif url.startswith("/") and not url.startswith("//"):
                url = self.url + url
            return f'{attr}="{url}"'
        return REF_RE.sub(fix, fragment)

    def _generated(self, page: Path) -> bool:
        try:
            return GENERATOR in page.read_text(encoding="utf-8")[:4000]
        except OSError:
            return False

    def _write(self, path: Path, text: str, report: Report) -> None:
        if path.is_file() and path.read_text(encoding="utf-8") == text:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        report.changed.append(self._rel(path))

    def _rel(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()
