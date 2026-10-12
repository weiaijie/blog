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

export function createFixedMap(width: number, height: number, seed: number): GameMap {
  const tiles: MapTile[] = []

  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      tiles.push({
        id: `tile:${x}:${y}`,
        x,
        y,
        terrainId: getTerrainForTile({ height, seed, width, x, y }),
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

function getTerrainForTile(params: {
  height: number
  seed: number
  width: number
  x: number
  y: number
}): TerrainId {
  const starterTerrain = getStarterTerrain(params.x, params.y)

  if (starterTerrain) {
    return starterTerrain
  }

  const continent = fractalNoise(params.seed, params.x, params.y, 0.13)
  const moisture = fractalNoise(params.seed + 101, params.x, params.y, 0.19)
  const elevation = fractalNoise(params.seed + 211, params.x, params.y, 0.22)
  const edgeBias = getEdgeBias(params.width, params.height, params.x, params.y)
  const landScore = continent * 0.72 + edgeBias * 0.28

  if (landScore < 0.29) {
    return 'water'
  }

  if (elevation > 0.72 && landScore > 0.43) {
    return 'hill'
  }

  if (moisture > 0.56) {
    return 'forest'
  }

  return 'grassland'
}

function getStarterTerrain(x: number, y: number): TerrainId | null {
  if (x === 8 && y === 8) {
    return 'forest'
  }

  if (x === 8 && y === 5) {
    return 'grassland'
  }

  if (x === 8 && y >= 6 && y <= 10) {
    return y % 2 === 0 ? 'grassland' : 'forest'
  }

  if ((x === 7 || x === 9) && y >= 8 && y <= 10) {
    return 'grassland'
  }

  return null
}

function getEdgeBias(width: number, height: number, x: number, y: number): number {
  const horizontal = Math.min(x, width - 1 - x) / Math.max(1, width / 2)
  const vertical = Math.min(y, height - 1 - y) / Math.max(1, height / 2)

  return smoothStep(Math.min(horizontal, vertical))
}

function fractalNoise(seed: number, x: number, y: number, scale: number): number {
  return (
    sampleSmoothNoise(seed, x * scale, y * scale) * 0.55 +
    sampleSmoothNoise(seed + 17, x * scale * 2.1, y * scale * 2.1) * 0.3 +
    sampleSmoothNoise(seed + 31, x * scale * 0.55, y * scale * 0.55) * 0.15
  )
}

function sampleSmoothNoise(seed: number, x: number, y: number): number {
  const x0 = Math.floor(x)
  const y0 = Math.floor(y)
  const x1 = x0 + 1
  const y1 = y0 + 1
  const tx = smoothStep(x - x0)
  const ty = smoothStep(y - y0)
  const top = lerp(hashNoise(seed, x0, y0), hashNoise(seed, x1, y0), tx)
  const bottom = lerp(hashNoise(seed, x0, y1), hashNoise(seed, x1, y1), tx)

  return lerp(top, bottom, ty)
}

function hashNoise(seed: number, x: number, y: number): number {
  let value = Math.imul(x, 374761393) ^ Math.imul(y, 668265263) ^ Math.imul(seed, 2246822519)
  value = Math.imul(value ^ (value >>> 13), 1274126177)
  value ^= value >>> 16

  return (value >>> 0) / 4294967295
}

function smoothStep(value: number): number {
  return value * value * (3 - 2 * value)
}

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t
}
