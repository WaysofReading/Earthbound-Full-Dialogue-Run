# Web Companion

A public-facing map + archive of every dialogue in EarthBound, built from the
committed extraction outputs in `resources/dialogue/extracted/`.

- **Map view** — the stitched overworld and detached/interior places, with every
  map-present entity as a clickable marker (NPC sprites from the game's own
  sprite groups; type glyphs for signs/doors/presents/photo events).
- **Dialogue panel** — a structured tree of a node's reachable script (all five
  edge types, effects, cycles as back-references, function-call previews) with a
  graph-mode toggle.
- **Archive** — a sortable/filterable table of all 6,153 nodes, including content
  unreachable in normal play.
- **Search** — entity scope (label/region/type) and full-text scope over node
  plaintext, with entity context.

Everything is a projection of one data substrate (`data-prep` outputs). Every
entity and node has a shareable hash URL.

## Architecture

```
data-prep/   Python ETL: extraction outputs -> web/public/{data,sprites,maps}
web/         Vite + React + TS + Tailwind + react-leaflet (CRS.Simple)
```

The web client does no geometry beyond reading the manifest's per-region
`translate`: an entity at global game pixel `(gx,gy)` in region `R` renders at
place-image pixel `(gx+tx, gy+ty)`, then `latLng(-y, x)` for CRS.Simple. The
committed `/#/smoke` page asserts the verified anchor (Onett scam house photo at
`(944,186)` → `latLng(-186,944)`) and is the regression guard for the transform.

## Build locally

```bash
# 1. Generate data (Python 3.11+, needs Pillow + PyYAML)
pip install -r data-prep/requirements.txt
python data-prep/prep.py --out web/public        # writes data/, sprites/, maps/

# 2. Run / build the app (Node 20+)
cd web
npm install
npm run dev                                       # http://localhost:5173
npm run build                                     # -> web/dist
```

`prep.py` invokes `web/scripts/build-search.mjs` to build the MiniSearch indices
(so the serialized format matches the client). It skips that step gracefully if
Node or `web/node_modules` aren't present; the deploy workflow always runs it
after `npm ci`.

`web/public/{data,sprites,maps}` and `web/dist` are generated and gitignored.

## Deploy

`.github/workflows/deploy.yml` runs `data-prep/prep.py`, builds the app, and
publishes `web/dist` to GitHub Pages on pushes to `main` that touch `web/`,
`data-prep/`, or the consumed `resources/` inputs. **Extraction is never run in
CI** — the site is always built from committed, validated extraction outputs.

Enable Pages once in the repo settings (Settings → Pages → Source: GitHub
Actions). The build uses `base: './'`, so it works under a project subpath.

## Known v1 limitations

- Photo events have no reachable script in the current extraction (the
  SHOW_PHOTOGRAPHER engine infra is a v2 extraction earmark); they render as
  marker + footprint rectangle only.
- The overworld ships as a single image (~6.8 MB). If the extent or size grows,
  switch `data-prep/regions.py` to a tile pyramid (the manifest already carries a
  `tiles` slot for places).
- Navigation doors are off by default in the map filter to keep the dialogue map
  legible; enable the "door" checkbox to show them.
