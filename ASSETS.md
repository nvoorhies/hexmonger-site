# Where the images come from

Everything in `assets/img/` is a resized copy. To change one, start from
the source and export it again. Don't edit the web copy.

| file | source | notes |
| --- | --- | --- |
| `cits-hero.webp`, `cits-hero-800.webp` | castles-in-the-sand `icon.png` (1024², the key art without the title) | Cropped to rows 250–890. The crop leaves out the bottom-right corner, which has a generator watermark sparkle |
| `og-image.jpg` | same, rows 200–738 | 1200×630 social preview |
| `cits-02-build.webp`, `cits-04-waves.webp`, `cits-06-hydraulics.webp` | castles-in-the-sand `store/screenshots/android-tablet/*.jpg` | 1200×750 |
| `necro-key.webp` | cute-fantasy `icon.png` | 900² |
| `gh-building_house.png`, `gh-barrow_mouth.png`, `gh-wall_tower.png` | topdown-bw `assets/art/*.png` | Shown pixelated on the Goblin Hunt card, which stays a placeholder until there is real key art |
| `hexmonger-mark.svg` | drawn for this site | Studio mark and favicon |

Fonts: Fraunces and Inter variable woff2, Latin subset, from Fontsource.
Both are under the SIL Open Font License; the license files are in
`assets/fonts/`.

## Castles in the Sand page

| file | source | notes |
| --- | --- | --- |
| `cits-key-tall*.webp` | castles-in-the-sand `icon.png`, rows 60–900 | Leaves out the watermark in the bottom-right corner |
| `cits-app-icon.webp` | same, cropped square from the castle and child | Also used as the page favicon. The Play Store icon has the watermark, so it isn't used here |
| `cits-03-tide.webp`, `cits-05-result.webp` | `store/screenshots/android-tablet/` | 1200×750 |
| `cits-og.jpg` | `store/feature_graphic_1024x500.png` on a sand-coloured 1200×630 canvas | Social preview |
| `fonts/lilita-one.ttf` | castles-in-the-sand `fonts/` | The game's own display font (SIL OFL). Served unmodified, because the font's name is reserved and a converted copy would need a new name |

## Goblin Hunt page

| file | source | notes |
| --- | --- | --- |
| `gh-village.webp`, `gh-wilds.webp`, `gh-tavern.webp`, `gh-dungeon.webp`, `gh-prologue.webp`, `gh-title.webp` | Captured from the itch.io prototype (hexmonger.itch.io/goblin-hunt) in a headless browser, Sept 2026 | Converted to greyscale and cropped to leave out the arena debug line. Recapture them from a release build before launch |
| `gh-riverbank.gif`, `gh-strike.gif` | Captured from the game itself: [nvoorhies/goblin-hunt](https://github.com/nvoorhies/goblin-hunt) `scripts/capture_gifs.sh` | 480×270, 12 fps. The probes behind them (`tests/visual_riverbank_probe.tscn`, `tests/visual_strike_probe.tscn`) boot the real game on a fixed map seed, so a re-run is the same shot. Re-run that script rather than editing the GIFs |
| `gh-og.jpg` | A 1200×630 render of the page's title leaf | Re-render if the title page changes |
| `fonts/fell-sc.woff2`, `fonts/fell-italic.woff2` | IM Fell English (SC and italic), from Fontsource | SIL OFL |
| `fonts/garamond*.woff2` | EB Garamond variable, from Fontsource | SIL OFL |
