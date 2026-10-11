import { describe, expect, it } from 'vitest'
import { createBoulderGeometry, createBroadleafGeometry, createFlowerGeometry, createGrassGeometry, createPineGeometry, createShrubGeometry } from '../../src/render/visuals/terrainWorldModels'

describe('C-style sculpted terrain props', () => {
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
      expect(geometry.boundingBox!.max.y).toBeLessThan(0.18)
      geometry.dispose()
    }
  })
})
