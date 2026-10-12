import { describe, expect, it } from 'vitest'
import * as THREE from 'three'
import { createTerrainField, createTerrainSurface, createWorldTiles, WATER_LEVEL } from '../../src/render/visuals/terrainWorld'
import { createCivilizationPlan } from '../../src/render/visuals/terrainWorldCivilization'
import { createLifePlan, createWorldLife, sampleActorMotion } from '../../src/render/visuals/terrainWorldLife'
import { advanceWorldDay, initialWorldDay, seasonalBlend, worldCalendar } from '../../src/render/visuals/terrainWorldTime'

describe('seeded world time',()=> {
  it('randomizes initial dates reproducibly, with optional explicit season',()=> {
    const days=[221648817,337863546,569575877,20261011,1,999999999].map((seed)=>initialWorldDay(seed))
    expect(new Set(days.map((d)=>worldCalendar(d).season.id)).size).toBeGreaterThanOrEqual(4)
    expect(initialWorldDay(221648817)).toBe(initialWorldDay(221648817))
    expect(worldCalendar(initialWorldDay(8,'snow')).season.id).toBe('snow')
  })
  it('advances at selected speed, freezes and wraps the year',()=> {
    expect(advanceWorldDay(359,2,5,true)).toBe(364)
    expect(advanceWorldDay(359,2,20,false)).toBe(359)
    expect(worldCalendar(360)).toMatchObject({year:2,day:1,index:0})
    expect(advanceWorldDay(10,-1,1,true)).toBe(10)
  })
  it('interpolates foliage, snow and colors continuously through every seasonal boundary',()=> {
    for(let boundary=45;boundary<=360;boundary+=45) {
      const before=seasonalBlend(boundary-0.001),after=seasonalBlend(boundary+0.001)
      for(const key of ['snow','foliage','bloom','dry','ice','litter'] as const) expect(Math.abs(before[key]-after[key])).toBeLessThan(0.001)
      expect(before.leaves).toEqual(after.leaves)
    }
  })
})

describe('visual residents and wildlife',()=> {
  const field=createTerrainField(221648817),surface=createTerrainSurface(field,createWorldTiles()),plan=createCivilizationPlan(field,surface.sample)
  it('creates deterministic travelers, carriers and habitat-specific herds',()=> {
    const actors=createLifePlan(field.seed,plan,surface.sample)
    expect(actors).toEqual(createLifePlan(field.seed,plan,surface.sample))
    expect(new Set(actors.map((a)=>a.kind))).toEqual(new Set(['traveler','cart','deer','sheep','bird']))
    for(const a of actors) {
      expect(a.length).toBeGreaterThan(0)
      if(a.kind==='traveler'||a.kind==='cart') {
        const from=plan.places.find((p)=>p.id===a.from)!,to=plan.places.find((p)=>p.id===a.to)!
        expect(a.path[0].x).toBeCloseTo(from.center.x)
        expect(a.path[a.path.length-1].z).toBeCloseTo(to.center.z)
      }
      for(const p of a.path) {
        expect([p.x,p.z,p.height].every(Number.isFinite)).toBe(true)
        const ground=surface.sample(p.x,p.z)
        if(a.kind==='deer'||a.kind==='sheep') expect(ground!.height).toBeGreaterThan(WATER_LEVEL)
        if(a.kind!=='bird' && ground) expect(p.height).toBeGreaterThanOrEqual(ground.height-0.003)
      }
    }
  })
  it('walks both ways, waits at destinations and stays continuous without teleporting',()=> {
    for(const a of createLifePlan(field.seed,plan,surface.sample)) {
      const travel=a.length/a.speed
      if(a.kind!=='bird') {
        expect(sampleActorMotion(a,travel+1-a.phase).moving).toBe(false)
        expect(sampleActorMotion(a,travel+a.wait+1-a.phase).moving).toBe(true)
      }
      for(let t=0;t<100;t+=0.37) {
        const p=sampleActorMotion(a,t),q=sampleActorMotion(a,t+0.01)
        expect(Math.hypot(p.x-q.x,p.z-q.z)).toBeLessThanOrEqual(a.speed*0.011)
        expect(sampleActorMotion(a,t)).toEqual(p)
      }
    }
  })
  it('batches animated geometry and changes instance matrices without rebuilding it',()=> {
    const life=createWorldLife(field.seed,plan,surface.sample),meshes:THREE.InstancedMesh[]=[]
    life.group.traverse((o)=>{if(o instanceof THREE.InstancedMesh) meshes.push(o)})
    expect(meshes.length).toBeLessThanOrEqual(18)
    const before=Array.from(meshes[0].instanceMatrix.array)
    life.animate(4)
    expect(Array.from(meshes[0].instanceMatrix.array)).not.toEqual(before)
    for(const mesh of meshes) {
      expect(Array.from(mesh.geometry.getAttribute('position').array).every(Number.isFinite)).toBe(true)
      expect(Array.from(mesh.instanceMatrix.array).every(Number.isFinite)).toBe(true)
      mesh.geometry.dispose();mesh.dispose()
    }
    ;(meshes[0].material as THREE.Material).dispose()
  })
})
