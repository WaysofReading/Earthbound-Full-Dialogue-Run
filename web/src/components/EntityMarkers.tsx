// Imperative marker + cluster layer. 3,694 entities is too many for React-managed
// markers, so we build an L.markerClusterGroup directly and rebuild it only when
// the visible set or clustering changes — NOT on selection (that just pans).
// markercluster culls to the viewport, so tile + cluster keep pan/zoom cheap.
// Photo events also get an L.rectangle of their footprint (outside the cluster).

import { useEffect, useRef } from 'react'
import { useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet.markercluster'
import { useNavigate } from 'react-router-dom'
import type { EntityIndexRow, EntityType, Manifest } from '../lib/types'
import { entityLatLng, entityBoundsLatLng } from '../lib/coords'
import { npcSpriteUrl, typeSpriteUrl, fallbackSpriteUrl } from '../lib/paths'

export interface Filters {
  types: Record<EntityType, boolean>
  showNoDialogue: boolean
  region: string | null
}

export function isVisible(row: EntityIndexRow, place: string, f: Filters): boolean {
  if (row.place !== place) return false
  if (!f.types[row.type]) return false
  if (f.region && row.region !== f.region) return false
  // Dialogue rule: dialogue-bearing entities show by default; doors (navigation)
  // and photo events (spatial) are governed only by their type checkbox; the
  // silent npc/sign/present appear only when the no-dialogue toggle is on.
  if (row.has_dialogue || row.type === 'door' || row.type === 'photo_event') return true
  return f.showNoDialogue && row.silent
}

function iconFor(row: EntityIndexRow): L.DivIcon {
  const fb = fallbackSpriteUrl()
  let url: string
  if (row.type === 'npc') url = row.sprite != null ? npcSpriteUrl(row.sprite) : fb
  else url = typeSpriteUrl(row.type)
  const html = `<img src="${url}" onerror="this.onerror=null;this.src='${fb}'" alt="${row.type}" />`
  return L.divIcon({ html, className: 'eb-marker', iconSize: [32, 48], iconAnchor: [16, 44] })
}

export default function EntityMarkers({
  manifest,
  index,
  place,
  filters,
  clusterRadius,
  selectedId,
}: {
  manifest: Manifest
  index: EntityIndexRow[]
  place: string
  filters: Filters
  clusterRadius: number
  selectedId?: string
}) {
  const map = useMap()
  const navigate = useNavigate()
  const navRef = useRef(navigate)
  navRef.current = navigate

  // Build (and rebuild only on visible-set / clustering changes) the marker layer.
  useEffect(() => {
    const cluster = L.markerClusterGroup({
      maxClusterRadius: clusterRadius,
      showCoverageOnHover: false,
      removeOutsideVisibleBounds: true,
      // Build markers in chunks so the ~1900-marker load doesn't block the main
      // thread (which otherwise starves base-tile decoding on first paint).
      chunkedLoading: true,
      animate: false,
      iconCreateFunction: (c) =>
        L.divIcon({
          html: `<div>${c.getChildCount()}</div>`,
          className: 'eb-cluster',
          iconSize: L.point(36, 36),
        }),
    })
    const overlays: L.Layer[] = []

    for (const row of index) {
      if (!isVisible(row, place, filters)) continue
      const ll = entityLatLng(manifest, row)
      if (!ll) continue

      const marker = L.marker(ll, { icon: iconFor(row) })
      marker.bindTooltip(`${row.label || row.id} · ${row.type}`, { direction: 'top' })
      marker.on('click', () => navRef.current(`/entity/${row.id}`))
      cluster.addLayer(marker)

      if (row.type === 'photo_event') {
        const box = entityBoundsLatLng(manifest, row)
        if (box && (box[0][0] !== box[1][0] || box[0][1] !== box[1][1])) {
          overlays.push(L.rectangle(box, { color: '#3b82f6', weight: 1, fillOpacity: 0.08 }))
        }
      }
    }

    map.addLayer(cluster)
    overlays.forEach((o) => map.addLayer(o))
    return () => {
      // Guard against react-leaflet teardown races: if the map is already
      // disposed (_mapPane gone), removeLayer -> onRemove throws.
      if (!(map as unknown as { _mapPane?: unknown })._mapPane) return
      map.removeLayer(cluster)
      overlays.forEach((o) => map.removeLayer(o))
    }
  }, [map, manifest, index, place, filters, clusterRadius])

  // Pan to the selected entity without rebuilding the marker layer.
  useEffect(() => {
    if (!selectedId) return
    const sel = index.find((e) => e.id === selectedId)
    if (!sel) return
    const ll = entityLatLng(manifest, sel)
    if (!ll) return
    const z = map.getZoom()
    map.setView(ll, Number.isFinite(z) ? Math.max(z, 0) : 0)
  }, [map, manifest, index, selectedId])

  return null
}
