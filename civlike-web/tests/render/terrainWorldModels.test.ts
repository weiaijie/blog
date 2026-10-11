import { describe, expect, it } from 'vitest'
import { createBoulderGeometry, createBroadleafGeometry, createFernGeometry, createFlowerGeometry, createGrassGeometry, createPineGeometry, createReedGeometry, createShrubGeometry } from '../../src/render/visuals/terrainWorldModels'
import { createBareTreeGeometry, createCactusGeometry, createLeafLitterGeometry, createLilyGeometry } from '../../src/render/visuals/terrainWorldModels'

describe('C-style sculpted terrain props', () => {
  it.each([createBareTreeGeometry,createCactusGeometry,createLeafLitterGeometry,createLilyGeometry])('builds seasonal biome geometry with finite attributes for %s',(create)=> {
    const geometry=create()
    for(const name of ['position','normal','color']) {
      expect(geometry.getAttribute(name).count).toBeGreaterThan(0)
      expect(Array.from(geometry.getAttribute(name).array).every(Number.isFinite)).toBe(true)
    }
    expect(geometry.getAttribute('position').count).toBe(geometry.getAttribute('color').count)
    geometry.dispose()
  })
  it.each([createBoulderGeometry, createBroadleafGeometry, createPineGeometry, createShrubGeometry])('builds reproducible, distinct faceted variants for %s', (create) => {
    const a = create(0), b = create(0), c = create(1)
    expect(Array.from(a.getAttribute('position').array)).toEqual(Array.from(b.getAttribute('position').array))
    expect(Array.from(a.getAttribute('position').array)).not.toEqual(Array.from(c.getAttribute('position').array))
    for (const geometry of [a, b, c]) {
      geometry.computeBoundingBox()
      expect(geometry.boundingBox!.max.y).toBeGreaterThan(geometry.boundingBox!.min.y)
      expect(geometry.getAttribute('color').count).toBe(geometry.getAttribute('position').count)
      expect(Array.from(geometry.getAttribute('position').array).every(Number.isFinite)).toBe(true)
      expect(Array.from(geometry.getAttribute('normal').array).every(Number.isFinite)).toBe(true)
      geometry.dispose()
    }
  })
  it('keeps meadow detail small relative to tree canopies', () => {
    for (const geometry of [createFlowerGeometry(), createGrassGeometry()]) {
      geometry.computeBoundingBox()
      expect(geometry.boundingBox!.min.y).toBeGreaterThanOrEqual(-0.001)
      expect(geometry.boundingBox!.max.y).toBeLessThan(0.3)
      geometry.dispose()
    }
  })
  it.each([createFernGeometry, createReedGeometry, createFlowerGeometry, createGrassGeometry])('builds rooted, colored detail with finite normals for %s', (create) => {
    const geometry = create()
    geometry.computeBoundingBox()
    expect(geometry.boundingBox!.min.y).toBeGreaterThanOrEqual(-0.001)
    expect(geometry.boundingBox!.max.y).toBeLessThan(0.6)
    expect(geometry.getAttribute('position').count).toBeGreaterThan(30)
    expect(geometry.getAttribute('color').count).toBe(geometry.getAttribute('position').count)
    expect(Array.from(geometry.getAttribute('normal').array).every(Number.isFinite)).toBe(true)
    geometry.dispose()
  })
})
