# MyVillage

My AI Village: a walkable 1950s pixel-art town in a single static web page.

- Open `index.html` in a browser (no install, no build). Arrow keys or WASD to walk, mouse wheel or +/- to zoom, 0 for the whole town.
- `maps/` holds the town art and collision data; `tools/` holds the Python + Pillow scripts that draw them (`python tools/make_town_hd.py maps`): `kit.py` for shared parts, `buildings.py` for one recipe per building. After changing a building, run `python tools/check_town.py`: it fails if any part of a building could be drawn under the walker instead of over them.
- `NOTES.md` is the running decision record and build log.
