// Asset URL helpers. BASE_URL is './' (set in vite.config) so these resolve
// relative to the deployed index.html — correct under a Pages project subpath.

const BASE = import.meta.env.BASE_URL

export const dataUrl = (rel: string) => `${BASE}data/${rel}`
export const assetUrl = (rel: string) => `${BASE}${rel}`

export const npcSpriteUrl = (spriteId: number) => assetUrl(`sprites/npc/${spriteId}.png`)
export const typeSpriteUrl = (name: string) => assetUrl(`sprites/type/${name}.png`)
export const fallbackSpriteUrl = () => assetUrl('sprites/type/fallback.png')
