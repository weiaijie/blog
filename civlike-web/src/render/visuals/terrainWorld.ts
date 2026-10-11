import { SimplexNoise } from 'three/examples/jsm/math/SimplexNoise.js'
import { getHexMetrics, getHexPolygonPoints } from '../coordinates/hexCoordinates'

export const WORLD_HEX_RADIUS = 1.18
export const WATER_LEVEL = 0.08
export const WORLD_SUBDIVISIONS = 5

export type GroundPoint = { x: number; z: number }
export type GroundSample = GroundPoint & {
  height: number
  shore: number
  forest: number
  dry: number
  rock: number
  patch: number
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
    const at = (u: number, v: number): GroundPoint => {
      const x = tile.center.x + (a.x - tile.center.x) * u / subdivisions + (b.x - tile.center.x) * v / subdivisions
      const z = tile.center.z + (a.z - tile.center.z) * u / subdivisions + (b.z - tile.center.z) * v / subdivisions
      const jitter = Math.min(1, (subdivisions - u - v) * 0.65) * 0.033
      return snap({ x: x + Math.sin(x * 124.7 + z * 89.3) * jitter, z: z + Math.sin(x * 73.1 - z * 117.9) * jitter })
    }
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

function sculptedPeak(cx: number, cz: number, width: number, length: number, height: number, rotation: number) {
  const apex = { x: -0.08, z: 0.06, height: 1 }
  const outer = Array.from({ length: 8 }, (_, i) => {
    const a = i * Math.PI / 4, r = [1.05, 0.85, 1.12, 0.95, 1.15, 0.82, 1.05, 0.93][i]
    return { x: Math.cos(a) * r, z: Math.sin(a) * r, height: 0 }
  })
  const inner = outer.map((p, i) => ({ x: p.x * (0.43 + i % 3 * 0.055), z: p.z * (0.41 + i % 2 * 0.13),
    height: [0.44, 0.68, 0.39, 0.6, 0.42, 0.7, 0.38, 0.57][i] }))
  const faces = outer.flatMap((p, i) => {
    const j = (i + 1) % 8
    return [[apex, inner[i], inner[j]], [inner[i], p, outer[j]], [inner[i], outer[j], inner[j]]]
  })
  return (x: number, z: number) => {
    const dx = x - cx, dz = z - cz
    const u = (dx * Math.cos(rotation) + dz * Math.sin(rotation)) / width
    const v = (-dx * Math.sin(rotation) + dz * Math.cos(rotation)) / length
    if (Math.abs(u) > 1.2 || Math.abs(v) > 1.2) return 0
    for (const [a, b, c] of faces) {
      const d = (b.z - c.z) * (a.x - c.x) + (c.x - b.x) * (a.z - c.z)
      const wa = ((b.z - c.z) * (u - c.x) + (c.x - b.x) * (v - c.z)) / d
      const wb = ((c.z - a.z) * (u - c.x) + (a.x - c.x) * (v - c.z)) / d
      if (wa >= 0 && wb >= 0 && wa + wb <= 1) return (a.height * wa + b.height * wb + c.height * (1 - wa - wb)) * height
    }
    return 0
  }
}

export function createTerrainField(seed: number) {
  const random = seededRandom(seed)
  const noise = new SimplexNoise({ random })
  const phase = (random() - 0.5) * 0.65
  const riverX = (z: number) => 0.2 - z * 0.56 + Math.sin(z * 1.03 + 0.65 + phase) * 0.65
  const riverWidth = (z: number) => 0.21 + smoothstep(-5, 4, z) * 0.24 + Math.sin(z * 1.5) * 0.025
  const crags = [sculptedPeak(3.55, -2.65, 1.7, 2.3, 2.95, -0.22),
    sculptedPeak(4.8, -1.3, 1.5, 1.7, 2.03, 0.4), sculptedPeak(2.6, -4.05, 1.4, 1.65, 2.35, -0.3)]
  // Broad asymmetric planes give connected ridges, rather than noisy conical peaks.
  const ridge = (x: number, z: number, cx: number, cz: number, width: number, length: number, height: number, angle: number) => {
    const dx = x - cx, dz = z - cz
    const u = (dx * Math.cos(angle) + dz * Math.sin(angle)) / width
    const v = (-dx * Math.sin(angle) + dz * Math.cos(angle)) / length
    const radius = Math.max(Math.abs(u) * 0.94 + Math.abs(v) * 0.34, Math.abs(v) + u * 0.14, -u * 0.8 - v * 0.42)
    return Math.max(0, 1 - radius) * height
  }
  const sample = (x: number, z: number): GroundSample => {
    // Shared world coordinates control both sides of every tile edge.
    const n = noise.noise(x * 0.48, z * 0.48)
    const river = Math.abs(x - riverX(z)) - riverWidth(z)
    const coast = 4.25 + x * 0.8 + Math.sin(x * 1.35 + phase) * 0.3 - z
    const shore = Math.min(river, coast)
    const forest = smoothstep(1.1, 3.6, -x + n * 0.65) * smoothstep(-0.6, 2.5, -z + n * 0.3)
    const dry = smoothstep(1.0, 3.6, x + n * 0.65) * (0.85 + n * 0.15)
    const hill = Math.max(
      ridge(x, z, -1.6, -3.75, 2.7, 2.1, 1.65, -0.55),
      ridge(x, z, 0.1, -4.9, 1.7, 2.2, 1.5, 0.4),
      ridge(x, z, -0.5, -1.95, 1.85, 1.45, 0.72, -0.7),
      ridge(x, z, -2.5, -1.7, 1.6, 1.8, 0.42, 0.5),
    )
    const peak = Math.max(...crags.map((crag) => crag(x, z)))
    const upland = Math.max(hill * smoothstep(0.35, 1.85, river), peak * smoothstep(0.18, 1.05, river))
    const elevation = 0.29 + (n * 0.11 + noise.noise(x * 1.6, z * 1.6) * 0.025) * (1 - smoothstep(0.3, 1.0, upland)) + upland
    const beachWidth = 0.45 + noise.noise(x * 0.7 + 13, z * 0.7) * 0.12
    const bed = -0.18 - smoothstep(0, 0.65, -shore) * 0.28
    const height = bed + (elevation - bed) * smoothstep(-0.12, beachWidth, shore)
    const rock = smoothstep(0.2, 1.15, peak + n * 0.24) * smoothstep(0.5, 1.15, elevation)
    return { x, z, height, shore, forest, dry, rock, patch: noise.noise(x * 2.6, z * 2.6) }
  }
  return { seed, sample, riverX, riverWidth }
}

// Props sample the rendered triangles, not the analytic field above/below them.
export function createTerrainSurface(field: TerrainField, tiles: WorldTile[]) {
  const triangles = tiles.flatMap((tile) => tileTriangles(tile).map((triangle) => triangle.map((p) => field.sample(p.x, p.z))))
  const buckets = new Map<string, GroundSample[][]>()
  for (const triangle of triangles) {
    const xs = triangle.map((p) => Math.floor(p.x * 2)), zs = triangle.map((p) => Math.floor(p.z * 2))
    for (let x = Math.min(...xs); x <= Math.max(...xs); x++) {
      for (let z = Math.min(...zs); z <= Math.max(...zs); z++) {
        const key = `${x}:${z}`, bucket = buckets.get(key) ?? []
        bucket.push(triangle)
        buckets.set(key, bucket)
      }
    }
  }
  const sample = (x: number, z: number): GroundSample | null => {
    for (const [a, b, c] of buckets.get(`${Math.floor(x * 2)}:${Math.floor(z * 2)}`) ?? []) {
      const d = (b.z - c.z) * (a.x - c.x) + (c.x - b.x) * (a.z - c.z)
      const u = ((b.z - c.z) * (x - c.x) + (c.x - b.x) * (z - c.z)) / d
      const v = ((c.z - a.z) * (x - c.x) + (a.x - c.x) * (z - c.z)) / d
      if (u >= -1e-7 && v >= -1e-7 && u + v <= 1 + 1e-7) {
        return { ...field.sample(x, z), height: a.height * u + b.height * v + c.height * (1 - u - v) }
      }
    }
    return null
  }
  return { triangles, sample }
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
