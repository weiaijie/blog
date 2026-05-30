import { describe, expect, it } from 'vitest'
import { tileToWorld, worldToTile } from '../../src/render/coordinates/squareCoordinates'

describe('square coordinates', () => {
  it('converts tile points to world points', () => {
    expect(tileToWorld({ x: 3, y: 4 }, { tileSize: 40 })).toEqual({ x: 120, y: 160 })
  })

  it('converts world points to tile points', () => {
    expect(worldToTile({ x: 159, y: 201 }, { tileSize: 40 })).toEqual({ x: 3, y: 5 })
  })
})
