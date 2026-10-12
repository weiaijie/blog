import { describe, expect, it } from 'vitest'
import * as THREE from 'three'
import { createAquaticPlan, createWorldAquatic, sampleFishMotion } from '../../src/render/visuals/terrainWorldAquatic'
import { createTerrainField, createTerrainSurface, createWorldTiles, WATER_LEVEL } from '../../src/render/visuals/terrainWorld'
import { sampleWaterHeight, waterEnvironment } from '../../src/render/visuals/terrainWorldWater'

const tiles=createWorldTiles()
describe('underwater wildlife',()=> {
  it.each([221648817,569575877,20261011])('keeps the whole swimming cycle in water for seed %i',(seed)=> {
    const surface=createTerrainSurface(createTerrainField(seed),tiles),fish=createAquaticPlan(seed,tiles,surface.sample)
    expect(fish.length).toBeGreaterThanOrEqual(20)
    expect(fish.length).toBeLessThanOrEqual(72)
    for(const item of fish) for(let frame=0;frame<100;frame++) {
      const time=frame*Math.PI*2/item.school.speed/100,p=sampleFishMotion(item,time,surface.sample)
      const bed=surface.sample(p.x,p.z)!
      expect(bed).not.toBeNull()
      expect(p.height-0.03).toBeGreaterThan(bed.height)
      expect(p.height+0.03).toBeLessThan(WATER_LEVEL-0.075)
      expect(Number.isFinite(p.yaw+p.tail)).toBe(true)
    }
    expect(sampleFishMotion(fish[0],0,surface.sample)).not.toEqual(sampleFishMotion(fish[0],3,surface.sample))
  })
  it('is reproducible, loops smoothly and batches all fish into three draws',()=> {
    const sample=createTerrainSurface(createTerrainField(221648817),tiles).sample
    const a=createWorldAquatic(221648817,tiles,sample),b=createAquaticPlan(221648817,tiles,sample)
    expect(a.fish).toEqual(b)
    expect(a.group.children).toHaveLength(3)
    const item=a.fish[0],start=sampleFishMotion(item,0,sample),end=sampleFishMotion(item,2*Math.PI/item.school.speed,sample)
    expect(start.x).toBeCloseTo(end.x,8);expect(start.z).toBeCloseTo(end.z,8)
    a.animate(3)
    const meshes=a.group.children as THREE.InstancedMesh[]
    const before=meshes.map((mesh)=>Array.from(mesh.instanceMatrix.array))
    a.animate(3)
    expect(meshes.map((mesh)=>Array.from(mesh.instanceMatrix.array))).toEqual(before)
    for(const mesh of meshes) {
      expect(Array.from(mesh.instanceMatrix.array).every(Number.isFinite)).toBe(true)
      mesh.geometry.dispose();(mesh.material as THREE.Material).dispose();mesh.dispose()
    }
  })
  it('does not spawn fish without a sufficiently deep connected habitat',()=> {
    const field=createTerrainField(1)
    expect(createAquaticPlan(1,tiles,(x,z)=>({...field.sample(x,z),height:WATER_LEVEL-0.05}))).toEqual([])
    expect(createAquaticPlan(1,tiles,()=>null)).toEqual([])
  })
  it('keeps fish bodies below maximum-strength wave troughs without entering the bed',()=> {
    const field=createTerrainField(221648817),sample=createTerrainSurface(field,tiles).sample
    const fish=createAquaticPlan(221648817,tiles,sample)
    for(let time=0;time<60;time+=0.4) {
      const waterAt=(x:number,z:number)=>sampleWaterHeight(x,z,time,waterEnvironment(field,sample(x,z)!),2)
      for(const item of fish) {
        const p=sampleFishMotion(item,time,sample,waterAt)
        expect(p.height+0.03).toBeLessThan(waterAt(p.x,p.z))
        expect(p.height-0.03).toBeGreaterThan(sample(p.x,p.z)!.height)
      }
    }
  })
})
