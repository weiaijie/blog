import { describe, expect, it } from 'vitest'
import { WATER_LEVEL, WORLD_SUBDIVISIONS, clipWaterTriangle, createTerrainField, createWorldTiles, edgePoints, getWorldEdges, pointKey, seededRandom, tileTriangles } from '../../src/render/visuals/terrainWorld'

describe('C-style continuous terrain', () => {
  const tiles = createWorldTiles()
  const edges = getWorldEdges(tiles)
  it('builds 37 tiles with shared internal edges and only an external cutaway', () => {
    expect(tiles).toHaveLength(37)
    expect(new Set(tiles.map((tile) => tile.id)).size).toBe(37)
    expect(edges.filter((edge) => edge.tiles.length === 1)).toHaveLength(42)
    expect(edges.filter((edge) => edge.tiles.length === 2)).toHaveLength(90)
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
})
