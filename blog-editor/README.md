# blog-editor

Write Hexmonger blog posts in Markdown, see them exactly as the site will show
them, and publish them into the site as plain HTML. It runs on your machine;
nothing is committed or pushed for you.

```sh
cd blog-editor
uv run blog-editor          # opens http://127.0.0.1:8765/_editor/
```

Markdown on the left, the live page on the right. The preview is the real page
that publishing will write, with the site's own stylesheets and fonts.

- **Save draft** (Ctrl+S) writes `posts/<slug>/draft.md`. The site doesn't change.
- **Publish** checks the post, then writes it into the site folder:
  `blog/<slug>/index.html` and the media it uses, the `blog/` index, the
  `blog/feed.xml` Atom feed and the `/blog/` lines of `sitemap.xml`. Then it
  runs `scripts/check-site.sh`. Review with `git status` and commit when you're
  ready.
- **More → Discard unpublished changes** drops the draft of a published post.
  **More → Unpublish** removes the post's page from the site and turns it back
  into a draft.

Posts with a LaTeX error, a missing image, no title or a bad date won't
publish; the preview's problem list shows these as you type, and clicking one
jumps to the line.

## Where things live

```
blog-editor/posts/<slug>/
  draft.md      unpublished work (a new post, or changes to a published one)
  post.md       the published source; the site's HTML is built from this
  *.webp, *.mp4 the post's media, referenced by bare file name
```

A post's address is `/blog/<slug>/`. You can rename a draft's slug until it is
first published; after that it stays put so links keep working.

This folder is left out of the deploy (`.github/workflows/pages.yml`) and out
of `scripts/check-site.sh`. Drafts are still visible in the repository if you
commit them, and the repository is public.

## Writing

Press **?** in the editor for the cheat sheet. In short:

| | |
| --- | --- |
| Images | Paste or drop a file into the text, or use **Image**. `![alt text](pic.webp "caption")`. An image on a line of its own becomes a figure; several on one line sit side by side. |
| Image options | `{.wide}` breaks out of the text column; `{.pixel}` keeps pixel art crisp; `{width=320}` sets a size. |
| Web-size | On by default: PNG and JPEG uploads become WebP, at most 1600 px wide. Turn it off in the Image dialog for pixel art. GIFs and SVGs are never touched. |
| Video | `![](clip.mp4)` (MP4 or WebM) plays with controls; `![](clip.webm){.loop}` plays silently on a loop, like a GIF; `{poster=still.webp}` sets the still. |
| Embeds | `![Trailer](https://youtu.be/…)` or a Vimeo link embeds the player (YouTube's no-cookie domain). |
| Math | `$E = mc^2$` inline, and `$$ … $$` on lines of their own for display. Written as LaTeX; converted to MathML when the page is built, so readers need no JavaScript. `$5 and $10` stays text. |
| Also | Tables, footnotes (`[^1]`), `~~strikethrough~~`, smart quotes, and raw HTML when you need it. |

A post's **summary** is shown under its title, on the blog index, in the feed
and in link previews. Its **cover** is the index thumbnail and the social
preview image.

## Changing the look

The pages come from `src/blog_editor/templates/` (Jinja) and `assets/blog.css`
in the site. After changing a template, rebuild every published post:

```sh
uv run blog-editor build
```

## Development

```sh
uv run pytest
```

The tests publish into a copy of the site and run `scripts/check-site.sh`
against the result.

| file | what it does |
| --- | --- |
| `src/blog_editor/content.py` | the posts folder: drafts, published sources, uploads |
| `src/blog_editor/render.py` | Markdown → HTML: math, figures, video, embeds |
| `src/blog_editor/site.py` | checks posts and writes the blog into the site |
| `src/blog_editor/server.py` | the local web server and its JSON API |
| `src/blog_editor/static/` | the editor page (plain HTML, CSS and JS; no build step) |
