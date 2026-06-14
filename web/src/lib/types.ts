// Data-model types mirroring the extraction schemas and data-prep manifest, so
// schema drift fails at compile time.

export type EdgeType =
  | 'unconditional'
  | 'flag_test'
  | 'menu_option'
  | 'case_branch'
  | 'function_call'

export interface Edge {
  type: EdgeType
  target?: string // case_branch may lack a target
  fallthrough?: string
  // flag_test
  flag?: number | null
  flag_label?: string | null
  polarity?: 'set' | 'cleared'
  // menu_option
  label?: string
  // case_branch
  discriminant?: string
  value?: string | number
  kind?: 'goto' | 'call'
}

export interface Effect {
  type: string
  flag?: number
  flag_label?: string | null
  raw?: string
  [k: string]: unknown
}

export interface DialogueNode {
  id: string
  label_kind: 'hex' | 'npc'
  plaintext: string
  raw: string
  effects: Effect[]
  referenced_by: string[]
  edges: Edge[]
  // v2 sidecar earmark (run-links). Rendered through an injectable hook; absent in v1.
  annotations?: Record<string, unknown>
}

export type EntityType = 'npc' | 'door' | 'sign' | 'present' | 'photo_event'

export interface Visibility {
  condition: 'always' | 'flag_set' | 'flag_cleared'
  flag: number | null
  flag_label: string | null
}

export interface EntityLocation {
  x0: number
  x1: number
  y0: number
  y1: number
  x_sector?: number
  y_sector?: number
  x_tile?: number
  y_tile?: number
}

export interface EntryPoint {
  node_id: string
  role: string
  gated_by_flag?: number | null
  gated_by_flag_label?: string | null
}

// Lean startup row (entities-index.json).
export interface EntityIndexRow {
  id: string
  type: EntityType
  label: string
  region: string | null
  place: string | null
  location: { x0: number; x1: number; y0: number; y1: number }
  has_dialogue: boolean
  silent: boolean
  visibility: Visibility
  sprite: number | null
}

// Full per-entity record (entities/<id>.json).
export interface Entity extends Omit<EntityIndexRow, 'place'> {
  place?: string | null
  entry_points: EntryPoint[]
  reachable_nodes: string[]
  properties: Record<string, unknown>
}

export interface PlaceManifest {
  id: string
  label: string
  kind: 'world' | 'overworld' | 'image' | 'tiled'
  size: [number, number]
  image?: string
  tiles?: {
    url: string
    tileSize: number
    minZoom: number
    maxZoom: number
    maxNativeZoom?: number
  }
}

// Jump targets on the monolithic map (level-0 regions). bounds_global is
// [x0,y0,x1,y1] in global game pixels.
export interface Area {
  id: string
  label: string
  bounds_global: [number, number, number, number]
}

export interface RegionManifest {
  place: string
  translate: [number, number] // local = (gx + tx, gy + ty)
  bundle?: string
}

export interface Manifest {
  places: Record<string, PlaceManifest>
  regions: Record<string, RegionManifest>
  place_by_region: Record<string, string>
  areas?: Area[]
  counts: {
    npc: number
    door: number
    sign: number
    present: number
    photo_event: number
    no_dialogue: number
    total: number
  }
}
