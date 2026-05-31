"""
Output emission: wipe-and-rewrite the extracted/ directory, then write all
JSON artifacts plus the two legacy CSVs.
"""

import csv
import json
import os
import time

from . import sources


# ───── filesystem wipe ─────────────────────────────────────────────────────

def wipe_and_prepare_output_dirs():
    """
    Google Drive sync holds freshly-written files; Python's shutil.rmtree
    races with the sync process. Windows' native `rmdir /s /q` is more
    tolerant, with exponential backoff for stragglers.
    """
    if os.path.exists(sources.EXTRACTED_DIR):
        delay = 0.5
        for attempt in range(8):
            ret = os.system(f'cmd /c rmdir /s /q "{sources.EXTRACTED_DIR}" 2>nul')
            if ret == 0 or not os.path.exists(sources.EXTRACTED_DIR):
                break
            if attempt == 7:
                raise RuntimeError(
                    f'Could not wipe {sources.EXTRACTED_DIR}; sync may be '
                    f'holding files. Manually delete and retry.')
            time.sleep(delay)
            delay = min(delay * 2, 4.0)
    os.makedirs(sources.ENTITIES_DIR, exist_ok=True)


# ───── JSON writers ────────────────────────────────────────────────────────

def _write_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, sort_keys=True)


def write_nodes(nodes):
    _write_json(sources.NODES_JSON, nodes)


def write_entity_index(index):
    _write_json(sources.ENTITIES_JSON, index)


def write_per_entity_files(entities):
    for entity_id, entity in entities.items():
        _write_json(os.path.join(sources.ENTITIES_DIR, f'{entity_id}.json'), entity)


def write_validation(validation):
    _write_json(sources.VALIDATION_JSON, validation)


def write_analytics(analytics):
    _write_json(sources.ANALYTICS_JSON, analytics)


# ───── legacy dialogue CSV ─────────────────────────────────────────────────

def write_legacy_dialogue_csv(nodes):
    """
    Hex-labeled nodes only, lowercase 6-digit hex address, raw script lines
    preserved byte-identical to the legacy CSV. The Lua text-access-monitor
    keys its lookup table by `tonumber(address, 16)` so `Npc####` would
    silently produce `nil` — those rows are filtered out.
    """
    with open(sources.LEGACY_DIALOGUE_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=',')
        writer.writerow(['address', 'dialogue'])
        for node_id in sorted(nodes.keys()):
            if not node_id.startswith('L_'):
                continue
            address = node_id[2:].lower()
            writer.writerow([address, nodes[node_id]['raw']])


# ───── legacy NPC table CSV ────────────────────────────────────────────────

_NPCS_CSV_COLUMNS = [
    'npc_id', 'sprite_label', 'map_location_label', 'npc_type', 'flag_condition',
    'sprite', 'x_tile', 'y_tile', 'x_pixel_abs', 'y_pixel_abs',
]


def _flag_condition_str(visibility):
    """
    Match the legacy format:
    - 'always'           when visibility.condition == 'always'
    - '~<label>'         when condition == 'flag_cleared'
    - '<label>'          when condition == 'flag_set'
    Missing flag labels fall back to 'Unknown Flag' (matching legacy behavior).
    """
    condition = visibility.get('condition')
    if condition == 'always':
        return 'always'
    label = visibility.get('flag_label') or 'Unknown Flag'
    if condition == 'flag_cleared':
        return '~' + label
    if condition == 'flag_set':
        return label
    return ''


def write_legacy_npcs_csv(entities, validation):
    """
    Same column structure as the legacy file. Populated from `npc`-type
    entities. Unplaced NPCs (no map_sprites entry) are not represented because
    they aren't entities; if column count differs from legacy expectations,
    that's recorded as a finding.
    """
    rows = []
    for entity_id, entity in entities.items():
        if entity.get('type') != 'npc':
            continue
        npc_id = int(entity_id.rsplit('_', 1)[-1])
        props = entity.get('properties') or {}
        loc = entity.get('location') or {}
        rows.append({
            'npc_id': npc_id,
            'sprite_label': props.get('sprite_label') or '',
            'map_location_label': entity.get('region') or '',
            'npc_type': props.get('npc_type') or '',
            'flag_condition': _flag_condition_str(entity.get('visibility') or {}),
            'sprite': props.get('sprite') if props.get('sprite') is not None else '',
            'x_tile': loc.get('x_tile') if loc.get('x_tile') is not None else '',
            'y_tile': loc.get('y_tile') if loc.get('y_tile') is not None else '',
            'x_pixel_abs': loc.get('x0') if loc.get('x0') is not None else '',
            'y_pixel_abs': loc.get('y0') if loc.get('y0') is not None else '',
        })
    rows.sort(key=lambda r: r['npc_id'])

    with open(sources.LEGACY_NPCS_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=_NPCS_CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


# ───── orchestrator ────────────────────────────────────────────────────────

def emit_all(nodes, entities, entity_index, validation, analytics):
    wipe_and_prepare_output_dirs()
    write_nodes(nodes)
    write_entity_index(entity_index)
    write_per_entity_files(entities)
    write_validation(validation)
    write_analytics(analytics)
    write_legacy_dialogue_csv(nodes)
    write_legacy_npcs_csv(entities, validation)
