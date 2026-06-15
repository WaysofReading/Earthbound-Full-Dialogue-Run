"""
Node store outputs:
- data/nodes/all.json: the full node store (archive + search), lazy-loaded.
- data/nodes/by-region/<slug>.json: nodes reachable from entities in a region,
  loaded when the map selects an entity there. Returns the region->bundle-slug
  map so the manifest can point the client at the right bundle (no slug drift).
"""

import json
import os

import common


def _write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, separators=(',', ':'))


def build(nodes, entities_full, out_dir, report):
    data_dir = os.path.join(out_dir, 'data')
    _write_json(os.path.join(data_dir, 'nodes', 'all.json'), nodes)

    # Group entities by region; union their reachable nodes into one bundle.
    by_region = {}
    for ent in entities_full.values():
        region = ent.get('region')
        if region and ent.get('reachable_nodes'):
            by_region.setdefault(region, set()).update(ent['reachable_nodes'])

    region_to_bundle = {}
    for region, node_ids in by_region.items():
        bundle = common.slug(region)
        region_to_bundle[region] = bundle
        subset = {nid: nodes[nid] for nid in node_ids if nid in nodes}
        _write_json(os.path.join(data_dir, 'nodes', 'by-region', f'{bundle}.json'),
                    subset)

    report.log(f"  nodes: {len(nodes)} total, "
               f"{len(region_to_bundle)} region bundles")
    return region_to_bundle
