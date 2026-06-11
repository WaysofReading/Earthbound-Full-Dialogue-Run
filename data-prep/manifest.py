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
