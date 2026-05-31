# Dialogue Extraction Rewrite: Implementation Plan

Companion to [dialogue-extraction-spec.md](dialogue-extraction-spec.md). The spec is the contract; this plan is the buildable decomposition.

## Module structure

Flat `extraction/` package alongside `process-dialogue.py`:

```
process-dialogue.py        # entry point, orchestrates phases, prints summary
extraction/
  __init__.py
  sources.py               # all YAML/CSV/text loaders, path constants
  script_index.py          # raw dumper text → {label: [opcode_line, ...]}
  opcodes.py               # opcode line → typed dataclass (Opcode subclasses)
  nodes.py                 # opcode list → Node (edges, effects, plaintext, raw)
  plaintext.py             # opcode list → display string + unknown-placeholder log
  menus.py                 # menu peephole matcher
  entities.py              # YAML → Entity records (npc/sign/door/present/photo dispatch)
  reachability.py          # graph walk + provenance inversion
  validation.py            # error + finding computation
  analytics.py             # metric computation
  output.py                # JSON + CSV writers, wipe-and-rewrite
```

`process-dialogue.py` shrinks to ~50 lines of orchestration. Each `extraction/` module is independently testable.

## Phase 0 — scaffolding

- Create `extraction/` package, drop the existing monolithic logic behind a flag (don't delete yet).
- Move path constants to `extraction/sources.py`.
- New `process-dialogue.py` shell: load sources → call phase functions → write outputs. Pseudo-stubs only; no real logic yet.
- Verify it runs and produces empty output files.

**Deliverable:** runnable skeleton, empty JSON outputs.

## Phase 1 — script indexing (port + improve)

- `extraction/script_index.py`: parse `script-dumper_output.txt` into `{label: [opcode_line_str, ...]}`.
- Reuse the current regex approach in `process-dialogue.py` but normalize labels: hex labels get the `L_` prefix preserved, NPC labels use `Npc0042` as-is.
- Capture script linear order — need it for sequential-fallthrough edges later. Suggest a parallel list `[(label, ordinal_index), ...]`.

**Deliverable:** indexed dict, plus a one-line summary `N hex labels, M npc labels, K total`. Cross-check against `addresses.txt`.

## Phase 2 — opcode parsing

- `extraction/opcodes.py`: dataclasses for each opcode kind that influences edges, effects, or plaintext.
- Pragmatic approach: don't model every opcode. Group them:
  - **Control flow** (edge-producing): `GOTO`, `GOTO_IF_FLAG`, `LOAD_FLAG`, `GOTO_IF_FALSE`, `GOTO_IF_TRUE`, `GOSUB`, `MULTI_GOTO`, `MULTI_GOSUB`, `POST_FADE_GOTO`, `END`.
  - **Effect-producing**: `SET_FLAG`, `CLR_FLAG`, `GIVE_ITEM`, `REMOVE_ITEM`, `ADD_MONEY`, `REMOVE_MONEY`, `RECOVER_HP`, `DEPLETE_HP`, `START_BATTLE`, `START_TELEPORT`, `PLAY_MUSIC`, `ADD_PMEMBER`, `REMOVE_PMEMBER`. Everything else falls into `{type: "other", raw: "<opcode>"}`.
  - **Text-influencing** (for plaintext only): `LINE_BREAK`, `START_LINE`, `WAIT`, `PAUSE`, `HALT`, `HALT_PROMPT`, `PRINT_ITEM`, `PRINT_NAME`, `PRINT_NUM`, `PRINT_MONEY`, `LOAD_STRING`, `PRINT_STRINGS_HORZ`, `PRINT_STRINGS_VERT`, `CREATE_MENU`, `CLEAR_LINE`.
  - **Plain text** lines (not in `[…]`): the actual character data.
- Output: per-line parser returning `Opcode | None` (None for unparseable; logged).

**Deliverable:** parser that converts a node's line list into a typed sequence; round-trip diff against the input shows what we don't yet understand.

## Phase 3 — node construction (the big one)

Split across sub-modules:

### 3a. Edge extraction (`nodes.py`)
For each node's opcode sequence, emit edges per the spec's discriminated union:
- `GOTO` / `POST_FADE_GOTO` → `unconditional`
- `GOTO_IF_FLAG` → `flag_test` with `polarity: "set"` and synthesized `fallthrough` (the next opcode's owning node — within the same labeled block until the block ends, this is the same node; for the last opcode of a block, this is the next labeled block in script order if execution would fall through, otherwise omitted)
- `LOAD_FLAG` + immediately-following `GOTO_IF_FALSE` → `flag_test` with `polarity: "cleared"` (peephole pair recognition)
- `GOTO_IF_TRUE` → also a `flag_test` after a `LOAD_FLAG`; or a generic conditional after `CHECK_EQUAL`. Handle the `LOAD_FLAG` + `GOTO_IF_TRUE` case symmetrically; treat `CHECK_EQUAL` + `GOTO_IF_TRUE` as `case_branch` with `discriminant: "REG_RESULT"` and `value` from the CHECK_EQUAL operand.
- `GOSUB` → `function_call`
- `MULTI_GOTO L_A L_B L_C` → three `case_branch` with `kind: "goto"`, values `"0"`, `"1"`, `"2"`
- `MULTI_GOSUB` → same with `kind: "call"`
- Sequential fallthrough: only relevant if a block ends without an explicit terminator. Per the dumper, blocks always end at `END`/`GOTO`, so this should be rare; emit if encountered, log if surprising.

### 3b. Effect extraction (`nodes.py`)
Walk the opcode list a second time pulling out effects:
- `SET_FLAG <flag>` → `{type: "set_flag", flag, flag_label}`
- `CLR_FLAG <flag>` → `{type: "clear_flag", flag, flag_label}`
- `GIVE_ITEM <item>` / `GIVE_ITEM_RETURN_SLOT` → `{type: "give_item", ...}`
- `ADD_MONEY <n>` / `REMOVE_MONEY <n>` → `{type: "change_money", amount: ±n}`
- `RECOVER_HP` / `DEPLETE_HP` → `{type: "change_hp", target, amount}`
- `START_BATTLE <enc>` → `{type: "start_battle", encounter}`
- `START_TELEPORT <dest>` → `{type: "teleport", destination: ...}`
- `PLAY_MUSIC <t>` → `{type: "play_music", track}`
- `ADD_PMEMBER` / `REMOVE_PMEMBER` → `{type: "change_party", action, member}`
- Anything else with side effects → `{type: "other", raw}`
- Order preserved.

### 3c. Plaintext rendering (`plaintext.py`)
- Drop all edge/effect opcodes from the output.
- Translate display placeholders to bracketed markers.
- Map unknown bracket-tokens to verbatim pass-through + log to `unknown_placeholders`.
- Concatenate plain-text bytes between opcodes.
- Convert `[WAIT]` and `[HALT]` (player-facing pauses) to `[PAUSE]` per the spec.
- Strip `[LINE_BREAK]` / `[START_LINE]` / `[CLEAR_LINE]` (formatting noise).

### 3d. Menu peephole (`menus.py`)
- Post-process each node's opcode sequence + provisional edges.
- Look for the strict pattern: `LOAD_STRING "X"` × N → `PRINT_STRINGS_HORZ N` (or `_VERT`) → `CREATE_MENU` → `CLEAR_LINE` → `MULTI_GOTO L_a L_b …`.
- On match: replace the N `case_branch` edges from the MULTI_GOTO with N `menu_option` edges (label from LOAD_STRING, target from MULTI_GOTO).
- On near-miss (CREATE_MENU present, MULTI_GOTO not the direct dispatcher, count mismatch): log to `unrecognized_menus` with reason `non_multigoto` / `mismatch` / `other`.
- On `CREATE_MENU` followed by something other than `CLEAR_LINE` + `MULTI_GOTO`: log to `unrecognized_menus` reason `non_multigoto`.

**Deliverable:** node store populated for all ~6,153 labeled blocks. Spot-check a few against the current `by_npc` output for sanity.

## Phase 4 — entity construction

`extraction/entities.py` with one sub-builder per source:

### 4a. NPC builder
- Iterate `npc_config_table.yml` entries with `Type ∈ {person, object}`.
- For each: find the map_sprites entry with matching `NPC ID` (current code does this); compute pixel coords.
- Compute tile/sector from pixels (centroid = pixel for points).
- Entry points: parse `Text Pointer 1` and `Text Pointer 2` to extract `L_XXXXXX` node IDs (current code uses regex on `data_XX.l_0xc######`); primary + secondary; secondary gated by `Event Flag`.
- Properties: `sprite`, `sprite_label` (from sprite-group-labels.csv), `direction`, `movement`, `npc_type` (engine Type).
- Region label from regions-and-rooms table (current code already does this).

### 4b. Present builder
- Iterate `npc_config_table.yml` entries with `Type: item`.
- Same coord + region + entry-point logic as NPCs.
- Properties: `item` resolution via `item_configuration_table.yml` cross-reference — best-effort; if no mapping found, emit `null` and log a finding under `presents_missing_item`.
- `container` inferred from sprite ID (present box vs trash can vs coffin); table of known sprite-to-container mappings; unknown → `null` + log.

### 4c. Sign builder
- Iterate `map_doors.yml` entries with `Type ∈ {object, switch, person}`.
- Coords: tile-within-sector → pixel (`x_pixel = x_sector × 256 + X × 8`).
- Entry point: `Text Pointer` (single).
- Properties: `sprite: null`, `subtype: <engine Type>` (object/switch/person).

### 4d. Door builder
- Iterate `map_doors.yml` entries with `Type ∈ {door, ladder, rope, stairway, escalator}`.
- Coords same as signs.
- Destination: `Destination X`, `Destination Y` (pixels, likely).
- Entry point: `Text Pointer` if not `$0` (interactive door); else empty.
- `kind: "interactive"` if entry point present, else `"navigation"`.
- Properties: `kind`, `destination`, `subtype: <engine Type>`.

### 4e. Photo event builder
- Iterate `photographer_cfg_table.yml` entries.
- Coords from `Unknown A` field, parsed as `[X_lo, X_hi, Y]` (= 944, 186 for entry 1 as a sanity check). 1×1 bounding box (point).
- Entry points: empty for v1 (photo events invoke shared infrastructure via `SHOW_PHOTOGRAPHER` opcode).
- Properties: `trigger: "region"` (per spec; revisit if needed), `photo_index` = the entry's own ID.

### 4f. Validation sanity check
- Add `door_coord_units_unverified` finding listing one known door's computed pixel coords for manual eyeball.

**Deliverable:** all entities populated. Expected counts: 1,407 npc, 220 sign, 1,805 door, 177 present, 32 photo_event = 3,641 entities.

## Phase 5 — graph computation

`extraction/reachability.py`:

### 5a. Reachability
- For each entity, BFS from all entry-point node IDs.
- Edge follow rules:
  - `unconditional.target`
  - `flag_test.target` and `flag_test.fallthrough` (both)
  - `menu_option.target`
  - `case_branch.target`
  - `function_call.target`
- Visited set scoped per entity to avoid cycles.
- Result: `entity.reachable_nodes`, sorted lexicographically.

### 5b. Provenance inversion
- Walk all entities, for each node in each entity's reachable set, append the entity ID to `node.referenced_by`.
- Sort each node's `referenced_by` lexicographically.

**Deliverable:** every entity has `reachable_nodes`; every node has `referenced_by`. Provenance is the inverse of reachability — assert this as a validation check (`provenance_inverse_mismatch`).

## Phase 6 — validation + analytics

`extraction/validation.py` and `extraction/analytics.py`. Straightforward: compute the metrics the spec lists; aggregate `findings` accumulated during earlier phases (unknown_placeholders, unrecognized_menus, presents_missing_item, door_coord_units_unverified, etc.).

Validation produces the exit code; analytics is informational.

**Deliverable:** `validation.json` and `analytics.json`.

## Phase 7 — output emission

`extraction/output.py`:
- `rmtree(resources/dialogue/extracted/)` then mkdir → wipe-and-rewrite.
- `nodes.json` — full node store, dict keyed by ID, `sort_keys=True`, `indent=2`.
- `entities.json` — summary index.
- `entities/<id>.json` — one per entity.
- `validation.json`, `analytics.json`.
- **Legacy CSVs**:
  - `process-dialogue_output.csv` — hex-labeled nodes only, lowercase 6-digit hex, raw script lines preserved byte-identical to current output (use `node.raw` minus the leading label line, joined with `\r\n`).
  - `npcs.csv` — same column structure as current. Populate from `type: "npc"` entities. Columns that can't be derived from new entity schema: emit placeholder + add `npcs_csv_columns_unfilled` finding.

**Deliverable:** all outputs written. Run the script clean, exit 0.

## Cross-cutting concerns

- **Determinism.** Sort every output array deterministically (IDs lex, references lex). No `time.time()`, no insertion-order dependence on dict iteration where output matters.
- **No `DIALOGUE_BLACKLIST`.** Make sure it's grep-clean from the new code.
- **Error vs finding policy.** Errors → non-zero exit; findings → informational. Be conservative about marking things errors during v1 — let surprising-but-non-broken things start as findings, promote later.
- **Performance.** ~6,000 nodes × ~3,600 entities × reachability walks could be slow if naive. Per-entity BFS is fine; if it's slow, memoize node-out-edges. Don't pre-optimize.

## Recommended execution order

The phases as listed are buildable in order. Phase 3 is the largest and most error-prone; everything downstream depends on its correctness. Recommend:

1. Phase 0 + 1 in one pass — get the skeleton solid.
2. Phase 2 + 3 next — opcode parsing + node construction. Lots of small decisions; spot-check often.
3. Phase 4 — entity builders. Each sub-builder is independent.
4. Phase 5–7 in one pass — graph + validation + output. Mostly mechanical.
