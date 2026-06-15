// The one substrate. A single store holds the manifest + entity index (loaded at
// startup) and lazily-populated caches for nodes, full entities, the full node
// store, and search indices. Every view (map, archive, search) is a projection
// of this store — no view needs data another cannot reach.

import { create } from 'zustand'
import MiniSearch from 'minisearch'
import type {
  Manifest,
  EntityIndexRow,
  Entity,
  DialogueNode,
} from './types'
import { dataUrl } from './paths'

async function fetchJson<T>(rel: string): Promise<T> {
  const res = await fetch(dataUrl(rel))
  if (!res.ok) throw new Error(`fetch ${rel}: ${res.status}`)
  return res.json() as Promise<T>
}

interface StoreState {
  manifest: Manifest | null
  index: EntityIndexRow[]
  indexById: Map<string, EntityIndexRow>
  nodeCache: Map<string, DialogueNode>
  entityCache: Map<string, Entity>
  loadedBundles: Set<string>
  allNodesLoaded: boolean
  entitySearch: MiniSearch | null
  fulltextSearch: MiniSearch | null
  error: string | null

  // UI: show raw control codes (� line markers, [PAUSE]) in dialogue text.
  showControlCodes: boolean
  setShowControlCodes: (v: boolean) => void

  loadStartup: () => Promise<void>
  loadBundle: (bundle: string) => Promise<void>
  getEntity: (id: string) => Promise<Entity | null>
  ensureAllNodes: () => Promise<Map<string, DialogueNode>>
  ensureSearch: () => Promise<void>
}

// In-flight de-duplication so concurrent callers share one fetch.
const inflight = new Map<string, Promise<unknown>>()
function once<T>(key: string, fn: () => Promise<T>): Promise<T> {
  if (!inflight.has(key)) inflight.set(key, fn().finally(() => inflight.delete(key)))
  return inflight.get(key) as Promise<T>
}

export const useStore = create<StoreState>((set, get) => ({
  manifest: null,
  index: [],
  indexById: new Map(),
  nodeCache: new Map(),
  entityCache: new Map(),
  loadedBundles: new Set(),
  allNodesLoaded: false,
  entitySearch: null,
  fulltextSearch: null,
  error: null,

  showControlCodes: false,
  setShowControlCodes: (v) => set({ showControlCodes: v }),

  loadStartup: () =>
    once('startup', async () => {
      try {
        const [manifest, index] = await Promise.all([
          fetchJson<Manifest>('manifest.json'),
          fetchJson<EntityIndexRow[]>('entities-index.json'),
        ])
        const indexById = new Map(index.map((e) => [e.id, e]))
        set({ manifest, index, indexById })
      } catch (e) {
        set({ error: String(e) })
      }
    }),

  loadBundle: (bundle) =>
    once(`bundle:${bundle}`, async () => {
      if (get().loadedBundles.has(bundle)) return
      const nodes = await fetchJson<Record<string, DialogueNode>>(
        `nodes/by-region/${bundle}.json`,
      )
      const cache = new Map(get().nodeCache)
      for (const [id, n] of Object.entries(nodes)) cache.set(id, n)
      const loaded = new Set(get().loadedBundles)
      loaded.add(bundle)
      set({ nodeCache: cache, loadedBundles: loaded })
    }),

  getEntity: async (id) => {
    const cached = get().entityCache.get(id)
    if (cached) return cached
    return once(`entity:${id}`, async () => {
      try {
        const ent = await fetchJson<Entity>(`entities/${id}.json`)
        const cache = new Map(get().entityCache)
        cache.set(id, ent)
        set({ entityCache: cache })
        return ent
      } catch {
        return null
      }
    })
  },

  ensureAllNodes: () =>
    once('allNodes', async () => {
      if (get().allNodesLoaded) return get().nodeCache
      const all = await fetchJson<Record<string, DialogueNode>>('nodes/all.json')
      const cache = new Map(get().nodeCache)
      for (const [id, n] of Object.entries(all)) if (!cache.has(id)) cache.set(id, n)
      set({ nodeCache: cache, allNodesLoaded: true })
      return cache
    }),

  ensureSearch: () =>
    once('search', async () => {
      if (get().entitySearch && get().fulltextSearch) return
      const [ent, full] = await Promise.all([
        fetchJson<object>('search-entities.idx'),
        fetchJson<object>('search-fulltext.idx'),
      ])
      set({
        entitySearch: MiniSearch.loadJS(ent as never, {
          fields: ['label', 'region', 'type'],
          storeFields: ['id', 'type', 'label', 'region'],
        }),
        fulltextSearch: MiniSearch.loadJS(full as never, {
          fields: ['plaintext'],
          storeFields: ['id'],
        }),
      })
    }),
}))
