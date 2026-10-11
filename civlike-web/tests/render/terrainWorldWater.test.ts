import { describe, expect, it } from 'vitest'
import { createTerrainWaterMaterial, sampleWaterHeight, type WaterEnvironment } from '../../src/render/visuals/terrainWorldWater'
import { WATER_LEVEL } from '../../src/render/visuals/terrainWorld'

describe('terrain water material', () => {
  it('shares the pausable flow clock without rebuilding its material', () => {
    const clock = { value: 0 }
    const material = createTerrainWaterMaterial(clock)
    expect(material.uniforms.flowTime).toBe(clock)
    clock.value = 2.5
    expect(material.uniforms.flowTime.value).toBe(2.5)
    expect(material.vertexShader).toContain('waterDepth')
    expect(material.vertexShader).toContain('waterFlow')
    expect(material.vertexShader).toContain('waterClimate')
    expect(material.uniforms.iceAmount.value).toBe(0)
    expect(material.transparent).toBe(true)
    expect(material.depthWrite).toBe(false)
    expect(material.vertexShader).toContain('waveHeight')
    expect(material.fragmentShader).toContain('dFdx(vWorld)')
    material.uniforms.iceAmount.value=1
    expect(material.uniforms.flowTime.value).toBe(2.5)
    expect(material.fragmentShader).toContain('tonemapping_fragment')
    expect(material.fragmentShader).toContain('colorspace_fragment')
    material.dispose()
  })
  const env:WaterEnvironment={depth:0.54,across:0.2,along:2,river:0,climate:1,still:0,edge:1}
  it('rolls above and below mean level and remains reproducible',()=> {
    const heights=Array.from({length:300},(_,i)=>sampleWaterHeight(1,2,i*0.1,env))
    expect(Math.max(...heights)-Math.min(...heights)).toBeGreaterThan(0.12)
    expect(sampleWaterHeight(1,2,3,env)).toBe(sampleWaterHeight(1,2,3,env))
    expect(sampleWaterHeight(1,2,3,env,0)).toBeCloseTo(WATER_LEVEL+0.006,10)
    expect(sampleWaterHeight(1,2,3,env,2)-WATER_LEVEL-0.006).toBeCloseTo((sampleWaterHeight(1,2,3,env)-WATER_LEVEL-0.006)*2,10)
  })
  it('attenuates at banks, map edges, still pools and under ice',()=> {
    for(const override of [{depth:0},{edge:0}]) for(const time of [0,4,11]) expect(sampleWaterHeight(1,2,time,{...env,...override},2)).toBeCloseTo(WATER_LEVEL+0.006,10)
    expect(sampleWaterHeight(1,2,4,env,2,1)).toBeCloseTo(WATER_LEVEL+0.006,10)
    const calm=Math.abs(sampleWaterHeight(1,2,4,{...env,still:1})-WATER_LEVEL-0.006)
    expect(calm).toBeLessThan(Math.abs(sampleWaterHeight(1,2,4,env)-WATER_LEVEL-0.006))
    for(let depth=0.001;depth<=0.54;depth+=0.01) for(let time=0;time<25;time+=0.4) {
      expect(sampleWaterHeight(1,2,time,{...env,depth},2)).toBeGreaterThan(WATER_LEVEL-depth)
    }
  })
  it('uses smaller directional waves in river channels',()=> {
    const range=(river:number)=> {
      const h=Array.from({length:300},(_,i)=>sampleWaterHeight(1,2,i*0.1,{...env,river}))
      return Math.max(...h)-Math.min(...h)
    }
    expect(range(1)).toBeGreaterThan(0.04)
    expect(range(1)).toBeLessThan(range(0))
  })
})
