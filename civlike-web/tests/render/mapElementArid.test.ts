import { readFileSync } from 'node:fs'
import { Group, Mesh, MeshStandardMaterial, Object3D, Raycaster, Vector3 } from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { describe, expect, it } from 'vitest'
import { createTerrainMotion, defaultTerrainSettings, terrainSnow } from '../../src/render/visuals/mapElementTerrain'

const ids=['volcano','lava-field','sand-dunes','desert-oasis']
async function load(id:string) {
  const b=readFileSync(new URL(`../../src/render/assets/elements/${id}.glb`,import.meta.url))
  return (await new GLTFLoader().parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'')).scene
}
function nodes(model:Object3D,key:string,value?:string) {const result:Object3D[]=[];model.traverse((o)=>{if(o.userData[key]!==undefined && (!value || o.userData[key]===value))result.push(o)});return result}
function signature(model:Group) {
  const result:unknown[]=[]
  model.traverse((o)=>{
    result.push(o.position.toArray(),o.quaternion.toArray(),o.visible)
    if(o instanceof Mesh){
      for(const key of ['position','color'])if(o.geometry.getAttribute(key))result.push(Array.from(o.geometry.getAttribute(key).array))
      for(const m of Array.isArray(o.material)?o.material:[o.material])result.push((m as MeshStandardMaterial).emissiveIntensity)
    }
  });return JSON.stringify(result)
}
describe('arid terrain effects',()=>{
  for(const id of ids)it(`${id} has independent effects, stays still at zero and freezes without resetting on pause`,async()=>{
    const model=await load(id),motion=createTerrainMotion(model)!,defaults=defaultTerrainSettings(id)
    expect(nodes(model,'snowThreshold')).toHaveLength(0)
    for(const phase of [0,.25,.5,.75])expect(terrainSnow(id,phase)).toBe(0)
    expect(nodes(model,'terrainEffect').length).toBeGreaterThan(0)
    motion.setSettings({...defaults,activity:0,wind:0});motion.update(0,true)
    const still=signature(model);motion.update(2,true);expect(signature(model)).toBe(still)
    motion.setSettings(defaults);motion.update(.7,true)
    const moving=signature(model);expect(moving).not.toBe(still)
    motion.update(.7,true);expect(signature(model)).not.toBe(moving)
    const paused=signature(model);motion.update(100,false);expect(signature(model)).toBe(paused)
    motion.update(.1,true);expect(signature(model)).not.toBe(paused)
    expect(model.scale.toArray()).toEqual([1,1,1])
    model.traverse((o)=>{if(o instanceof Mesh)expect(Array.from(o.geometry.getAttribute('position').array).every(Number.isFinite)).toBe(true)})
  })
  it('moves actual water vertices vertically, with limited bank displacement and independent frond wind',async()=>{
    const model=await load('desert-oasis'),motion=createTerrainMotion(model)!,root=nodes(model,'terrainEffect','water')[0]
    const meshes:Mesh[]=[];root.traverse((o)=>{if(o instanceof Mesh)meshes.push(o)})
    const vertices=()=>meshes.flatMap((m)=>{m.updateWorldMatrix(true,false);const a=m.geometry.getAttribute('position');return Array.from({length:a.count},(_,i)=>new Vector3().fromBufferAttribute(a,i).applyMatrix4(m.matrixWorld))})
    motion.setSettings({...defaultTerrainSettings('desert-oasis'),activity:0,wind:0});motion.update(0,true)
    const base=vertices(),fronds=nodes(model,'terrainTuft').map((o)=>o.quaternion.toArray())
    motion.setSettings({...defaultTerrainSettings('desert-oasis'),wind:0});motion.update(1,true)
    const next=vertices()
    expect(next.some((v,i)=>Math.abs(v.y-base[i].y)>.001)).toBe(true)
    for(let i=0;i<next.length;i++){
      expect(next[i].x).toBeCloseTo(base[i].x,7);expect(next[i].z).toBeCloseTo(base[i].z,7)
      expect(Math.abs(next[i].y-base[i].y)).toBeLessThan(.011)
    }
    expect(nodes(model,'terrainTuft').map((o)=>o.quaternion.toArray())).toEqual(fronds)
    expect(nodes(model,'terrainTuft').filter((o)=>o.name.startsWith('OasisFrond'))).toHaveLength(24)
  })
  it('has a recessed crater with a lower liquid surface and a separate low fissure field',async()=>{
    const model=await load('volcano');model.updateMatrixWorld(true)
    const heights:number[]=[],center:number[]=[]
    const surface=model.getObjectByName('LandformRoot_mesh')!
    expect(surface).toBeDefined()
    surface.traverse((o)=>{if(o instanceof Mesh){
      const p=o.geometry.getAttribute('position')
      for(let i=0;i<p.count;i++){
        const v=new Vector3().fromBufferAttribute(p,i).applyMatrix4(o.matrixWorld),r=Math.hypot(v.x+.18,v.z+.12)
        if(r<.12 && v.y>.08)center.push(v.y)
        if(r>.36 && r<.58)heights.push(v.y)
      }
    }})
    expect(Math.max(...heights)-Math.max(...center)).toBeGreaterThan(.25)
    expect(nodes(model,'terrainEffect','lava')).toHaveLength(4)
    expect(nodes(model,'terrainEffect','ash')).toHaveLength(14)
    const field=await load('lava-field');expect(nodes(field,'terrainEffect','lava')).toHaveLength(13)
    expect(nodes(field,'terrainEffect','ash')).toHaveLength(0)
  })
  it('keeps every sand path in the hex bounds and follows its sampled height instead of levitating',async()=>{
    const model=await load('sand-dunes'),motion=createTerrainMotion(model)!,particles=nodes(model,'terrainEffect','sand')
    model.updateMatrixWorld(true)
    const ground=model.getObjectByName('LandformRoot_mesh')!,ray=new Raycaster(),down=new Vector3(0,-1,0)
    expect(particles).toHaveLength(24)
    for(const p of particles){expect(p.userData.driftPath).toHaveLength(963);expect(p.userData.driftPath.every(Number.isFinite)).toBe(true)}
    motion.setSettings({...defaultTerrainSettings('sand-dunes'),wind:1})
    for(let i=0;i<50;i++){
      motion.update(.2,true)
      for(const p of particles){
        const v=p.position
        const norm=Math.max(Math.abs(v.x/1.75+v.z/(Math.sqrt(3)*1.75)),Math.abs(2*v.z/(Math.sqrt(3)*1.75)),Math.abs(v.x/1.75-v.z/(Math.sqrt(3)*1.75)))
        expect(norm).toBeLessThan(.95);expect(v.y).toBeGreaterThan(.08)
        if(i%5===0){
          ray.set(new Vector3(v.x,5,v.z),down)
          const hit=ray.intersectObject(ground,true)[0]
          expect(hit).toBeDefined()
          expect(v.y-hit.point.y).toBeGreaterThan(0)
          expect(v.y-hit.point.y).toBeLessThan(.04)
        }
      }
    }
  })
})
