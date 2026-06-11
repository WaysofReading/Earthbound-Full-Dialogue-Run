// Collapsible list of places: overworld (default), detached worlds, and per-town
// interior groups. Selecting a place swaps the map image + entity set.

import { useMemo, useState } from 'react'
import type { Manifest } from '../lib/types'

export default function PlacesSidebar({
  manifest,
  activePlace,
  onSelect,
}: {
  manifest: Manifest
  activePlace: string
  onSelect: (place: string) => void
}) {
  const [open, setOpen] = useState(true)

  const { overworld, worlds, interiors } = useMemo(() => {
    const all = Object.values(manifest.places)
    return {
      overworld: all.filter((p) => p.id === 'overworld'),
      worlds: all
        .filter((p) => p.id !== 'overworld' && !p.id.endsWith('-interiors'))
        .sort((a, b) => a.label.localeCompare(b.label)),
      interiors: all
        .filter((p) => p.id.endsWith('-interiors'))
        .sort((a, b) => a.label.localeCompare(b.label)),
    }
  }, [manifest])

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="absolute top-2 left-2 z-[1000] bg-neutral-900/90 border border-neutral-700 rounded px-2 py-1 text-xs"
      >
        ☰ Places
      </button>
    )
  }

  const Item = ({ id, label }: { id: string; label: string }) => (
    <button
      onClick={() => onSelect(id)}
      className={`block w-full text-left px-2 py-1 rounded text-sm truncate ${
        id === activePlace ? 'bg-amber-700/40 text-amber-100' : 'hover:bg-neutral-800'
      }`}
    >
      {label}
    </button>
  )

  return (
    <div className="absolute top-2 left-2 z-[1000] w-56 max-h-[calc(100%-1rem)] overflow-y-auto bg-neutral-900/95 border border-neutral-700 rounded shadow-lg p-2">
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs font-semibold text-neutral-400 uppercase tracking-wide">
          Places
        </span>
        <button onClick={() => setOpen(false)} className="text-neutral-500 hover:text-neutral-200">
          ×
        </button>
      </div>
      {overworld.map((p) => (
        <Item key={p.id} id={p.id} label={p.label} />
      ))}
      <div className="mt-2 text-[10px] font-semibold text-neutral-500 uppercase px-2">
        Detached worlds
      </div>
      {worlds.map((p) => (
        <Item key={p.id} id={p.id} label={p.label} />
      ))}
      <div className="mt-2 text-[10px] font-semibold text-neutral-500 uppercase px-2">
        Interiors
      </div>
      {interiors.map((p) => (
        <Item key={p.id} id={p.id} label={p.label} />
      ))}
    </div>
  )
}
