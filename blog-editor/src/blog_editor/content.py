"""Where posts live on disk, and how they are read and written.

Each post is a folder, ``blog-editor/posts/<slug>/``, holding:

- ``post.md`` — the published source. It exists once the post has been
  published, and is what the site's HTML is built from.
- ``draft.md`` — unpublished work. It exists for a post that has never been
  published, or for changes to a published post that aren't live yet.
- the post's images and videos, referenced from the Markdown by bare file
  name. Publishing copies the ones the post uses next to its HTML.

Both Markdown files start with a small YAML front matter block.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import io
import re
import shutil
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml
from PIL import Image, ImageOps

TOOL_DIRNAME = "blog-editor"
DRAFT = "draft.md"
PUBLISHED = "post.md"

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".svg"}
VIDEO_EXTS = {".mp4", ".webm"}
# Other files a post may link to for download.
OTHER_EXTS = {".pdf", ".zip", ".txt", ".csv"}
MEDIA_EXTS = IMAGE_EXTS | VIDEO_EXTS | OTHER_EXTS

# Uploads wider than this are scaled down when "web-size" is on. The widest
# thing on a post page is a .wide figure at 1080 CSS px.
WEB_MAX_WIDTH = 1600
WEB_QUALITY = 82


class ContentError(ValueError):
    """A request the store refuses: bad slug, missing post, and so on."""


@dataclass
class Meta:
    title: str = ""
    date: str = ""  # YYYY-MM-DD
    summary: str = ""
    cover: str = ""  # a media file name in the post folder, or ""

    @classmethod
    def from_dict(cls, d: dict | None) -> Meta:
        d = d or {}
        date = d.get("date") or ""
        if isinstance(date, (dt.date, dt.datetime)):
            date = date.strftime("%Y-%m-%d")
        return cls(
            title=str(d.get("title") or "").strip(),
            date=str(date).strip(),
            summary=" ".join(str(d.get("summary") or "").split()),
            cover=str(d.get("cover") or "").strip(),
        )

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Post:
    slug: str
    meta: Meta
    body: str


def parse_markdown_file(text: str) -> tuple[Meta, str]:
    """Split a file into its front matter and Markdown body."""
    text = text.replace("\r\n", "\n")
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end == -1 and text.endswith("\n---"):
            end = len(text) - 4
        if end != -1:
            front = yaml.safe_load(text[4:end]) or {}
            if not isinstance(front, dict):
                raise ContentError("front matter is not a mapping")
            return Meta.from_dict(front), text[end + 5 :].lstrip("\n")
    return Meta(), text


def format_markdown_file(meta: Meta, body: str) -> str:
    front = {k: v for k, v in meta.to_dict().items() if v or k in ("title", "date")}
    head = yaml.safe_dump(front, sort_keys=False, allow_unicode=True, width=1000)
    body = body.replace("\r\n", "\n").strip("\n")
    return f"---\n{head}---\n\n{body}\n"


def slugify(title: str) -> str:
    s = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s[:60].rstrip("-") or "untitled"


def media_kind(name: str) -> str:
    ext = Path(name).suffix.lower()
    if ext in IMAGE_EXTS:
        return "image"
    if ext in VIDEO_EXTS:
        return "video"
    return "file"


def clean_filename(name: str) -> str:
    """A safe, lower-case file name that keeps its extension."""
    p = Path(name.replace("\\", "/")).name
    stem, ext = Path(p).stem, Path(p).suffix.lower()
    if ext == ".jpeg":
        ext = ".jpg"
    stem = unicodedata.normalize("NFKD", stem).encode("ascii", "ignore").decode()
    stem = re.sub(r"[^a-z0-9._-]+", "-", stem.lower()).strip("-._") or "file"
    return f"{stem[:80]}{ext}"


class Store:
    """The posts folder: listing, loading and saving posts and their media."""

    def __init__(self, site_root: Path):
        self.site_root = site_root
        self.root = site_root / TOOL_DIRNAME / "posts"

    # ---------- paths ----------

    def folder(self, slug: str) -> Path:
        if not SLUG_RE.match(slug or ""):
            raise ContentError(f"not a valid slug: {slug!r}")
        return self.root / slug

    def existing(self, slug: str) -> Path:
        d = self.folder(slug)
        if not d.is_dir():
            raise ContentError(f"no such post: {slug}")
        return d

    def media_path(self, slug: str, name: str) -> Path:
        d = self.existing(slug)
        if name != Path(name).name or name.startswith(".") or name in (DRAFT, PUBLISHED):
            raise ContentError(f"not a media file: {name!r}")
        return d / name

    # ---------- reading ----------

    def status(self, slug: str) -> str:
        d = self.folder(slug)
        has_draft, has_post = (d / DRAFT).is_file(), (d / PUBLISHED).is_file()
        if has_post and has_draft:
            return "changed"  # published, with unpublished changes in the draft
        return "published" if has_post else "draft"

    def read(self, slug: str, which: str) -> Post | None:
        f = self.folder(slug) / which
        if not f.is_file():
            return None
        meta, body = parse_markdown_file(f.read_text(encoding="utf-8"))
        return Post(slug, meta, body)

    def load(self, slug: str) -> Post:
        """The version to edit: the draft if there is one, else the published post."""
        self.existing(slug)
        post = self.read(slug, DRAFT) or self.read(slug, PUBLISHED)
        if post is None:
            raise ContentError(f"post {slug} has neither {DRAFT} nor {PUBLISHED}")
        return post

    def slugs(self) -> list[str]:
        if not self.root.is_dir():
            return []
        return sorted(
            d.name
            for d in self.root.iterdir()
            if d.is_dir() and SLUG_RE.match(d.name)
            and ((d / DRAFT).is_file() or (d / PUBLISHED).is_file())
        )

    def summaries(self) -> list[dict]:
        out = []
        for slug in self.slugs():
            post = self.load(slug)
            out.append({"slug": slug, "title": post.meta.title, "date": post.meta.date,
                        "status": self.status(slug)})
        out.sort(key=lambda p: (p["date"], p["slug"]), reverse=True)
        return out

    def published(self) -> list[Post]:
        """Every published post, newest first."""
        posts = [p for s in self.slugs() if (p := self.read(s, PUBLISHED))]
        posts.sort(key=lambda p: (p.meta.date, p.slug), reverse=True)
        return posts

    def media(self, slug: str) -> list[dict]:
        d = self.existing(slug)
        files = sorted(
            f for f in d.iterdir()
            if f.is_file() and not f.name.startswith(".") and f.suffix.lower() in MEDIA_EXTS
        )
        return [{"name": f.name, "kind": media_kind(f.name), "size": f.stat().st_size} for f in files]

    # ---------- writing ----------

    def create(self, title: str, today: dt.date | None = None) -> Post:
        base = slugify(title)
        slug, n = base, 2
        while self.folder(slug).exists():
            slug, n = f"{base}-{n}", n + 1
        meta = Meta(title=title.strip() or "Untitled", date=(today or dt.date.today()).isoformat())
        self.folder(slug).mkdir(parents=True)
        self.save_draft(slug, meta, "")
        return Post(slug, meta, "")

    def save_draft(self, slug: str, meta: Meta, body: str) -> None:
        d = self.folder(slug)
        d.mkdir(parents=True, exist_ok=True)
        _write(d / DRAFT, format_markdown_file(meta, body))

    def save_published(self, slug: str, meta: Meta, body: str) -> None:
        """Make this the published source, and drop the draft it came from."""
        d = self.existing(slug)
        _write(d / PUBLISHED, format_markdown_file(meta, body))
        (d / DRAFT).unlink(missing_ok=True)

    def discard_draft(self, slug: str) -> Post:
        """Throw away unpublished changes to a published post."""
        d = self.existing(slug)
        if not (d / PUBLISHED).is_file():
            raise ContentError("this post has never been published, so there is nothing to go back to")
        (d / DRAFT).unlink(missing_ok=True)
        return self.load(slug)

    def unpublish(self, slug: str) -> None:
        """Turn a published post back into a draft. Newer draft changes win."""
        d = self.existing(slug)
        post = d / PUBLISHED
        if not post.is_file():
            raise ContentError("this post is not published")
        if (d / DRAFT).is_file():
            post.unlink()
        else:
            post.rename(d / DRAFT)

    def rename(self, slug: str, new_slug: str) -> None:
        src, dst = self.existing(slug), self.folder(new_slug)
        if (src / PUBLISHED).is_file():
            raise ContentError("a published post keeps its address; unpublish it first to rename it")
        if dst.exists():
            raise ContentError(f"there is already a post called {new_slug}")
        src.rename(dst)

    def add_media(self, slug: str, filename: str, data: bytes, web_size: bool) -> str:
        """Store an uploaded file in the post folder and return its name."""
        name = clean_filename(filename)
        if Path(name).suffix not in MEDIA_EXTS:
            allowed = ", ".join(sorted(MEDIA_EXTS))
            raise ContentError(f"{filename}: can't use this kind of file here (use {allowed})")
        if web_size:
            name, data = _web_size(name, data)
        d = self.existing(slug)
        stem, ext = Path(name).stem, Path(name).suffix
        candidate, n = name, 2
        while (d / candidate).exists():
            if _same_bytes(d / candidate, data):
                return candidate  # the same file uploaded twice
            candidate, n = f"{stem}-{n}{ext}", n + 1
        (d / candidate).write_bytes(data)
        return candidate


def _write(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def _same_bytes(path: Path, data: bytes) -> bool:
    if path.stat().st_size != len(data):
        return False
    return hashlib.sha256(path.read_bytes()).digest() == hashlib.sha256(data).digest()


def _web_size(name: str, data: bytes) -> tuple[str, bytes]:
    """Re-encode a still PNG/JPEG as WebP no wider than WEB_MAX_WIDTH.

    GIFs, SVGs and anything animated are kept as they are.
    """
    ext = Path(name).suffix
    if ext not in {".png", ".jpg", ".webp"}:
        return name, data
    try:
        im = Image.open(io.BytesIO(data))
        if getattr(im, "is_animated", False):
            return name, data
        im = ImageOps.exif_transpose(im)
    except Exception:
        return name, data  # not an image Pillow can read; keep it untouched
    if ext == ".webp" and im.width <= WEB_MAX_WIDTH:
        return name, data
    if im.width > WEB_MAX_WIDTH:
        im = im.resize((WEB_MAX_WIDTH, round(im.height * WEB_MAX_WIDTH / im.width)), Image.LANCZOS)
    if im.mode not in ("RGB", "RGBA"):
        im = im.convert("RGBA" if "A" in im.getbands() or "transparency" in im.info else "RGB")
    out = io.BytesIO()
    im.save(out, "WEBP", quality=WEB_QUALITY, method=6)
    return f"{Path(name).stem}.webp", out.getvalue()


def copy_if_changed(src: Path, dst: Path) -> bool:
    if dst.is_file():
        s, d = src.stat(), dst.stat()
        if s.st_size == d.st_size and src.read_bytes() == dst.read_bytes():
            return False
    shutil.copyfile(src, dst)
    return True
