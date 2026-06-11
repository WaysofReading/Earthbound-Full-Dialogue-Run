import { useEffect, useMemo, useState } from 'react'
import { MapContainer, ImageOverlay, useMap } from 'react-leaflet'
import { CRS } from 'leaflet'
import { useParams, useSearchParams } from 'react-router-dom'
import { useStore } from '../lib/store'
import { placeBounds } from '../lib/coords'
import { assetUrl } from '../lib/paths'
import type { EntityType } from '../lib/types'
import EntityMarkers, { type Filters } from '../components/EntityMarkers'
import PlacesSidebar from '../components/PlacesSidebar'
import FilterSidebar from '../components/FilterSidebar'
import DialoguePanel from '../components/DialoguePanel'
import Banner from '../components/Banner'

const DEFAULT_FILTERS: Filters = {
  // Doors (1,805 navigation markers) are off by default to keep the dialogue
  // map legible; everything else is on.
  types: { npc: true, sign: true, door: false, present: true, photo_event: true },
  showNoDialogue: false,
  region: null,
}

// Keeps the image overlay + view in sync when the active place changes.
function PlaceLayer({ placeId }: { placeId: string }) {
  const manifest = useStore((s) => s.manifest)!
  const map = useMap()
  const place = manifest.places[placeId] ?? manifest.places['overworld']
  const bounds = placeBounds(place)

  useEffect(() => {
    map.fitBounds(bounds)
    map.setMaxBounds(undefined as never)
  }, [map, placeId]) // eslint-disable-line react-hooks/exhaustive-deps

  return <ImageOverlay key={placeId} url={assetUrl(place.image!)} bounds={bounds} />
}

export default function MapView() {
  const manifest = useStore((s) => s.manifest)!
  const index = useStore((s) => s.index)
  const indexById = useStore((s) => s.indexById)
  const { id: selectedId } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()

  const [filters, setFilters] = useState<Filters>(DEFAULT_FILTERS)

  // Active place: explicit ?place=, else selected entity's place, else overworld.
  const selected = selectedId ? indexById.get(selectedId) : undefined
  const placeParam = searchParams.get('place')
  const activePlace =
    placeParam || selected?.place || 'overworld'

  // If the selected entity carries a region, scope the filter to it once.
  useEffect(() => {
    const regionParam = searchParams.get('region')
    setFilters((f) => ({ ...f, region: regionParam }))
  }, [searchParams])

  // Ensure the selected entity's type is visible even if its checkbox is off.
  const effectiveFilters = useMemo<Filters>(() => {
    if (selected && !filters.types[selected.type as EntityType]) {
      return { ...filters, types: { ...filters.types, [selected.type]: true } }
    }
    return filters
  }, [filters, selected])

  const selectPlace = (place: string) => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev)
      next.set('place', place)
      next.delete('region')
      return next
    })
  }

  return (
    <div className="absolute inset-0 flex">
      <div className="relative flex-1 min-w-0">
        <MapContainer
          crs={CRS.Simple}
          minZoom={-4}
          maxZoom={3}
          zoomSnap={0.25}
          className="h-full w-full"
          attributionControl={false}
        >
          <PlaceLayer placeId={activePlace} />
          <EntityMarkers
            manifest={manifest}
            index={index}
            place={activePlace}
            filters={effectiveFilters}
            selectedId={selectedId}
          />
        </MapContainer>

        <PlacesSidebar manifest={manifest} activePlace={activePlace} onSelect={selectPlace} />
        <FilterSidebar
          manifest={manifest}
          index={index}
          place={activePlace}
          filters={filters}
          setFilters={setFilters}
        />
        <Banner />
      </div>

      {selectedId && <DialoguePanel anchor={{ kind: 'entity', id: selectedId }} />}
    </div>
  )
}
