# Dialogue Extraction Rewrite: Specification

## Goals

Rewrite `process-dialogue.py` to extract Earthbound's dialogue and entity data into a graph-shaped data model that preserves conditional structure, avoids recursive inlining, and supports a map-based public-facing UI.

The current script forces a graph into a tree by recursive unrolling, loses edge semantics by flattening flag information into an unstructured list, and requires a hardcoded blacklist (`DIALOGUE_BLACKLIST`) to manage cycles. The rewrite addresses all three by treating the script as a directed graph with typed edges, storing each block exactly once, and computing reachability rather than inlining.

## Scope

In scope:
- Replacement of `process-dialogue.py` with a new extraction pipeline
- New output artifacts (described below)
- Expanded entity coverage beyond NPCs to include signs, doors, presents, and photo events
- Continued emission of `resources/dialogue/process-dialogue_output.csv` (consumed by the Lua text-access-monitor) and `resources/tables/npcs.csv` (legacy NPC table), both treated as deprecated
- Validation and analytics outputs

Out of scope:
- Lua text-access-monitor updates (legacy CSV preserved instead)
- Route spreadsheet updates
- UI implementation
- Parsing CCScript directly — the script-dumper output remains the input
- Item descriptions, hints, hotel newspaper headlines (these don't fit the map-based entity model)
- Backward compatibility with the existing nested per-NPC JSON / text files in `resources/dialogue/by_npc/`, `resources/dialogue/by_npc_working-set/`, and `resources/routes/by_npc/` — deprecated; the new entity files supersede them

## Input sources

The script consumes the inputs the current script uses, plus additional decompilation files for the expanded entity scope. The first implementation task is to inventory `resources/decompilations/20230106/` and map each entity type to its source file(s).

Currently confirmed:
- `resources/decompilations/20230106/npc_config_table.yml` — NPC records
- `resources/decompilations/20230106/map_sprites.yml` — sprite placement on the map
- `resources/dialogue/script-dumper_output.txt` — tokenized script
- `resources/dialogue/addresses.txt` — canonical list of dialogue address labels (used by validation)
- `resources/tables/regions-and-rooms.csv` — region bounding boxes
- `resources/tables/flags.csv` — English flag labels (derived from CataLatas constants, but consume from here)
- `resources/tables/npcs.csv` — current NPC table (output from the existing `process-dialogue.py`; see legacy-output note below)
- `resources/labels/sprite-group-labels.csv` — sprite labels

To be located within the decompilation directory at `resources/decompilations/20230106/`:
- Sign / interactive object data
- Door data including destinations
- Present data including item references
- Photo event data including trigger regions

If item, music, sprite, or other label tables become useful for `properties` or `effects`, source them from `utilities/earthbound-script-dumper/constants/`. Prefer the CSVs in `resources/tables/` over the Python constants files where both exist.

### Legacy outputs to consider

The existing `process-dialogue.py` produces two artifacts beyond the per-NPC JSON files:

- `resources/dialogue/process-dialogue_output.csv` — consumed by the Lua text-access-monitor. **Preserve**, as discussed in the Scope section.
- `resources/tables/npcs.csv` — a flat table of all NPCs. No known external consumer, but it has been part of the output contract. **Decision:** the rewrite preserves this CSV as well, emitting it from the new entity store. Treat as deprecated alongside `process-dialogue_output.csv`. If the new entity schema cannot cleanly populate one of its columns, emit a placeholder and log a finding rather than failing.

## Data model

The output centers on two collections: **nodes** (dialogue blocks) and **entities** (map-present things that may have dialogue). Edges live on their source nodes; effects also live on nodes. Entities reference nodes via entry points and reachability sets, never by inlining.

### Identifiers

Node IDs use the script-dumper's existing labels:
- Hex-labeled blocks: `L_C5E069` (preserving the `L_` prefix)
- NPC-labeled blocks: `Npc0042` (preserving the `Npc` prefix)

Entity IDs use a type prefix and zero-padded numeric ID separated by underscore: `npc_0042`, `sign_0007`, `door_0103`, `present_0021`, `photo_0003`. Filenames match: `npc_0042.json`.

All IDs are deterministic across runs given the same source data.

### Node schema

A node represents one labeled dialogue block.

```json
{
  "id": "L_C5E069",
  "label_kind": "hex",
  "raw": "<full script with control codes intact>",
  "plaintext": "<cleaned rendering for display>",
  "edges": [ /* see edge schema */ ],
  "effects": [ /* see effect schema */ ],
  "referenced_by": ["npc_0042", "npc_0107"]
}
```

`label_kind` is `"hex"` for `L_XXXXXX` labels and `"npc"` for `NpcNNNN` labels.

`referenced_by` is the per-node provenance list: entity IDs whose transitive reachability sets include this node. Sorted lexicographically.

### Plaintext rendering rules

- Strip pure formatting control codes (within-window line breaks, pauses for text speed, window open/close, etc.)
- Encode narrative pauses (player-facing waits) as `[PAUSE]` — disambiguates from typographical ellipses in the source text
- Translate name/party-position placeholders to bracketed display markers: `[NESS]`, `[PAULA]`, `[FAVORITE_FOOD]`, `[FAVORITE_THING]`, `[PARTY_MEMBER_1]`, etc. The exact set is determined by the placeholder vocabulary the script-dumper exposes
- When a control code or placeholder isn't in the explicit mapping, fail open: pass the dumper's bracketed token through to `plaintext` verbatim, and add the token to `validation.findings.unknown_placeholders` (deduplicated). The dumper's tokens are reasonably human-readable, so the UI degrades gracefully; the finding lets us decide whether to map them in a follow-up
- Drop everything else — flag tests, gotos, function calls, menu opcodes — since they appear as edges, not text

### Edge schema

Each edge is a discriminated union by `type`:

```json
{ "type": "unconditional", "target": "L_C5E069" }

{ "type": "flag_test", "flag": 42, "flag_label": "ONETT_INTRO",
  "polarity": "set", "target": "L_C5E069", "fallthrough": "L_C5E0A9" }

{ "type": "menu_option", "label": "Yes", "target": "L_C5E069" }

{ "type": "case_branch", "discriminant": "REG_RESULT",
  "value": "0", "kind": "goto", "target": "L_C5E069" }

{ "type": "function_call", "target": "L_C5E069" }
```

Notes:
- `unconditional` covers `GOTO` and `POST_FADE_GOTO` opcodes, plus sequential fallthrough into the next labeled block
- `flag_test.polarity` is `"set"` or `"cleared"`. Both branches are materialized: the conditional `target` and the implicit `fallthrough`. Sourced from `GOTO_IF_FLAG` (polarity `"set"`) and from the `LOAD_FLAG` + `GOTO_IF_FALSE` pair (polarity `"cleared"`)
- `function_call` is sourced from `GOSUB` and `MULTI_GOSUB`, which the script-dumper distinguishes from `GOTO`. The edge carries only `target`. The call returns to the next opcode within the same labeled block (GOSUB does not end the block), so a `return_to` field would be tautological with the edge's source node and is omitted. There is no `function_return` edge: the engine returns from a subroutine via `[END]`, which is indistinguishable from a script-terminating `[END]` without whole-program call-stack analysis. Reachability terminates at `[END]` regardless
- `case_branch` is sourced from `MULTI_GOTO` (`kind: "goto"`) and `MULTI_GOSUB` (`kind: "call"`). Each table-dispatch opcode produces one `case_branch` edge per target, in table order, with `discriminant: "REG_RESULT"` and `value` as the zero-based index as a string. The `kind` field defaults to `"goto"`; `"call"` carries the same return-to-caller semantic as `function_call`. The `discriminant` and `value` strings remain lossy-generic and may be refined later if the UI needs them
- `menu_option` edges are synthesized via a peephole pass over each node's opcodes. The recognized pattern is: `LOAD_STRING "X"` × N → `PRINT_STRINGS_HORZ N` (or `PRINT_STRINGS_VERT`) → `CREATE_MENU` → `CLEAR_LINE` → `MULTI_GOTO L_a L_b ...`. When matched, emit one `menu_option` edge per option, pairing each `LOAD_STRING` value with the corresponding `MULTI_GOTO` target; the `case_branch` edges that would otherwise have been emitted from the `MULTI_GOTO` are replaced. The match is strict — any deviation (extra opcodes between `CREATE_MENU` and `MULTI_GOTO`, count mismatch between strings and targets, dispatch via something other than `MULTI_GOTO`) falls back to ordinary `case_branch` edges and logs to `validation.findings.unrecognized_menus`. v1 only recognizes `MULTI_GOTO`-driven menus; other menu shapes (e.g. `CHECK_EQUAL` + `GOTO_IF_TRUE` chains) remain raw and are also logged to `unrecognized_menus`

Sequential fallthrough through script order — where one labeled block ends without an explicit goto and execution would continue into the next labeled block — must be materialized as an explicit `unconditional` edge.

### Effect schema

Effects are node-level side effects that fire when the node executes. Array order matches script order within the node.

```json
{ "type": "set_flag", "flag": 42, "flag_label": "ONETT_INTRO" }
{ "type": "clear_flag", "flag": 42, "flag_label": "ONETT_INTRO" }
{ "type": "give_item", "item": 17, "item_label": "Hamburger" }
{ "type": "take_item", "item": 17, "item_label": "Hamburger" }
{ "type": "change_money", "amount": -50 }
{ "type": "change_hp", "target": "ness", "amount": -10 }
{ "type": "start_battle", "encounter": 3 }
{ "type": "teleport", "destination": { "region": "onett", "x": 1024, "y": 512 } }
{ "type": "play_music", "track": 12 }
{ "type": "change_party", "action": "add", "member": "paula" }
{ "type": "other", "raw": "<opcode string from script dumper>" }
```

Lossy-generic principle: if the script-dumper exposes an opcode that doesn't fit a known type, emit `{ "type": "other", "raw": "<opcode>" }`. Add explicit types as they prove useful.

### Entity schema

Unified across types, discriminated by `type`.

```json
{
  "id": "npc_0042",
  "type": "npc",
  "label": "Onett Boy",
  "region": "<region label>",
  "location": {
    "x0": <int>, "y0": <int>, "x1": <int>, "y1": <int>,
    "x_tile": <int>, "y_tile": <int>,
    "x_sector": <int>, "y_sector": <int>
  },
  "visibility": {
    "condition": "always",
    "flag": null,
    "flag_label": null
  },
  "entry_points": [
    { "role": "primary", "node_id": "Npc0042" },
    { "role": "secondary", "node_id": "L_C5E069", "gated_by_flag": 42, "gated_by_flag_label": "ONETT_INTRO" }
  ],
  "reachable_nodes": ["L_C5E069", "L_C5E0A9", "Npc0042"],
  "properties": { /* type-specific */ }
}
```

`type` ∈ {`npc`, `sign`, `door`, `present`, `photo_event`}.

`location` is always a bounding box. Point entities (NPCs, signs, presents, doors) have `x0 == x1` and `y0 == y1`; their `x_tile`/`y_tile`/`x_sector`/`y_sector` fields derive from that point. Region entities (photo events) have real bounds; their tile/sector fields derive from the bounding-box centroid (`(x0+x1)//2`, `(y0+y1)//2`), accepting that a region spanning multiple sectors is assigned to one.

`visibility.condition` ∈ {`always`, `flag_set`, `flag_cleared`}.

`entry_points` order matches semantic priority (primary first). For NPCs: primary = Text Pointer 1, secondary = Text Pointer 2 with `gated_by_flag` populated from the NPC's Event Flag.

`reachable_nodes` is the transitive closure from all entry points, sorted lexicographically. Stored explicitly so the entity file is self-contained at the metadata level: the UI fetches the entity file, then fetches the listed nodes from `nodes.json`.

#### Type-specific `properties`

NPC:
```json
{ "sprite": <int>, "sprite_label": "<name>",
  "direction": "<dir>", "movement": "<pattern>" }
```

Sign:
```json
{ "sprite": <int> | null }
```

Door:
```json
{ "kind": "navigation" | "interactive",
  "destination": { "region": "<id>", "x": <int>, "y": <int> } | null }
```
Navigation-only doors have empty `entry_points` and non-null `destination`. Interactive doors may have both.

Present:
```json
{ "item": <int> | null, "item_label": "<name>" | null,
  "container": "present" | "trash" | "coffin" }
```
Present entry points reference shared presentation-infrastructure nodes (the Present Case/Switch blocks). The item is a parameter on the entity, not a unique dialogue. The UI is responsible for substitution at render time.

Photo event:
```json
{ "trigger": "region" | "npc", "photo_index": <int> | null }
```

## Pipeline stages

Internal organization is implementation latitude. Conceptual stages:

1. **Source ingestion.** Read decompilation YAMLs, region table, sprite labels, flag/item constants, and script-dumper output. Validate file presence and basic format.

2. **Script indexing.** Parse the script-dumper output into a map of label → ordered list of opcode lines. Intermediate, not output.

3. **Node construction.** For each indexed label, produce a node: parse opcode lines into `raw`, `plaintext`, `edges`, and `effects`. Do not follow references — build nodes locally. Materialize sequential fallthrough edges here using script linear order. Run the menu peephole pass after edge extraction: where the strict `LOAD_STRING` × N → `PRINT_STRINGS_HORZ` → `CREATE_MENU` → `CLEAR_LINE` → `MULTI_GOTO` pattern matches, replace the corresponding `case_branch` edges with `menu_option` edges; log near-misses to `validation.findings.unrecognized_menus`.

4. **Entity construction.** For each entity source, produce entity records with `entry_points` pointing to node IDs.

5. **Reachability computation.** For each entity, compute the transitive closure of nodes reachable from its entry points by following edges of any type. Store as `reachable_nodes`.

6. **Provenance computation.** Invert the reachability sets to populate each node's `referenced_by`.

7. **Validation pass.** Compute errors and findings.

8. **Analytics pass.** Compute analytics metrics.

9. **Output emission.** Write all output artifacts. Wipe-and-rewrite, not append.

## Output artifacts

All paths relative to repo root.

```
resources/dialogue/extracted/
  nodes.json                   global node store, dict keyed by node ID
  entities.json                global entity index (summary fields only)
  entities/
    npc_0042.json              one file per entity, full record
    sign_0007.json
    door_0103.json
    ...
  validation.json
  analytics.json
resources/dialogue/
  process-dialogue_output.csv  legacy, address → plaintext, for Lua scripts
resources/tables/
  npcs.csv                     legacy NPC table, populated from the new entity store
```

`nodes.json` contains the full global node store keyed by node ID. Estimated 2–5 MB. Loadable up front by the UI.

`entities.json` is a summary index: one row per entity containing `id`, `type`, `label`, `region`, and `location`. Used by the UI for map placement and search; full records loaded on demand.

`entities/<entity_id>.json` contains the full entity record.

All JSON pretty-printed with `indent=2` and sorted keys. Arrays sorted by stable criteria (IDs lexicographic, references lexicographic) so the outputs diff cleanly between runs.

Legacy CSV (`process-dialogue_output.csv`): columns `address`, `dialogue`. Filtered to hex-labeled nodes only (no `Npc####` rows — the Lua text-access-monitor keys its lookup table by `tonumber(address, 16)`, so `Npc####` would silently produce `nil`). Address values use the lowercase 6-digit hex form (e.g. `c5e069`, not `L_C5E069`). Dialogue values keep the raw script lines (control codes intact, minus the leading label line) to preserve byte-for-byte compatibility with the existing CSV that the Lua tool already parses; this differs from each node's `plaintext` field, which strips control codes for the UI.

Legacy NPC CSV (`npcs.csv`): match the column structure of the existing file. Populate from entities where `type == "npc"`. If a column in the existing file cannot be cleanly derived from the new entity schema, emit the placeholder and add an entry to `validation.findings` under a new key `npcs_csv_columns_unfilled`.

## Validation

`validation.json`:

```json
{
  "summary": {
    "node_count": <int>,
    "edge_count": <int>,
    "entity_count_total": <int>,
    "entity_count_by_type": { "npc": <int>, "sign": <int>, "door": <int>,
                              "present": <int>, "photo_event": <int> }
  },
  "errors": {
    "unresolved_edge_targets": [
      { "node": "<id>", "edge_index": <int>, "target": "<bad id>" }
    ],
    "unresolved_entity_entry_points": [
      { "entity": "<id>", "entry_index": <int>, "target": "<bad id>" }
    ],
    "missing_labels_from_addresses_txt": ["<label>"],
    "provenance_inverse_mismatch": [
      { "node": "<id>", "issue": "<description>" }
    ],
    "schema_violations": [
      { "object_id": "<id>", "issue": "<description>" }
    ]
  },
  "findings": {
    "unreachable_nodes": ["<id>"],
    "entities_without_entry_points": [
      { "entity": "<id>", "type": "<type>" }
    ],
    "duplicate_plaintext": [
      { "ids": ["<id1>", "<id2>"], "sample": "<excerpt>" }
    ],
    "unknown_placeholders": ["<token>"],
    "unrecognized_menus": [
      { "node": "<id>", "reason": "mismatch" | "non_multigoto" | "other" }
    ]
  }
}
```

Exit code: non-zero if any `errors.*` array is non-empty; zero otherwise. `findings` do not affect exit code.

Validation semantics:

- `unresolved_edge_targets`: an edge's `target` or `fallthrough` references a node ID not in the node store. Bug.
- `unresolved_entity_entry_points`: an entity's entry point references a non-existent node. Bug.
- `missing_labels_from_addresses_txt`: every label in `resources/dialogue/addresses.txt` should appear in the node store. Missing labels are bugs.
- `provenance_inverse_mismatch`: for every node N, N's `referenced_by` must equal the set of entities whose `reachable_nodes` contains N. Mismatch is a bug.
- `schema_violations`: any object failing schema constraints (missing required fields, wrong types, unknown enum values).
- `unreachable_nodes`: nodes not in any entity's `reachable_nodes`. Earthbound contains genuinely unreachable dialogue, so this is expected non-empty.
- `entities_without_entry_points`: expected for navigation-only doors; flagged for review on other types.
- `duplicate_plaintext`: nodes with identical `plaintext`. Useful for spotting unintentional duplication; cheap to compute.
- `unknown_placeholders`: control codes or placeholder tokens passed through verbatim because no explicit mapping exists. Expected non-empty on first run; useful for sizing the placeholder mapping table.
- `unrecognized_menus`: nodes where the menu peephole pattern didn't match cleanly. Expected non-empty if non-`MULTI_GOTO` menu shapes are present (out of scope for v1).

Stdout on completion: one-line summary plus error and finding counts.

## Analytics

`analytics.json`:

```json
{
  "totals": {
    "nodes": <int>,
    "reachable_nodes": <int>,
    "unreachable_nodes": <int>,
    "entities_by_type": { "npc": <int>, "sign": <int>, "door": <int>,
                          "present": <int>, "photo_event": <int> },
    "dialogue_bytes_total": <int>,
    "dialogue_bytes_reachable": <int>
  },
  "shared_infrastructure": [
    { "node_id": "<id>", "reference_count": <int>, "plaintext_sample": "<excerpt>" }
  ],
  "regions": [
    { "region": "<label>", "entity_count": <int>,
      "entity_count_by_type": { ... } }
  ],
  "entity_dialogue_volume": [
    { "entity": "<id>", "label": "<name>",
      "reachable_node_count": <int>, "reachable_byte_count": <int> }
  ]
}
```

No validation semantics. Sort: `shared_infrastructure` descending by `reference_count`; `entity_dialogue_volume` descending by `reachable_byte_count`; `regions` by region label.

## Implementation notes

- Python 3.10+
- No new top-level dependencies expected beyond `requirements.txt`. Justify any additions in code comments.
- Script is fully re-runnable: wipe and rewrite outputs, do not append.
- All file I/O paths via the existing `CD` pattern from the current script.
- Output JSON pretty-printed with `indent=2` and sorted keys.
- Keep `process-dialogue.py` as the entry point filename; new module structure may split into multiple files (e.g., `extraction/nodes.py`, `extraction/entities.py`, `extraction/validation.py`) if useful.
- The `DIALOGUE_BLACKLIST` from the existing script should not appear in the new code. Its function is subsumed by the graph representation — shared infrastructure blocks are stored once and referenced by all callers.

## Definition of done

1. `process-dialogue.py` runs cleanly against the current decompilation and produces all output artifacts.
2. `validation.json` shows no errors (zero exit).
3. Legacy CSV is emitted with the same `address`, `dialogue` column structure as the existing output.
4. Spot check: pick three NPCs of varying complexity (a simple greeter, a shopkeeper, a plot-critical character) and manually inspect their entity files plus reachable nodes for fidelity to in-game behavior.
5. `DIALOGUE_BLACKLIST` is not present in the new code.
6. `findings` may be non-empty (unreachable nodes are expected); the values should be reviewable and explainable.
