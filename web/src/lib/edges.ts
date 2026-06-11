// Edge presentation, shared by the structured tree and the graph view. Ported
// from tools/visualize_entity.py (EDGE_STYLES, _edge_label) so both renderings
// agree on color and labeling.

import type { Edge, EdgeType } from './types'

export const EDGE_COLOR: Record<EdgeType, string> = {
  unconditional: '#888888',
  flag_test: '#33aa77',
  menu_option: '#ee6633',
  case_branch: '#aa44cc',
  function_call: '#3366cc',
}

export const EDGE_DASHED: Record<EdgeType, boolean> = {
  unconditional: false,
  flag_test: false,
  menu_option: false,
  case_branch: false,
  function_call: true,
}

// Human flag label with a raw-number fallback (flag_label is often null).
export function flagName(edge: Pick<Edge, 'flag' | 'flag_label'>): string {
  if (edge.flag_label) return edge.flag_label
  if (edge.flag != null) return `flag #${edge.flag}`
  return 'flag'
}

export function edgeLabel(edge: Edge): string {
  switch (edge.type) {
    case 'flag_test':
      return `if ${edge.polarity ?? '?'} ${flagName(edge)}`
    case 'menu_option':
      return `"${edge.label ?? ''}"`
    case 'case_branch':
      return (
        `${edge.discriminant ?? '?'}=${edge.value ?? '?'}` +
        (edge.kind === 'call' ? ' (call)' : '')
      )
    case 'function_call':
      return 'call'
    default:
      return ''
  }
}

// The two outgoing targets an edge may carry (fallthrough is rare).
export function edgeTargets(edge: Edge): { target: string; fallthrough: boolean }[] {
  const out: { target: string; fallthrough: boolean }[] = []
  if (edge.target) out.push({ target: edge.target, fallthrough: false })
  if (edge.fallthrough) out.push({ target: edge.fallthrough, fallthrough: true })
  return out
}
