// Places navigation for the monolithic map. The whole game is one coordinate
// space (no subdivisions), so selecting a place recenters the single world map
// on that area rather than swapping images. "Entire map" resets to the full view.

import { useState } from 'react'
import type { Area } from '../lib/types'

export default function PlacesSidebar({
  areas,
  onJump,
  onReset,
}: {
  areas: Area[]
  onJump: (area: Area) => void
  onReset: () => void
}) {
  const [open, setOpen] = useState(true)

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
      <button
        onClick={onReset}
        className="block w-full text-left px-2 py-1 rounded text-sm hover:bg-neutral-800 text-amber-200"
      >
        Entire map
      </button>
      <div className="mt-1 border-t border-neutral-800 pt-1">
        {areas.map((a) => (
          <button
            key={a.id}
            onClick={() => onJump(a)}
            className="block w-full text-left px-2 py-1 rounded text-sm truncate hover:bg-neutral-800"
          >
            {a.label}
          </button>
        ))}
      </div>
    </div>
  )
}
