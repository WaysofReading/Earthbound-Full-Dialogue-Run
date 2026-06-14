// Coordinate regression test (Definition of Done #1). Places the one verified
// photo event — Onett scam house, global pixel (944,186) — and asserts it lands
// at CRS.Simple latLng(-186,944) (Onett's world origin is (0,0)). This page is
// committed and survives as the regression guard for the coordinate transform.

import { useMemo } from 'react'
import { MapContainer, ImageOverlay, CircleMarker, Rectangle, useMap } from 'react-leaflet'
import { CRS } from 'leaflet'
import { useStore } from '../lib/store'
import { entityLatLng, entityBoundsLatLng, placeBounds } from '../lib/coords'
import { assetUrl } from '../lib/paths'

const EXPECTED: [number, number] = [-186, 944]

function FitToImage({ bounds }: { bounds: [[number, number], [number, number]] }) {
  const map = useMap()
  useMemo(() => {
    map.setView([-300, 1000], -1)
    void bounds
  }, [map, bounds])
  return null
}

export default function SmokeTest() {
  const manifest = useStore((s) => s.manifest)!
  const index = useStore((s) => s.index)

  const photo = index.find((e) => e.id === 'photo_0001')
  const overworld = manifest.places['world'] ?? manifest.places['overworld']

  if (!photo || !overworld) {
    return <div className="p-6 text-red-400">photo_0001 or world place missing.</div>
  }

  const ll = entityLatLng(manifest, photo)
  const box = entityBoundsLatLng(manifest, photo)
  const pass =
    ll != null && Math.abs(ll[0] - EXPECTED[0]) < 0.5 && Math.abs(ll[1] - EXPECTED[1]) < 0.5

  return (
    <div className="h-full flex flex-col">
      <div
        className={`px-4 py-2 font-mono text-sm ${
          pass ? 'bg-green-900 text-green-200' : 'bg-red-900 text-red-200'
        }`}
      >
        {pass ? '✓ PASS' : '✗ FAIL'} — photo_0001 @ global (944,186) → latLng{' '}
        {ll ? `(${ll[0]}, ${ll[1]})` : 'null'} · expected ({EXPECTED[0]}, {EXPECTED[1]})
      </div>
      <div className="flex-1 min-h-0">
        <MapContainer
          crs={CRS.Simple}
          minZoom={-3}
          maxZoom={2}
          className="h-full w-full"
          attributionControl={false}
        >
          <ImageOverlay
            url={assetUrl(overworld.image!)}
            bounds={placeBounds(overworld)}
          />
          {box && <Rectangle bounds={box} pathOptions={{ color: '#3b82f6', weight: 2 }} />}
          {ll && (
            <CircleMarker
              center={ll}
              radius={8}
              pathOptions={{ color: '#facc15', weight: 3, fillOpacity: 0.4 }}
            />
          )}
          <FitToImage bounds={placeBounds(overworld)} />
        </MapContainer>
      </div>
    </div>
  )
}
