import { describe, expect, it } from 'vitest'
import { WATER_LEVEL, WORLD_LAYOUT_SCALE, WORLD_SUBDIVISIONS, clipWaterTriangle, createTerrainField, createTerrainSurface, createWorldTiles, edgePoints, getWorldEdges, pointKey, seededRandom, tileTriangles } from '../../src/render/visuals/terrainWorld'

describe('C-style continuous terrain', () => {
  const tiles = createWorldTiles()
  const edges = getWorldEdges(tiles)
  it('builds 469 tiles with shared internal edges and only an external cutaway', () => {
    expect(tiles).toHaveLength(469)
    expect(new Set(tiles.map((tile) => tile.id)).size).toBe(469)
    expect(edges.filter((edge) => edge.tiles.length === 1)).toHaveLength(150)
    expect(edges.filter((edge) => edge.tiles.length === 2)).toHaveLength(1332)
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
    const samples=tiles.map(({center})=>field.sample(center.x/WORLD_LAYOUT_SCALE*scale,center.z/WORLD_LAYOUT_SCALE*scale)).filter((p)=>p.height>WATER_LEVEL)
    expect(Math.max(...samples.map((p)=>p.forest))).toBeGreaterThan(0.8)
    expect(Math.min(...samples.map((p)=>p.forest))).toBeLessThan(0.1)
    expect(Math.max(...samples.map((p)=>p.height))).toBeGreaterThan(1.5)
    expect(Math.max(...samples.map((p)=>p.rock))).toBeGreaterThan(0.7)
    expect(Math.max(...samples.map((p)=>p.dry))).toBeGreaterThan(0.8)
  })
  it('changes continental silhouettes, mountain ranges and forest regions across seeds',()=> {
    const fields=[221648817,569575877,337863546,20261011,1,999999999].map((s)=>createTerrainField(s))
    expect(new Set(fields.map((f)=>f.layout)).size).toBe(3)
    for(let i=1;i<fields.length;i++) {
      const a=tiles.map((t)=>fields[0].sample(t.center.x,t.center.z)),b=tiles.map((t)=>fields[i].sample(t.center.x,t.center.z))
      expect(a.filter((p,j)=>(p.height<WATER_LEVEL)!==(b[j].height<WATER_LEVEL)).length).toBeGreaterThan(30)
      expect(a.filter((p,j)=>Math.abs(p.forest-b[j].forest)>0.3).length).toBeGreaterThan(30)
      expect(a.filter((p,j)=>Math.abs(p.height-b[j].height)>0.5).length).toBeGreaterThan(20)
    }
  })
  it('advects river coordinates monotonically downstream across tile boundaries', () => {
    const field = createTerrainField(263745286)
    let previous = -Infinity
    for (let z = -15; z <= 15; z += 0.07) {
      const flow = field.waterCoordinates(field.riverX(z), z)
      expect(flow.across).toBeCloseTo(0)
      expect(flow.along*field.flowDirection).toBeGreaterThan(previous)
      expect(flow.river).toBeGreaterThanOrEqual(0)
      expect(flow.river).toBeLessThanOrEqual(1)
      previous = flow.along*field.flowDirection
    }
    for (const edge of edges) for (const p of edgePoints(edge.a,edge.b)) {
      expect(Object.values(field.waterCoordinates(p.x,p.z)).every(Number.isFinite)).toBe(true)
    }
  })
})
