import { describe, expect, it } from 'vitest'
import { createTerrainWaterMaterial } from '../../src/render/visuals/terrainWorldWater'

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
    material.uniforms.iceAmount.value=1
    expect(material.uniforms.flowTime.value).toBe(2.5)
    expect(material.fragmentShader).toContain('tonemapping_fragment')
    expect(material.fragmentShader).toContain('colorspace_fragment')
    material.dispose()
  })
})
