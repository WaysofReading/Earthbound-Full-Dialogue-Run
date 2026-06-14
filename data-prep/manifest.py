"""
World structure + entity index outputs:
- data/manifest.json: places (image/size refs), per-region place + transform,
  place_by_region, counts.
- data/entities-index.json: one lean row per entity (startup payload).
- data/entities/<id>.json: passthrough of the full per-entity records.

The per-region `translate` is the only geometry the web client needs: an entity
at global game pixel (gx, gy) in region R sits at place-image pixel
(gx + tx, gy + ty). See common.plan_places.
"""

import json
import os

import common

_DIALOGUE_TYPES = ('npc', 'sign', 'present')


def _write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, separators=(',', ':'))


def _index_row(ent, plan, region_to_bundle):
    region = ent.get('region')
    reg = plan['regions'].get(region) if region else None
    props = ent.get('properties') or {}
    has_dialogue = bool(ent.get('entry_points'))
    sprite = props.get('sprite') if ent['type'] in ('npc', 'present') else None
    loc = ent.get('location') or {}
    return {
        'id': ent['id'],
        'type': ent['type'],
        'label': ent.get('label', ''),
        'region': region,
        'place': reg['place'] if reg else None,
        'location': {k: loc.get(k) for k in ('x0', 'x1', 'y0', 'y1')},
        'has_dialogue': has_dialogue,
        'silent': ent['type'] in _DIALOGUE_TYPES and not has_dialogue,
        'visibility': ent.get('visibility')
        or {'condition': 'always', 'flag': None, 'flag_label': None},
        'sprite': sprite,
    }


def _world_index_row(ent):
    props = ent.get('properties') or {}
    has_dialogue = bool(ent.get('entry_points'))
    sprite = props.get('sprite') if ent['type'] in ('npc', 'present') else None
    loc = ent.get('location') or {}
    region = ent.get('region')
    return {
        'id': ent['id'],
        'type': ent['type'],
        'label': ent.get('label', ''),
        'region': region,
        'place': 'world' if region else None,
        'location': {k: loc.get(k) for k in ('x0', 'x1', 'y0', 'y1')},
        'has_dialogue': has_dialogue,
        'silent': ent['type'] in _DIALOGUE_TYPES and not has_dialogue,
        'visibility': ent.get('visibility')
        or {'condition': 'always', 'flag': None, 'flag_label': None},
        'sprite': sprite,
    }


def build_world(entities_full, regions, world, region_to_bundle, out_dir, report):
    """
    Monolithic manifest: one `world` place spanning the whole coordinate space.
    Every region maps to it with a zero translate (entities use raw global
    pixels). Level-0 regions become `areas` — jump targets for the Places nav,
    which now recenters the single map instead of swapping images.
    """
    data_dir = os.path.join(out_dir, 'data')

    index = []
    counts = {t: 0 for t in ('npc', 'door', 'sign', 'present', 'photo_event')}
    no_dialogue = 0
    ent_out = os.path.join(data_dir, 'entities')
    os.makedirs(ent_out, exist_ok=True)
    for ent in entities_full.values():
        row = _world_index_row(ent)
        index.append(row)
        counts[ent['type']] = counts.get(ent['type'], 0) + 1
        if row['silent']:
            no_dialogue += 1
        _write_json(os.path.join(ent_out, f"{ent['id']}.json"), ent)
    _write_json(os.path.join(data_dir, 'entities-index.json'), index)

    region_map = {}
    for r in regions:
        fname = r['filename']
        entry = {'place': 'world', 'translate': [0, 0]}
        if fname in region_to_bundle:
            entry['bundle'] = region_to_bundle[fname]
        region_map[fname] = entry

    areas = []
    for r in regions:
        if int(r['hierarchy_level']) == 0:
            areas.append({
                'id': common.slug(r['filename']),
                'label': r['filename'].replace('-', ' '),
                'bounds_global': [int(r['x0']), int(r['y0']), int(r['x1']), int(r['y1'])],
            })
    areas.sort(key=lambda a: a['label'])

    world_place = {
        'id': 'world',
        'label': 'EarthBound',
        'kind': 'world',
        'size': world['size'],
    }
    if 'tiles' in world:
        world_place['tiles'] = world['tiles']
    if 'image' in world:
        world_place['image'] = world['image']

    manifest = {
        'places': {'world': world_place},
        'regions': region_map,
        'place_by_region': {fname: 'world' for fname in region_map},
        'areas': areas,
        'counts': {**counts, 'no_dialogue': no_dialogue, 'total': len(entities_full)},
    }
    _write_json(os.path.join(data_dir, 'manifest.json'), manifest)
    report.log(f"  manifest: monolithic world {world['size'][0]}x{world['size'][1]}, "
               f"{len(index)} entities, {no_dialogue} silent, {len(areas)} areas")
    return manifest


def build(entities_full, plan, rendered, region_to_bundle, out_dir, report):
    data_dir = os.path.join(out_dir, 'data')

    # ── entities index + passthrough ────────────────────────────────────────
    index = []
    counts = {t: 0 for t in ('npc', 'door', 'sign', 'present', 'photo_event')}
    no_dialogue = 0
    placeless = 0
    ent_out = os.path.join(data_dir, 'entities')
    os.makedirs(ent_out, exist_ok=True)
    for ent in entities_full.values():
        row = _index_row(ent, plan, region_to_bundle)
        index.append(row)
        counts[ent['type']] = counts.get(ent['type'], 0) + 1
        if row['silent']:
            no_dialogue += 1
        if row['place'] is None:
            placeless += 1
        _write_json(os.path.join(ent_out, f"{ent['id']}.json"), ent)
    _write_json(os.path.join(data_dir, 'entities-index.json'), index)

    # ── manifest ────────────────────────────────────────────────────────────
    places = {}
    for pid, place in plan['places'].items():
        entry = {
            'id': pid,
            'label': place['label'],
            'kind': place['kind'],
            'size': list(place['size']),
        }
        entry.update(rendered.get(pid, {}))   # 'image' (or 'tiles' later)
        places[pid] = entry

    regions = {}
    place_by_region = {}
    for fname, info in plan['regions'].items():
        tx, ty = info['translate']
        regions[fname] = {'place': info['place'], 'translate': [tx, ty]}
        if fname in region_to_bundle:
            regions[fname]['bundle'] = region_to_bundle[fname]
        place_by_region[fname] = info['place']

    manifest = {
        'places': places,
        'regions': regions,
        'place_by_region': place_by_region,
        'counts': {**counts, 'no_dialogue': no_dialogue,
                   'total': len(entities_full)},
    }
    _write_json(os.path.join(data_dir, 'manifest.json'), manifest)

    report.log(f"  manifest: {len(places)} places, {len(index)} entities, "
               f"{no_dialogue} silent, {placeless} placeless")
    return manifest
