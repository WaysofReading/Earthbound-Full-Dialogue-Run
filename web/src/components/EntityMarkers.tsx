// Imperative marker + cluster layer. 3,694 entities is too many for React-managed
// markers, so we build an L.markerClusterGroup directly and rebuild it when the
// active place or filters change. Photo events also get an L.rectangle of their
// real footprint (added outside the cluster so the box is always visible).

import { useEffect } from 'react'
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
  selectedId,
}: {
  manifest: Manifest
  index: EntityIndexRow[]
  place: string
  filters: Filters
  selectedId?: string
}) {
  const map = useMap()
  const navigate = useNavigate()

  useEffect(() => {
    const cluster = L.markerClusterGroup({
      maxClusterRadius: 40,
      showCoverageOnHover: false,
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
      marker.on('click', () => navigate(`/entity/${row.id}`))
      cluster.addLayer(marker)

      if (row.type === 'photo_event') {
        const box = entityBoundsLatLng(manifest, row)
        if (box && (box[0][0] !== box[1][0] || box[0][1] !== box[1][1])) {
          overlays.push(
            L.rectangle(box, { color: '#3b82f6', weight: 1, fillOpacity: 0.08 }),
          )
        }
      }
    }

    map.addLayer(cluster)
    overlays.forEach((o) => map.addLayer(o))

    // Pan to the selected entity if it's in this place.
    if (selectedId) {
      const sel = index.find((e) => e.id === selectedId)
      if (sel) {
        const ll = entityLatLng(manifest, sel)
        if (ll) map.setView(ll, Math.max(map.getZoom(), 0))
      }
    }

    return () => {
      map.removeLayer(cluster)
      overlays.forEach((o) => map.removeLayer(o))
    }
  }, [map, manifest, index, place, filters, selectedId, navigate])

  return null
}
