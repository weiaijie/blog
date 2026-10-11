import { describe, expect, it } from 'vitest'
import * as THREE from 'three'
import { createTerrainField, createTerrainSurface, createWorldTiles, WATER_LEVEL } from '../../src/render/visuals/terrainWorld'
import { civilizationOccupies, createCivilizationPlan, insideTile, roadDistance } from '../../src/render/visuals/terrainWorldCivilization'
import { createWorldScenery } from '../../src/render/visuals/terrainWorldScenery'
import { TERRAIN_SEASONS } from '../../src/render/visuals/terrainWorldClimate'

function build(seed:number) {
  const field=createTerrainField(seed),surface=createTerrainSurface(field,createWorldTiles())
  return {surface,field,plan:createCivilizationPlan(field,surface.sample)}
}

describe('connected scenery, independent of gameplay',()=> {
  it.each([221648817,337863546,569575877,20261011,1,999999999])('places varied settlements and safe roads for seed %i',(seed)=> {
    const {plan,surface}=build(seed)
    expect(plan.places.length).toBeGreaterThanOrEqual(7)
    expect(plan.buildings.length).toBeGreaterThanOrEqual(25)
    expect(new Set(plan.farms.map((farm)=>farm.crop)).size).toBe(3)
    expect(plan.farms.length).toBeGreaterThan(2)
    expect(plan.buildings.filter((b)=>b.kind==='mill').length).toBe(2)
    expect(plan.roads.some((road)=>road.bridge)).toBe(true)
    for(const place of plan.places) {
      if(place.kind!=='quarry') expect(plan.buildings.some((b)=>b.placeId===place.id),place.id).toBe(true)
      expect(plan.roads.some((r)=>r.from===place.id || r.to===place.id)).toBe(true)
      expect(civilizationOccupies(plan,place.center)).toBe(true)
    }
    expect(plan.docks).toHaveLength(1)
    for(const road of plan.roads) {
      expect(road.points.length).toBeGreaterThan(1)
      for(let i=1;i<road.points.length;i++) {
        const a=road.points[i-1],b=road.points[i]
        if(road.bridge) {
          expect(a.height).toBeGreaterThan(WATER_LEVEL)
          expect(b.height).toBeGreaterThan(WATER_LEVEL)
          expect(surface.sample((a.x+b.x)/2,(a.z+b.z)/2)!.height).toBeLessThan(WATER_LEVEL)
          continue
        }
        const length=Math.hypot(b.x-a.x,b.z-a.z)
        expect(Math.abs(a.height-b.height)/length).toBeLessThanOrEqual(0.42)
        for(let j=0;j<=10;j++) {
          const t=j/10
          expect(surface.sample(a.x+(b.x-a.x)*t,a.z+(b.z-a.z)*t)!.height).toBeGreaterThan(WATER_LEVEL+0.025)
        }
      }
    }
    for(const b of plan.buildings) {
      expect(roadDistance(b.center,plan.roads)).toBeGreaterThan(b.size*0.53+0.14)
      expect(b.center.height).toBeGreaterThan(WATER_LEVEL)
      const place=plan.places.find((p)=>p.id===b.placeId)!,tile=createWorldTiles().find((t)=>t.id===place.tileId)!
      expect(insideTile(b.center,tile,b.size*0.65)).toBe(true)
    }
    expect(plan.buildings.filter((b)=>b.placeId==='town').length).toBeGreaterThanOrEqual(12)
    expect(new Set(plan.places.map((p)=>p.tileId)).size).toBe(plan.places.length)
    for(const farm of plan.farms) {
      const tile=createWorldTiles().find((t)=>t.id===farm.tileId)!
      for(const x of [-1,1]) for(const z of [-1,1]) expect(insideTile({x:farm.center.x+x*farm.width/2,z:farm.center.z+z*farm.depth/2},tile,0.04)).toBe(true)
    }
  },20000)
  it('is deterministic while different seeds change layout',()=> {
    const {field,surface,plan}=build(337863546)
    expect(createCivilizationPlan(field,surface.sample)).toEqual(plan)
    expect(build(569575877).plan).not.toEqual(plan)
  })
  it('has finite geometry, seasonal colors and animated windmills without moving foundations',()=> {
    const {plan,surface}=build(337863546)
    const scenery=createWorldScenery(plan,surface.sample)
    expect(scenery.rotors).toBe(2)
    const meshes:THREE.Mesh[]=[]
    scenery.group.traverse((obj)=>{if(obj instanceof THREE.Mesh) meshes.push(obj)})
    expect(meshes.length).toBeLessThan(40)
    const positions=meshes.map((mesh)=>Array.from(mesh.geometry.getAttribute('position').array))
    for(const season of TERRAIN_SEASONS) {
      scenery.updateSeason(season);scenery.animate(12)
      meshes.forEach((mesh,i)=> {
        expect(Array.from(mesh.geometry.getAttribute('position').array)).toEqual(positions[i])
        expect(positions[i].every(Number.isFinite)).toBe(true)
        const colors=mesh.geometry.getAttribute('color')
        if(colors) expect(Array.from(colors.array).every(Number.isFinite)).toBe(true)
      })
    }
    meshes.forEach((mesh)=>{mesh.geometry.dispose();for(const mat of Array.isArray(mesh.material)?mesh.material:[mesh.material]) mat.dispose()})
  })
})
