"""
Marker graphics.

NPC markers: crop the front-facing (south) standing frame from each sprite-group
sheet. CoilSnake lays sprite-group frames left-to-right, top-to-bottom with the
south-facing standing pose first, so the top-left WxH cell (W/H from
sprite_groups.yml `Size`) is the front-facing frame.

Type markers (sign/door/present/photo_event) and the NPC missing-sprite fallback
are drawn programmatically from simple game-palette glyphs so the marker set is
self-contained and the fallback is visually distinct from every type icon.
"""

import os

import yaml
from PIL import Image, ImageDraw

import common


def _load_frame_sizes():
    with open(common.SPRITE_GROUPS_YAML) as f:
        groups = yaml.safe_load(f)
    sizes = {}
    for gid, info in groups.items():
        size = info.get('Size')
        if not size or 'x' not in str(size):
            continue
        w, h = str(size).split('x')
        try:
            sizes[int(gid)] = (int(w), int(h))
        except ValueError:
            pass
    return sizes


def _crop_front_frame(sprite_id, frame_sizes):
    path = os.path.join(common.SPRITE_GROUPS_DIR, f'{sprite_id:03d}.png')
    if not os.path.exists(path):
        return None
    sheet = Image.open(path).convert('RGBA')
    w, h = frame_sizes.get(sprite_id, (16, 24))
    w, h = min(w, sheet.width), min(h, sheet.height)
    return sheet.crop((0, 0, w, h))


# ───── programmatic type / fallback glyphs ───────────────────────────────────

_BG = {
    'sign': (181, 122, 51),       # wood brown
    'door': (90, 60, 120),        # doorway purple
    'present': (208, 60, 70),     # gift red
    'photo_event': (60, 130, 200),  # camera blue
    'fallback': (96, 104, 120),   # neutral slate (distinct from all types)
}


def _glyph(kind):
    """A 16x24 marker chip with a simple shape so types read at a glance."""
    img = Image.new('RGBA', (16, 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    bg = _BG[kind]
    outline = (0, 0, 0)
    d.rounded_rectangle((1, 4, 14, 22), radius=3, fill=bg, outline=outline)
    fg = (255, 255, 255)
    if kind == 'sign':
        d.rectangle((4, 8, 11, 14), fill=fg)
        d.line((7, 14, 7, 20), fill=outline, width=1)
    elif kind == 'door':
        d.rounded_rectangle((5, 7, 11, 20), radius=2, fill=fg)
        d.ellipse((9, 13, 10, 14), fill=outline)
    elif kind == 'present':
        d.rectangle((4, 11, 12, 19), fill=fg)
        d.line((8, 8, 8, 19), fill=bg, width=2)
        d.line((4, 12, 12, 12), fill=bg, width=1)
    elif kind == 'photo_event':
        d.rectangle((4, 10, 12, 18), fill=fg)
        d.ellipse((6, 12, 10, 16), fill=bg)
    else:  # fallback — a person silhouette, unmistakably "an NPC, no sprite"
        d.ellipse((6, 6, 10, 10), fill=fg)        # head
        d.rounded_rectangle((5, 11, 11, 20), radius=2, fill=fg)  # body
    return img


def build(out_dir, report):
    sprites_dir = os.path.join(out_dir, 'sprites')
    npc_dir = os.path.join(sprites_dir, 'npc')
    type_dir = os.path.join(sprites_dir, 'type')
    os.makedirs(npc_dir, exist_ok=True)
    os.makedirs(type_dir, exist_ok=True)

    frame_sizes = _load_frame_sizes()
    cropped = 0
    for sprite_id in frame_sizes:
        frame = _crop_front_frame(sprite_id, frame_sizes)
        if frame is not None:
            frame.save(os.path.join(npc_dir, f'{sprite_id}.png'))
            cropped += 1

    for kind in (*_BG.keys(),):
        name = 'fallback' if kind == 'fallback' else kind
        _glyph(kind).save(os.path.join(type_dir, f'{name}.png'))

    report.log(f"  sprites: {cropped} NPC front-frames, "
               f"{len(_BG)} type/fallback glyphs")
