import { useEffect, useMemo, useState } from 'react'
import { MapContainer, ImageOverlay, useMap } from 'react-leaflet'
import { CRS, latLngBounds } from 'leaflet'
import { useParams } from 'react-router-dom'
import { useStore } from '../lib/store'
import { placeBounds, globalBoundsToLatLng } from '../lib/coords'
import { assetUrl } from '../lib/paths'
import type { Area, EntityType } from '../lib/types'
import EntityMarkers, { type Filters } from '../components/EntityMarkers'
import PlacesSidebar from '../components/PlacesSidebar'
import FilterSidebar from '../components/FilterSidebar'
import DialoguePanel from '../components/DialoguePanel'
import Banner from '../components/Banner'

const DEFAULT_FILTERS: Filters = {
  // Doors (navigation markers) are off by default to keep the dialogue map
  // legible; everything else is on.
  types: { npc: true, sign: true, door: false, present: true, photo_event: true },
  showNoDialogue: false,
  region: null,
}

// Fits the world image on mount (unless an entity is selected — EntityMarkers
// pans to it) and recenters when a jump target is set.
function ViewController({
  worldBounds,
  jump,
  skipInitialFit,
}: {
  worldBounds: [[number, number], [number, number]]
  jump: [[number, number], [number, number]] | null
  skipInitialFit: boolean
}) {
  const map = useMap()
  useEffect(() => {
    if (!skipInitialFit) map.fitBounds(worldBounds)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [map, worldBounds])
  useEffect(() => {
    if (jump) map.flyToBounds(latLngBounds(jump), { maxZoom: 1, duration: 0.5 })
  }, [map, jump])
  return null
}

export default function MapView() {
  const manifest = useStore((s) => s.manifest)!
  const index = useStore((s) => s.index)
  const indexById = useStore((s) => s.indexById)
  const { id: selectedId } = useParams()

  const [filters, setFilters] = useState<Filters>(DEFAULT_FILTERS)
  const [jump, setJump] = useState<[[number, number], [number, number]] | null>(null)

  const world = manifest.places['world']
  const worldBounds = useMemo(() => placeBounds(world), [world])
  const selected = selectedId ? indexById.get(selectedId) : undefined

  // Ensure the selected entity's type is visible even if its checkbox is off.
  const effectiveFilters = useMemo<Filters>(() => {
    if (selected && !filters.types[selected.type as EntityType]) {
      return { ...filters, types: { ...filters.types, [selected.type]: true } }
    }
    return filters
  }, [filters, selected])

  const onJump = (area: Area) => setJump(globalBoundsToLatLng(area.bounds_global))
  const onReset = () => setJump(worldBounds)

  return (
    <div className="absolute inset-0 flex">
      <div className="relative flex-1 min-w-0">
        <MapContainer
          crs={CRS.Simple}
          minZoom={-5}
          maxZoom={3}
          zoomSnap={0.25}
          className="h-full w-full"
          attributionControl={false}
        >
          <ImageOverlay url={assetUrl(world.image!)} bounds={worldBounds} />
          <EntityMarkers
            manifest={manifest}
            index={index}
            place="world"
            filters={effectiveFilters}
            selectedId={selectedId}
          />
          <ViewController
            worldBounds={worldBounds}
            jump={jump}
            skipInitialFit={!!selectedId}
          />
        </MapContainer>

        <PlacesSidebar areas={manifest.areas ?? []} onJump={onJump} onReset={onReset} />
        <FilterSidebar
          manifest={manifest}
          index={index}
          place="world"
          filters={filters}
          setFilters={setFilters}
        />
        <Banner />
      </div>

      {selectedId && <DialoguePanel anchor={{ kind: 'entity', id: selectedId }} />}
    </div>
  )
}
