import { describe, expect, it } from 'vitest'
import { createFixedMap } from '../../src/game/state/map'

describe('fixed map generation', () => {
  it('creates deterministic maps from the same seed', () => {
    expect(createFixedMap(16, 16, 1001)).toEqual(createFixedMap(16, 16, 1001))
  })

  it('creates different layouts from different seeds', () => {
    const first = getTerrainSignature(createFixedMap(16, 16, 1001))
    const second = getTerrainSignature(createFixedMap(16, 16, 2002))

    expect(first).not.toBe(second)
  })

  it('creates stable tile ids and dimensions', () => {
    const map = createFixedMap(20, 20, 1001)

    expect(map.id).toBe('map:20x20:1001')
    expect(map.tiles).toHaveLength(400)
    expect(map.tiles[0]?.id).toBe('tile:0:0')
    expect(map.tiles[399]?.id).toBe('tile:19:19')
  })

  it('keeps the default opening corridor playable for smoke paths', () => {
    const map = createFixedMap(16, 16, 2002)
    const starterTileIds = ['tile:8:5', 'tile:8:6', 'tile:8:7', 'tile:8:8', 'tile:8:9', 'tile:8:10']

    for (const tileId of starterTileIds) {
      expect(map.tiles.find((tile) => tile.id === tileId)?.terrainId).not.toBe('water')
    }

    expect(map.tiles.find((tile) => tile.id === 'tile:8:8')?.terrainId).toBe('forest')
    expect(map.tiles.find((tile) => tile.id === 'tile:8:5')?.terrainId).toBe('grassland')
  })

  it('creates a reasonable terrain mix', () => {
    const map = createFixedMap(32, 32, 3003)
    const counts = countTerrains(map)
    const waterRatio = (counts.water ?? 0) / map.tiles.length

    expect(Object.keys(counts).length).toBeGreaterThanOrEqual(4)
    expect(waterRatio).toBeGreaterThan(0.05)
    expect(waterRatio).toBeLessThan(0.35)
  })

  it('creates coherent terrain patches instead of a checkerboard', () => {
    const map = createFixedMap(32, 32, 4004)
    const byId = new Map(map.tiles.map((tile) => [tile.id, tile]))
    let matchingEdges = 0
    let edgeCount = 0

    for (const tile of map.tiles) {
      for (const [dx, dy] of [
        [1, 0],
        [0, 1],
      ]) {
        const neighbor = byId.get(`tile:${tile.x + dx}:${tile.y + dy}`)

        if (!neighbor) {
          continue
        }

        edgeCount += 1
        if (neighbor.terrainId === tile.terrainId) {
          matchingEdges += 1
        }
      }
    }

    expect(matchingEdges / edgeCount).toBeGreaterThan(0.38)
  })
})

function getTerrainSignature(map: ReturnType<typeof createFixedMap>): string {
  return map.tiles.map((tile) => tile.terrainId[0]).join('')
}

function countTerrains(map: ReturnType<typeof createFixedMap>): Record<string, number> {
  return map.tiles.reduce<Record<string, number>>((counts, tile) => {
    counts[tile.terrainId] = (counts[tile.terrainId] ?? 0) + 1

    return counts
  }, {})
}
