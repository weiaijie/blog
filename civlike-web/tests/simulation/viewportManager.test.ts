import { describe, expect, it } from 'vitest'
import { calculateChunkStats } from '../../src/render/chunks/chunkManager'
import { calculateActiveTileRect } from '../../src/render/chunks/viewportManager'
import { getHexMapWorldSize } from '../../src/render/coordinates/hexCoordinates'

describe('viewport manager', () => {
  it('calculates active tiles for a hex map', () => {
    const worldSize = getHexMapWorldSize(3, 3, { hexRadius: 20 })
    const activeRect = calculateActiveTileRect({
      camera: { x: 0, y: 0, zoom: 1 },
      viewportWidth: worldSize.width,
      viewportHeight: worldSize.height,
      mapWidth: 3,
      mapHeight: 3,
      hexRadius: 20,
    })

    expect(activeRect).toEqual({
      count: 9,
      maxX: 3,
      maxY: 3,
      minX: 0,
      minY: 0,
    })
    expect(calculateChunkStats(activeRect, 8).activeChunkCount).toBe(1)
  })
})
