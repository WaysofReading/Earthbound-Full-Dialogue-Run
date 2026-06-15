// Filter panel, hidden by default and toggled from a map control. Type
// checkboxes, region selector (within the active place), and the no-dialogue
// toggle (default off; count is the audited 267 silent entities).

import { useMemo, useState } from 'react'
import type { EntityIndexRow, EntityType, Manifest } from '../lib/types'
import type { Filters } from './EntityMarkers'

const TYPES: EntityType[] = ['npc', 'sign', 'door', 'present', 'photo_event']

// Clustering presets. "Off" keeps a tiny radius so markercluster still culls to
// the viewport (the perf win) while only merging exact pixel overlaps.
export const CLUSTER_PRESETS: { label: string; radius: number }[] = [
  { label: 'Off', radius: 1 },
  { label: 'Tight', radius: 20 },
  { label: 'Default', radius: 40 },
  { label: 'Loose', radius: 80 },
]

export default function FilterSidebar({
  manifest,
  index,
  place,
  filters,
  setFilters,
  clusterRadius,
  setClusterRadius,
}: {
  manifest: Manifest
  index: EntityIndexRow[]
  place: string
  filters: Filters
  setFilters: (f: Filters) => void
  clusterRadius: number
  setClusterRadius: (r: number) => void
}) {
  const [open, setOpen] = useState(false)

  const regions = useMemo(() => {
    const set = new Set<string>()
    for (const e of index) if (e.place === place && e.region) set.add(e.region)
    return [...set].sort()
  }, [index, place])

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="absolute top-2 right-2 z-[1000] bg-neutral-900/90 border border-neutral-700 rounded px-2 py-1 text-xs"
      >
        ⚙ Filters
      </button>
    )
  }

  const toggleType = (t: EntityType) =>
    setFilters({ ...filters, types: { ...filters.types, [t]: !filters.types[t] } })

  return (
    <div className="absolute top-2 right-2 z-[1000] w-60 bg-neutral-900/95 border border-neutral-700 rounded shadow-lg p-3">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-neutral-400 uppercase tracking-wide">
          Filters
        </span>
        <button onClick={() => setOpen(false)} className="text-neutral-500 hover:text-neutral-200">
          ×
        </button>
      </div>

      <div className="space-y-1 mb-3">
        {TYPES.map((t) => (
          <label key={t} className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={filters.types[t]}
              onChange={() => toggleType(t)}
            />
            <span className="capitalize">{t.replace('_', ' ')}</span>
          </label>
        ))}
      </div>

      <label className="block text-xs text-neutral-400 mb-1">Region</label>
      <select
        value={filters.region ?? ''}
        onChange={(e) => setFilters({ ...filters, region: e.target.value || null })}
        className="w-full bg-neutral-800 border border-neutral-700 rounded px-2 py-1 text-sm mb-3"
      >
        <option value="">All regions</option>
        {regions.map((r) => (
          <option key={r} value={r}>
            {r}
          </option>
        ))}
      </select>

      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={filters.showNoDialogue}
          onChange={() => setFilters({ ...filters, showNoDialogue: !filters.showNoDialogue })}
        />
        <span>Show entities with no dialogue ({manifest.counts.no_dialogue})</span>
      </label>

      <label className="block text-xs text-neutral-400 mt-3 mb-1">Clustering</label>
      <div className="flex gap-1">
        {CLUSTER_PRESETS.map((p) => (
          <button
            key={p.label}
            onClick={() => setClusterRadius(p.radius)}
            className={`flex-1 px-1.5 py-1 rounded text-xs ${
              clusterRadius === p.radius
                ? 'bg-amber-700/50 text-amber-100'
                : 'bg-neutral-800 hover:bg-neutral-700'
            }`}
          >
            {p.label}
          </button>
        ))}
      </div>
    </div>
  )
}
