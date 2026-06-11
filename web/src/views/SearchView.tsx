// Unified search: entity scope (label/region/type → map) and full-text scope
// (node plaintext → archive, with entity context). Indices are prebuilt at
// data-prep time and lazy-loaded on first search.

import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useStore } from '../lib/store'

export default function SearchView() {
  const ensureSearch = useStore((s) => s.ensureSearch)
  const ensureAllNodes = useStore((s) => s.ensureAllNodes)
  const entitySearch = useStore((s) => s.entitySearch)
  const fulltextSearch = useStore((s) => s.fulltextSearch)
  const nodeCache = useStore((s) => s.nodeCache)
  const indexById = useStore((s) => s.indexById)

  const [params, setParams] = useSearchParams()
  const q = params.get('q') ?? ''
  const [draft, setDraft] = useState(q)

  useEffect(() => {
    ensureSearch()
    ensureAllNodes()
  }, [ensureSearch, ensureAllNodes])

  useEffect(() => setDraft(q), [q])

  const entityResults = useMemo(
    () => (q && entitySearch ? entitySearch.search(q, { prefix: true, fuzzy: 0.2 }).slice(0, 50) : []),
    [q, entitySearch],
  )
  const nodeResults = useMemo(
    () => (q && fulltextSearch ? fulltextSearch.search(q, { prefix: true, fuzzy: 0.2 }).slice(0, 80) : []),
    [q, fulltextSearch],
  )

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    setParams(draft ? { q: draft } : {})
  }

  return (
    <div className="absolute inset-0 overflow-auto">
      <div className="max-w-3xl mx-auto p-4">
        <form onSubmit={submit} className="mb-4">
          <input
            autoFocus
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Search characters, places, or any line of dialogue…"
            className="w-full bg-neutral-800 border border-neutral-700 rounded px-3 py-2 text-base"
          />
        </form>

        {!q && (
          <p className="text-neutral-500 text-sm">
            Try a character (“Pokey”), a place (“Onett”), or a memorable phrase
            (“fuzzy pickles”).
          </p>
        )}

        {q && (
          <div className="grid md:grid-cols-2 gap-6">
            <section>
              <h2 className="text-xs font-semibold uppercase text-neutral-400 mb-2">
                Entities ({entityResults.length})
              </h2>
              <div className="space-y-1">
                {entityResults.map((r) => {
                  const row = indexById.get(r.id as string)
                  return (
                    <Link
                      key={r.id}
                      to={`/entity/${r.id}`}
                      className="block px-2 py-1 rounded hover:bg-neutral-800 text-sm"
                    >
                      <span className="font-medium">{(r as { label?: string }).label || r.id}</span>
                      <span className="text-neutral-500 text-xs ml-2">
                        {row?.type}
                        {row?.region ? ` · ${row.region}` : ''}
                      </span>
                    </Link>
                  )
                })}
                {entityResults.length === 0 && (
                  <p className="text-neutral-600 text-sm">No matching entities.</p>
                )}
              </div>
            </section>

            <section>
              <h2 className="text-xs font-semibold uppercase text-neutral-400 mb-2">
                Dialogue ({nodeResults.length})
              </h2>
              <div className="space-y-2">
                {nodeResults.map((r) => {
                  const node = nodeCache.get(r.id as string)
                  const refs = node?.referenced_by ?? []
                  const context = refs
                    .map((eid) => indexById.get(eid))
                    .filter(Boolean)
                    .slice(0, 3)
                  return (
                    <Link
                      key={r.id}
                      to={`/node/${r.id}`}
                      className="block px-2 py-1.5 rounded hover:bg-neutral-800"
                    >
                      <div className="text-sm text-neutral-200 line-clamp-2">
                        {node?.plaintext || <span className="italic text-neutral-600">(no text)</span>}
                      </div>
                      <div className="text-xs text-neutral-500 mt-0.5">
                        <span className="font-mono">{r.id}</span>
                        {context.length > 0 && (
                          <>
                            {' · '}
                            {context.map((c) => `${c!.label || c!.id} (${c!.region ?? '?'})`).join(', ')}
                            {refs.length > 3 ? ` +${refs.length - 3}` : ''}
                          </>
                        )}
                      </div>
                    </Link>
                  )
                })}
                {nodeResults.length === 0 && (
                  <p className="text-neutral-600 text-sm">No matching dialogue.</p>
                )}
              </div>
            </section>
          </div>
        )}
      </div>
    </div>
  )
}
