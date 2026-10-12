import { readFileSync } from 'node:fs'
import { Box3, Group, Mesh, MeshStandardMaterial, Object3D, Quaternion, Raycaster, Vector3 } from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { describe, expect, it } from 'vitest'
import { createTransportMotion, defaultTransportSettings, steeringAngle } from '../../src/render/visuals/mapElementTransport'

const ids=['rickshaw','bicycle','early-car','freight-wagon']
async function load(id:string){const b=readFileSync(new URL(`../../src/render/assets/elements/${id}.glb`,import.meta.url));return (await new GLTFLoader().parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'')).scene}
function nodes(model:Group,key:string){const r:Object3D[]=[];model.traverse((o)=>{if(o.userData[key]!==undefined)r.push(o)});return r}
function advance(m:NonNullable<ReturnType<typeof createTransportMotion>>,time:number,playing=true){for(let i=0;i<time*60;i++)m.update(1/60,playing);return {...m.update(0,playing)}}
function snapshot(model:Group){model.updateMatrixWorld(true);return JSON.stringify(model.toJSON().object)}

describe('transport geometry and mechanisms',()=>{
  for(const id of ids){
    it(`${id} has separate wheel pivots, controlled roll and exact pause`,async()=>{
      const model=await load(id),motion=createTransportMotion(model)!,wheels=nodes(model,'vehicleWheel')
      expect(wheels.length).toBe(['rickshaw','bicycle'].includes(id)?2:4)
      const root=nodes(model,'vehicleKind')[0]
      expect(root.userData.routeProfile).toBe(id==='freight-wagon'?'narrow-rail-0668-v1':'road-145-v1')
      motion.setSettings({...defaultTransportSettings,speed:.6})
      const state=advance(motion,1);expect(state.distance).toBeCloseTo(.6,7)
      for(const wheel of wheels){
        const q=new Quaternion().setFromAxisAngle(new Vector3(1,0,0),.6/wheel.userData.wheelRadius)
        expect(wheel.quaternion.angleTo(q)).toBeLessThan(1e-6)
      }
      const paused=snapshot(model),position={...motion.update(0,false)};advance(motion,1,false)
      expect(snapshot(model)).toBe(paused);expect(motion.update(0,false)).toEqual(position)
      motion.setSettings({...defaultTransportSettings,speed:-.6});expect(advance(motion,1).distance).toBeCloseTo(0,7)
      for(const wheel of wheels)expect(wheel.quaternion.angleTo(new Quaternion())).toBeLessThan(1e-6)
      motion.setSettings({...defaultTransportSettings,speed:0});const zero=snapshot(model);advance(motion,1);expect(snapshot(model)).toBe(zero)
      expect(root.scale.toArray()).toEqual([1,1,1]);expect(root.position.toArray()).toEqual([0,0,0])
      model.updateMatrixWorld(true);const bounds=new Box3().setFromObject(model)
      expect(bounds.getSize(new Vector3()).x).toBeLessThan(1.45)
      expect(bounds.min.y).toBeGreaterThanOrEqual(id==='freight-wagon'?-.018:-.0001)
      expect(bounds.min.y).toBeLessThan(.001)
    })
  }
  it('keeps bicycle pedals level and moves a connected chain at the geared speed',async()=>{
    const model=await load('bicycle'),motion=createTransportMotion(model)!,crank=nodes(model,'vehicleCrank')[0],pedals=nodes(model,'vehiclePedal'),links=nodes(model,'vehicleChain')
    motion.update(0,false);expect(links).toHaveLength(56)
    const before=links.map((p)=>p.position.clone());motion.setSettings({...defaultTransportSettings,speed:.6});advance(motion,1)
    expect(crank.quaternion.angleTo(new Quaternion().setFromAxisAngle(new Vector3(1,0,0),.8))).toBeLessThan(1e-6)
    model.updateMatrixWorld(true)
    for(const pedal of pedals){expect(pedal.getWorldQuaternion(new Quaternion()).angleTo(new Quaternion())).toBeLessThan(1e-6);expect(pedal.getWorldPosition(new Vector3()).distanceTo(crank.position)).toBeCloseTo(Math.hypot(.10,.13),5)}
    expect(links.some((p,i)=>p.position.distanceTo(before[i])>.03)).toBe(true)
    for(const link of links){expect(link.position.x).toBeCloseTo(.065,5);expect(link.position.y).toBeGreaterThan(.17);expect(link.position.y).toBeLessThan(.43)}
  })
  it('steers the front wheels only and uses inside/outside Ackermann angles',async()=>{
    const model=await load('early-car'),motion=createTransportMotion(model)!,front=nodes(model,'vehicleSteer')
    motion.setSettings({...defaultTransportSettings,speed:0,steering:.4});advance(motion,2)
    const left=front.find((p)=>p.userData.steerSide===-1)!,right=front.find((p)=>p.userData.steerSide===1)!
    expect(right.rotation.y).toBeGreaterThan(left.rotation.y)
    expect(right.rotation.y).toBeCloseTo(steeringAngle(.4,1,.96,1.3),5)
    for(const wheel of nodes(model,'vehicleWheel'))expect(wheel.getWorldPosition(new Vector3()).y).toBeCloseTo(.25,5)
    expect(nodes(model,'vehicleSteer')).toHaveLength(2)
    motion.setSettings({...defaultTransportSettings,speed:0,steering:-.4});advance(motion,2)
    expect(Math.abs(left.rotation.y)).toBeGreaterThan(Math.abs(right.rotation.y))
  })
  for(const id of ['rickshaw','early-car','freight-wagon']){
    it(`${id} opens independent parts, pauses mid-action and interlocks rolling`,async()=>{
      const model=await load(id),motion=createTransportMotion(model)!
      motion.update(0,false);const initial=snapshot(model)
      motion.setSettings({...defaultTransportSettings,speed:0,access:true});const mid=advance(motion,.2)
      expect(mid.access).toBeGreaterThan(.2);expect(mid.access).toBeLessThan(.9);const paused=snapshot(model);advance(motion,1,false);expect(snapshot(model)).toBe(paused)
      expect(advance(motion,3).access).toBe(1);expect(snapshot(model)).not.toBe(initial)
      motion.setSettings({...defaultTransportSettings,speed:.7,access:true});expect(motion.update(0,true).speed).toBe(0)
      const distance=motion.update(.01,true).distance;expect(distance).toBe(0)
      const closed=advance(motion,3);expect(closed.access).toBeLessThan(.001);expect(closed.speed).toBe(.7)
      if(id==='rickshaw'){
        motion.setSettings({...defaultTransportSettings,speed:0,access:true});advance(motion,3)
        const fabric:Mesh[]=[];model.traverse((o)=>{if(o instanceof Mesh&&o.parent?.userData.vehicleCanopySurface)fabric.push(o)})
        expect(fabric).toHaveLength(1)
        expect(fabric[0].position.length()).toBeLessThan(1e-6)
        const p=fabric[0].geometry.getAttribute('position'),angles=[]
        for(let i=0;i<p.count;i++)angles.push(Math.atan2(-p.getZ(i),p.getY(i)))
        expect(Math.max(...angles)-Math.min(...angles)).toBeCloseTo(.12,5)
        const box=new Box3().setFromObject(fabric[0]);expect(box.getSize(new Vector3()).y).toBeLessThan(.14)
        expect(nodes(model,'vehicleCanopy')).toHaveLength(5)
      }
    })
  }
  it('loads six discrete crates and aligns rail treads with the actual rail profile',async()=>{
    const model=await load('freight-wagon'),motion=createTransportMotion(model)!,wheels=nodes(model,'vehicleWheel'),couplers=nodes(model,'vehicleCoupler')
    for(let i=0;i<=6;i++){motion.setSettings({...defaultTransportSettings,load:i/6});expect(motion.update(0,false).cargo).toBe(i);expect(nodes(model,'vehicleCargo').filter((p)=>p.visible)).toHaveLength(i)}
    expect(couplers).toHaveLength(2);expect(couplers[0].position.y).toBeCloseTo(couplers[1].position.y,6)
    const track=await load('rail-track'),profile=nodes(track,'routeKind')[0]
    for(const wheel of wheels)expect(Math.abs(wheel.position.x)*2).toBeCloseTo(profile.userData.railCenterSpacing,6)
    expect(nodes(model,'vehicleKind')[0].userData.routeProfile).toBe(nodes(track,'routePort')[0].userData.profile)
    expect(nodes(model,'vehicleKind')[0].userData.track).toBeCloseTo(.72,5)
  })
  it('does not add transport controls to other assets',()=>expect(createTransportMotion(new Group())).toBeUndefined())
  it('keeps the canopy fabric attached to all five ribs during folding',async()=>{
    const model=await load('rickshaw'),motion=createTransportMotion(model)!,ribs=nodes(model,'vehicleCanopy')
    let fabric:Mesh|undefined;model.traverse((o)=>{if(o instanceof Mesh&&o.parent?.userData.vehicleCanopySurface)fabric=o})
    expect(fabric).toBeDefined()
    motion.setSettings({...defaultTransportSettings,speed:0,access:true})
    for(const seconds of [0,.1,3]){
      advance(motion,seconds);model.updateMatrixWorld(true)
      const position=fabric!.geometry.getAttribute('position'),vertices=Array.from({length:position.count},(_,i)=>new Vector3().fromBufferAttribute(position,i).applyMatrix4(fabric!.matrixWorld))
      for(const rib of ribs){
        const a=rib.userData.vehicleCanopy,p=new Vector3(0,Math.cos(a)*.86,-Math.sin(a)*.86).applyMatrix4(rib.matrixWorld)
        expect(Math.min(...vertices.map((v)=>v.distanceTo(p)))).toBeLessThan(1e-5)
      }
    }
  })
  it('places actual wagon wheel treads on actual straight rail heads',async()=>{
    const wagon=await load('freight-wagon'),track=await load('rail-track'),straight=nodes(track,'routeShape').find((o)=>o.userData.routeShape==='straight')!
    wagon.updateMatrixWorld(true);track.updateMatrixWorld(true)
    const railMeshes:Mesh[]=[];straight.traverse((o)=>{if(o instanceof Mesh&&o.material instanceof MeshStandardMaterial&&o.material.name==='route_steel')railMeshes.push(o)})
    const normal=new Vector3().fromArray(nodes(track,'routePort')[0].userData.normalGltf),yaw=Math.atan2(normal.x,normal.z),ray=new Raycaster()
    for(const wheel of nodes(wagon,'vehicleWheel')){
      const center=wheel.getWorldPosition(new Vector3())
      ray.set(new Vector3(center.x,-.05,center.z),new Vector3(0,1,0));const tread=ray.intersectObject(wheel,true)
      expect(tread.length).toBeGreaterThan(0);expect(tread[0].point.y).toBeCloseTo(0,5)
      const point=tread[0].point.clone().applyAxisAngle(new Vector3(0,1,0),yaw);point.y=.30
      ray.set(point,new Vector3(0,-1,0));const steel=ray.intersectObjects(railMeshes,false)
      expect(steel.length).toBeGreaterThan(0);expect(steel[0].point.y).toBeCloseTo(.28,5)
    }
  })
  it('exports a transparent windshield rather than a painted panel',async()=>{
    const model=await load('early-car'),glass:MeshStandardMaterial[]=[]
    model.traverse((o)=>{if(o instanceof Mesh&&o.material instanceof MeshStandardMaterial&&o.material.name==='transport_glass')glass.push(o.material)})
    expect(glass.length).toBeGreaterThan(0);for(const material of glass){expect(material.transparent).toBe(true);expect(material.opacity).toBeCloseTo(.22,5)}
  })
})
