import { SimplexNoise } from 'three/examples/jsm/math/SimplexNoise.js'
import { getHexMetrics, getHexPolygonPoints } from '../coordinates/hexCoordinates'

export const WORLD_HEX_RADIUS = 1.18
export const WATER_LEVEL = 0.08
export const WORLD_SUBDIVISIONS = 9

export type GroundPoint = { x: number; z: number }
export type GroundSample = GroundPoint & {
  height: number
  shore: number
  forest: number
  dry: number
  rock: number
}
export type WorldTile = { id: string; q: number; r: number; center: GroundPoint; corners: GroundPoint[] }
export type WorldEdge = { a: GroundPoint; b: GroundPoint; tiles: string[] }
export type TerrainField = ReturnType<typeof createTerrainField>

export function seededRandom(seed: number): () => number {
  let state = seed >>> 0
  return () => {
    state = (Math.imul(state, 1664525) + 1013904223) >>> 0
    return state / 4_294_967_296
  }
}

export function smoothstep(low: number, high: number, value: number): number {
  const t = Math.max(0, Math.min(1, (value - low) / (high - low)))
  return t * t * (3 - 2 * t)
}

export function pointKey(point: GroundPoint): string {
  return `${Math.round(point.x * 1e6)},${Math.round(point.z * 1e6)}`
}

function snap(point: GroundPoint): GroundPoint {
  return { x: Math.round(point.x * 1e6) / 1e6, z: Math.round(point.z * 1e6) / 1e6 }
}

export function createWorldTiles(radius = 3): WorldTile[] {
  const tiles: WorldTile[] = []
  const metrics = getHexMetrics(WORLD_HEX_RADIUS)
  for (let q = -radius; q <= radius; q++) {
    for (let r = Math.max(-radius, -q - radius); r <= Math.min(radius, -q + radius); r++) {
      const center = { x: metrics.horizontalSpacing * (q + r / 2), z: metrics.verticalSpacing * r }
      const corners = getHexPolygonPoints({ x: center.x, y: center.z }, WORLD_HEX_RADIUS)
        .map((point) => snap({ x: point.x, z: point.y }))
      tiles.push({ id: `${q}:${r}`, q, r, center, corners })
    }
  }
  return tiles
}

export function getWorldEdges(tiles: WorldTile[]): WorldEdge[] {
  const edges = new Map<string, WorldEdge>()
  for (const tile of tiles) {
    tile.corners.forEach((a, index) => {
      const b = tile.corners[(index + 1) % 6]
      const key = [pointKey(a), pointKey(b)].sort().join('|')
      const edge = edges.get(key)
      if (edge) edge.tiles.push(tile.id)
      else edges.set(key, { a, b, tiles: [tile.id] })
    })
  }
  return [...edges.values()]
}

export function edgePoints(a: GroundPoint, b: GroundPoint, count = WORLD_SUBDIVISIONS): GroundPoint[] {
  return Array.from({ length: count + 1 }, (_, index) => snap({
    x: a.x + (b.x - a.x) * index / count,
    z: a.z + (b.z - a.z) * index / count,
  }))
}

export function tileTriangles(tile: WorldTile, subdivisions = WORLD_SUBDIVISIONS): GroundPoint[][] {
  const triangles: GroundPoint[][] = []
  tile.corners.forEach((a, sector) => {
    const b = tile.corners[(sector + 1) % 6]
    const at = (u: number, v: number): GroundPoint => snap({
      x: tile.center.x + (a.x - tile.center.x) * u / subdivisions + (b.x - tile.center.x) * v / subdivisions,
      z: tile.center.z + (a.z - tile.center.z) * u / subdivisions + (b.z - tile.center.z) * v / subdivisions,
    })
    for (let u = 0; u < subdivisions; u++) {
      for (let v = 0; v < subdivisions - u; v++) {
        triangles.push([at(u, v), at(u, v + 1), at(u + 1, v)])
        if (u + v < subdivisions - 1) {
          triangles.push([at(u + 1, v), at(u, v + 1), at(u + 1, v + 1)])
        }
      }
    }
  })
  return triangles
}

export function createTerrainField(seed: number) {
  const random = seededRandom(seed)
  const noise = new SimplexNoise({ random })
  const phase = random() * 3
  const riverX = (z: number) => 0.15 + Math.sin(z * 0.56 + phase * 0.17) * 1.15 + z * 0.24
  const riverWidth = (z: number) => 0.22 + smoothstep(-5, 4, z) * 0.24
  const sample = (x: number, z: number): GroundSample => {
    // Shared world coordinates control both sides of every tile edge.
    const n = noise.noise(x * 0.48, z * 0.48)
    const river = Math.abs(x - riverX(z)) - riverWidth(z)
    const coast = 3.45 + x * 0.31 + Math.sin(x * 0.85 + phase) * 0.34 - z
    const shore = Math.min(river, coast)
    const forest = smoothstep(-0.2, 2.8, -x + n * 0.8) * smoothstep(-1.4, 2, -z)
    const dry = smoothstep(0.7, 4.4, x + n * 0.45)
    const hill = Math.exp(-((x - 1.6) ** 2 / 5.5 + (z + 2.8) ** 2 / 3.5)) * 0.75
      + Math.exp(-((x - 3.3) ** 2 / 2.8 + (z - 0.25) ** 2 / 2.1)) * 0.48
    const ridge = (cx: number, cz: number, width: number, length: number, height: number) => {
      const dx = x - cx + noise.noise(x * 1.5, z * 1.5) * 0.1
      const dz = z - cz + noise.noise(x * 1.5 + 8, z * 1.5) * 0.1
      return Math.max(0, 1 - Math.abs(dx) / width - Math.abs(dz) / length) * height
    }
    const peak = Math.max(
      ridge(3.4, -3.1, 1.65, 2.4, 2.7),
      ridge(2.6, -2.15, 1.3, 1.6, 1.8),
      ridge(1.6, -4.6, 1.25, 1.4, 1.7),
    )
    const upland = (hill + peak) * smoothstep(0.2, 1.0, river)
    const elevation = 0.32 + n * 0.09 + noise.noise(x * 1.65, z * 1.65) * 0.025 + upland
    const height = -0.38 + (elevation + 0.38) * smoothstep(-0.16, 0.48, shore)
    return { x, z, height, shore, forest, dry, rock: smoothstep(0.9, 1.65, height + n * 0.23) }
  }
  return { seed, sample, riverX, riverWidth }
}

export function randomTilePoint(tile: WorldTile, random: () => number): GroundPoint {
  const edge = Math.floor(random() * 6)
  const a = tile.corners[edge]
  const b = tile.corners[(edge + 1) % 6]
  let u = random(), v = random()
  if (u + v > 1) { u = 1 - u; v = 1 - v }
  return { x: tile.center.x + (a.x - tile.center.x) * u + (b.x - tile.center.x) * v,
    z: tile.center.z + (a.z - tile.center.z) * u + (b.z - tile.center.z) * v }
}

// Clip each terrain triangle at one shared water plane, including three-cell junctions.
export function clipWaterTriangle(triangle: GroundSample[]): GroundSample[] {
  const polygon: GroundSample[] = []
  triangle.forEach((a, index) => {
    const b = triangle[(index + 1) % triangle.length]
    const insideA = a.height < WATER_LEVEL, insideB = b.height < WATER_LEVEL
    if (insideA) polygon.push(a)
    if (insideA !== insideB) {
      const t = (WATER_LEVEL - a.height) / (b.height - a.height)
      polygon.push({ ...a, x: a.x + (b.x - a.x) * t, z: a.z + (b.z - a.z) * t, height: WATER_LEVEL })
    }
  })
  return polygon
}
