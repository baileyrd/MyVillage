# My AI Village: notes

Running record of every decision, plus the build log. Read this first each session.

## Ground rules (from Nano)

- Nano is the director and says what they want in plain words. Claude builds it.
- It is a web page that runs on Nano's own computer. Everything lives in this folder, `ai-village`.
- Every decision goes in this file.
- Each finished piece is shown to Nano before moving on.
- Before creating, overwriting or deleting files, running anything on Nano's computer, or spending anything, Claude says what it is about to do in plain words and waits for a yes.
- Keep the code small, simple and light on dependencies.

## Style guide (use word for word in every art prompt)

> A cozy village drawn in 32-bit pixel art, in the manner of a late-1990s console role-playing game, with crisp square pixels and no blur or smoothing. The palette is warm: honey and amber wood, terracotta and brick-red roofs, sun-yellowed greens for grass and leaves, sandy tan paths, and soft cream highlights, with shadows leaning toward warm brown and plum rather than gray or black. Everything is seen from a top-down three-quarter view, so roofs and the front walls of buildings are both visible and nothing is shown in side-on or true overhead view. Light comes from the upper left, so upper and left edges are brighter and every object casts a short, soft shadow toward the lower right. Every object has a dark outline, one pixel wide, in a deep warm brown instead of pure black. There is no text anywhere: no letters, numbers, signs with writing, labels, logos or watermarks.

Nano's own words for the style: 32-bit pixel art, warm colors, top-down three-quarter view, light from the upper left, dark outlines, no text anywhere.

## Decisions

| Date | Decision |
|---|---|
| 2026-11-16 | Project is called "My AI Village" and lives at `C:\Users\baile\ai-village`. |
| 2026-11-16 | Built with Fable 5.2, at Nano's request. |
| 2026-11-16 | Vision: a top-down 32-bit RPG village. Each of Nano's AI agents will live and work in their own house. First build is the whole town with nobody in it: houses, paths, trees, a town square and a town hall. Every house can be walked into. |
| 2026-11-16 | Keep a build log here: per session the date, start and end time, and what was built. Total the hours and cost when the build is done. |
| 2026-11-16 | Ignore usage numbers: no reminders to check the Claude usage screen and no logging of those figures. |
| 2026-11-16 | Style guide written before any art. The paragraph above is used word for word in every art prompt. |
| 2026-11-16 | Art is drawn in code by Claude (no image generator in the thread), with the style guide as the brief for every piece. `tools/make_maps.py` draws the town maps (needs Python and Pillow; it was run in Claude's cloud workspace, not on Nano's computer). |
| 2026-11-16 | Town map: one image, 1280 x 960 pixels, an 80 x 60 grid of 16-pixel tiles. 10 houses around a central square with a fountain, town hall on the north side, a path to every front door, and a three-tile-deep open yard in front of every house. All versions share one layout, so doors, yards and paths are in the same place whichever is picked. |
| 2026-11-16 | Five period versions made for Nano to choose from, in `maps/`: 1 Iron Age (about 500 BC), 2 Roman (about 100 AD), 3 Medieval (about 1300), 4 Victorian (about 1880), 5 1950s. |
| 2026-11-16 | Nano picked map 5, the 1950s small town (`maps/town-5-nineteen-fifties.png`). The village is set in the 1950s from here on. |
| 2026-11-16 | Nano wants the map at the highest quality for zooming in and out. Made a master, `maps/town-5-nineteen-fifties-4x.png`, 5120 x 3840: every art pixel is a crisp 4 x 4 block (same art, no blur). The web page must always scale the map with crisp pixels, never smoothing. A redraw with finer detail is on offer if Nano wants it. |
| 2026-11-16 | Nano asked to see a sample house in finer detail. Claude drew one 1950s house at three times the detail (48-pixel tiles) and showed it beside the current one. |
| 2026-11-16 | Nano said yes to the finer style. The whole 1950s town was redrawn at three times the detail: `maps/town-1950s-hd.png`, 3840 x 2880, 48-pixel tiles. Same layout and tree positions as the map Nano picked; one old tile is one new tile, three times larger. This is now the town map. The earlier 1x and 4x maps are kept as history. |
| 2026-11-16 | Nano said yes to the walkable town page: `index.html`, opened by double-clicking, nothing installed. A visitor in a hat and coat (`maps/visitor.png`) walks with the arrow keys or WASD, starting on the south road, and bumps into houses, trees, the fountain, benches, lamps and mailboxes. Things nearer the camera are drawn over the visitor (`maps/town-1950s-objects.png`). Blocked ground and the list of standing things are in `maps/town-1950s.js`. Mouse wheel or + and - zoom; 0 shows the whole town. Pixels stay crisp zoomed in and are smoothed only when shrunk below full size. |
| 2026-11-16 | `tools/make_town_hd.py OUT_DIR` draws the map, the objects layer, the data file and the visitor in one go (needs Python, Pillow, and `make_maps.py` beside it). It was run in Claude's cloud workspace, not on Nano's computer. |

## Open questions


- Price per credit and Claude plan cost, needed for the final cost total.
- Nano's time zone. Times below are UTC until known.

## Build log

| Session | Date | Start | End | What we built |
|---|---|---|---|---|
| 1 | 2026-11-16 | 01:50 UTC | 02:55 UTC | Agreed ground rules, location and vision. Created this notes file with the style guide. Drew five period versions of the town map; Nano picked the 1950s. Made a 4x enlargement and a sample detailed house, redrew the whole 1950s town in finer detail, and built the walkable town page. Nano's computer went offline about 02:45 UTC, so the last files were copied over in session 2. |
| 2 | 2026-11-16 | 11:51 UTC | | Copied the detailed map and the walkable town page into this folder and brought these notes up to date. |
