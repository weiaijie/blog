import { readFileSync } from 'node:fs'
import { Box3, Group, Mesh, MeshStandardMaterial, Object3D, Quaternion, Raycaster, Vector3 } from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { describe, expect, it } from 'vitest'
import { createTransportMotion, defaultTransportSettings } from '../../src/render/visuals/mapElementTransport'
import { createVesselMotion, defaultVesselSettings } from '../../src/render/visuals/mapElementVessels'

async function load(id:string){const b=readFileSync(new URL(`../../src/render/assets/elements/${id}.glb`,import.meta.url));return (await new GLTFLoader().parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'')).scene}
function nodes(model:Group,key:string){const out:Object3D[]=[];model.traverse((o)=>{if(o.userData[key]!==undefined)out.push(o)});return out}
function snapshot(model:Group){model.updateMatrixWorld(true);const vertices:number[][]=[];model.traverse((o)=>{if(o instanceof Mesh&&o.parent?.userData.vesselSail)vertices.push(Array.from(o.geometry.getAttribute('position').array))});return JSON.stringify([model.toJSON().object,vertices])}
function position(o:Object3D){return o.getWorldPosition(new Vector3())}

describe('steam crank-slider and marine geometry',()=>{
  it('keeps every main/coupling rod on the crank pins throughout a wheel revolution',async()=>{
    const model=await load('steam-locomotive'),motion=createTransportMotion(model)!,anchors=new Map(nodes(model,'steamAnchor').map((o)=>[o.userData.steamAnchor,o])),rods=nodes(model,'steamRod')
    expect(rods).toHaveLength(8);expect(nodes(model,'vehicleWheel')).toHaveLength(6)
    motion.setSettings({...defaultTransportSettings,speed:.27*Math.PI*2})
    for(let i=0;i<120;i++){
      motion.update(1/120,true);model.updateMatrixWorld(true)
      for(const rod of rods){
        const [from,to]=rod.userData.steamRod,a=position(anchors.get(from)!),b=position(anchors.get(to)!)
        expect(new Vector3().applyMatrix4(rod.matrixWorld).distanceTo(a)).toBeLessThan(1e-6)
        expect(new Vector3(0,1,0).applyMatrix4(rod.matrixWorld).distanceTo(b)).toBeLessThan(1e-6)
        if(rod.userData.rodLength)expect(a.distanceTo(b)).toBeCloseTo(rod.userData.rodLength,5)
        const meshes:Mesh[]=[];rod.traverse((o)=>{if(o instanceof Mesh)meshes.push(o)})
        const points=meshes.flatMap((m)=>{const p=m.geometry.getAttribute('position');return Array.from({length:p.count},(_,i)=>new Vector3().fromBufferAttribute(p,i).applyMatrix4(m.matrixWorld))})
        const axis=b.clone().sub(a).normalize(),projections=points.map((p)=>p.clone().sub(a).dot(axis))
        expect(Math.min(...projections)).toBeCloseTo(0,5);expect(Math.max(...projections)).toBeCloseTo(a.distanceTo(b),5)
      }
      for(const cross of nodes(model,'steamCrosshead'))expect(position(cross).y).toBeCloseTo(.27,6)
    }
    const left=position(anchors.get('pin-1_0')!),right=position(anchors.get('pin1_0')!)
    expect(Math.abs(left.y-right.y)).toBeCloseTo(.065,5)
    const paused=snapshot(model);motion.update(.4,false);expect(snapshot(model)).toBe(paused)
    motion.setSettings({...defaultTransportSettings,speed:0});motion.update(0,true);const zero=snapshot(model);motion.update(1,true);expect(snapshot(model)).toBe(zero)
    motion.setSettings({...defaultTransportSettings,speed:-.6});const before=motion.update(0,true).distance;expect(motion.update(1,true).distance).toBeLessThan(before)
  })
  it('retains the wagon gauge, coupler height and bounded steam exhaust',async()=>{
    const model=await load('steam-locomotive'),motion=createTransportMotion(model)!,wagon=await load('freight-wagon')
    const root=nodes(model,'vehicleKind')[0];expect(root.userData.routeProfile).toBe('narrow-rail-0668-v1')
    for(const wheel of nodes(model,'vehicleWheel'))expect(Math.abs(position(wheel).x)).toBeCloseTo(.36,6)
    for(const port of nodes(model,'vehicleCoupler'))expect(position(port).y).toBeCloseTo(position(nodes(wagon,'vehicleCoupler')[0]).y,6)
    const puffs=nodes(model,'steamPuff');expect(puffs).toHaveLength(10)
    for(let i=0;i<120;i++){motion.update(.1,true);model.updateMatrixWorld(true);for(const puff of puffs){expect(position(puff).y).toBeGreaterThan(1.52);expect(new Box3().setFromObject(puff).max.y).toBeLessThan(2.50)}}
  })
  it('places all six actual driving-wheel treads on the straight rail heads',async()=>{
    const engine=await load('steam-locomotive'),track=await load('rail-track'),straight=nodes(track,'routeShape').find((o)=>o.userData.routeShape==='straight')!
    engine.updateMatrixWorld(true);track.updateMatrixWorld(true)
    const rails:Mesh[]=[];straight.traverse((o)=>{if(o instanceof Mesh&&o.material instanceof MeshStandardMaterial&&o.material.name==='route_steel')rails.push(o)})
    const normal=new Vector3().fromArray(nodes(track,'routePort')[0].userData.normalGltf),yaw=Math.atan2(normal.x,normal.z),ray=new Raycaster()
    for(const wheel of nodes(engine,'vehicleWheel')){
      const center=position(wheel)
      ray.set(new Vector3(center.x,-.05,center.z),new Vector3(0,1,0));const tread=ray.intersectObject(wheel,true)
      expect(tread.length).toBeGreaterThan(0);expect(tread[0].point.y).toBeCloseTo(0,5)
      const point=tread[0].point.clone().applyAxisAngle(new Vector3(0,1,0),yaw);point.y=.30
      ray.set(point,new Vector3(0,-1,0));const steel=ray.intersectObjects(rails,false)
      expect(steel.length).toBeGreaterThan(0);expect(steel[0].point.y).toBeCloseTo(.28,5)
    }
  })
  for(const id of ['sailboat','river-barge']){
    it(`${id} has an open cockpit or hold, waterline and pause-safe floating motion`,async()=>{
      const model=await load(id),motion=createVesselMotion(model)!,root=nodes(model,'vesselKind')[0]
      expect(root.userData.waterline).toBe(0);expect(root.userData.routeProfile).toBe('water-channel-v1')
      motion.setSettings({...defaultVesselSettings,load:0,wind:0,waves:0,speed:0,trim:0});for(let i=0;i<120;i++)motion.update(1/60,true)
      model.updateMatrixWorld(true)
      // Probe the cockpit below the boom and backstay; rigging above it is intentional.
      const z=id==='sailboat'?-.65:0,ray=new Raycaster(new Vector3(0,id==='sailboat'?.7:2,z),new Vector3(0,-1,0))
      const hits=ray.intersectObject(model,true).filter((h)=>{let p:Object3D|null=h.object;while(p){if(!p.visible)return false;p=p.parent}return true})
      expect(hits.length).toBeGreaterThan(0);expect(hits[0].point.y).toBeLessThan(id==='sailboat'?.12:0)
      expect(new Box3().setFromObject(model).min.y).toBeLessThan(-.2)
      const flat=snapshot(model);motion.setSettings({...defaultVesselSettings,load:0});motion.update(.8,true);expect(snapshot(model)).not.toBe(flat)
      const frozen=snapshot(model),state={...motion.update(0,false)};motion.update(.4,false);expect(snapshot(model)).toBe(frozen);expect(motion.update(0,false)).toEqual(state)
      motion.setSettings({...defaultVesselSettings,waves:0,wind:0,speed:0,rudder:0,trim:0});for(let i=0;i<180;i++)motion.update(1/30,true)
      expect(root.quaternion.angleTo(new Quaternion())).toBeLessThan(1e-6);expect(root.position.length()).toBe(0)
      expect(nodes(model,'mooringSide')).toHaveLength(4)
    })
  }
  it('fills the interior sail while keeping all three edges fixed and reverses trim',async()=>{
    const model=await load('sailboat'),motion=createVesselMotion(model)!,sails:Mesh[]=[]
    model.traverse((o)=>{if(o instanceof Mesh&&o.parent?.userData.vesselSail)sails.push(o)});expect(sails).toHaveLength(2)
    motion.setSettings({...defaultVesselSettings,wind:0,waves:0,trim:0});motion.update(0,false)
    const rests=sails.map((m)=>Array.from(m.geometry.getAttribute('position').array))
    motion.setSettings({...defaultVesselSettings,wind:1,waves:0,trim:.6});for(let i=0;i<120;i++)motion.update(1/60,true)
    let moved=0,pinned=0
    for(let j=0;j<sails.length;j++){
      const m=sails[j],p=m.geometry.getAttribute('position'),corners=m.parent!.userData.sailCorners.map((a:number[])=>new Vector3().fromArray(a))
      for(let i=0;i<p.count;i++){
        const before=new Vector3().fromArray(rests[j],i*3),after=new Vector3().fromBufferAttribute(p,i)
        expect(after.y).toBeCloseTo(before.y,6);expect(after.z).toBeCloseTo(before.z,6)
        const edge=corners.some((a:Vector3,k:number)=>{const b=corners[(k+1)%3],t=before.clone().sub(a).dot(b.clone().sub(a))/a.distanceToSquared(b);return t>=-.001&&t<=1.001&&a.clone().lerp(b,t).distanceTo(before)<.0001})
        if(edge){expect(after.distanceTo(before)).toBeLessThan(1e-6);pinned++}else if(after.distanceTo(before)>.02)moved++
      }
    }
    expect(pinned).toBeGreaterThan(30);expect(moved).toBeGreaterThan(30)
    const boom=nodes(model,'vesselBoom')[0];expect(boom.rotation.y).toBeCloseTo(.6,4)
    motion.setSettings({...defaultVesselSettings,trim:-.6});for(let i=0;i<120;i++)motion.update(1/60,true);expect(boom.rotation.y).toBeCloseTo(-.6,4)
  })
  it('reverses the propeller, turns the attached rudder and removes all six crates',async()=>{
    const model=await load('river-barge'),motion=createVesselMotion(model)!,prop=nodes(model,'vesselPropeller')[0],rudder=nodes(model,'vesselRudder')[0],helm=nodes(model,'vesselHelm')[0]
    motion.setSettings({...defaultVesselSettings,speed:.5,rudder:.4});motion.update(.5,true);const forward=prop.rotation.z
    motion.setSettings({...defaultVesselSettings,speed:-.5,rudder:-.4});motion.update(.5,true);expect(prop.rotation.z).toBeCloseTo(0,6);expect(forward).toBeGreaterThan(0);expect(rudder.rotation.y).toBeLessThan(0)
    expect(helm.rotation.z).toBeCloseTo(rudder.rotation.y*3,6)
    for(let i=0;i<=6;i++){motion.setSettings({...defaultVesselSettings,load:i/6});expect(motion.update(0,false).cargo).toBe(i);expect(nodes(model,'vesselCargo').filter((o)=>o.visible)).toHaveLength(i)}
  })
})
