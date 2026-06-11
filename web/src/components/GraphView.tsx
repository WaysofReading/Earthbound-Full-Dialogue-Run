// Graph-mode rendering of a reachable subgraph, ported from
// tools/visualize_entity.py (build_graph). Entry nodes are highlighted; edge
// colors match the structured tree. Clicking a node deep-links to its archive URL.

import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { DataSet } from 'vis-data'
import { Network } from 'vis-network'
import { useStore } from '../lib/store'
import { EDGE_COLOR, EDGE_DASHED, edgeLabel } from '../lib/edges'

function truncate(text: string, max = 32): string {
  const flat = (text || '').replace(/\s+/g, ' ').trim()
  return flat.length <= max ? flat : flat.slice(0, max) + '…'
}

export default function GraphView({
  reachableIds,
  entryIds,
}: {
  rootIds: string[]
  reachableIds: string[]
  entryIds: Set<string>
}) {
  const ref = useRef<HTMLDivElement>(null)
  const nodeCache = useStore((s) => s.nodeCache)
  const navigate = useNavigate()

  useEffect(() => {
    if (!ref.current) return
    const reachable = new Set(reachableIds)

    const nodes = new DataSet(
      reachableIds
        .filter((id) => nodeCache.has(id))
        .map((id) => {
          const node = nodeCache.get(id)!
          const isEntry = entryIds.has(id)
          return {
            id,
            label: `${id}\n${truncate(node.plaintext) || '(no text)'}`,
            shape: 'box',
            color: {
              background: isEntry ? '#3f2d12' : '#1f1f1f',
              border: isEntry ? '#ee6633' : '#555',
            },
            font: { color: '#e5e5e5', size: 11, face: 'monospace' },
            borderWidth: isEntry ? 3 : 1,
          }
        }),
    )

    const edges = new DataSet(
      [] as { id: string; from: string; to: string; [k: string]: unknown }[],
    )
    let eid = 0
    for (const id of reachableIds) {
      const node = nodeCache.get(id)
      if (!node) continue
      for (const edge of node.edges) {
        for (const field of ['target', 'fallthrough'] as const) {
          const tgt = edge[field]
          if (!tgt || !reachable.has(tgt)) continue
          edges.add({
            id: `e${eid++}`,
            from: id,
            to: tgt,
            label: edgeLabel(edge) + (field === 'fallthrough' ? ' (else)' : ''),
            arrows: 'to',
            color: { color: EDGE_COLOR[edge.type] },
            dashes: field === 'fallthrough' ? true : EDGE_DASHED[edge.type],
            font: { color: '#aaa', size: 9, strokeWidth: 0 },
          })
        }
      }
    }

    const network = new Network(
      ref.current,
      { nodes, edges },
      {
        layout: { improvedLayout: true },
        physics: {
          solver: 'forceAtlas2Based',
          forceAtlas2Based: { gravitationalConstant: -80, springLength: 120 },
          stabilization: { iterations: 150 },
        },
        interaction: { hover: true, tooltipDelay: 100 },
      },
    )
    network.on('selectNode', (params) => {
      const id = params.nodes?.[0]
      if (id) navigate(`/node/${id}`)
    })

    return () => network.destroy()
  }, [reachableIds, entryIds, nodeCache, navigate])

  return <div ref={ref} className="h-full w-full" />
}
