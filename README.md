# hexmonger-site

The studio website at **https://hexmonger.com** — plain static HTML and CSS,
no build step and no JavaScript. What is in this repo is exactly what is
served.

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
| `404.html` | the not-found page (Pages serves it for any missing path) |
| `assets/site.css` | all styles |
| `assets/fonts/` | Fraunces + Inter, self-hosted (SIL OFL) so no page load goes to a third party |
| `assets/img/` | web-sized art; see `ASSETS.md` for where each file came from |
| `CNAME` | `hexmonger.com` — tells Pages which domain to serve |
| `scripts/check-site.sh` | fails on a page without a title, a broken local link, or a wrong CNAME |

Preview locally:

```sh
python3 -m http.server 8000   # then open http://localhost:8000
```

`scripts/check-site.sh` runs in CI on every push and pull request; a
failing check does not deploy.

## Common edits

- **A store listing goes live** — in `index.html` and in `castles-in-the-sand/index.html` (which has it in two places: the hero and the closing section), replace the matching
  `<span class="btn btn-soon">…</span>` with
  `<a class="btn btn-ghost" href="…">App Store</a>` (the comment above the
  buttons has the shape). Update the eyebrow line ("Coming soon to …").
- **YouTube** — uncomment the YouTube line under *Elsewhere* and fix the
  handle; add the URL to `sameAs` in the JSON-LD block too.
- **A game gets its own page** — make `<game>/index.html` using the same
  header/footer, link the card to it, and add it to `sitemap.xml`.

## Publishing

`.github/workflows/pages.yml` deploys to GitHub Pages on every push to
`main`, serving the repo minus `scripts/`, `.github/` and the docs.

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
