import { readFileSync } from 'node:fs'
import { Box3, Group, Mesh, Object3D, Quaternion, Raycaster, Vector3 } from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { describe, expect, it } from 'vitest'
import { createMountedMotion, defaultMountedSettings } from '../../src/render/visuals/mapElementMounted'
import { createAnimalMotion, defaultAnimalSettings } from '../../src/render/visuals/mapElementAnimals'

async function load(id:string){const b=readFileSync(new URL(`../../src/render/assets/elements/${id}.glb`,import.meta.url));return (await new GLTFLoader().parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'')).scene}
function nodes(model:Group,key:string){const result:Object3D[]=[];model.traverse((o)=>{if(o.userData[key]!==undefined)result.push(o)});return result}
function snapshot(model:Group){model.updateMatrixWorld(true);const vertices:number[][]=[];model.traverse((o)=>{if(o instanceof Mesh&&o.parent?.userData.mountCable)vertices.push(Array.from(o.geometry.getAttribute('position').array))});return JSON.stringify([model.toJSON().object,vertices])}
function world(o:Object3D){return o.getWorldPosition(new Vector3())}

describe('mounted assets and attached tack',()=>{
  for(const id of ['rider','horse-cart']){
    it(`${id} preserves one adult horse and seat attachment through a complete gait`,async()=>{
      const model=await load(id),motion=createMountedMotion(model)!,anchors=nodes(model,'mountAnchor'),horse=nodes(model,'mountedHorse')[0]
      expect(createAnimalMotion(model)).toBeUndefined();expect(nodes(model,'mountedHorse')).toHaveLength(1)
      const root=nodes(model,'mountKind')[0],seat=anchors.find((p)=>p.userData.mountAnchor==='seat')!,pelvis=anchors.find((p)=>p.userData.mountAnchor==='pelvis')!
      expect(root.userData.routeProfile).toBe('road-145-v1')
      const feet=nodes(model,'animalRole').filter((p)=>p.userData.animalRole==='foot'),phases:number[][]=[]
      motion.setSettings({...defaultMountedSettings,speed:.8})
      for(let i=0;i<120;i++){
        motion.update(1/60,true);model.updateMatrixWorld(true)
        expect(world(seat).distanceTo(world(pelvis))).toBeLessThan(1e-6)
        for(const foot of feet){const box=new Box3().setFromObject(foot);expect(box.min.y).toBeGreaterThan(-.001);expect(box.min.y).toBeLessThan(.11)}
        phases.push(feet.map((p)=>p.position.y));expect(horse.scale.toArray()).toEqual([1,1,1])
        expect(root.position.length()).toBe(0);expect(root.scale.toArray()).toEqual([1,1,1])
        if(id==='rider')for(const s of [-1,1]){
          const boot=anchors.find((p)=>p.userData.mountAnchor===`boot${s}`)!,stirrup=anchors.find((p)=>p.userData.mountAnchor===`stirrup${s}`)!
          expect(world(boot).distanceTo(world(stirrup))).toBeLessThan(.001)
        }
      }
      expect(new Set(feet.map((_,i)=>phases.map((p)=>p[i].toFixed(5)).join(','))).size).toBe(4)
      expect(motion.update(0,false).distance).toBeCloseTo(1.6,6)
      const initial=snapshot(model);motion.update(1,false);expect(snapshot(model)).toBe(initial)
      motion.setSettings({...defaultMountedSettings,speed:0});motion.update(.1,true);const stopped=snapshot(model);motion.update(2,true);expect(snapshot(model)).toBe(stopped)
      motion.setSettings({...defaultMountedSettings,speed:1.4});motion.update(.1,true);expect(snapshot(model)).not.toBe(stopped)
    })
    it(`${id} keeps every flexible cable on the actual hand, bit and harness anchors`,async()=>{
      const model=await load(id),motion=createMountedMotion(model)!,anchors=new Map(nodes(model,'mountAnchor').map((o)=>[o.userData.mountAnchor,o]))
      const cables:Mesh[]=[];model.traverse((o)=>{if(o instanceof Mesh&&o.parent?.userData.mountCable)cables.push(o)})
      expect(cables).toHaveLength(id==='rider'?2:6)
      for(let frame=0;frame<60;frame++){
        motion.update(1/30,true);model.updateMatrixWorld(true)
        for(const mesh of cables){
          const p=mesh.geometry.getAttribute('position'),d=mesh.parent!.userData
          const points=Array.from({length:p.count},(_,i)=>new Vector3().fromBufferAttribute(p,i).applyMatrix4(mesh.matrixWorld))
          for(const name of d.mountCable){
            const target=world(anchors.get(name)!),ring=points.filter((p)=>Math.abs(p.distanceTo(target)-d.cableRadius)<.0001)
            expect(ring.length).toBeGreaterThanOrEqual(6)
            const center=ring.reduce((s,p)=>s.add(p),new Vector3()).multiplyScalar(1/ring.length)
            expect(center.distanceTo(target)).toBeLessThan(.0001)
          }
          expect(points.every((p)=>p.toArray().every(Number.isFinite))).toBe(true)
        }
      }
    })
  }
  it('matches wheel travel to gait distance and supports four real cargo pieces',async()=>{
    const model=await load('horse-cart'),motion=createMountedMotion(model)!,wheels=nodes(model,'mountWheelRadius')
    expect(wheels).toHaveLength(2);motion.setSettings({...defaultMountedSettings,speed:.6});motion.update(1,true)
    for(const wheel of wheels)expect(wheel.quaternion.angleTo(new Quaternion().setFromAxisAngle(new Vector3(1,0,0),.6/.52))).toBeLessThan(1e-6)
    for(let i=0;i<=4;i++){motion.setSettings({...defaultMountedSettings,load:i/4});expect(motion.update(0,false).cargo).toBe(i);expect(nodes(model,'mountCargo').filter((o)=>o.visible)).toHaveLength(i)}
    expect(new Box3().setFromObject(model).getSize(new Vector3()).x).toBeLessThan(1.45)
  })
  it('supports the boots on actual stirrup treads, not just coincident metadata anchors',async()=>{
    const model=await load('rider'),motion=createMountedMotion(model)!,anchors=nodes(model,'mountAnchor')
    for(let i=0;i<60;i++){
      motion.update(1/30,true);model.updateMatrixWorld(true)
      for(const stirrup of nodes(model,'mountStirrup')){
        const boot=anchors.find((p)=>p.userData.mountAnchor===`boot${stirrup.userData.mountStirrup}`)!
        const target=world(boot),ray=new Raycaster(target.clone().add(new Vector3(0,.07,0)),new Vector3(0,-1,0))
        const hits=ray.intersectObject(stirrup,true);expect(hits.length).toBeGreaterThan(0)
        expect(Math.abs(hits[0].point.y-target.y)).toBeLessThan(.012)
      }
    }
  })
  it('keeps stance hooves at the wheel-equivalent ground velocity',async()=>{
    const model=await load('horse-cart'),motion=createMountedMotion(model)!,foot=nodes(model,'animalRole').find((p)=>p.userData.animalRole==='foot'&&p.userData.legIndex===0)!
    motion.setSettings({...defaultMountedSettings,speed:.8});motion.update(.05,true);const initial=world(foot)
    motion.update(.1,true);const next=world(foot)
    expect(next.z-initial.z).toBeCloseTo(-.08,5);expect(next.y).toBeCloseTo(initial.y,5)
  })
  it('does not alter the existing standalone horse family and growth controller',async()=>{
    const model=await load('horse');expect(createMountedMotion(model)).toBeUndefined()
    const animal=createAnimalMotion(model)!
    animal.setSettings({...defaultAnimalSettings,age:.04});for(let i=0;i<120;i++)animal.update(1/30,true)
    expect(animal.state.age).toBeCloseTo(.04,3);expect(nodes(model,'faunaSpecies')).toHaveLength(3)
    animal.setSettings({...defaultAnimalSettings,family:true});for(let i=0;i<400;i++)animal.update(1/30,true)
    expect(animal.state.offspring).toBe(1)
  })
})
