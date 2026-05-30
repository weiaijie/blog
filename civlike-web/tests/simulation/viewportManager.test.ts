import { describe, expect, it } from 'vitest'
import { calculateChunkStats } from '../../src/render/chunks/chunkManager'
import { calculateActiveTileRect } from '../../src/render/chunks/viewportManager'

describe('viewport manager', () => {
  it('calculates active tiles and chunks', () => {
    const activeRect = calculateActiveTileRect({
      camera: { x: 24, y: 24, zoom: 1 },
      viewportWidth: 320,
      viewportHeight: 240,
      mapWidth: 16,
      mapHeight: 16,
      tileSize: 40,
    })

    expect(activeRect).toEqual({
      count: 48,
      maxX: 8,
      maxY: 6,
      minX: 0,
      minY: 0,
    })
    expect(calculateChunkStats(activeRect, 8).activeChunkCount).toBe(1)
  })
})
