import { describe, expect, it } from 'vitest'
import { getTerrainConfig, terrainConfigs } from '../../src/game/config/terrain'

describe('terrain config', () => {
  it('keeps stable unique terrain ids', () => {
    const ids = terrainConfigs.map((terrain) => terrain.id)

    expect(new Set(ids).size).toBe(ids.length)
    expect(ids).toEqual(['grassland', 'forest', 'hill', 'water'])
  })

  it('returns terrain by id', () => {
    expect(getTerrainConfig('grassland').food).toBe(2)
  })
})
