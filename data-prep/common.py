"""
Shared foundation for the data-prep ETL: repo paths, extraction-module reuse,
and the place model that maps every region to a navigable "place" plus the
per-region translation from global game pixels into that place's image space.

The web client never recomputes geometry; it reads the translations this module
produces. See `plan_places` for the model.
"""

import os
import sys

# Make the repo root importable so `from extraction import ...` works when this
# package is run as plain scripts (`python data-prep/prep.py`).
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from extraction import sources  # noqa: E402
from extraction.entities import (  # noqa: E402
    _load_regions,
    _load_sprite_labels,
    _load_flag_labels,
    _normalize_region_name,
)

REGION_IMAGES_DIR = os.path.join(
    REPO_ROOT, 'resources', 'maps', 'regions-trimmed-flat-by-name')
SPRITE_GROUPS_DIR = os.path.join(sources.DECOMPILATION_PATH, 'SpriteGroups')
SPRITE_GROUPS_YAML = os.path.join(sources.DECOMPILATION_PATH, 'sprite_groups.yml')

# Level-0 regions whose coordinates sit in transparent gaps of the surface map
# but which are conceptually separate worlds reached by other means. They get
# their own place rather than being composited into the overworld.
DETACHED_WORLDS = {
    'Magicant',
    'Moonside',
    'Lost-Underworld',
    'Deep-Darkness',
}

OVERWORLD = 'overworld'


def slug(name):
    """Filesystem/URL-safe place id from a region filename."""
    out = []
    for ch in name.lower():
        out.append(ch if ch.isalnum() else '-')
    s = ''.join(out)
    while '--' in s:
        s = s.replace('--', '-')
    return s.strip('-')


def level0_ancestor(filename):
    """The level-0 region filename a (possibly nested) region belongs to."""
    return filename.split('_', 1)[0] if '_' in filename else filename


def place_for_region(row):
    """Place id for a region row from rooms_and_regions.csv."""
    name = row['filename']
    if row['hierarchy_level'] == 0:
        return OVERWORLD if name not in DETACHED_WORLDS else slug(name)
    return slug(level0_ancestor(name)) + '-interiors'


def _bbox(row):
    return int(row['x0']), int(row['y0']), int(row['x1']), int(row['y1'])


def _shelf_pack(rows, target_width, gap=4):
    """
    Pack scattered interior rooms into a compact canvas. Interiors live in a
    sparse scratch coordinate area (per-town spans reach ~80 MP of mostly empty
    space), so we re-pack each room's trimmed image instead of compositing at
    absolute coordinates. Returns (placements, width, height) where placements
    maps filename -> (px, py) top-left in the packed canvas.
    """
    ordered = sorted(rows, key=lambda r: (_bbox(r)[3] - _bbox(r)[1]), reverse=True)
    placements = {}
    x = y = shelf_h = 0
    max_w = 0
    for r in ordered:
        x0, y0, x1, y1 = _bbox(r)
        w, h = x1 - x0, y1 - y0
        if x > 0 and x + w > target_width:
            x = 0
            y += shelf_h + gap
            shelf_h = 0
        placements[r['filename']] = (x, y)
        x += w + gap
        shelf_h = max(shelf_h, h)
        max_w = max(max_w, x)
    return placements, max_w, y + shelf_h


def plan_places(regions=None, interior_pack_width=2048):
    """
    Compute the place model. Returns a dict:

      {
        'places': {
            place_id: {
                'label': str,
                'kind': 'overworld' | 'image',
                'members': [region_row, ...],
                'origin': (ox, oy),     # canvas (0,0) corresponds to this
                                        # global pixel (overworld/detached only)
                'size': (W, H),
                'placement': {filename: (px, py)},  # top-left in canvas
            },
        },
        'regions': {
            filename: {
                'place': place_id,
                'translate': (tx, ty),  # local = (gx + tx, gy + ty)
            },
        },
      }

    For surface/detached places a region is composited at its world position,
    so translate = canvas_topleft - world_origin. For interior places the room
    image is re-packed, so translate maps the room's world coords onto its
    packed slot.
    """
    if regions is None:
        regions = _load_regions()

    by_place = {}
    for r in regions:
        by_place.setdefault(place_for_region(r), []).append(r)

    places = {}
    region_map = {}
    for place_id, members in by_place.items():
        is_interior = place_id.endswith('-interiors')
        if is_interior:
            placement, w, h = _shelf_pack(members, interior_pack_width)
            label = level0_ancestor(members[0]['filename']) + ' (interiors)'
            places[place_id] = {
                'label': label,
                'kind': 'image',
                'members': members,
                'origin': (0, 0),
                'size': (w, h),
                'placement': placement,
            }
            for r in members:
                x0, y0, _, _ = _bbox(r)
                px, py = placement[r['filename']]
                region_map[r['filename']] = {
                    'place': place_id,
                    'translate': (px - x0, py - y0),
                }
        else:
            xs0 = min(_bbox(r)[0] for r in members)
            ys0 = min(_bbox(r)[1] for r in members)
            xs1 = max(_bbox(r)[2] for r in members)
            ys1 = max(_bbox(r)[3] for r in members)
            label = OVERWORLD.title() if place_id == OVERWORLD \
                else members[0]['filename'].replace('-', ' ')
            placement = {r['filename']: (_bbox(r)[0] - xs0, _bbox(r)[1] - ys0)
                         for r in members}
            places[place_id] = {
                'label': label,
                'kind': 'overworld' if place_id == OVERWORLD else 'image',
                'members': members,
                'origin': (xs0, ys0),
                'size': (xs1 - xs0, ys1 - ys0),
                'placement': placement,
            }
            for r in members:
                x0, y0, _, _ = _bbox(r)
                region_map[r['filename']] = {
                    'place': place_id,
                    'translate': (placement[r['filename']][0] - x0,
                                  placement[r['filename']][1] - y0),
                }

    return {'places': places, 'regions': region_map}
