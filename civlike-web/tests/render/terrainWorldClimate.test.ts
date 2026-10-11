import { describe, expect, it } from 'vitest'
import { createTerrainField, createWorldTiles, edgePoints, getWorldEdges, WORLD_LAYOUT_SCALE } from '../../src/render/visuals/terrainWorld'
import { getTerrainSeason, snowCover, terrainBiome, terrainGroundColor, TERRAIN_BIOMES, TERRAIN_SEASONS } from '../../src/render/visuals/terrainWorldClimate'

describe('visual biome and seasonal layers', () => {
  const tiles=createWorldTiles()
  it.each([569575877,337863546,20261011,1,999999999])('represents all 14 terrain families in 217 cells for seed %i', (seed)=> {
    const field=createTerrainField(seed)
    const present=new Set(tiles.map(({center})=>terrainBiome(field.sample(center.x,center.z))))
    expect([...present].sort()).toEqual(TERRAIN_BIOMES.map(({id})=>id).sort())
  })
  it('offers eight distinct seasonal stages and safely resolves URL input', ()=> {
    expect(TERRAIN_SEASONS).toHaveLength(8)
    expect(new Set(TERRAIN_SEASONS.map(({id})=>id)).size).toBe(8)
    expect(getTerrainSeason(null).id).toBe('bloom')
    expect(getTerrainSeason('invalid').id).toBe('bloom')
    expect(getTerrainSeason('rust').label).toBe('深秋')
    for(const season of TERRAIN_SEASONS) for(const key of ['snow','foliage','bloom','dry','ice','litter'] as const) {
      expect(season[key]).toBeGreaterThanOrEqual(0)
      expect(season[key]).toBeLessThanOrEqual(1)
    }
  })
  it('varies flowering, foliage, leaf litter, snow and ice instead of only hue',()=> {
    const spring=getTerrainSeason('bloom'),autumn=getTerrainSeason('rust'),winter=getTerrainSeason('snow')
    expect(spring.bloom).toBeGreaterThan(autumn.bloom)
    expect(autumn.foliage).toBeLessThan(spring.foliage)
    expect(autumn.litter).toBeGreaterThan(spring.litter)
    expect(winter.foliage).toBe(0)
    expect(winter.ice).toBe(1)
    const field=createTerrainField(569575877),scale=WORLD_LAYOUT_SCALE
    const temperate=field.sample(-2*scale,0),desert=field.sample(4*scale,3*scale)
    expect(snowCover(temperate,winter)).toBeGreaterThan(0.9)
    expect(snowCover(desert,winter)).toBeLessThan(0.15)
    expect(terrainGroundColor(temperate,winter).getHex()).not.toBe(terrainGroundColor(temperate,spring).getHex())
  })
  it('preserves world heights, classifications and edge colors across seasons',()=> {
    const field=createTerrainField(569575877)
    const before=tiles.map(({center})=>field.sample(center.x,center.z))
    for(const season of TERRAIN_SEASONS) {
      for(const edge of getWorldEdges(tiles).filter(({tiles})=>tiles.length===2)) {
        const a=edgePoints(edge.a,edge.b),b=edgePoints(edge.b,edge.a).reverse()
        a.forEach((p,index)=> {
          const c=terrainGroundColor(field.sample(p.x,p.z),season)
          expect(c.toArray().every(Number.isFinite)).toBe(true)
          expect(c.getHex()).toBe(terrainGroundColor(field.sample(b[index].x,b[index].z),season).getHex())
        })
      }
    }
    expect(tiles.map(({center})=>field.sample(center.x,center.z))).toEqual(before)
  })
})
