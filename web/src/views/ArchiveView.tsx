// Archive view: a virtualized table of all 6,153 nodes — the same corpus as the
// map, indexed by node rather than place, including substrate unreachable in
// normal play. Sortable columns, reachability + label-kind filters. Row click
// opens the shared dialogue panel anchored at that node.

import { useEffect, useMemo, useState } from 'react'
import { FixedSizeList } from 'react-window'
import { useParams, useNavigate } from 'react-router-dom'
import { useStore } from '../lib/store'
import type { DialogueNode } from '../lib/types'
import { displayDialogue } from '../lib/text'
import DialoguePanel from '../components/DialoguePanel'

type SortKey = 'id' | 'excerpt' | 'reachable' | 'refby' | 'edges'
interface Row {
  id: string
  kind: 'hex' | 'npc'
  excerpt: string
  reachable: boolean
  refby: number
  edges: number
}

function buildRows(nodes: Map<string, DialogueNode>, showCodes: boolean): Row[] {
  const rows: Row[] = []
  for (const n of nodes.values()) {
    rows.push({
      id: n.id,
      kind: n.label_kind,
      excerpt: displayDialogue(n.plaintext || '', showCodes).replace(/\s+/g, ' ').trim(),
      reachable: n.referenced_by.length > 0,
      refby: n.referenced_by.length,
      edges: n.edges.length,
    })
  }
  return rows
}

export default function ArchiveView() {
  const ensureAllNodes = useStore((s) => s.ensureAllNodes)
  const nodeCache = useStore((s) => s.nodeCache)
  const allLoaded = useStore((s) => s.allNodesLoaded)
  const showCodes = useStore((s) => s.showControlCodes)
  const { id: selectedId } = useParams()
  const navigate = useNavigate()

  const [sortKey, setSortKey] = useState<SortKey>('id')
  const [asc, setAsc] = useState(true)
  const [reachFilter, setReachFilter] = useState<'all' | 'reachable' | 'unreachable'>('all')
  const [kindFilter, setKindFilter] = useState<'all' | 'hex' | 'npc'>('all')

  useEffect(() => {
    ensureAllNodes()
  }, [ensureAllNodes])

  const rows = useMemo(
    () => (allLoaded ? buildRows(nodeCache, showCodes) : []),
    [allLoaded, nodeCache, showCodes],
  )

  const filtered = useMemo(() => {
    let r = rows
    if (reachFilter !== 'all') r = r.filter((x) => x.reachable === (reachFilter === 'reachable'))
    if (kindFilter !== 'all') r = r.filter((x) => x.kind === kindFilter)
    const dir = asc ? 1 : -1
    return [...r].sort((a, b) => {
      const av = a[sortKey]
      const bv = b[sortKey]
      if (av < bv) return -dir
      if (av > bv) return dir
      return 0
    })
  }, [rows, reachFilter, kindFilter, sortKey, asc])

  const onSort = (k: SortKey) => {
    if (k === sortKey) setAsc(!asc)
    else {
      setSortKey(k)
      setAsc(true)
    }
  }

  const Header = ({ k, label, w }: { k: SortKey; label: string; w: string }) => (
    <button
      onClick={() => onSort(k)}
      className={`${w} text-left px-2 py-1 text-xs font-semibold text-neutral-300 hover:text-white shrink-0`}
    >
      {label} {sortKey === k ? (asc ? '▲' : '▼') : ''}
    </button>
  )

  return (
    <div className="absolute inset-0 flex">
      <div className="flex-1 min-w-0 flex flex-col">
        <div className="p-3 border-b border-neutral-800">
          <h1 className="text-sm font-semibold">
            All dialogue nodes
            <span className="text-neutral-500 font-normal">
              {' '}
              — {filtered.length} of {rows.length}, indexed by node. Includes content
              unreachable through normal play.
            </span>
          </h1>
          <div className="flex gap-3 mt-2 text-xs">
            <label className="flex items-center gap-1">
              Reachability
              <select
                value={reachFilter}
                onChange={(e) => setReachFilter(e.target.value as never)}
                className="bg-neutral-800 border border-neutral-700 rounded px-1 py-0.5"
              >
                <option value="all">all</option>
                <option value="reachable">reachable</option>
                <option value="unreachable">unreachable</option>
              </select>
            </label>
            <label className="flex items-center gap-1">
              Label kind
              <select
                value={kindFilter}
                onChange={(e) => setKindFilter(e.target.value as never)}
                className="bg-neutral-800 border border-neutral-700 rounded px-1 py-0.5"
              >
                <option value="all">all</option>
                <option value="hex">hex</option>
                <option value="npc">npc</option>
              </select>
            </label>
          </div>
        </div>

        <div className="flex border-b border-neutral-800 bg-neutral-950">
          <Header k="id" label="Node" w="w-32" />
          <Header k="excerpt" label="Plaintext" w="flex-1" />
          <Header k="reachable" label="Reach" w="w-20" />
          <Header k="refby" label="Ref" w="w-14" />
          <Header k="edges" label="Edges" w="w-14" />
        </div>

        <div className="flex-1 min-h-0">
          {!allLoaded ? (
            <div className="p-4 text-sm text-neutral-500">Loading node store…</div>
          ) : (
            <FixedSizeList
              height={Math.max(200, window.innerHeight - 180)}
              width="100%"
              itemCount={filtered.length}
              itemSize={32}
            >
              {({ index, style }) => {
                const r = filtered[index]
                return (
                  <div
                    style={style}
                    onClick={() => navigate(`/node/${r.id}`)}
                    className={`flex items-center cursor-pointer text-sm border-b border-neutral-900 hover:bg-neutral-800 ${
                      r.id === selectedId ? 'bg-neutral-800' : ''
                    }`}
                  >
                    <span className="w-32 px-2 font-mono text-xs text-amber-300 truncate shrink-0">
                      {r.id}
                    </span>
                    <span className="flex-1 px-2 truncate text-neutral-300">
                      {r.excerpt || <span className="text-neutral-600 italic">(no text)</span>}
                    </span>
                    <span className="w-20 px-2 text-xs shrink-0">
                      <span className={r.reachable ? 'text-green-500' : 'text-red-500'}>
                        {r.reachable ? 'yes' : 'no'}
                      </span>
                    </span>
                    <span className="w-14 px-2 text-xs text-neutral-400 shrink-0">{r.refby}</span>
                    <span className="w-14 px-2 text-xs text-neutral-400 shrink-0">{r.edges}</span>
                  </div>
                )
              }}
            </FixedSizeList>
          )}
        </div>
      </div>

      {selectedId && <DialoguePanel anchor={{ kind: 'node', id: selectedId }} />}
    </div>
  )
}
