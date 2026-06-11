// The only geometry the client computes. Everything is driven by the manifest's
// per-region `translate`: an entity at global game pixel (gx,gy) in region R sits
// at place-image pixel (gx+tx, gy+ty). CRS.Simple LatLng is (lat=-y, lng=x) — the
// Y is flipped because image space grows downward while Leaflet latitude grows up.

import type { Manifest, EntityIndexRow, PlaceManifest } from './types'

export type LatLng = [number, number] // [lat, lng]

export function localPixel(
  manifest: Manifest,
  region: string | null,
  gx: number,
  gy: number,
): [number, number] | null {
  if (!region) return null
  const reg = manifest.regions[region]
  if (!reg) return null
  return [gx + reg.translate[0], gy + reg.translate[1]]
}

export function toLatLng(
  manifest: Manifest,
  region: string | null,
  gx: number,
  gy: number,
): LatLng | null {
  const local = localPixel(manifest, region, gx, gy)
  if (!local) return null
  return [-local[1], local[0]]
}

export function entityCenter(row: EntityIndexRow): [number, number] {
  return [(row.location.x0 + row.location.x1) / 2, (row.location.y0 + row.location.y1) / 2]
}

export function entityLatLng(manifest: Manifest, row: EntityIndexRow): LatLng | null {
  const [gx, gy] = entityCenter(row)
  return toLatLng(manifest, row.region, gx, gy)
}

// Bounding box (in CRS.Simple coords) of an entity's real footprint — used for
// photo-event rectangles. Returns [[lat,lng],[lat,lng]] (SW, NE).
export function entityBoundsLatLng(
  manifest: Manifest,
  row: EntityIndexRow,
): [LatLng, LatLng] | null {
  const a = toLatLng(manifest, row.region, row.location.x0, row.location.y0)
  const b = toLatLng(manifest, row.region, row.location.x1, row.location.y1)
  if (!a || !b) return null
  return [
    [Math.min(a[0], b[0]), Math.min(a[1], b[1])],
    [Math.max(a[0], b[0]), Math.max(a[1], b[1])],
  ]
}

// Image overlay / map bounds for a place: image spans lng 0..W, lat -H..0.
export function placeBounds(place: PlaceManifest): [LatLng, LatLng] {
  const [w, h] = place.size
  return [
    [-h, 0],
    [0, w],
  ]
}
