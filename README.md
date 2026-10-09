# hexmonger-site

The studio website at **https://hexmonger.com** — plain static HTML and CSS,
no build step. The only JavaScript is the Cloudflare Web Analytics beacon in
every page's `<head>`, which counts visits without cookies. What is in this
repo is exactly what is served. Blog posts are the one generated part: they
are written in Markdown with `blog-editor/`, which writes their HTML into
`blog/`, and that HTML is committed like everything else.

Privacy policies and support pages are **not** here. They live in
[nvoorhies/hexmonger-policies](https://github.com/nvoorhies/hexmonger-policies)
at `https://policies.hexmonger.com/<app>/…`, where their history is what the
store reviewers saw. This site only links to them.

## Layout

| path | what it is |
| --- | --- |
| `index.html` | the home page: featured game, coming-soon games, studio, contact |
| `castles-in-the-sand/index.html` | the Castles in the Sand page, styled like the game (`assets/castles.css`) |
| `goblin-hunt/index.html` | the Goblin Hunt page, set like an old printed rulebook (`assets/goblin-hunt.css`) |
| `tin-coffins/index.html` | the Tin Coffins page, dressed like the game's briefing terminal (`assets/tin-coffins.css`) |
| `blog/` | the blog: an index, a feed, and a folder per post. **Generated** by `blog-editor/` — edit posts there, not here |
| `404.html` | the not-found page (Pages serves it for any missing path) |
| `assets/site.css` | the shared styles |
| `assets/blog.css` | blog posts and the blog index, on top of `site.css` |
| `assets/fonts/` | Fraunces + Inter, self-hosted (SIL OFL) rather than loaded from Google Fonts |
| `assets/img/` | web-sized art; see `ASSETS.md` for where each file came from |
| `CNAME` | `hexmonger.com` — tells Pages which domain to serve |
| `scripts/check-site.sh` | fails on a page without a title, a broken local link, or a wrong CNAME |
| `blog-editor/` | the Markdown blog editor (Python, run with uv) and the posts' sources. Not deployed |

Preview locally:

```sh
python3 -m http.server 8000   # then open http://localhost:8000
```

`scripts/check-site.sh` runs in CI on every push and pull request; a
failing check does not deploy.

## Common edits

- **Write a blog post** — `cd blog-editor && uv run blog-editor`, write, then
  *Publish*. That writes the HTML into `blog/` and updates `sitemap.xml`; it
  doesn't commit. See `blog-editor/README.md`.
- **Google Play goes live** — the App Store listing is live (as of 2026-09-30),
  so its links are the pattern to copy. In `index.html`, uncomment the
  Google Play button beside the App Store one and drop "Android soon" from
  the eyebrow and "Google Play soon" from the platforms line. In
  `castles-in-the-sand/index.html` (the hero and the closing section),
  replace each `<span class="btn btn-soon">Google Play …</span>` with
  `<a class="btn btn-store" href="…">Google Play</a>`, add a Play `Offer`
  to the JSON-LD, and fix the platform note. Both pages' meta descriptions
  say "coming soon to Android" too.
- **The App Store link** — the site links the region-free
  `https://apps.apple.com/app/castles-in-the-sand/id6767951967`, which
  Apple redirects to the visitor's own storefront. The Castles page also
  carries an `apple-itunes-app` meta tag, which puts Safari's Smart App
  Banner (Get / Open) on top of the page on iPhone and iPad.
- **The Steam pages** — Cozy Necromancy (`app/5349910`) and Tin Coffins
  (`app/4943260`) are up on Steam as "coming soon", and each game's page
  asks for a wishlist in four places: the nav button, the hero, the
  closing section and the footer. The home page's cards and its *Elsewhere*
  list link them too. Every one of those links carries UTM tags
  (`utm_source=hexmonger.com&utm_medium=website`, `utm_campaign` = the page,
  `utm_content` = where on it: `nav`, `hero`, `closing`, `footer`, `card`,
  `elsewhere`), so Steamworks' UTM traffic report shows which button
  brought each visit; a new Steam link should get the same tags. The
  JSON-LD `sameAs` keeps the bare URL. When a game launches, change
  "Wishlist on Steam" to "Buy on Steam" (or "Play on Steam"), retitle the
  closing section, drop "In development", and add an `Offer` to the page's
  JSON-LD.
- **The trailers** — the Castles and Cozy Necromancy pages play theirs from
  YouTube, but load nothing from YouTube until someone presses play (each
  iframe's `srcdoc` is a local poster). To change a video, change its ID in
  both the iframe's `src` and the link inside `srcdoc`, and re-export its
  poster (`assets/img/cits-trailer.webp`, `assets/img/cn-trailer.webp`).
- **A game gets its own page** — make `<game>/index.html` using the same
  header/footer and the analytics beacon in the `<head>`, link the card to it,
  and add it to `sitemap.xml`.
- **Analytics** — Cloudflare Web Analytics (dashboard → Web Analytics →
  hexmonger.com). It sets no cookies and stores nothing on the visitor's
  device, so the site needs no cookie banner; keep it that way. Every page
  carries the same one-line beacon right after the viewport meta; blog
  pages get it from `blog-editor/src/blog_editor/templates/_layout.html`,
  which leaves it out of the editor's live preview so drafting doesn't
  count as visits.

## Publishing

`.github/workflows/pages.yml` deploys to GitHub Pages on every push to
`main`, serving the repo minus `scripts/`, `.github/`, `blog-editor/` and the
docs.

One-time setup:

1. **Settings → Pages → Source: GitHub Actions**, then re-run the workflow.
2. **Settings → Pages → Custom domain:** `hexmonger.com`, and tick
   *Enforce HTTPS* once the certificate is issued.
3. Verify the domain for the account (**Profile → Settings → Pages → Add a
   domain**) so no other repo can claim it.

### DNS (hexmonger.com is on Cloudflare)

| type | name | value |
| --- | --- | --- |
| A | `@` | `185.199.108.153` |
| A | `@` | `185.199.109.153` |
| A | `@` | `185.199.110.153` |
| A | `@` | `185.199.111.153` |
| AAAA | `@` | `2606:50c0:8000::153`, `…8001::153`, `…8002::153`, `…8003::153` |
| CNAME | `www` | `nvoorhies.github.io` |

Leave `policies` as it is. Set these records to **DNS only** (grey cloud)
until GitHub has issued the certificate. If you turn the proxy back on
afterwards, use SSL mode **Full (strict)**, or the site will loop on
redirects.

### Public or private repo

Pages on a free account needs a **public** repo. Nothing here is secret —
it is the same HTML anyone can already download from the live site — so
public is fine and matches `hexmonger-policies`.

To keep the source private instead, either:

- use GitHub Pro, where Pages works from private repos; or
- keep the repo private and deploy with **Cloudflare Pages** (free, and
  the domain is already on Cloudflare). Connect the repo, leave the build
  command empty, set the output directory to `/`, and add `hexmonger.com`
  as a custom domain. Then delete `pages.yml` and `CNAME`, but keep the
  check running in CI.
