import manifest from './elements/manifest.json'

const models = import.meta.glob('./elements/*.glb', { eager: true, query: '?url', import: 'default' }) as Record<string, string>
const references = import.meta.glob('../../../design/asset-orthographics-20261012-expanded/{05-wheat-field,06-plowed-field-v2,07-vegetable-field,09-timber-bridge-v2,12-fishing-boat-v2,24-river-fish-v2,20-sheep,25-pine-tree,27-berry-shrub,29-reeds-v2,31-village-well,36-handcart-v2}.png', { eager: true, query: '?url', import: 'default' }) as Record<string, string>
const labels: Record<string, [string, string]> = {
  'wheat-field': ['成熟麦田', '农田'],
  'plowed-field': ['翻耕田地', '农田'],
  'vegetable-field': ['蔬菜田', '农田'],
  'timber-bridge': ['木制车行桥', '设施'],
  'fishing-boat': ['近岸渔船', '运输'],
  'river-fish': ['河鱼', '动物'],
  sheep: ['绵羊', '动物'],
  'pine-tree': ['针叶树', '植被'],
  'berry-shrub': ['浆果灌木', '植被'],
  reeds: ['水岸芦苇', '植被'],
  'village-well': ['水井', '设施'],
  handcart: ['双轮手推车', '运输'],
}

export const mapElements = manifest.assets.map((asset) => ({
  ...asset,
  family: asset.id.replace(/-v2$/, ''),
  revision: asset.id.endsWith('-v2') ? 2 : 1,
  label: labels[asset.id.replace(/-v2$/, '')]?.[0] ?? asset.id,
  category: labels[asset.id.replace(/-v2$/, '')]?.[1] ?? '其他',
  url: models[`./elements/${asset.id}.glb`],
  referenceUrl: references[`../../../design/asset-orthographics-20261012-expanded/${asset.reference}`],
}))
export type MapElement = typeof mapElements[number]

export const mapElementLibrary = [...new Set(mapElements.map((asset) => asset.family))].map((family) =>
  mapElements.filter((asset) => asset.family === family).sort((a, b) => b.revision - a.revision)[0],
)

export function initialMapElement(search: string): MapElement {
  const params = new URLSearchParams(search)
  const id = params.get('element') ?? 'wheat-field'
  const exact = mapElements.find((asset) => asset.id === id)
  if (exact && (params.get('revision') === '1' || exact.revision === 2)) return exact
  return mapElementLibrary.find((asset) => asset.family === id) ?? mapElementLibrary[0]
}
