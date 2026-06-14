"""
data-prep ETL orchestrator.

Transforms the committed extraction outputs (resources/dialogue/extracted, region
images, sprite groups) into UI-shaped JSON, place images, marker sprites, and
search indices under web/public/. Writes ONLY into web/public/ (gitignored).

Usage:
    python data-prep/prep.py [--out web/public] [--skip-search]

Extraction is never run here; this consumes its committed, validated outputs.
"""

import argparse
import json
import os
import shutil
import sys

import common
import manifest as manifest_mod
import nodes as nodes_mod
import regions as regions_mod
import sprites as sprites_mod
import search as search_mod
from extraction import sources

# Optional user-supplied blank full-world map (e.g. a CoilSnake export). When
# present it overrides the composited stand-in for the monolithic map.
USER_WORLD_MAP = os.path.join(common.REPO_ROOT, 'resources', 'maps', 'world-map.png')


class Report:
    def __init__(self):
        self.warnings = []

    def log(self, msg):
        print(msg, flush=True)

    def warn(self, msg):
        self.warnings.append(msg)
        print(f'  ! WARN: {msg}', flush=True)


def _load_entities_full():
    """Load every per-entity record (the lean entities.json lacks entry_points,
    reachable_nodes, properties, visibility — those live per-file)."""
    out = {}
    for name in os.listdir(sources.ENTITIES_DIR):
        if name.endswith('.json'):
            with open(os.path.join(sources.ENTITIES_DIR, name), encoding='utf-8') as f:
                ent = json.load(f)
            out[ent['id']] = ent
    return out


def _on_rm_error(func, path, _exc):
    # Windows/Google-Drive can transiently lock files; clear read-only and retry.
    try:
        os.chmod(path, 0o777)
        func(path)
    except OSError:
        pass  # generated output — subsequent writes overwrite any survivors.


def _clean(out_dir):
    for sub in ('data', 'sprites', 'maps'):
        path = os.path.join(out_dir, sub)
        if os.path.isdir(path):
            shutil.rmtree(path, onexc=_on_rm_error)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Build web companion data.')
    parser.add_argument('--out', default=os.path.join(common.REPO_ROOT, 'web', 'public'))
    parser.add_argument('--skip-search', action='store_true')
    parser.add_argument('--places', action='store_true',
                        help='emit the multi-place model instead of the monolithic world map')
    args = parser.parse_args(argv)

    out_dir = os.path.abspath(args.out)
    report = Report()
    report.log(f'data-prep -> {out_dir}')
    _clean(out_dir)

    report.log('loading extraction outputs...')
    with open(sources.NODES_JSON, encoding='utf-8') as f:
        all_nodes = json.load(f)
    entities_full = _load_entities_full()
    regions = common._load_regions()
    report.log(f'  {len(all_nodes)} nodes, {len(entities_full)} entities')

    report.log('cropping sprites...')
    sprites_mod.build(out_dir, report)

    report.log('writing node bundles...')
    region_to_bundle = nodes_mod.build(all_nodes, entities_full, out_dir, report)

    if args.places:
        # Multi-place model (overworld/detached/interiors) — retained for future use.
        report.log('rendering place images...')
        plan = common.plan_places(regions)
        rendered = regions_mod.build(plan, out_dir, report)
        report.log('writing manifest + entity index...')
        manifest_mod.build(entities_full, plan, rendered, region_to_bundle, out_dir, report)
    else:
        # Monolithic world map (default): the whole coordinate space, tiled.
        report.log('rendering monolithic world map...')
        world_img = regions_mod.build_world_image(report, regions, USER_WORLD_MAP)
        world = regions_mod.build_world_tiles(world_img, out_dir, report)
        report.log('writing manifest + entity index...')
        manifest_mod.build_world(entities_full, regions, world, region_to_bundle, out_dir, report)

    if not args.skip_search:
        report.log('building search indices...')
        search_mod.build(out_dir, report)

    report.log(f'done. {len(report.warnings)} warning(s).')
    return 0


if __name__ == '__main__':
    sys.exit(main())
