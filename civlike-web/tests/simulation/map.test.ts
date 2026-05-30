import { describe, expect, it } from 'vitest'
import { createFixedMap } from '../../src/game/state/map'

describe('fixed map generation', () => {
  it('creates deterministic maps from the same seed', () => {
    expect(createFixedMap(16, 16, 1001)).toEqual(createFixedMap(16, 16, 1001))
  })

  it('creates stable tile ids and dimensions', () => {
    const map = createFixedMap(20, 20, 1001)

    expect(map.id).toBe('map:20x20:1001')
    expect(map.tiles).toHaveLength(400)
    expect(map.tiles[0]?.id).toBe('tile:0:0')
    expect(map.tiles[399]?.id).toBe('tile:19:19')
  })
})
