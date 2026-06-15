// Recursive structured-tree rendering of a dialogue node. Plaintext is the
// primary reading content; effects render inline (muted/monospace); outgoing
// edges are expand-on-click affordances styled per type; cycles render as
// back-references instead of re-expanding.

import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useStore } from '../lib/store'
import type { DialogueNode, Edge } from '../lib/types'
import { EDGE_COLOR, flagName } from '../lib/edges'
import { displayDialogue } from '../lib/text'
import { renderNodeAnnotations } from './annotations'

function firstSentence(text: string, max = 90): string {
  const flat = text.replace(/\s+/g, ' ').trim()
  const cut = flat.search(/[.!?]\s/)
  const s = cut > 0 && cut < max ? flat.slice(0, cut + 1) : flat.slice(0, max)
  return s + (s.length < flat.length ? '…' : '')
}

function preview(node: DialogueNode | undefined, showCodes: boolean): string {
  if (!node) return '(not loaded)'
  const text = displayDialogue(node.plaintext || '', showCodes)
  if (text.trim()) return firstSentence(text)
  const menu = node.edges.filter((e) => e.type === 'menu_option').map((e) => e.label)
  if (menu.length) return 'menu: ' + menu.map((m) => `"${m}"`).join(' / ')
  return '(no text)'
}

function Effects({ node }: { node: DialogueNode }) {
  if (!node.effects?.length) return null
  return (
    <div className="mt-1 space-y-0.5">
      {node.effects.map((eff, i) => (
        <div key={i} className="font-mono text-[11px] text-cyan-400/80">
          ⚙ {eff.type}
          {eff.flag_label ? ` ${eff.flag_label}` : eff.flag != null ? ` #${eff.flag}` : ''}
          {!eff.flag_label && eff.flag == null && eff.raw ? ` ${eff.raw}` : ''}
        </div>
      ))}
    </div>
  )
}

// One outgoing edge target as an expand-on-click affordance.
function EdgeRow({
  edge,
  target,
  isFallthrough,
  visited,
  depth,
}: {
  edge: Edge
  target: string
  isFallthrough: boolean
  visited: Set<string>
  depth: number
}) {
  const nodeCache = useStore((s) => s.nodeCache)
  const showCodes = useStore((s) => s.showControlCodes)
  const [open, setOpen] = useState(false)
  const isCycle = visited.has(target)
  const color = EDGE_COLOR[edge.type]

  let label: JSX.Element
  if (isFallthrough) {
    label = <span className="text-neutral-400">Otherwise:</span>
  } else {
    switch (edge.type) {
      case 'flag_test':
        label = (
          <span>
            If <span className="font-mono text-amber-300">{flagName(edge)}</span>{' '}
            {edge.polarity === 'cleared' ? 'is cleared' : 'is set'}:
          </span>
        )
        break
      case 'menu_option':
        label = <span className="text-orange-300">“{edge.label}”</span>
        break
      case 'case_branch':
        label = (
          <span className="text-neutral-400">
            <span className="font-mono">{edge.discriminant ?? '?'}</span> ={' '}
            <span className="text-purple-300">{String(edge.value ?? '?')}</span>
            {edge.kind === 'call' ? ' (call)' : ''}
          </span>
        )
        break
      case 'function_call':
        label = <span className="text-blue-300">Calls →</span>
        break
      default:
        label = <span className="text-neutral-500">→</span>
    }
  }

  return (
    <div
      className="mt-1.5 pl-2 border-l-2"
      style={{ borderColor: color }}
    >
      <button
        onClick={() => !isCycle && setOpen((o) => !o)}
        className="text-left text-sm flex items-start gap-1.5 group"
        disabled={isCycle}
      >
        <span className="text-xs text-neutral-600 mt-0.5 w-3 shrink-0">
          {isCycle ? '↩' : open ? '▾' : '▸'}
        </span>
        <span>
          {label}{' '}
          {isCycle ? (
            <span className="text-neutral-500">returns to </span>
          ) : null}
          <span className="font-mono text-xs text-neutral-500 group-hover:text-neutral-300">
            {target}
          </span>
          {edge.type === 'function_call' && !isCycle && !open && (
            <span className="text-neutral-500 italic"> — {preview(nodeCache.get(target), showCodes)}</span>
          )}
        </span>
      </button>
      {open && !isCycle && (
        // Indent branch content clearly beneath its conditional affordance.
        <div className="ml-2 mt-1 pl-3 border-l-2 border-dashed" style={{ borderColor: color }}>
          <NodeTree nodeId={target} visited={visited} depth={depth + 1} />
        </div>
      )}
    </div>
  )
}

export default function NodeTree({
  nodeId,
  visited,
  depth,
  isRoot = false,
}: {
  nodeId: string
  visited: Set<string>
  depth: number
  isRoot?: boolean
}) {
  const node = useStore((s) => s.nodeCache.get(nodeId))
  const showCodes = useStore((s) => s.showControlCodes)

  if (!node) {
    return (
      <div className="font-mono text-xs text-neutral-600">
        {nodeId} <span className="italic">(not loaded)</span>
      </div>
    )
  }

  const text = displayDialogue(node.plaintext || '', showCodes)

  const nextVisited = new Set(visited)
  nextVisited.add(nodeId)

  const rows: { edge: Edge; target: string; isFallthrough: boolean }[] = []
  for (const edge of node.edges) {
    if (edge.target) rows.push({ edge, target: edge.target, isFallthrough: false })
    if (edge.fallthrough) rows.push({ edge, target: edge.fallthrough, isFallthrough: true })
  }

  return (
    <div className={isRoot ? 'mb-4' : 'mt-1'}>
      <div className="text-[15px] leading-snug whitespace-pre-wrap">
        {text.trim() ? (
          text
        ) : (
          <span className="text-neutral-600 italic">(no text)</span>
        )}
      </div>
      <Effects node={node} />
      {renderNodeAnnotations(node)}
      {depth === 0 && node.referenced_by.length > 1 && (
        <details className="mt-1 text-xs text-neutral-500">
          <summary className="cursor-pointer">
            shared with {node.referenced_by.length - 1} other{' '}
            {node.referenced_by.length - 1 === 1 ? 'entity' : 'entities'}
          </summary>
          <div className="flex flex-wrap gap-1 mt-1">
            {node.referenced_by.map((eid) => (
              <Link key={eid} to={`/entity/${eid}`} className="font-mono text-amber-300 hover:underline">
                {eid}
              </Link>
            ))}
          </div>
        </details>
      )}
      {rows.map((r, i) => (
        <EdgeRow
          key={i}
          edge={r.edge}
          target={r.target}
          isFallthrough={r.isFallthrough}
          visited={nextVisited}
          depth={depth}
        />
      ))}
    </div>
  )
}
