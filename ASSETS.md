# Where the images come from

Everything in `assets/img/` is a resized copy. To change one, start from
the source and export it again. Don't edit the web copy.

| file | source | notes |
| --- | --- | --- |
| `cits-hero.webp`, `cits-hero-800.webp` | castles-in-the-sand `icon.png` (1024², the key art without the title) | Cropped to rows 250–890. The crop leaves out the bottom-right corner, which has a generator watermark sparkle |
| `og-image.jpg` | same, rows 200–738 | 1200×630 social preview |
| `cits-02-build.webp`, `cits-04-waves.webp`, `cits-06-hydraulics.webp` | castles-in-the-sand `store/screenshots/android-tablet/*.jpg` | 1200×750, WebP quality 80. Re-derive them whenever that repo re-captures its masters |
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
| `cn-hero.webp`, `cn-hero-560.webp`, `cn-wood.webp`, `cn-village.webp`, `cn-dialogue.webp`, `cn-chatter.webp`, `cn-moonwell.webp` | The Steam screenshots: [nvoorhies/cute-fantasy](https://github.com/nvoorhies/cute-fantasy) `store/screenshots/desktop/` `03-wood`, `02-village`, `01-dialogue`, `05-chatter`, `06-moonwell` (1920×1080, captured Oct 2 2026 by `scripts/capture_promo.sh` with the procedural blade grass: `a22c178`, and `f76a2b3` for the chatter; `store/steam.md` *The screenshots* has the recipe) | WebP quality 82. `cn-hero` is the page's hero: a 1080² square of `03-wood` from x 510, at 900² and 560². `cn-wood` (the home page's main picture), `cn-dialogue` and `cn-village` are 1400×788: the first two whole frames, the village cut from x 120–1800, y 0–945 to lose some empty sand. `cn-chatter` and `cn-moonwell` are 1.9:1 at 1180×621, so they stand the same height side by side: the full width, from y 20 and y 0. The chatter shot's Driver Kess line is the on-device model's; Georg's reply is his written fallback line. Re-derive these whenever cute-fantasy re-captures its screenshots |
| `cn-trailer.webp` | The trailer's own frame at 1:18 (the ritual circle), the frame YouTube uses as its thumbnail, taken from the 1080p master | 1280×720, WebP quality 80. The poster shown until the trailer is played. Replace it if the trailer changes |
| `cn-og.jpg` | The same `03-wood` screenshot, with cute-fantasy's logotype `store/steam/library_logo.png` laid on it by `tools/promo/steam_art.py` | 1200×630 social preview: x 200–1800, y 240–1080 of the frame (closer in than the Steam capsules, so the necromancer holds up as a small thumbnail), then `_with_logo` at 0.55 of the width along the bottom, as on the header capsule. JPEG quality 88. The game's key art (`icon.png`) is model-generated, so the site uses none of it |

## Tin Coffins page

Everything here is captured from the game by its own harness — [nvoorhies/robot-fps](https://github.com/nvoorhies/robot-fps) `tools/promo/capture.sh` (see that repo's `tools/promo/README.md`) — so a graphics update is a re-capture, not a redraw. The game's art is still in progress, and the page says so; re-derive every file below when that repo re-captures. Last re-captured 2026-10-12 from robot-fps `2261787` (nvoorhies/robot-fps#632, on master `2de1f5b`): the cartouche HUD, the opening force at today's density. The Steam set is seven stills now, so the page's old `salvo` and `smoke` slots took `05-exchange` and `07-wreck`.

| file | source | notes |
| --- | --- | --- |
| `tc-firefight.webp`, `tc-dropship.webp`, `tc-orders.webp`, `tc-exchange.webp`, `tc-arrival.webp`, `tc-wreck.webp` | robot-fps `store/screenshots/desktop/` `01-firefight`, `02-dropship`, `03-orders`, `05-exchange`, `06-arrival`, `07-wreck` (the Steam screenshots) | 1400×788, WebP quality 82. `04-hero` is the page's hero below, so it isn't used twice |
| `tc-hero.webp`, `tc-hero-480.webp` | robot-fps `capture.sh art` frame `04-hero-tall.png` (2160×2880, HUD hidden): the key-art frame the Steam tall capsules are cut from | 4:5 at full width, y 100–2800 (less sky). 880×1100 and 480×600, WebP quality 82 |
| `tc-home-hero.webp`, `tc-home-hero-800.webp` | `capture.sh art` frame `04-hero.png` (3840×2160, HUD hidden) | The home page's hero. 16:10 at full height from x 96, so the firing mech sits right of the copy; 1600×1000 and 800×500, WebP quality 82 |
| `tc-og.jpg` | `capture.sh art` frame `02-dropship.png` with the wordmark, as `tools/promo/steam_art.py` lays it on the capsules | 1200×630 social preview: cut and graded like the header capsule (`_cover` focus 0.5, 0.42, then `_grade`), the wordmark along the bottom at 66% of the width on the header's ink band (`_with_logo`, band 0.42), JPEG quality 88 |
| `tc-wordmark.webp` | robot-fps `store/steam/library_logo.png` (drawn by `tools/promo/brand.py`: Michroma since 2026-10-09) | Cropped to the ink, 1240 wide (1240×175), with alpha, WebP quality 90 |
| `tc-combat-effective.webp` and five more citation badges | robot-fps `store/steam/achievements/large/` (`tools/promo/achievement_icons.py`) | 176×176. The hidden achievement and the act finales are left off — they name the story |
| `fonts/roboto-condensed-bold.woff2` | Roboto Condensed Bold, the page's heading face (robot-fps `store/fonts/`, where it sets the icons' stencil and the trailer's cards) | Latin subset, converted with fontTools. Apache 2.0 (`LICENSE-roboto-condensed.txt`) |

## Goblin Hunt page

| file | source | notes |
| --- | --- | --- |
| `gh-village.webp`, `gh-wilds.webp`, `gh-tavern.webp`, `gh-dungeon.webp`, `gh-prologue.webp`, `gh-title.webp` | Captured from the itch.io prototype (hexmonger.itch.io/goblin-hunt) in a headless browser, Sept 2026 | Converted to greyscale and cropped to leave out the arena debug line. Recapture them from a release build before launch |
| `gh-riverbank.gif`, `gh-strike.gif` | Captured from the game itself: [nvoorhies/goblin-hunt](https://github.com/nvoorhies/goblin-hunt) `scripts/capture_gifs.sh` | 480×270, 12 fps. The probes behind them (`tests/visual_riverbank_probe.tscn`, `tests/visual_strike_probe.tscn`) boot the real game on a fixed map seed, so a re-run is the same shot. Re-run that script rather than editing the GIFs |
| `gh-og.jpg` | A 1200×630 render of the page's title leaf | Re-render if the title page changes |
| `fonts/fell-sc.woff2`, `fonts/fell-italic.woff2` | IM Fell English (SC and italic), from Fontsource | SIL OFL |
| `fonts/garamond*.woff2` | EB Garamond variable, from Fontsource | SIL OFL |
