import manifest from './elements/manifest.json'
import { botanicalFamilies, mapElementRoadmap } from './mapElementRoadmap'

const models = import.meta.glob('./elements/*.glb', { eager: true, query: '?url', import: 'default' }) as Record<string, string>
const references = import.meta.glob('../../../design/asset-orthographics-20261012-expanded/{05-wheat-field,06-plowed-field-v2,07-vegetable-field,09-timber-bridge-v2,12-fishing-boat-v2,24-river-fish-v2,20-sheep,25-pine-tree,27-berry-shrub,29-reeds-v2,31-village-well,36-handcart-v2}.png', { eager: true, query: '?url', import: 'default' }) as Record<string, string>
const labels = new Map(mapElementRoadmap.map((item) => [item.id, item]))
const minimumBotanicalRevision: Record<string,number> = { 'berry-shrub':4,'pine-tree':4,reeds:4 }

export const mapElements = manifest.assets.map((asset) => {
  const family=asset.id.replace(/-v\d+$/, '')
  const revision=Number(asset.id.match(/-v(\d+)$/)?.[1] ?? 1)
  return {
    ...asset,
    family,
    revision,
    label: labels.get(family)?.label ?? asset.id,
    category: labels.get(family)?.category ?? '其他',
    lifecycle: botanicalFamilies.has(family) && revision>=(minimumBotanicalRevision[family]??1),
    animal: ['sheep-v5','cow','horse','chicken','goat','pig','duck','deer'].includes(asset.id),
    building: ['cottage','barn','windmill','watermill','watchtower','castle-keep','castle-gate','castle-wall'].includes(asset.id),
    gate: asset.id==='castle-gate',
    terrain: ['grassland','rolling-hills','rocky-mountain','snow-peak'].includes(family),
    url: models[`./elements/${asset.id}.glb`],
    referenceUrl: references[`../../../design/asset-orthographics-20261012-expanded/${asset.reference}`],
  }
})
export type MapElement = typeof mapElements[number]

export const mapElementLibrary = [...new Set(mapElements.map((asset) => asset.family))].map((family) =>
  mapElements.filter((asset) => asset.family === family).sort((a, b) => b.revision - a.revision)[0],
)

export function initialMapElement(search: string): MapElement {
  const params = new URLSearchParams(search)
  const id = params.get('element') ?? 'wheat-field'
  const family = id.replace(/-v\d+$/, '')
  const revision = Number(params.get('revision') ?? id.match(/-v(\d+)$/)?.[1])
  return mapElements.find((asset) => asset.family === family && asset.revision === revision)
    ?? mapElementLibrary.find((asset) => asset.family === family) ?? mapElementLibrary[0]
}

export function elementVersionLabel(revision: number) {
  return revision === 1 ? '原版' : revision === 2 ? '改进版' : revision === 3 ? '自然动态' : revision === 4 ? '物候动态' : '成长动态'
}
