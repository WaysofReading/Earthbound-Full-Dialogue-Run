"""
Render place images from the place plan: composite each place's member region
PNGs (alpha-composited at their planned offsets) into one image per place.

Regions were exported as layers from one shared canvas, so their trimmed PNGs
alpha-composite without opaque collisions. We assert that for the overworld as
a build-time guard against a mis-classified detached world leaking in.
"""

import math
import os

from PIL import Image, ImageChops

import common

# If a single composited place image exceeds either limit we warn.
_MAX_DIM_WARN = 16384
_MAX_BYTES_WARN = 30 * 1024 * 1024

TILE = 256
WORLD_MIN_ZOOM = -5   # whole map fits in ~1 tile at this zoom
WORLD_MAX_ZOOM = 3    # upscales native tiles for close-in sprite inspection


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


def build_world_image(report, regions, user_map_path=None):
    """
    Produce the monolithic world image (in memory): the entire global coordinate
    space, so entities render at their raw global pixel (no per-region transform).

    Prefers a user-supplied blank full map (e.g. a CoilSnake export). Otherwise
    composites every region at its global origin as a working stand-in (parents
    first so nested child rooms paint on top; duplicate paint is harmless).
    """
    w, h = common.world_extent(regions)

    if user_map_path and os.path.exists(user_map_path):
        img = Image.open(user_map_path).convert('RGBA')
        if abs(img.width - w) > 64 or abs(img.height - h) > 64:
            report.warn(f"provided world map is {img.width}x{img.height} but entity "
                        f"coordinates span {w}x{h} — placements may be offset")
        report.log(f"  world: using provided map ({img.width}x{img.height})")
        return img

    canvas = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    for r in sorted(regions, key=lambda r: int(r['hierarchy_level'])):
        canvas.alpha_composite(_open_region(r['filename']), (int(r['x0']), int(r['y0'])))
    report.log(f"  world: composited {len(regions)} regions -> {w}x{h} "
               f"(stand-in; drop a blank map at resources/maps/world-map.png to override)")
    return canvas


def build_world_tiles(world_img, out_dir, report):
    """
    Slice the world image into a CRS.Simple tile pyramid so the client renders
    only the tiles in view at the current zoom (huge pan/zoom win over one giant
    imageOverlay). Native resolution is zoom 0 (1 game px = 1 map unit, matching
    the client's latLng(-y, x) convention); negative zooms are downscaled mips.

    CRS.Simple's transformation is (1,0,-1,0) — it flips Y — so a marker at
    latLng(-gy, gx) projects to (gx*2^z, gy*2^z), both positive. A tile therefore
    indexes as standard top-left XYZ: image cell (column c, row r) -> tile
    (x=c, y=r). Transparent tiles are skipped.
    """
    base = os.path.join(out_dir, 'maps', 'world')
    w, h = world_img.size
    count = 0
    for z in range(0, WORLD_MIN_ZOOM - 1, -1):
        scale = 2.0 ** z
        sw, sh = max(1, round(w * scale)), max(1, round(h * scale))
        scaled = world_img if z == 0 else world_img.resize((sw, sh), Image.LANCZOS)
        cols, rows = math.ceil(sw / TILE), math.ceil(sh / TILE)
        for r in range(rows):
            for c in range(cols):
                crop = scaled.crop((c * TILE, r * TILE,
                                    min((c + 1) * TILE, sw), min((r + 1) * TILE, sh)))
                if crop.getchannel('A').getbbox() is None:
                    continue  # fully transparent — don't emit
                tile = Image.new('RGBA', (TILE, TILE), (0, 0, 0, 0))
                tile.paste(crop, (0, 0))
                d = os.path.join(base, str(z), str(c))
                os.makedirs(d, exist_ok=True)
                tile.save(os.path.join(d, f'{r}.png'))
                count += 1
    report.log(f"  world tiles: {count} tiles, zoom 0..{WORLD_MIN_ZOOM}")
    return {
        'tiles': {
            'url': 'maps/world/{z}/{x}/{y}.png',
            'tileSize': TILE,
            'minZoom': WORLD_MIN_ZOOM,
            'maxZoom': WORLD_MAX_ZOOM,
            'maxNativeZoom': 0,
        },
        'size': [w, h],
    }


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
