#!/usr/bin/env python
"""
Report on entities without entry points (= no dialogue extracted) so each
can be triaged: legitimate game-design choice (e.g. a decorative sign), or
an extraction gap (e.g. a Text Pointer we failed to parse).

Excludes the always-empty categories (navigation-only doors, photo events).

Output: tools/entities_without_dialogue.csv with one row per entity, plus
a per-type and per-region summary to stdout.
"""

import csv
import json
import os
import sys
from collections import Counter

CD = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
ENTITIES_DIR = os.path.join(CD, 'resources', 'dialogue', 'extracted', 'entities')
VALIDATION_JSON = os.path.join(CD, 'resources', 'dialogue', 'extracted', 'validation.json')
OUT_CSV = os.path.join(CD, 'tools', 'entities_without_dialogue.csv')


def _load_entity(eid):
    with open(os.path.join(ENTITIES_DIR, f'{eid}.json'), encoding='utf-8') as f:
        return json.load(f)


def _subtype(ent):
    props = ent.get('properties') or {}
    return (props.get('npc_type') or props.get('subtype')
            or ('present' if ent['type'] == 'present' else ''))


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    with open(VALIDATION_JSON, encoding='utf-8') as f:
        validation = json.load(f)
    listing = validation['findings']['entities_without_entry_points']

    fieldnames = [
        'entity_id', 'type', 'subtype', 'label', 'region',
        'x_pixel', 'y_pixel', 'visibility_condition', 'visibility_flag_label',
        'gating_flag_label', 'direction', 'movement', 'door_kind',
    ]

    rows = []
    for finding in listing:
        ent = _load_entity(finding['entity'])
        props = ent.get('properties') or {}
        loc = ent.get('location') or {}
        vis = ent.get('visibility') or {}
        rows.append({
            'entity_id': ent['id'],
            'type': ent['type'],
            'subtype': _subtype(ent),
            'label': ent.get('label', ''),
            'region': ent.get('region') or '',
            'x_pixel': loc.get('x0', ''),
            'y_pixel': loc.get('y0', ''),
            'visibility_condition': vis.get('condition', ''),
            'visibility_flag_label': vis.get('flag_label') or '',
            'gating_flag_label': props.get('gating_flag_label') or '',
            'direction': props.get('direction') or '',
            'movement': props.get('movement') or '',
            'door_kind': props.get('kind') or '',
        })

    rows.sort(key=lambda r: (r['region'] or '~', r['type'], r['entity_id']))

    with open(OUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f'{len(rows)} entities without dialogue')
    print(f'wrote {OUT_CSV}')
    print()

    by_type = Counter(r['type'] for r in rows)
    print('by type:')
    for t, n in by_type.most_common():
        sub = Counter(r['subtype'] for r in rows if r['type'] == t)
        print(f'  {t}: {n}  ({dict(sub)})')

    print()
    print('top regions:')
    regions = Counter(r['region'] for r in rows)
    for region, n in regions.most_common(15):
        print(f'  {region or "(unassigned)"}: {n}')


if __name__ == '__main__':
    main()
