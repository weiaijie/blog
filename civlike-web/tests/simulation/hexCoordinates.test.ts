import { describe, expect, it } from 'vitest'
import { areHexNeighbors, getHexDistance } from '../../src/game/simulation/hexGrid'
import { tileToWorld, worldToTile } from '../../src/render/coordinates/hexCoordinates'

describe('hex coordinates', () => {
  it('converts odd-row offset tile points to world centers', () => {
    expect(tileToWorld({ x: 0, y: 0 }, { hexRadius: 24 }).x).toBeCloseTo(20.78, 2)
    expect(tileToWorld({ x: 0, y: 0 }, { hexRadius: 24 }).y).toBe(24)
    expect(tileToWorld({ x: 0, y: 1 }, { hexRadius: 24 }).x).toBeCloseTo(41.57, 2)
    expect(tileToWorld({ x: 0, y: 1 }, { hexRadius: 24 }).y).toBe(60)
  })

  it('picks the closest hex from world coordinates', () => {
    expect(worldToTile(tileToWorld({ x: 3, y: 4 }, { hexRadius: 24 }), { hexRadius: 24 })).toEqual({
      x: 3,
      y: 4,
    })
    expect(worldToTile(tileToWorld({ x: 3, y: 5 }, { hexRadius: 24 }), { hexRadius: 24 })).toEqual({
      x: 3,
      y: 5,
    })
  })

  it('calculates six-direction hex adjacency', () => {
    expect(areHexNeighbors({ x: 8, y: 9 }, { x: 8, y: 10 })).toBe(true)
    expect(areHexNeighbors({ x: 8, y: 9 }, { x: 10, y: 10 })).toBe(false)
    expect(getHexDistance({ x: 8, y: 9 }, { x: 10, y: 10 })).toBe(2)
  })
})
