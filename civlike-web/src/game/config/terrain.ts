export type TerrainId = 'grassland' | 'forest' | 'hill' | 'water'

export type TerrainConfig = {
  id: TerrainId
  label: string
  food: number
  production: number
  science: number
  movementCost: number
  color: number
}

export const terrainConfigs: TerrainConfig[] = [
  {
    id: 'grassland',
    label: '草地',
    food: 2,
    production: 0,
    science: 0,
    movementCost: 1,
    color: 0x7fb069,
  },
  {
    id: 'forest',
    label: '森林',
    food: 1,
    production: 1,
    science: 0,
    movementCost: 2,
    color: 0x426b45,
  },
  {
    id: 'hill',
    label: '丘陵',
    food: 0,
    production: 2,
    science: 0,
    movementCost: 2,
    color: 0x9c7f52,
  },
  {
    id: 'water',
    label: '水域',
    food: 1,
    production: 0,
    science: 1,
    movementCost: 2,
    color: 0x4f8fc0,
  },
]

export function getTerrainConfig(id: TerrainId): TerrainConfig {
  const config = terrainConfigs.find((terrain) => terrain.id === id)

  if (!config) {
    throw new Error(`Unknown terrain id: ${id}`)
  }

  return config
}
