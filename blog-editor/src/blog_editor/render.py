"""Markdown to the HTML inside a post page's ``<div class="prose">``.

On top of CommonMark this understands:

- ``$x^2$`` inline and ``$$ … $$`` display math, turned into MathML here so
  the published page needs no JavaScript;
- tables, ~~strikethrough~~, footnotes (``[^1]``) and smart quotes;
- ``{.class key=value}`` attributes after an image or link;
- media through image syntax: ``![alt](pic.webp "caption")`` for pictures,
  ``![alt](clip.mp4)`` for video (``{.loop}`` plays it silently on a loop,
  like a GIF), and ``![title](https://youtu.be/…)`` or a Vimeo link for an
  embedded player. An image alone in its paragraph becomes a ``<figure>``
  whose caption is the title; several in one paragraph become a gallery.
"""

from __future__ import annotations

import functools
import html
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from latex2mathml.converter import convert as latex_to_mathml
from markdown_it import MarkdownIt
from mdit_py_plugins.anchors import anchors_plugin
from mdit_py_plugins.attrs import attrs_plugin
from mdit_py_plugins.dollarmath import dollarmath_plugin
from mdit_py_plugins.footnote import footnote_plugin
from PIL import Image

from .content import VIDEO_EXTS

YOUTUBE_RE = re.compile(
    r"^(?:https?://)?(?:www\.|m\.)?"
    r"(?:youtube\.com/(?:watch\?(?:.*&)?v=|embed/|shorts/|live/)|youtu\.be/)([\w-]{11})"
)
VIMEO_RE = re.compile(r"^(?:https?://)?(?:www\.|player\.)?vimeo\.com/(?:video/)?(\d+)")
SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")
# latex2mathml passes commands it doesn't know through as literal text.
UNKNOWN_COMMAND_RE = re.compile(r"<m[io]>(\\[A-Za-z]+)</m[io]>")


@dataclass
class Rendered:
    html: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def render_body(body: str, media_dir: Path, preview: bool = False) -> Rendered:
    """Render a post body.

    ``media_dir`` is the post folder, used to read image sizes. In preview
    mode each top-level block carries ``data-line`` (its first source line,
    0-based) so the editor can keep the preview scrolled alongside the text.
    """
    env = {"media_dir": media_dir, "preview": preview, "errors": [], "warnings": []}
    out = _markdown(preview).render(body, env)
    return Rendered(out, env["errors"], env["warnings"])


def is_local_ref(url: str) -> bool:
    """A reference to a file next to the post: no scheme, not root-relative, not a fragment."""
    return bool(url) and not (url.startswith(("/", "#", "?")) or SCHEME_RE.match(url))


def local_name(url: str) -> str:
    return unquote(url.split("#", 1)[0].split("?", 1)[0])


@functools.cache
def _markdown(preview: bool) -> MarkdownIt:
    md = MarkdownIt("commonmark", {"html": True, "typographer": True})
    md.enable(["table", "strikethrough", "replacements", "smartquotes"])
    md.use(footnote_plugin)
    # Pandoc's rules for inline $: no space just inside the dollars, and no
    # digit straight after the closing one, so "$5 and $10" stays text.
    md.use(dollarmath_plugin, allow_space=False, allow_digits=False,
           allow_labels=False, allow_blank_lines=False, double_inline=True)
    md.use(attrs_plugin)
    md.use(anchors_plugin, min_level=2, max_level=3)
    md.core.ruler.push("inline_lines", _inline_lines)
    md.core.ruler.push("figures", _figures)
    if preview:
        md.core.ruler.push("source_lines", _source_lines)
    md.add_render_rule("image", _render_image)
    md.add_render_rule("math_inline", _render_math(display=False, block=False))
    md.add_render_rule("math_inline_double", _render_math(display=True, block=False))
    md.add_render_rule("math_block", _render_math(display=True, block=True))
    return md


# ---------- core rules ----------

def _inline_lines(state) -> None:
    """Give inline tokens the (1-based) line they are on, for messages."""
    for tok in state.tokens:
        if tok.type == "inline" and tok.map and tok.children:
            for child in tok.children:
                child.meta.setdefault("line", tok.map[0] + 1)


def _figures(state) -> None:
    """A paragraph holding only images renders as a figure, or a gallery of them."""
    toks = state.tokens
    for i in range(len(toks) - 2):
        p_open, inline, p_close = toks[i], toks[i + 1], toks[i + 2]
        if (p_open.type, inline.type, p_close.type) != ("paragraph_open", "inline", "paragraph_close"):
            continue
        kids = [k for k in inline.children or []
                if not (k.type == "softbreak" or (k.type == "text" and not k.content.strip()))]
        if not kids or any(k.type != "image" for k in kids):
            continue
        for k in kids:
            k.meta["figure"] = True
        if len(kids) == 1:
            p_open.hidden = p_close.hidden = True
            kids[0].meta["block_line"] = p_open.map[0] if p_open.map else None
        else:
            p_open.tag = p_close.tag = "div"
            p_open.attrJoin("class", "gallery")
            inline.children = kids


def _source_lines(state) -> None:
    for tok in state.tokens:
        if tok.level == 0 and tok.map and tok.nesting >= 0 and tok.type != "inline":
            tok.attrSet("data-line", str(tok.map[0]))


# ---------- render rules ----------

def _attrs(pairs: dict) -> str:
    # `is` checks, not `in`: 0 == False, and data-line="0" must survive.
    return "".join(
        f" {k}" if v is True else f' {k}="{html.escape(str(v))}"'
        for k, v in pairs.items() if not (v is None or v is False or v == "")
    )


def _render_image(self, tokens, idx, options, env) -> str:
    tok = tokens[idx]
    src = tok.attrGet("src") or ""
    title = tok.attrGet("title") or ""
    alt = self.renderInlineAsText(tok.children or [], options, env)
    extra = {k: v for k, v in tok.attrs.items() if k not in ("src", "alt", "title")}
    classes = str(extra.pop("class", "")).split()
    line = tok.meta.get("line", "?")
    figure = tok.meta.get("figure", False)

    ext = Path(local_name(src)).suffix.lower()
    if m := YOUTUBE_RE.match(src):
        element = _embed(f"https://www.youtube-nocookie.com/embed/{m[1]}{_youtube_start(src)}",
                         alt or title or "YouTube video", extra)
    elif m := VIMEO_RE.match(src):
        element = _embed(f"https://player.vimeo.com/video/{m[1]}?dnt=1", alt or title or "Vimeo video", extra)
    elif ext in VIDEO_EXTS:
        if "loop" in classes:
            play = {"autoplay": True, "loop": True, "muted": True, "playsinline": True}
        else:
            play = {"controls": True, "preload": "metadata", "playsinline": True}
        a = {"src": src, **play, "aria-label": alt or None, **extra}
        if not figure:
            a["class"] = " ".join(classes)
        element = f"<video{_attrs(a)}>{html.escape(alt)}</video>"
    else:
        if not alt:
            env["warnings"].append(f"line {line}: image {src or '(no file)'} has no alt text")
        a = {"src": src, "alt": alt}
        if "width" not in extra and "height" not in extra and is_local_ref(src):
            size = _image_size(env["media_dir"] / local_name(src))
            if size:
                a["width"], a["height"] = size
        a.update({"loading": "lazy", "decoding": "async", **extra})
        if not figure:
            a["class"] = " ".join(classes)
            if title:
                a["title"] = title
        element = f"<img{_attrs(a)}>"

    if not figure:
        return element
    fig = {"class": " ".join(classes)}
    if env["preview"] and tok.meta.get("block_line") is not None:
        fig["data-line"] = tok.meta["block_line"]
    caption = f"<figcaption>{html.escape(title)}</figcaption>" if title else ""
    # A lone figure replaces its paragraph, so it ends the line the <p> would have.
    end = "\n" if "block_line" in tok.meta else ""
    return f"<figure{_attrs(fig)}>{element}{caption}</figure>{end}"


def _embed(src: str, title: str, extra: dict) -> str:
    a = {
        "src": src, "title": title, "loading": "lazy",
        "allow": "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share",
        "referrerpolicy": "strict-origin-when-cross-origin", "allowfullscreen": True, **extra,
    }
    return f'<div class="embed"><iframe{_attrs(a)}></iframe></div>'


def _youtube_start(url: str) -> str:
    t = (parse_qs(urlparse(url if "//" in url else "https://" + url).query).get("t") or [""])[0]
    m = re.fullmatch(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s?)?", t)
    if not t or not m:
        return ""
    h, mi, s = (int(g or 0) for g in m.groups())
    seconds = h * 3600 + mi * 60 + s
    return f"?start={seconds}" if seconds else ""


def _render_math(display: bool, block: bool):
    def render(self, tokens, idx, options, env) -> str:
        tok = tokens[idx]
        latex = tok.content.strip()
        line = tok.map[0] + 1 if tok.map else tok.meta.get("line", "?")
        try:
            out = latex_to_mathml(latex, display="block" if display else "inline")
        except Exception:
            env["errors"].append(f"line {line}: this LaTeX doesn't parse — check the braces: {latex}")
            out = f'<code class="math-error">{html.escape(latex)}</code>'
        else:
            if unknown := sorted(set(UNKNOWN_COMMAND_RE.findall(out))):
                env["errors"].append(f"line {line}: unknown LaTeX command {', '.join(unknown)}")
        if block:
            return f'<div{self.renderAttrs(tok)} class="math block">\n{out}\n</div>\n'
        return out
    return render


@functools.lru_cache(maxsize=512)
def _size_of(path: str, mtime_ns: int) -> tuple[int, int] | None:
    try:
        with Image.open(path) as im:
            return im.size
    except Exception:
        return None  # SVG, or not an image Pillow reads


def _image_size(path: Path) -> tuple[int, int] | None:
    try:
        return _size_of(str(path), path.stat().st_mtime_ns)
    except OSError:
        return None
