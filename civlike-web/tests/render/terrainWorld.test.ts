import { describe, expect, it } from 'vitest'
import { WATER_LEVEL, WORLD_LAYOUT_SCALE, WORLD_SUBDIVISIONS, clipWaterTriangle, createTerrainField, createTerrainSurface, createWorldTiles, edgePoints, getWorldEdges, pointKey, seededRandom, tileTriangles } from '../../src/render/visuals/terrainWorld'

describe('C-style continuous terrain', () => {
  const tiles = createWorldTiles()
  const edges = getWorldEdges(tiles)
  it('builds 217 tiles with shared internal edges and only an external cutaway', () => {
    expect(tiles).toHaveLength(217)
    expect(new Set(tiles.map((tile) => tile.id)).size).toBe(217)
    expect(edges.filter((edge) => edge.tiles.length === 1)).toHaveLength(102)
    expect(edges.filter((edge) => edge.tiles.length === 2)).toHaveLength(600)
    expect(edges.every((edge) => edge.tiles.length <= 2)).toBe(true)
  })
  it.each([20261011, 1, 999999999])('keeps all sampled shared edges identical with seed %i', (seed) => {
    const field = createTerrainField(seed)
    const meshes = new Map(tiles.map((tile) => [tile.id, new Set(tileTriangles(tile).flat().map(pointKey))]))
    for (const edge of edges.filter((edge) => edge.tiles.length === 2)) {
      const first = edgePoints(edge.a, edge.b)
      const second = edgePoints(edge.b, edge.a).reverse()
      expect(first).toEqual(second)
      for (const p of first) {
        for (const id of edge.tiles) expect(meshes.get(id)?.has(pointKey(p))).toBe(true)
        expect(field.sample(p.x, p.z)).toEqual(createTerrainField(seed).sample(p.x, p.z))
      }
    }
  })
  it('uses reproducible seeds, without global randomness', () => {
    const a = createTerrainField(41), b = createTerrainField(41), c = createTerrainField(42)
    const samples = tiles.map((tile) => tile.center)
    expect(samples.map((p) => a.sample(p.x, p.z))).toEqual(samples.map((p) => b.sample(p.x, p.z)))
    expect(samples.map((p) => a.sample(p.x, p.z))).not.toEqual(samples.map((p) => c.sample(p.x, p.z)))
    const r1 = seededRandom(7), r2 = seededRandom(7)
    expect(Array.from({ length: 50 }, r1)).toEqual(Array.from({ length: 50 }, r2))
  })
  it('triangulates without inverted or degenerate faces', () => {
    for (const tile of tiles) {
      const triangles = tileTriangles(tile)
      expect(triangles).toHaveLength(6 * WORLD_SUBDIVISIONS ** 2)
      for (const [a, b, c] of triangles) {
        expect((b.z - a.z) * (c.x - a.x) - (b.x - a.x) * (c.z - a.z)).toBeGreaterThan(0)
      }
    }
  })
  it('keeps the river connected to the sea and clips water to the same terrain surface', () => {
    const field = createTerrainField(20261011)
    for (let z = -5; z <= 5; z += 0.1) expect(field.sample(field.riverX(z), z).height).toBeLessThan(WATER_LEVEL)
    let wet = 0, dry = 0, shore = 0
    for (const tile of tiles) {
      for (const triangle of tileTriangles(tile)) {
        const samples = triangle.map((p) => field.sample(p.x, p.z))
        const polygon = clipWaterTriangle(samples)
        if (!polygon.length) dry++
        else if (samples.every((p) => p.height < WATER_LEVEL)) wet++
        else shore++
        expect(polygon.length).toBeLessThanOrEqual(4)
        for (const point of polygon) expect(point.height).toBeLessThanOrEqual(WATER_LEVEL + 1e-9)
      }
    }
    expect(wet).toBeGreaterThan(100)
    expect(dry).toBeGreaterThan(100)
    expect(shore).toBeGreaterThan(100)
  })
  it.each([20261011, 263745286, 999999999])('keeps the rendered river open and the seabed within the cutaway for seed %i', (seed) => {
    const field = createTerrainField(seed), surface = createTerrainSurface(field, tiles)
    for (let z = -5 * WORLD_LAYOUT_SCALE; z <= 5 * WORLD_LAYOUT_SCALE; z += 0.05) {
      const sample = surface.sample(field.riverX(z), z)
      if (sample) expect(sample.height).toBeLessThan(WATER_LEVEL)
    }
    for (const triangle of surface.triangles) for (const p of triangle) expect(p.height).toBeGreaterThan(-0.53)
  })
  it('anchors props on the exact rendered triangle, including mountain and bank slopes', () => {
    const surface = createTerrainSurface(createTerrainField(20261011), tiles)
    for (const triangle of surface.triangles) {
      const x = triangle.reduce((sum, p) => sum + p.x, 0) / 3
      const z = triangle.reduce((sum, p) => sum + p.z, 0) / 3
      const height = triangle.reduce((sum, p) => sum + p.height, 0) / 3
      expect(surface.sample(x, z)?.height).toBeCloseTo(height, 6)
    }
    expect(surface.sample(100, 100)).toBeNull()
  })
  it.each([1, WORLD_LAYOUT_SCALE])('keeps distinct biome regions at layout scale %f', (scale) => {
    const field = createTerrainField(20261011, scale)
    expect(field.sample(-4 * scale, -2 * scale).forest).toBeGreaterThan(0.6)
    expect(field.sample(-1.5 * scale, 0.9 * scale).forest).toBeLessThan(0.15)
    expect(field.sample(-1.6 * scale, -3.75 * scale).height).toBeGreaterThan(1.5)
    expect(field.sample(3.4 * scale, -2.55 * scale).rock).toBeGreaterThan(0.7)
    expect(field.sample(4 * scale, 2 * scale).dry).toBeGreaterThan(0.65)
  })
  it('advects river coordinates monotonically downstream across tile boundaries', () => {
    const field = createTerrainField(263745286)
    let previous = -Infinity
    for (let z = -15; z <= 15; z += 0.07) {
      const flow = field.waterCoordinates(field.riverX(z), z)
      expect(flow.across).toBeCloseTo(0)
      expect(flow.along).toBeGreaterThan(previous)
      expect(flow.river).toBeGreaterThanOrEqual(0)
      expect(flow.river).toBeLessThanOrEqual(1)
      previous = flow.along
    }
    for (const edge of edges) for (const p of edgePoints(edge.a,edge.b)) {
      expect(Object.values(field.waterCoordinates(p.x,p.z)).every(Number.isFinite)).toBe(true)
    }
  })
})
