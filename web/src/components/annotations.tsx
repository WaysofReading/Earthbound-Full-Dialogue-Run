// v2 sidecar extension point. Run-performance data (run-links.json: node_id →
// YouTube timestamps) will arrive from a separate artifact and attach to
// node.annotations. The dialogue panel calls this for every node; in v1 it is a
// no-op, so adding the affordance later requires no panel restructuring.

import type { DialogueNode } from '../lib/types'

export function renderNodeAnnotations(_node: DialogueNode): JSX.Element | null {
  // v1: nothing. v2 example:
  //   const links = _node.annotations?.runLinks as RunLink[] | undefined
  //   return links ? <RunLinks links={links} /> : null
  return null
}
