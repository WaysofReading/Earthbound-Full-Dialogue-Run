// Build the prebuilt MiniSearch indices from data-prep's JSON outputs. Run by
// data-prep/search.py (and `npm run build-search`) AFTER prep emits the data, so
// the serialized index uses the same MiniSearch version the client loads.
//
// Usage: node scripts/build-search.mjs [--out <web/public dir>]

import { readFileSync, writeFileSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import MiniSearch from 'minisearch'

const here = dirname(fileURLToPath(import.meta.url))
const outArg = process.argv.indexOf('--out')
const publicDir = outArg !== -1 ? process.argv[outArg + 1] : join(here, '..', 'public')
const dataDir = join(publicDir, 'data')

const readJson = (p) => JSON.parse(readFileSync(p, 'utf-8'))

// ── entity index: label / region / type ──────────────────────────────────────
const index = readJson(join(dataDir, 'entities-index.json'))
const entitySearch = new MiniSearch({
  fields: ['label', 'region', 'type'],
  storeFields: ['id', 'type', 'label', 'region'],
})
entitySearch.addAll(
  index.map((e) => ({
    id: e.id,
    label: e.label || '',
    region: e.region || '',
    type: e.type,
  })),
)
writeFileSync(join(dataDir, 'search-entities.idx'), JSON.stringify(entitySearch))

// ── full-text index over node plaintext ──────────────────────────────────────
const nodes = readJson(join(dataDir, 'nodes', 'all.json'))
const docs = Object.values(nodes)
  .filter((n) => n.plaintext && n.plaintext.trim())
  .map((n) => ({ id: n.id, plaintext: n.plaintext }))
const fulltextSearch = new MiniSearch({
  fields: ['plaintext'],
  storeFields: ['id'],
})
fulltextSearch.addAll(docs)
writeFileSync(join(dataDir, 'search-fulltext.idx'), JSON.stringify(fulltextSearch))

console.log(
  `  search: ${index.length} entities, ${docs.length} text nodes indexed`,
)
