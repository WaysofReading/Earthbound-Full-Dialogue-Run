"""
Render place images from the place plan: composite each place's member region
PNGs (alpha-composited at their planned offsets) into one image per place.

Regions were exported as layers from one shared canvas, so their trimmed PNGs
alpha-composite without opaque collisions. We assert that for the overworld as
a build-time guard against a mis-classified detached world leaking in.
"""

import os

from PIL import Image, ImageChops

import common

# If the composited overworld exceeds either limit we warn — a future refinement
# is a tile pyramid. v1 ships a single image per place.
_MAX_DIM_WARN = 16384
_MAX_BYTES_WARN = 30 * 1024 * 1024


def _open_region(filename):
    return Image.open(
        os.path.join(common.REGION_IMAGES_DIR, filename + '.png')).convert('RGBA')


def _composite(place, report):
    """
    Alpha-composite members onto the place canvas. Tracks an opaque-coverage
    mask and flags collisions (where a region paints opaque pixels over already
    opaque ones) — the build-time guard that no detached world leaked into the
    overworld. The check is scoped to each region's own footprint to stay cheap.
    """
    w, h = place['size']
    canvas = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    occupied = Image.new('L', (w, h), 0)
    collisions = 0
    for r in place['members']:
        img = _open_region(r['filename'])
        iw, ih = img.size
        px, py = place['placement'][r['filename']]
        canvas.alpha_composite(img, (px, py))
        opaque = img.getchannel('A').point(lambda v: 255 if v > 16 else 0)
        window = occupied.crop((px, py, px + iw, py + ih))
        if ImageChops.multiply(window, opaque).getbbox() is not None:
            collisions += 1
        occupied.paste(ImageChops.lighter(window, opaque), (px, py))
    if collisions:
        report.warn(f"place '{place['id']}': {collisions} region(s) opaque-overlap "
                    f"others (possible mis-classified detached world)")
    return canvas


def build_world(out_dir, report, regions, user_map_path=None):
    """
    Render the monolithic world map: the entire global coordinate space as one
    image, so entities render at their raw global pixel (no per-region transform).

    Prefers a user-supplied blank full map (e.g. a CoilSnake export) when present
    — that is the canonical single tilemap. Otherwise composites every region at
    its global origin as a working stand-in (parents first so nested child rooms
    paint on top; duplicate paint over identical tiles is harmless).
    """
    maps_dir = os.path.join(out_dir, 'maps')
    os.makedirs(maps_dir, exist_ok=True)
    rel = 'maps/world.png'
    dest = os.path.join(out_dir, rel)

    w, h = common.world_extent(regions)

    if user_map_path and os.path.exists(user_map_path):
        img = Image.open(user_map_path).convert('RGBA')
        img.save(dest)
        if abs(img.width - w) > 64 or abs(img.height - h) > 64:
            report.warn(f"provided world map is {img.width}x{img.height} but entity "
                        f"coordinates span {w}x{h} — placements may be offset")
        report.log(f"  world: using provided map ({img.width}x{img.height})")
        return {'image': rel, 'size': [img.width, img.height]}

    canvas = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    for r in sorted(regions, key=lambda r: int(r['hierarchy_level'])):
        img = _open_region(r['filename'])
        canvas.alpha_composite(img, (int(r['x0']), int(r['y0'])))
    canvas.save(dest, optimize=True)
    nbytes = os.path.getsize(dest)
    report.log(f"  world: composited {len(regions)} regions -> {w}x{h}, {nbytes // 1024}KB "
               f"(stand-in; drop a blank map at resources/maps/world-map.png to override)")
    return {'image': rel, 'size': [w, h]}


def build(plan, out_dir, report):
    """
    Render every place to web/public/maps/. Returns per-place render metadata
    merged into the manifest by manifest.build: {place_id: {'image'|'tiles', ...}}.
    """
    maps_dir = os.path.join(out_dir, 'maps')
    places_dir = os.path.join(maps_dir, 'places')
    os.makedirs(places_dir, exist_ok=True)

    rendered = {}
    for place_id, place in plan['places'].items():
        place['id'] = place_id
        canvas = _composite(place, report)
        w, h = place['size']

        rel = f'maps/places/{place_id}.png'
        path = os.path.join(out_dir, rel)
        canvas.save(path, optimize=True)
        nbytes = os.path.getsize(path)
        rendered[place_id] = {'image': rel}

        if place_id == common.OVERWORLD and (
                max(w, h) > _MAX_DIM_WARN or nbytes > _MAX_BYTES_WARN):
            report.warn(
                f"overworld image is {w}x{h}, {nbytes // 1024}KB — exceeds soft "
                f"limits; consider a tile pyramid")
        report.log(f"  place {place_id}: {w}x{h}, {nbytes // 1024}KB, "
                   f"{len(place['members'])} regions")

    return rendered
