import type { TerrainId } from '../config/terrain'

export type MapTile = {
  id: string
  x: number
  y: number
  terrainId: TerrainId
}

export type GameMap = {
  id: string
  width: number
  height: number
  seed: number
  tiles: MapTile[]
}

const terrainCycle: TerrainId[] = ['grassland', 'forest', 'hill', 'water']

export function createFixedMap(width: number, height: number, seed: number): GameMap {
  const tiles: MapTile[] = []

  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const terrainIndex = Math.abs((x * 17 + y * 31 + seed) % terrainCycle.length)

      tiles.push({
        id: `tile:${x}:${y}`,
        x,
        y,
        terrainId: terrainCycle[terrainIndex],
      })
    }
  }

  return {
    id: `map:${width}x${height}:${seed}`,
    width,
    height,
    seed,
    tiles,
  }
}
