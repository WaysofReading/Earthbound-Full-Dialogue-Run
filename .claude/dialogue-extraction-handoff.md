# Dialogue Extraction Rewrite: Handoff

Companion to [dialogue-extraction-spec.md](dialogue-extraction-spec.md) (the contract) and [dialogue-extraction-plan.md](dialogue-extraction-plan.md) (the buildable decomposition). This document is the after-action: what got built, where things live, and what's still open.

## Status

**Shipped.** v1 of the rewrite is committed (commits `13318bd`, `d0b7a6a`, `e345d56`). The new pipeline runs end-to-end, exits 0, produces all output artifacts the spec defines, and emits the two legacy CSVs byte-compatible with the old code for every shared row. No commits pushed to origin yet.

```
$ python process-dialogue.py
indexed: hex=5138 npc=1015 total=6153 missing_from_addresses_txt=0
parsed: opcodes=47517 distinct=207 round_trip_mismatches=0
edges: total=6449 case_branch=1142 flag_test=2454 function_call=2051 menu_option=358 unconditional=444
menus: unrecognized=86 by_reason={'non_multigoto': 14, 'other': 72}
effects: total=7965 ...
plaintext: nodes_with_text=4775/6153 total_bytes=483213 unknown_placeholders=0
entities: total=3694 {'npc': 1405, 'sign': 275, 'door': 1805, 'present': 177, 'photo_event': 32}
reachability: union=3097/6153 unreachable=3056 avg_per_entity=2.9 max_per_entity=89
provenance: inverse_mismatches=0
nodes=6153 entities=3694 edges=6449 errors=0 findings=3563
exit=0
```

## Layout

```
process-dialogue.py            # ~150-line orchestration shell
process-dialogue-legacy.py     # the old monolithic script, preserved for reference

extraction/                    # the new pipeline, one module per concern
  sources.py                   #   all input/output path constants
  script_index.py              #   raw dumper text → labels + address_to_label
  opcodes.py                   #   line → typed Opcode / Plaintext tokens
  nodes.py                     #   token list → Node (edges, effects)
  plaintext.py                 #   token list → display string
  menus.py                     #   strict LOAD_STRING→MULTI_GOTO peephole
  entities.py                  #   YAML/CSV → entities of 5 types
  reachability.py              #   per-entity BFS + provenance inversion
  validation.py                #   errors + findings per spec
  analytics.py                 #   totals, shared infra, regions, volume
  output.py                    #   wipe-and-rewrite + JSON + legacy CSVs

tools/
  visualize_entity.py          #   per-entity subgraph HTML viewer (vis-network)
  regenerate_addresses.py      #   rebuild addresses.txt from dumper output
  viz/                         #   sample visualizations (committed)

resources/dialogue/extracted/  # the canonical output
  nodes.json                   #   6,153 nodes
  entities.json                #   3,694-entry summary index
  entities/<id>.json           #   3,694 per-entity files
  validation.json
  analytics.json

resources/dialogue/process-dialogue_output.csv  # legacy, byte-identical
resources/tables/npcs.csv                       # legacy, cell-identical
resources/dialogue/addresses.txt                # rebuilt from dumper output
```

## Decisions that matter for future work

Captured here so they don't have to be re-derived from code:

- **`function_call` carries only `target`.** No `return_to` field (would be tautological — GOSUB returns to the same node). No `function_return` edge (`[END]` is statically indistinguishable from script-terminating END).
- **`MULTI_GOTO` → N `case_branch` edges. `MULTI_GOSUB` → same with `kind: "call"`.** The `kind` field on `case_branch` defaults to `"goto"`.
- **Menu peephole is strict.** Recognized pattern: `LOAD_STRING "X" × N → PRINT_STRINGS_HORZ N → CREATE_MENU → CLEAR_LINE → MULTI_GOTO`. Anything else is logged to `unrecognized_menus` and falls back to ordinary `case_branch` edges. `CHECK_EQUAL`/`GOTO_IF_TRUE` chain menus are out of scope for v1.
- **Sign entities include `Type ∈ {object, switch, person}` from `map_doors.yml`.** The 6 switches and 49 tile-anchored persons fold into `sign` with `properties.subtype` carrying the engine discriminator.
- **Photo event coordinates** are decoded from `Unknown A` as `[X_lo, X_hi, Y_byte]`. Heuristic — only `photo_0001` is verified (the Onett scam-house photo at pixel (944, 186), region "Onett", flag `GOT_PHOTO_SCAM_HOUSE`).
- **Legacy CSV scoping:** `process-dialogue_output.csv` is filtered to hex-labeled nodes only. `Npc####` rows are dropped because the Lua text-access-monitor keys by `tonumber(address, 16)` and would silently get `nil` for those.
- **Unknown placeholders are fail-open.** Unmapped opcodes in `plaintext` are dropped silently for v1 because the explicit classification covers all 207 dumper opcode names; the infrastructure to log unknowns exists if it becomes relevant.
- **`addresses.txt` is treated as a regenerable artifact** — rebuild via `tools/regenerate_addresses.py` whenever the script-dumper output changes. The previous committed copy was stale.

## Known caveats / open work

1. **Door tile-offset coordinate units are unverified.** I assumed 8 px/tile (`x_pixel = x_sector × 256 + X × 8`). A spot-check against in-game position for one known door is logged in `validation.findings.door_coord_units_unverified`. If the assumption is wrong, swap is one line.
2. **31 of 32 photo event coordinates are unverified.** All 32 are decoded and logged to `validation.findings.photo_coords_unverified` for review.
3. **Photo events have empty entry points** for v1. They invoke shared photographer infrastructure via `SHOW_PHOTOGRAPHER` opcode (`0x1F 0xD2`), which we don't model at the engine level. Their reachable_nodes is empty.
4. **2 NPCs are unplaced** (no `map_sprites` entry) — skipped because entities are defined as map-present things. 1,405 of 1,407 typed NPCs become entities. Same is true for 1 NPC missing from `npcs.csv`.
5. **Presents lack `item` and `container` resolution.** Spec defers to a cross-reference with `item_configuration_table.yml`; not implemented. All 177 present entities have `item: null`, `container: null`. `findings.presents_missing_item` is empty (we don't even try).
6. **`unreachable_nodes`: 3,056.** Genuinely unreachable per the spec — most are shop / ATM / phone / sleep infrastructure invoked by engine-level opcodes that script-level reachability doesn't trace. Expected non-empty.
7. **`entities_without_entry_points`: 267.** NPCs/signs/presents/interactive-doors without a Text Pointer (excludes the 1,500+ navigation-only doors and the 32 photo events that legitimately have no entry points). Worth a curatorial pass; unclear if all 267 are genuinely textless or if some have entry points we failed to extract.
8. **Spot-check (DoD item 4) is informal.** Three sample entities were visualized in `tools/viz/` and looked structurally correct. A formal play-through-and-compare hasn't been done.

## How to extend or modify

- **Adopting prettier symbol names** (e.g. `SHOPTEXT_Greeting` instead of `L_C50000`): re-run the dumper with `symbols/symbols_US.txt` and update `script_index.LABEL_RE` to accept arbitrary identifiers; downstream opcode-arg parsing already handles non-`L_` references via `address_to_label`. ~1 hour.
- **Resolving present items**: load `item_configuration_table.yml`, build flag → item map, populate `properties.item` and `item_label` in `entities._build_npc_or_present` for `Type: item`. Container can be inferred from sprite ID (small mapping table).
- **Filling in additional menu shapes** (Decision B4 was MULTI_GOTO-only): `extraction/menus.py` has a single `_match_menu_at` function. Extend to recognize `CHECK_EQUAL` + `GOTO_IF_TRUE` chains.

## Investigation log (interesting bugs and what they taught)

- **Inline `; $XXXXXX` address comments** appear at the end of an opcode line when the next instruction needs a label but the prior opcode didn't add a trailing `\n`. Caught when `L_C7DC85`'s plaintext was rendering as `'; $C7DC97'`. Fixed in `script_index.py` with `INLINE_ADDRESS_RE`.
- **Canonical-label resolution.** NPC text pointers in `npc_config_table.yml` reference hex addresses (e.g. `data_28.l_0xc74c07`), but the dumper labels those addresses as `Npc####` because the NPC resolution pass runs first. Initial entity entry points were `L_C74C07` (which didn't exist in the node store); fixed by passing the dumper's `address_to_label` map into entry-point extraction. Reachability went from union=511 to union=3,083 after the fix.
- **`addresses.txt` was unreliable.** Investigation in Phase 6 buckets showed 942 of 1,028 "missing" labels were in-range — the file claimed addresses the dumper doesn't actually emit. Most likely generated by a different process or a broader dumper config. Rebuilt from the dumper's actual emit.
- **Region assignment was buggy** in the initial pass — `door_0001` at outdoor coords (424, 112) was getting assigned "Deep Darkness_Tenda Village_Main" because that row in `rooms_and_regions.csv` has miscoded coordinates (claims to start at world origin). Fixed by recognizing that indoor rooms in EarthBound legitimately live at "scratch" world coords outside their level-0 namesake's outdoor footprint — so the level-0 ancestor check only applies when a level-0 region also matches the point. Reassigned 463 entities to correct regions; 87% unchanged.

## When the pipeline doesn't run cleanly

`exit=0` requires every `errors.*` array in `validation.json` to be empty. If any becomes non-empty:

- **`missing_labels_from_addresses_txt`**: `addresses.txt` is out of sync with the dumper output. Run `python tools/regenerate_addresses.py`.
- **`unresolved_edge_targets` / `unresolved_entity_entry_points`**: a node ID in the graph doesn't exist in the node store. Likely a parser bug or a stale source file. Check `address_to_label` resolution.
- **`provenance_inverse_mismatch`**: never seen non-zero; would indicate a bug in `reachability.compute_provenance`.
- **`schema_violations`**: never seen non-zero; basic shape checks. If it lights up, something is constructing malformed records.
