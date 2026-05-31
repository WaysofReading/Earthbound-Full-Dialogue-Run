"""
Entity construction: produce npc / sign / door / present / photo_event records
from the decompilation YAMLs and label tables.
"""

import csv
import re

import yaml

from . import sources


_POINTER_RE = re.compile(r'0x([0-9a-fA-F]{6})')

_TILE_SIZE = 32      # 8x8 px native, but the legacy code uses 32 (4-tile chunks)
_SECTOR_SIZE = 256
_DOOR_TILE_PX = 8    # map_doors X/Y are in 8-px tile units within the sector


# ───── source loaders ──────────────────────────────────────────────────────

def _load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)


def _load_sprite_labels():
    out = {}
    with open(sources.SPRITE_GROUP_LABELS_CSV, encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if len(row) >= 2:
                try:
                    out[int(row[0])] = row[1]
                except ValueError:
                    pass
    return out


def _load_flag_labels():
    out = {}
    with open(sources.FLAGS_CSV, encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if len(row) >= 2:
                try:
                    out[int(row[0])] = row[1]
                except ValueError:
                    pass
    return out


def _load_regions():
    rows = []
    with open(sources.ROOMS_AND_REGIONS_CSV, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            casted = {}
            for k, v in row.items():
                try:
                    casted[k] = int(v)
                except (ValueError, TypeError):
                    casted[k] = v
            rows.append(casted)
    return rows


# ───── helpers ──────────────────────────────────────────────────────────────

def _extract_node_id(pointer, address_to_label=None):
    """
    Parse a YAML pointer like `data_28.l_0xc74c07` to the canonical label the
    script-dumper assigned at that address. NPC text pointers usually resolve
    to `NpcNNNN`; other refs to `L_XXXXXX`. Falls back to the synthesized
    `L_XXXXXX` form if no map is provided or the address is unknown.
    """
    if not pointer or pointer == '$0':
        return None
    m = _POINTER_RE.search(str(pointer))
    if not m:
        return None
    address = m.group(1).upper()
    if address_to_label is not None:
        canonical = address_to_label.get(address)
        if canonical is not None:
            return canonical
    return f'L_{address}'


def _assign_region(x, y, regions):
    for r in regions:
        if r['x0'] <= x <= r['x1'] and r['y0'] <= y <= r['y1']:
            return r.get('filename')
    return None


def _point_location(x_px, y_px, x_sector, y_sector):
    return {
        'x0': x_px, 'y0': y_px,
        'x1': x_px, 'y1': y_px,
        'x_tile': x_px // _TILE_SIZE,
        'y_tile': y_px // _TILE_SIZE,
        'x_sector': x_sector,
        'y_sector': y_sector,
    }


def _visibility(show_field, flag_id, flag_labels):
    if show_field == 'always' or not flag_id:
        return {'condition': 'always', 'flag': None, 'flag_label': None}
    label = flag_labels.get(flag_id)
    if show_field == 'when event flag set':
        return {'condition': 'flag_set', 'flag': flag_id, 'flag_label': label}
    return {'condition': 'flag_cleared', 'flag': flag_id, 'flag_label': label}


def _index_map_sprites(map_sprites):
    """Index map_sprites by NPC ID, augmenting each sprite with its sector coords."""
    out = {}
    for y_sector, x_sectors in (map_sprites or {}).items():
        if not x_sectors:
            continue
        for x_sector, sprites in x_sectors.items():
            if not sprites:
                continue
            for sprite in sprites:
                npc_id = sprite.get('NPC ID')
                if npc_id is None:
                    continue
                out[npc_id] = {**sprite, 'x_sector': x_sector, 'y_sector': y_sector}
    return out


# ───── 4a/4b — NPC and present builders ────────────────────────────────────

def _build_npc_or_present(npc_id, npc, map_sprite, sprite_labels, flag_labels,
                          regions, address_to_label):
    is_present = (npc.get('Type') == 'item')

    if map_sprite is None:
        return None  # unplaced — not a map entity

    x_sector = map_sprite['x_sector']
    y_sector = map_sprite['y_sector']
    x_px = x_sector * _SECTOR_SIZE + map_sprite['X']
    y_px = y_sector * _SECTOR_SIZE + map_sprite['Y']
    location = _point_location(x_px, y_px, x_sector, y_sector)

    flag_id = npc.get('Event Flag') or 0
    visibility = _visibility(npc.get('Show Sprite', 'always'), flag_id, flag_labels)

    p1 = _extract_node_id(npc.get('Text Pointer 1'), address_to_label)
    p2 = _extract_node_id(npc.get('Text Pointer 2'), address_to_label)
    entry_points = []
    if p1:
        entry_points.append({'role': 'primary', 'node_id': p1})
    if p2:
        ep = {'role': 'secondary', 'node_id': p2}
        if flag_id:
            ep['gated_by_flag'] = flag_id
            ep['gated_by_flag_label'] = flag_labels.get(flag_id)
        entry_points.append(ep)

    sprite_id = npc.get('Sprite')
    sprite_label = sprite_labels.get(sprite_id, '')

    if is_present:
        properties = {
            'item': None,
            'item_label': None,
            'container': None,
            'sprite': sprite_id,
            'sprite_label': sprite_label,
        }
        entity_type = 'present'
    else:
        properties = {
            'sprite': sprite_id,
            'sprite_label': sprite_label,
            'direction': npc.get('Direction'),
            'movement': npc.get('Movement'),
            'npc_type': npc.get('Type'),
        }
        entity_type = 'npc'

    return {
        'id': f'{entity_type}_{npc_id:04d}',
        'type': entity_type,
        'label': sprite_label,
        'region': _assign_region(x_px, y_px, regions),
        'location': location,
        'visibility': visibility,
        'entry_points': entry_points,
        'reachable_nodes': [],
        'properties': properties,
    }


def build_npcs_and_presents(npc_table, map_sprites, sprite_labels, flag_labels,
                            regions, address_to_label):
    sprite_index = _index_map_sprites(map_sprites)
    npcs, presents = {}, {}
    for npc_id, npc in (npc_table or {}).items():
        if npc_id == 0:
            continue
        npc_type = npc.get('Type')
        if npc_type not in ('person', 'object', 'item'):
            continue
        entity = _build_npc_or_present(npc_id, npc, sprite_index.get(npc_id),
                                       sprite_labels, flag_labels, regions,
                                       address_to_label)
        if entity is None:
            continue
        if entity['type'] == 'present':
            presents[entity['id']] = entity
        else:
            npcs[entity['id']] = entity
    return npcs, presents


# ───── 4c/4d — sign and door builders ──────────────────────────────────────

_SIGN_TYPES = {'object', 'switch', 'person'}
_DOOR_TYPES = {'door', 'ladder', 'rope', 'stairway', 'escalator'}


def _door_or_sign_location(x_sector, y_sector, tile_x, tile_y):
    x_px = x_sector * _SECTOR_SIZE + tile_x * _DOOR_TILE_PX
    y_px = y_sector * _SECTOR_SIZE + tile_y * _DOOR_TILE_PX
    return _point_location(x_px, y_px, x_sector, y_sector), x_px, y_px


def _build_sign(seq, record, x_sector, y_sector, flag_labels, regions, address_to_label):
    location, x_px, y_px = _door_or_sign_location(x_sector, y_sector,
                                                  record['X'], record['Y'])
    text_pointer = _extract_node_id(record.get('Text Pointer'), address_to_label)
    entry_points = [{'role': 'primary', 'node_id': text_pointer}] if text_pointer else []
    flag_id = record.get('Event Flag') or 0
    return {
        'id': f'sign_{seq:04d}',
        'type': 'sign',
        'label': '',
        'region': _assign_region(x_px, y_px, regions),
        'location': location,
        'visibility': _visibility('always', 0, flag_labels),
        'entry_points': entry_points,
        'reachable_nodes': [],
        'properties': {
            'sprite': None,
            'subtype': record.get('Type'),
            'gating_flag': flag_id or None,
            'gating_flag_label': flag_labels.get(flag_id) if flag_id else None,
        },
    }


def _build_door(seq, record, x_sector, y_sector, flag_labels, regions, address_to_label):
    location, x_px, y_px = _door_or_sign_location(x_sector, y_sector,
                                                  record['X'], record['Y'])
    text_pointer = _extract_node_id(record.get('Text Pointer'), address_to_label)
    entry_points = [{'role': 'primary', 'node_id': text_pointer}] if text_pointer else []
    kind = 'interactive' if entry_points else 'navigation'

    dest_x = record.get('Destination X')
    dest_y = record.get('Destination Y')
    if dest_x is not None and dest_y is not None:
        destination = {
            'region': _assign_region(dest_x, dest_y, regions),
            'x': dest_x,
            'y': dest_y,
        }
    else:
        destination = None

    flag_id = record.get('Event Flag') or 0
    return {
        'id': f'door_{seq:04d}',
        'type': 'door',
        'label': '',
        'region': _assign_region(x_px, y_px, regions),
        'location': location,
        'visibility': _visibility('always', 0, flag_labels),
        'entry_points': entry_points,
        'reachable_nodes': [],
        'properties': {
            'kind': kind,
            'destination': destination,
            'subtype': record.get('Type'),
            'direction': record.get('Direction'),
            'style': record.get('Style'),
            'gating_flag': flag_id or None,
            'gating_flag_label': flag_labels.get(flag_id) if flag_id else None,
        },
    }


def build_signs_and_doors(map_doors, flag_labels, regions, findings, address_to_label):
    signs, doors = {}, {}
    sign_seq, door_seq = 0, 0
    sample_door_recorded = False
    for y_sector, x_sectors in (map_doors or {}).items():
        if not x_sectors:
            continue
        for x_sector, records in x_sectors.items():
            if not records:
                continue
            for record in records:
                rtype = record.get('Type')
                if rtype in _SIGN_TYPES:
                    sign_seq += 1
                    sign = _build_sign(sign_seq, record, x_sector, y_sector,
                                       flag_labels, regions, address_to_label)
                    signs[sign['id']] = sign
                elif rtype in _DOOR_TYPES:
                    door_seq += 1
                    door = _build_door(door_seq, record, x_sector, y_sector,
                                       flag_labels, regions, address_to_label)
                    doors[door['id']] = door
                    if not sample_door_recorded and door['region']:
                        findings.append({
                            'door_id': door['id'],
                            'region': door['region'],
                            'x_pixel': door['location']['x0'],
                            'y_pixel': door['location']['y0'],
                            'note': 'first door with assigned region — '
                                    'verify pixel coords against in-game location to '
                                    'confirm tile-offset (×8) assumption',
                        })
                        sample_door_recorded = True
    return signs, doors


# ───── 4e — photo event builder ────────────────────────────────────────────

def build_photo_events(photographer_table, flag_labels, regions, findings):
    photos = {}
    for entry_id, record in (photographer_table or {}).items():
        unknown_a = record.get('Unknown A') or []
        if len(unknown_a) >= 3:
            x_px = unknown_a[0] + unknown_a[1] * _SECTOR_SIZE
            y_px = unknown_a[2]
        else:
            x_px = y_px = 0
        x_sector = x_px // _SECTOR_SIZE
        y_sector = y_px // _SECTOR_SIZE
        location = _point_location(x_px, y_px, x_sector, y_sector)
        flag_id = record.get('Event Flag') or 0

        photo = {
            'id': f'photo_{entry_id:04d}',
            'type': 'photo_event',
            'label': '',
            'region': _assign_region(x_px, y_px, regions),
            'location': location,
            'visibility': _visibility('always', 0, flag_labels),
            'entry_points': [],
            'reachable_nodes': [],
            'properties': {
                'trigger': 'region',
                'photo_index': entry_id,
                'gating_flag': flag_id or None,
                'gating_flag_label': flag_labels.get(flag_id) if flag_id else None,
            },
        }
        photos[photo['id']] = photo
        findings.append({
            'photo_id': photo['id'],
            'x_pixel': x_px,
            'y_pixel': y_px,
            'region': photo['region'],
            'unknown_a': list(unknown_a),
            'unknown_b': record.get('Unknown B'),
            'unknown_c': record.get('Unknown C'),
            'note': 'Unknown A decoded as [X_lo, X_hi, Y_byte] — verify against '
                    'in-game photo trigger location',
        })
    return photos


# ───── orchestrator ────────────────────────────────────────────────────────

def build_entities(address_to_label):
    """Load all entity sources and build the full entity dict."""
    npc_table = _load_yaml(sources.NPC_CONFIG_TABLE)
    map_sprites = _load_yaml(sources.MAP_SPRITES)
    map_doors = _load_yaml(sources.MAP_DOORS)
    photographer_table = _load_yaml(sources.PHOTOGRAPHER_CFG_TABLE)
    sprite_labels = _load_sprite_labels()
    flag_labels = _load_flag_labels()
    regions = _load_regions()

    findings = {
        'door_coord_units_unverified': [],
        'presents_missing_item': [],
        'photo_coords_unverified': [],
    }

    entities = {}
    npcs, presents = build_npcs_and_presents(npc_table, map_sprites,
                                             sprite_labels, flag_labels, regions,
                                             address_to_label)
    signs, doors = build_signs_and_doors(map_doors, flag_labels, regions,
                                         findings['door_coord_units_unverified'],
                                         address_to_label)
    photos = build_photo_events(photographer_table, flag_labels, regions,
                                findings['photo_coords_unverified'])
    entities.update(npcs)
    entities.update(presents)
    entities.update(signs)
    entities.update(doors)
    entities.update(photos)

    counts = {
        'npc': len(npcs),
        'sign': len(signs),
        'door': len(doors),
        'present': len(presents),
        'photo_event': len(photos),
    }

    return entities, counts, findings


def build_entity_index(entities):
    """Summary index (id/type/label/region/location) for entities.json."""
    return {
        eid: {
            'id': e['id'],
            'type': e['type'],
            'label': e['label'],
            'region': e['region'],
            'location': e['location'],
        }
        for eid, e in entities.items()
    }
