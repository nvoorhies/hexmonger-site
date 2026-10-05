# Where the images come from

Everything in `assets/img/` is a resized copy. To change one, start from
the source and export it again. Don't edit the web copy.

| file | source | notes |
| --- | --- | --- |
| `cits-hero.webp`, `cits-hero-800.webp` | castles-in-the-sand `icon.png` (1024², the key art without the title) | Cropped to rows 250–890. The crop leaves out the bottom-right corner, which has a generator watermark sparkle |
| `og-image.jpg` | same, rows 200–738 | 1200×630 social preview |
| `cits-02-build.webp`, `cits-04-waves.webp`, `cits-06-hydraulics.webp` | castles-in-the-sand `store/screenshots/android-tablet/*.jpg` | 1200×750, WebP quality 80. Re-derive them whenever that repo re-captures its masters |
| `necro-key.webp` | cute-fantasy `icon.png` | 900² |
| `gh-building_house.png`, `gh-barrow_mouth.png`, `gh-wall_tower.png` | topdown-bw `assets/art/*.png` | Shown pixelated on the Goblin Hunt card, which stays a placeholder until there is real key art |
| `hexmonger-mark.svg` | drawn for this site | Studio mark and favicon |

Fonts: Fraunces and Inter variable woff2, Latin subset, from Fontsource.
Both are under the SIL Open Font License; the license files are in
`assets/fonts/`.

## Blog

| file | source | notes |
| --- | --- | --- |
| `fonts/stix-two-math.woff2` | STIX Two Math, from Fontsource (`@fontsource/stix-two-math` 5.3.0) | SIL OFL (`LICENSE-stix-two.txt`). The whole font, with its MATH table, for the MathML in blog posts. `blog.css` loads it, and browsers only fetch it on a page that has math |

Images and videos in posts live with each post's Markdown in
`blog-editor/posts/<slug>/`; publishing copies the ones a post uses to
`blog/<slug>/`. Edit or replace them there, not in `blog/`.

## Castles in the Sand page

| file | source | notes |
| --- | --- | --- |
| `cits-key-tall*.webp` | castles-in-the-sand `icon.png`, rows 60–900 | Leaves out the watermark in the bottom-right corner |
| `cits-app-icon.webp` | same, cropped square from the castle and child | Also used as the page favicon. The Play Store icon has the watermark, so it isn't used here |
| `cits-03-tide.webp`, `cits-05-result.webp` | `store/screenshots/android-tablet/` | 1200×750, WebP quality 80 |
| `cits-trailer.webp` | The trailer's YouTube thumbnail (`i.ytimg.com/vi/_sMItYFR6MU/maxresdefault.jpg`), a frame of the game | 1280×720, WebP quality 80. The poster shown until the trailer is played. Replace it with the new thumbnail if the trailer changes |
| `cits-og.jpg` | `store/feature_graphic_1024x500.png` on a sand-coloured 1200×630 canvas | Social preview |
| `fonts/lilita-one.ttf` | castles-in-the-sand `fonts/` | The game's own display font (SIL OFL). Served unmodified, because the font's name is reserved and a converted copy would need a new name |

## Cozy Necromancy page

| file | source | notes |
| --- | --- | --- |
| `cn-wood.webp`, `cn-square.webp`, `cn-chatter.webp` | Captured from the game: [nvoorhies/cute-fantasy](https://github.com/nvoorhies/cute-fantasy) `scripts/capture_promo.sh` (shots `wood`, `village`, `chatter`), Sept 30 2026 | 1920×1080 grabs. `cn-wood` is the whole frame at 1400 wide. `cn-square` and `cn-chatter` are 1.9:1 crops at 1180×621, so they stand the same height side by side: the square from x 300–1600, y 95–779; the chatter from x 0–1180, y 130–751, which leaves out a tower wall at the right edge. The harness turns the foliage up past its shipping values (3D trees to 150 m, impostors to 700, shell grass on), keeps the crowd out of the foreground, and runs in its own user-data folder so nobody's Settings (a depth-of-field blur, say) get into the shots — a re-run reproduces them. The chatter line is the on-device model's (Thimble answering Old Jasper); on a machine without the model the harness gets a written fallback line, so re-shoot where the gguf is. Edit the harness, not the images |
| `cn-trailer.webp` | The trailer's own frame at 1:18 (the ritual circle), the frame YouTube uses as its thumbnail, taken from the 1080p master | 1280×720, WebP quality 80. The poster shown until the trailer is played. Replace it if the trailer changes |
| `cn-key.webp`, `cn-key-560.webp` | cute-fantasy `icon.png` | The game's key art, resized. **Model-generated** — so nothing on the page describes it as painted or drawn by hand. `necro-key.webp` on the home page is the same source |
| `cn-og.jpg` | The key art on a dusk field | 1200×630 social preview |

## Tin Coffins page

Everything here is captured from the game by its own harness — [nvoorhies/robot-fps](https://github.com/nvoorhies/robot-fps) `tools/promo/capture.sh` (see that repo's `tools/promo/README.md`) — so a graphics update is a re-capture, not a redraw. The game's art is still in progress, and the page says so; re-derive every file below when that repo re-captures. Last re-captured 2026-10-05 from robot-fps master `8b05569`: the restyled city and the Blender-built mechs.

| file | source | notes |
| --- | --- | --- |
| `tc-firefight.webp`, `tc-dropship.webp`, `tc-orders.webp`, `tc-salvo.webp`, `tc-smoke.webp`, `tc-arrival.webp` | robot-fps `store/screenshots/desktop/0N-*.png` (the Steam screenshots) | 1400×788, WebP quality 82 |
| `tc-hero.webp`, `tc-hero-480.webp` | robot-fps `capture.sh art` frame `04-salvo.png` (3840×2160, HUD hidden) | 4:5 crop around the mech, x 1400–2720, y 480–2130, so the muzzle flash and the rocket's trail are in frame. 880×1100 and 480×600, WebP quality 82 |
| `tc-card.webp` | `capture.sh art` frame `06-arrival.png` | 16:10 at full height, centred; 960×600, for the home page card |
| `tc-og.jpg` | `capture.sh art` frame `02-dropship.png` with the wordmark, as `tools/promo/steam_art.py` lays it on the capsules | 1200×630 social preview: cut and graded like the header capsule (`_cover` focus 0.5, 0.42, then `_grade`), the wordmark along the bottom at 66% of the width |
| `tc-wordmark.webp` | robot-fps `store/steam/library_logo.png` (drawn by `tools/promo/brand.py`) | Cropped to the ink, 1240 wide, with alpha |
| `tc-combat-effective.webp` and five more citation badges | robot-fps `store/steam/achievements/large/` (`tools/promo/achievement_icons.py`) | 176×176. The hidden achievement and the act finales are left off — they name the story |
| `fonts/roboto-condensed-bold.woff2` | Roboto Condensed Bold, the logotype's face (robot-fps `store/fonts/`) | Latin subset, converted with fontTools. Apache 2.0 (`LICENSE-roboto-condensed.txt`) |

## Goblin Hunt page

| file | source | notes |
| --- | --- | --- |
| `gh-village.webp`, `gh-wilds.webp`, `gh-tavern.webp`, `gh-dungeon.webp`, `gh-prologue.webp`, `gh-title.webp` | Captured from the itch.io prototype (hexmonger.itch.io/goblin-hunt) in a headless browser, Sept 2026 | Converted to greyscale and cropped to leave out the arena debug line. Recapture them from a release build before launch |
| `gh-riverbank.gif`, `gh-strike.gif` | Captured from the game itself: [nvoorhies/goblin-hunt](https://github.com/nvoorhies/goblin-hunt) `scripts/capture_gifs.sh` | 480×270, 12 fps. The probes behind them (`tests/visual_riverbank_probe.tscn`, `tests/visual_strike_probe.tscn`) boot the real game on a fixed map seed, so a re-run is the same shot. Re-run that script rather than editing the GIFs |
| `gh-og.jpg` | A 1200×630 render of the page's title leaf | Re-render if the title page changes |
| `fonts/fell-sc.woff2`, `fonts/fell-italic.woff2` | IM Fell English (SC and italic), from Fontsource | SIL OFL |
| `fonts/garamond*.woff2` | EB Garamond variable, from Fontsource | SIL OFL |
