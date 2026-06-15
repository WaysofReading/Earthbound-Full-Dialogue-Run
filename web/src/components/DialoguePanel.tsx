// Shared dialogue panel, anchored on an entity (map view) or a node (archive
// view). Renders the structured tree (default) or the graph view. The same
// component backs both views — the design principle's "one substrate, many
// projections" at the component level.

import { useEffect, useState, lazy, Suspense } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useStore } from '../lib/store'
import type { Entity, DialogueNode } from '../lib/types'
import NodeTree from './NodeTree'
import { npcSpriteUrl, fallbackSpriteUrl, typeSpriteUrl } from '../lib/paths'

// vis-network is heavy; load graph mode only when the user opens it.
const GraphView = lazy(() => import('./GraphView'))

export type Anchor = { kind: 'entity'; id: string } | { kind: 'node'; id: string }

function VisibilityLine({ entity }: { entity: Entity }) {
  const v = entity.visibility
  if (!v || v.condition === 'always') return <span className="text-neutral-400">always present</span>
  const flag = v.flag_label || (v.flag != null ? `flag #${v.flag}` : 'flag')
  const verb = v.condition === 'flag_set' ? 'when set' : 'when cleared'
  return (
    <span className="text-neutral-400">
      visible {verb}: <span className="font-mono text-amber-300">{flag}</span>
    </span>
  )
}

function EntityHeader({ entity }: { entity: Entity }) {
  const sprite =
    entity.type === 'npc'
      ? entity.sprite != null
        ? npcSpriteUrl(entity.sprite)
        : fallbackSpriteUrl()
      : typeSpriteUrl(entity.type)
  return (
    <div className="flex gap-3 items-start">
      <img
        src={sprite}
        onError={(e) => ((e.target as HTMLImageElement).src = fallbackSpriteUrl())}
        className="eb-marker-img h-12 w-auto [image-rendering:pixelated] shrink-0"
        alt={entity.type}
      />
      <div className="min-w-0">
        <div className="font-semibold truncate">{entity.label || entity.id}</div>
        <div className="text-xs text-neutral-400">
          <span className="capitalize">{entity.type.replace('_', ' ')}</span>
          {entity.region && <> · {entity.region}</>}
        </div>
        <div className="text-xs mt-0.5">
          <VisibilityLine entity={entity} />
        </div>
      </div>
    </div>
  )
}

function NodeHeader({ node }: { node: DialogueNode }) {
  const reachable = node.referenced_by.length > 0
  return (
    <div>
      <div className="font-mono font-semibold">{node.id}</div>
      <div className="text-xs text-neutral-400 mt-0.5">
        {node.label_kind} ·{' '}
        <span className={reachable ? 'text-green-400' : 'text-red-400'}>
          {reachable ? 'reachable' : 'unreachable'}
        </span>
        {' · '}
        referenced by {node.referenced_by.length}{' '}
        {node.referenced_by.length === 1 ? 'entity' : 'entities'}
      </div>
      {node.referenced_by.length > 0 && (
        <div className="text-xs mt-1 flex flex-wrap gap-1">
          {node.referenced_by.map((eid) => (
            <Link
              key={eid}
              to={`/entity/${eid}`}
              className="font-mono text-amber-300 hover:underline"
            >
              {eid}
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

export default function DialoguePanel({ anchor }: { anchor: Anchor }) {
  const navigate = useNavigate()
  const manifest = useStore((s) => s.manifest)!
  const nodeCache = useStore((s) => s.nodeCache)
  const getEntity = useStore((s) => s.getEntity)
  const loadBundle = useStore((s) => s.loadBundle)
  const ensureAllNodes = useStore((s) => s.ensureAllNodes)
  const showCodes = useStore((s) => s.showControlCodes)
  const setShowCodes = useStore((s) => s.setShowControlCodes)

  const [entity, setEntity] = useState<Entity | null>(null)
  const [ready, setReady] = useState(false)
  const [mode, setMode] = useState<'tree' | 'graph'>('tree')
  const [wide, setWide] = useState(false) // graph-mode fly-out to ~67vw

  useEffect(() => {
    let cancelled = false
    setReady(false)
    setEntity(null)
    ;(async () => {
      if (anchor.kind === 'entity') {
        const e = await getEntity(anchor.id)
        if (cancelled) return
        setEntity(e)
        const bundle = e?.region ? manifest.regions[e.region]?.bundle : undefined
        if (bundle) await loadBundle(bundle)
        else await ensureAllNodes()
      } else {
        await ensureAllNodes()
      }
      if (!cancelled) setReady(true)
    })()
    return () => {
      cancelled = true
    }
  }, [anchor.kind, anchor.id, getEntity, loadBundle, ensureAllNodes, manifest])

  const close = () => navigate(anchor.kind === 'entity' ? '/' : '/archive')

  // Roots for the tree + the node set for the graph.
  const rootIds =
    anchor.kind === 'entity'
      ? (entity?.entry_points ?? []).map((ep) => ep.node_id)
      : [anchor.id]
  const reachableIds =
    anchor.kind === 'entity'
      ? (entity?.reachable_nodes ?? [])
      : neighborhood(anchor.id, nodeCache)

  // 33vw by default; graph mode can fly out to ~67vw.
  const widthClass = mode === 'graph' && wide ? 'w-[67vw]' : 'w-[33vw]'

  return (
    <aside
      className={`${widthClass} min-w-[360px] h-full bg-neutral-900 border-l border-neutral-800 flex flex-col shrink-0 transition-[width] duration-200`}
    >
      <div className="flex items-start gap-2 p-3 border-b border-neutral-800">
        <div className="flex-1 min-w-0">
          {anchor.kind === 'entity' && entity && <EntityHeader entity={entity} />}
          {anchor.kind === 'node' && nodeCache.get(anchor.id) && (
            <NodeHeader node={nodeCache.get(anchor.id)!} />
          )}
          {anchor.kind === 'entity' && ready && !entity && (
            <div className="text-sm text-red-400">Entity {anchor.id} not found.</div>
          )}
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <button
            onClick={() => setShowCodes(!showCodes)}
            title="Show control codes (� line markers, [PAUSE])"
            className={`text-xs px-2 py-1 rounded font-mono ${
              showCodes ? 'bg-amber-700/50 text-amber-100' : 'bg-neutral-800 hover:bg-neutral-700'
            }`}
          >
            {'</>'}
          </button>
          {mode === 'graph' && (
            <button
              onClick={() => setWide((w) => !w)}
              title={wide ? 'Narrow panel' : 'Widen panel'}
              className="text-xs px-2 py-1 rounded bg-neutral-800 hover:bg-neutral-700"
            >
              {wide ? '⇥' : '⇤'}
            </button>
          )}
          <button
            onClick={() => setMode(mode === 'tree' ? 'graph' : 'tree')}
            className="text-xs px-2 py-1 rounded bg-neutral-800 hover:bg-neutral-700"
          >
            {mode === 'tree' ? 'Graph' : 'Tree'}
          </button>
          <button
            onClick={close}
            className="text-neutral-500 hover:text-neutral-200 px-1"
            aria-label="Close"
          >
            ×
          </button>
        </div>
      </div>

      <div className="flex-1 min-h-0 overflow-auto">
        {!ready && <div className="p-4 text-sm text-neutral-500">Loading dialogue…</div>}
        {ready && mode === 'tree' && (
          <div className="p-3">
            {rootIds.length === 0 && (
              <div className="text-sm text-neutral-500">
                No dialogue entry points
                {anchor.kind === 'entity' && entity?.type === 'photo_event' && (
                  <> — photo events have no reachable script in this build.</>
                )}
                .
              </div>
            )}
            {rootIds.map((rid) => (
              <NodeTree key={rid} nodeId={rid} visited={new Set()} depth={0} isRoot />
            ))}
          </div>
        )}
        {ready && mode === 'graph' && (
          <Suspense fallback={<div className="p-4 text-sm text-neutral-500">Loading graph…</div>}>
            <GraphView
              rootIds={rootIds}
              reachableIds={reachableIds}
              entryIds={new Set(rootIds)}
            />
          </Suspense>
        )}
      </div>
    </aside>
  )
}

// For a node anchor, the graph neighborhood = the node, its out-targets, and
// its referencing nodes (one hop), bounded to what's loaded.
function neighborhood(nodeId: string, cache: Map<string, DialogueNode>): string[] {
  const set = new Set<string>([nodeId])
  const node = cache.get(nodeId)
  if (node) {
    for (const e of node.edges) {
      if (e.target) set.add(e.target)
      if (e.fallthrough) set.add(e.fallthrough)
    }
  }
  for (const [id, n] of cache) {
    if (n.edges.some((e) => e.target === nodeId || e.fallthrough === nodeId)) set.add(id)
  }
  return [...set]
}
