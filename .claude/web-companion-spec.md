# Web Companion: Specification

## Goals

Build a public-facing web companion to the Earthbound Full Dialogue Run: a manipulable map of the game with every map-present entity rendered as a clickable marker, surfacing the extracted dialogue graph through a structured reading interface. The companion is archive-faithful: all 6,153 dialogue nodes are browsable, including content unreachable through normal play.

The companion is a published artifact. The spec covers the app, the data-prep pipeline that feeds it, and the build/deploy infrastructure — not just the UI.

Design principle: **the data layer is one substrate; the views are projections of it.** The map view and the archive view render the same node and entity stores through different lenses. No view requires data the others cannot access. Future projections (timeline, character network, monolithic map) should be addable without re-architecting.

One anticipated refinement: the project will eventually layer a second substrate over the first — **run-performance data** (when each dialogue node was reached in a recorded run, linking to YouTube timestamps). Game data describes what the ROM contains; performance data describes what one playthrough did. These stay in separate artifacts: extraction outputs are ROM-derived and stable, run overlays are derived from a specific recording and regenerate independently. v1 builds nothing for this but must not preclude it — concretely, the dialogue panel's node rendering should tolerate per-node annotation data arriving from a sidecar source (see v2 earmarks).

## Scope

In scope:
- `web/` — the web application (Vite + React + Tailwind + react-leaflet)
- `data-prep/` — Python ETL transforming extraction outputs into UI-shaped JSON, search indices, stitched map images, and sprite marker crops
- GitHub Pages deployment via GitHub Action
- Map view, dialogue panel, archive view, entity search, full-text search
- URL scheme with addressable entities and nodes

Out of scope (v1):
- Re-running extraction in CI (extraction stays manual; the Action consumes committed outputs)
- Per-flag visibility filtering ("show the world as it exists when flag X is set") — v2
- Information zoom (labels/sprites appearing around markers at high zoom) — v2
- Interactive transcript dialogue mode (IF-reader-style path walking) — v2
- Monolithic single-coordinate-space map mode — v2
- Cluster contents as side-panel list on modified click — v2
- Run-to-video linking (node → YouTube timestamp in the recorded run) — v2
- Analytics integration — decide at deploy time; if added, privacy-respecting only (Plausible/Umami)

## Repository structure

```
web/                       # Vite + React app
  public/
    data/                  # data-prep outputs (gitignored; generated at build)
    sprites/               # marker sprite crops (gitignored; generated at build)
  src/
    components/
    views/                 # MapView, ArchiveView
    lib/                   # data loading, search, routing helpers
  index.html
  package.json
  vite.config.ts

data-prep/                 # Python ETL, sibling of extraction/
  prep.py                  # orchestration entry point
  regions.py               # region bundle chunking, overworld stitching
  sprites.py               # front-facing sprite crops from spritesheets
  search.py                # prebuilt search index generation
  manifest.py              # entity summary index, world/places index
```

`data-prep/` reads from `resources/dialogue/extracted/` (nodes, entities, per-entity files), `resources/maps/regions-trimmed-flat-by-name/` (region images), `resources/tables/regions-and-rooms.csv`, and the NPC spritesheet directory. It writes only into `web/public/`.

Stack notes:
- TypeScript recommended for `web/` — the data model is non-trivial and schema drift should fail at compile time.
- react-leaflet with `CRS.Simple` for the map; `leaflet.markercluster` for semantic zoom.
- Search index prebuilt at data-prep time with MiniSearch or FlexSearch (implementation's choice; both produce serializable indices loadable client-side).

## Data-prep outputs

All under `web/public/`:

```
data/
  manifest.json            # world structure: places, regions, image refs, coord transforms
  entities-index.json      # summary index: id, type, label, region, location, has_dialogue,
                           #   visibility condition, sprite ref — one row per entity (~3,694)
  entities/<id>.json       # passthrough of extraction per-entity files (or merged bundles
                           #   per region if file count becomes a deploy problem)
  nodes/by-region/<region>.json   # node bundles for map use: nodes reachable from entities
                                  #   in that region
  nodes/all.json           # full node store for archive + search use, lazy-loaded
  search-entities.idx      # prebuilt entity search index
  search-fulltext.idx      # prebuilt full-text search index over node plaintext
sprites/
  npc/<sprite_id>.png      # front-facing crops, deterministic naming from sprite ID
  type/<type>.png          # type markers for sign, door, present, photo_event, and
                           #   the missing-sprite fallback
maps/
  overworld/...            # stitched contiguous overworld (tiled if size requires)
  places/<place>.png       # detached worlds and interiors: Magicant, Moonside,
                           #   Lost Underworld, interiors as grouped places
```

### Coordinate handling

The chain is: game pixel coordinates (from entity `location`) → position within the stitched overworld or place image → Leaflet `CRS.Simple` coordinates. `manifest.json` carries the transform parameters for each place (origin offset, image dimensions). 

**Required smoke test:** before any UI work beyond the map shell, place one known entity (recommend the Onett scam-house photo trigger at pixel (944, 186), the one verified photo coordinate) and visually confirm the marker lands correctly. Build this as a standalone test page or storybook entry that survives into the repo — it is the regression test for the transform.

### Overworld stitching

Earthbound's overworld regions share a global coordinate space; the region PNGs' filenames encode their bounding boxes. `data-prep/regions.py` stitches contiguous overworld regions into one image (or a tile pyramid if the assembled image exceeds practical limits for a single `L.imageOverlay`). Detached coordinate spaces (Magicant, Moonside, Lost Underworld, interiors) become separate places.

Decide at implementation: single large image vs. Leaflet tile pyramid. If the stitched overworld exceeds ~8K×8K or ~20 MB, generate tiles (standard z/x/y layout, `L.tileLayer` with `CRS.Simple`). Note GitHub Pages limits: 1 GB repo, ~100 MB per file — tiles also avoid the per-file cap.

### Sprite marker generation

`data-prep/sprites.py` carves the front-facing view from each NPC spritesheet PNG (filenames match in-game sprite IDs). Deterministic: same input → same output filename, so the UI constructs sprite URLs from sprite IDs without an index. 

Non-NPC entity types (sign, door, present, photo_event) and the missing-sprite fallback use graphics from the Earthbound graphics set — unused or rarely-used sprites chosen to read as type icons. The specific sprite-ID assignments are an implementation deliverable; the constraint is that all marker graphics come from the game's own iconography, and the missing-sprite fallback must be visually distinct from all type markers (it means "NPC with no sprite available," not "this is a sign").

## Map view

Default landing view. Stitched overworld zoomed to fit, all dialogue-bearing entity markers visible, a brief dismissable banner introducing the project (one or two sentences plus a link to the Substack).

### Places navigation

A places sidebar (collapsible) lists the detached worlds and interior groups. Selecting a place swaps the map to that place's image and entity set. The overworld is the default place.

### Markers

- NPCs: front-facing game sprite as the marker icon.
- Signs, doors, presents, photo events: type-appropriate Earthbound graphics (see data-prep).
- Photo events render their real bounding box as an `L.rectangle` in addition to a marker at the box center.
- Entities with no dialogue (no entry points): **hidden by default**, surfaced via filter toggle.
- NPCs with no matching sprite asset: fallback marker, visually distinct from type markers.

### Semantic zoom

`leaflet.markercluster` with:
- Cluster radius 40 px (tight — the game stacks NPCs closely)
- Monochrome cluster styling with numeric badge (count only, not type breakdown)
- Click cluster → zoom until expansion (plugin default)

### Hover and click

- Hover: unobtrusive tooltip with entity label and type. Serves disambiguation in dense areas and signals interactivity.
- Click: side panel slides in with the dialogue panel (below). Map remains interactive in the remaining space. Selecting another marker replaces panel content.

### Filter sidebar

Hidden by default, toggled from a control on the map. Contents:
- Entity type checkboxes (npc / sign / door / present / photo_event)
- Region selector (within the current place)
- "Show entities with no dialogue (N)" toggle, default off, count computed from data

Per-flag visibility filtering is explicitly v2.

## Dialogue panel

Shared component used by both views. Anchored on an entity (map view) or a node (archive view).

### Header

Entity context: label, type, region, sprite, visibility condition (always / flag-gated with flag name). When anchored on a node instead, show node ID, label kind, reachable/unreachable status, and referenced-by count with click-through to the referencing entities.

### Rendering: structured tree (default mode)

Entry points are roots. Each node renders:
- Plaintext, styled as the primary reading content
- Effects inline beneath the text, visually distinct from dialogue (muted color, icon prefix, monospace — implementation's choice, but the styling should signal "this is the script *doing* something, not saying something")
- Outgoing edges as labeled affordances, expand-on-click:
  - `unconditional`: thin connector, minimal chrome
  - `flag_test`: prominent; both branches labeled ("If MET_BOB is set:" / "Otherwise:") using flag labels from the extraction
  - `menu_option`: labeled list ("Yes:" / "No:" / "Goodbye:")
  - `case_branch`: discriminant in muted text, branch value as label
  - `function_call`: rendered as a cross-reference with inline preview — first sentence or menu options of the called node, plus click-to-expand for full content. Marked visually as a call ("Calls →"). Subject to revision once seen in practice.
- Cycles render as back-references ("↩ returns to [node]" with anchor link), never re-expansion.

Shared infrastructure: when a node's referenced-by count exceeds 1, surface it ("shared with N other entities") with click-through to the list.

### Rendering: graph mode (toggle)

A node-edge diagram of the entity's reachable subgraph (or the node's neighborhood when anchored on a node). Visual basis: the existing `tools/visualize_entity.py` vis-network rendering. Edge colors by type, consistent with the structured tree's labeling. This mode exists because the graphs are visually compelling and make the executable character of the script legible.

The toggle preserves anchor and selection state across modes where feasible.

## Archive view

Separate top-level view, reachable from the nav bar. Deliberately cheap: a projection of the same data with no custom interactions.

- Table of all 6,153 nodes: columns for node ID, plaintext excerpt, reachable/unreachable, referenced-by count, edge count. Sortable by any column. Filters: reachability, label kind (hex / npc).
- Row click → the shared dialogue panel anchored at that node.
- Header copy frames the view correctly: this is the same corpus as the map, indexed by node rather than by place — including the substrate unreachable through normal play.

No bespoke layouts, no anticipated research workflows. If usage justifies investment, elaborate later.

## Search

Both search scopes ship in v1.

- **Entity search**: by label, region, type. Serves "I remember the character but not where."
- **Full-text search**: across all node plaintext, returning nodes with entity context (which entities reach this node, where they are). Serves the cultural-corpus use case — memorable phrases are how people remember this game, and phrase → speaker → place is the index of record.

Implementation: prebuilt indices generated at data-prep time, lazy-loaded on first search. Results display in a unified results panel; entity results link into the map view, node results into the archive view (or the map view via a referencing entity).

## URL scheme

Hash-based routing (GitHub Pages has no server-side rewrites; the 404.html redirect hack is brittle). Clean paths become trivial later behind a custom domain + CDN; note as v2 polish.

Addressable states:
```
/#/                         map, default landing
/#/map?place=overworld&region=onett
/#/entity/npc_0042          map, entity selected, panel open, map centered on entity
/#/node/L_C5E069            archive, node selected, panel open
/#/archive                  archive table
/#/search?q=fuzzy+pickles   search results
```

Consistency requirement: entity URLs and node URLs are co-equal first-class citizens. The dialogue panel cross-links between them — an entity's panel links to its nodes' archive URLs; a node's panel links to its referencing entities' map URLs. Every shareable thing has a URL. This is what makes the site quotable from the Substack.

## Build and deploy

GitHub Action:

1. Trigger: push to main affecting `web/`, `data-prep/`, or `resources/dialogue/extracted/`
2. Run `data-prep/prep.py` → outputs into `web/public/`
3. `npm ci && npm run build` in `web/`
4. Deploy `web/dist/` to GitHub Pages

Extraction is **not** run in CI. It is manual, slow, changes rarely, and its outputs are committed and validated (exit-code semantics from the extraction spec). The deployed site is always built from committed, validated extraction outputs — an extraction regression cannot break the published site.

Data loading at runtime:
- `manifest.json` and `entities-index.json` load at startup (small)
- Per-region node bundles lazy-load as the map enters regions
- `nodes/all.json` and search indices lazy-load on first archive visit or first search

## Definition of done

1. Coordinate smoke test passes: the verified photo event (Onett scam house, pixel (944, 186)) renders at the correct map position, and the test page is committed.
2. Map view renders the stitched overworld with all dialogue-bearing entities as sprite/type markers; clustering behaves at 40 px radius; places sidebar navigates to at least Magicant and one interior group.
3. Clicking any entity opens the dialogue panel; the structured tree renders all five edge types with their specified treatments; effects render inline and visually distinct; cycles render as back-references; graph mode toggle works.
4. Archive view lists all 6,153 nodes, sortable and filterable; row click opens the panel; unreachable nodes are present and labeled.
5. Both search scopes return results; a search for a known memorable phrase surfaces the right node and its entity context.
6. Every entity and node URL round-trips: navigating to the URL directly reproduces the selection state.
7. The site deploys to GitHub Pages via the Action from a clean clone.
8. The no-dialogue filter toggle reveals the 267 audited silent entities.

## v2 earmarks

Recorded so they aren't re-derived later. None of these constrain v1 except where noted above.

- **Per-flag visibility filtering**: render the world as it exists at a given plot state. Depends on entity visibility conditions (already extracted) and possibly node-level flag reasoning.
- **Information zoom**: labels, sprite enlargements, or summary chips appearing around markers at high zoom.
- **Interactive transcript mode**: IF-reader-style path walking through an entity's dialogue, building a transcript of one traversal. Player-faithful complement to the structured tree.
- **Monolithic map mode**: the entire game coordinate space as one deep-zoom view, regional boundaries as overlays. Data-natural — `regions-and-rooms.csv` already partitions the space.
- **Conceptual-NPC grouping**: one marker per conceptual character linking multiple TPT instances (deferred from the original map discussion).
- **Cluster contents list**: modified click on a cluster shows its contents in the side panel.
- **Clean URL paths** behind a custom domain.
- **Photo-event entry points**: model SHOW_PHOTOGRAPHER engine infrastructure so photo events gain reachable nodes (extraction-side work surfaced in the handoff).
- **Present item/container resolution** (extraction-side, handoff caveat #6) — improves present marker tooltips and panel content.
- **Run-to-video linking**: per-node "watch this moment" affordances in the dialogue panel, linking to timestamps in the recorded run on YouTube (currently three parts). Implementation sketch, recorded so the dependencies are visible:
  - *Data source.* The text-access-monitor already logs every dialogue label accessed during a `.bk2` movie. To produce timestamps, the log must also capture the **frame number** at each access. Verify whether the current Lua logging includes frames; if not, this is a requirement on the planned Lua rewrite (cross-project dependency — note it in that work when it starts).
  - *Calibration.* Emulator frames do not map linearly to video time across the whole recording: each YouTube part has its own start offset, and pauses/loads/editing introduce drift. Plan for a small per-part calibration table (a handful of anchor points: known frame → known video timestamp, interpolated between). Manual to create, but only needed once per published recording.
  - *Sidecar artifact.* A `run-links.json` mapping `node_id → [{video_id, timestamp_seconds, occurrence_index}]`. One-to-many: nodes visited multiple times in the run carry multiple entries. Lives in `data-prep` output, generated from the access log + calibration table. Never merged into `nodes.json` — performance data stays separate from game data per the design principle.
  - *UI.* The dialogue panel renders a per-node affordance when an entry exists ("▶ 2:14:33 in Part 2"), deep-linking via `youtu.be/<id>?t=<seconds>`. Nodes without entries show nothing. Reachable-but-unvisited nodes are themselves interesting (route gaps) — a possible archive-view filter.
  - *No v1 changes required.* The schema, URL scheme, and panel structure all accommodate this as a sidecar annotation. The only v1 obligation is the design-principle note above: per-node annotations from sidecar sources must be renderable without restructuring the panel.
