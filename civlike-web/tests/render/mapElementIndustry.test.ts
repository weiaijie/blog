import { readFileSync } from 'node:fs'
import { Box3, Group, Mesh, Object3D, Raycaster, Vector3 } from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { describe, expect, it } from 'vitest'
import { createBuildingMotion, defaultBuildingSettings } from '../../src/render/visuals/mapElementBuildings'

async function load(id:string){const b=readFileSync(new URL(`../../src/render/assets/elements/${id}.glb`,import.meta.url));return (await new GLTFLoader().parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'')).scene}
function nodes(root:Object3D,key:string){const a:Object3D[]=[];root.traverse((o)=>{if(o.userData[key]!==undefined)a.push(o)});return a}
function meshes(root:Object3D){const a:Mesh[]=[];root.traverse((o)=>{if(o instanceof Mesh)a.push(o)});return a}
function active(root:Object3D){return meshes(root).filter((m)=>{let o:Object3D|null=m;while(o){if(!o.visible)return false;o=o.parent}return true})}
function snap(root:Group){const a:unknown[]=[];root.traverse((o)=>a.push([o.visible,...o.position.toArray(),...o.quaternion.toArray()]));return JSON.stringify(a)}
function settle(motion:NonNullable<ReturnType<typeof createBuildingMotion>>,progress:number,tier:1|2=1){motion.setSettings({...defaultBuildingSettings,progress,tier,working:false});for(let i=0;i<180;i++)motion.update(1/60,false)}

describe('industrial assets and railway clearances',()=>{
  for(const id of ['train-station','factory']){
    it(`${id} assembles real parts, preserves sockets and exposes an inspectable interior`,async()=>{
      const model=await load(id),motion=createBuildingMotion(model)!,parts=nodes(model,'buildStart'),root=nodes(model,'buildingType')[0],ports=nodes(model,'connectionKind'),anchors=ports.map((o)=>o.position.toArray())
      expect(parts.length).toBeGreaterThan(35);let previous=0
      for(const progress of [0,.25,.50,.78,1]){
        settle(motion,progress)
        const count=parts.filter((o)=>o.visible&&!o.userData.buildingTemporary).length
        expect(count).toBeGreaterThanOrEqual(previous);previous=count
        if(progress===0)expect(count).toBe(1)
        expect(root.scale.toArray()).toEqual([1,1,1]);expect(ports.map((o)=>o.position.toArray())).toEqual(anchors)
      }
      expect(parts.filter((o)=>o.userData.buildingTemporary).every((o)=>!o.visible)).toBe(true)
      const upgrades=parts.filter((o)=>o.userData.buildingTier===2);expect(upgrades.length).toBeGreaterThan(0);expect(upgrades.every((o)=>!o.visible)).toBe(true)
      settle(motion,1,2);expect(upgrades.every((o)=>o.visible)).toBe(true)
      const covers=nodes(model,'inspectionCover');expect(covers.length).toBeGreaterThan(10)
      for(const cover of covers)cover.visible=false
      motion.update(.1,true);expect(covers.every((o)=>!o.visible)).toBe(true)
    })
    it(`${id} freezes mechanisms and automatic construction when paused`,async()=>{
      const model=await load(id),motion=createBuildingMotion(model)!
      motion.update(0,true);const before=snap(model);motion.update(.4,true);expect(snap(model)).not.toBe(before)
      const working=snap(model);motion.update(1,false);expect(snap(model)).toBe(working)
      motion.setSettings({...defaultBuildingSettings,speed:0});motion.update(1,true);expect(snap(model)).toBe(working)
      motion.setSettings({...defaultBuildingSettings,working:false});motion.update(1,true);expect(snap(model)).toBe(working)
      settle(motion,0);motion.setSettings({...defaultBuildingSettings,progress:0,automatic:true})
      const state={...motion.update(0,false)};motion.update(1,false);expect(motion.state).toEqual(state)
      for(let i=0;i<2100;i++)motion.update(1/60,true)
      expect(motion.state.progress).toBe(1)
    })
  }
  it('keeps the moving belt splices on the actual closed pulley path at the rim speed',async()=>{
    const model=await load('factory'),motion=createBuildingMotion(model)!,parts=nodes(model,'buildStart'),splices=parts.filter((o)=>o.userData.buildingMotion==='belt-loop'),pulleys=parts.filter((o)=>o.name.startsWith('BeltPulley')),spindle=parts.find((o)=>o.name==='LatheSpindle')!
    expect(splices).toHaveLength(8);expect(pulleys).toHaveLength(2)
    motion.update(0,true);model.updateMatrixWorld(true)
    const belt=parts.find((o)=>o.name==='DriveBelt')!,bounds=new Box3().setFromObject(belt,true)
    for(let frame=0;frame<140;frame++){
      const before=splices.map((o)=>o.position.clone()),q=pulleys[0].quaternion.clone(),sq=spindle.quaternion.clone()
      motion.update(.04,true);model.updateMatrixWorld(true)
      const angle=q.angleTo(pulleys[0].quaternion)
      expect(angle).toBeCloseTo(1.8*.6*.04,5);expect(sq.angleTo(spindle.quaternion)).toBeCloseTo(angle,5)
      for(let i=0;i<splices.length;i++){
        const p=splices[i].getWorldPosition(new Vector3()),nearestX=Math.max(-1.35,Math.min(1.35,p.x))
        expect(Math.hypot(p.x-nearestX,p.y-1.1)).toBeCloseTo(.38,5)
        expect(p.z).toBeCloseTo(.94,5);expect(p.z).toBeGreaterThan(bounds.min.z);expect(p.z).toBeLessThan(bounds.max.z)
        expect(p.distanceTo(before[i])/(.04*.6)).toBeCloseTo(.38*1.8,3)
        expect(p.x).toBeGreaterThanOrEqual(bounds.min.x-1e-5);expect(p.x).toBeLessThanOrEqual(bounds.max.x+1e-5)
        const geometryCenter=new Box3().setFromObject(splices[i],true).getCenter(new Vector3());expect(geometryCenter.distanceTo(p)).toBeLessThan(1e-5)
      }
    }
  })
  it('keeps both rail heads at socket height and preserves the existing narrow-gauge profile',async()=>{
    const station=await load('train-station'),route=await load('rail-track'),motion=createBuildingMotion(station)!
    settle(motion,1);station.updateMatrixWorld(true)
    const ports=nodes(station,'connectionKind').filter((o)=>o.userData.connectionKind==='rail'),rail=nodes(station,'buildStart').filter((o)=>o.name.startsWith('RailCourse'))
    expect(ports).toHaveLength(2)
    const routeRoot=nodes(route,'routeKind')[0],root=nodes(station,'buildingType')[0]
    expect(root.userData.gauge).toBe(routeRoot.userData.gauge);expect(root.userData.railCenterSpacing).toBe(routeRoot.userData.railCenterSpacing)
    for(const port of ports){expect(port.userData.profile).toBe(nodes(route,'routePort')[0].userData.profile);expect(port.position.y).toBeCloseTo(.28,5)}
    expect(new Vector3().fromArray(ports[0].userData.normalGltf).dot(new Vector3().fromArray(ports[1].userData.normalGltf))).toBe(-1)
    for(const z of [-3.6,-2,0,2,3.6])for(const x of [1.04,1.76]){
      const hit=new Raycaster(new Vector3(x,2,z),new Vector3(0,-1,0)).intersectObjects(rail,true)[0]
      expect(hit).toBeDefined();expect(hit.point.y).toBeCloseTo(.28,5)
    }
    for(const z of [-3,0,3])expect(new Raycaster(new Vector3(1.4,2,z),new Vector3(0,-1,0)).intersectObjects(rail,true)).toHaveLength(0)
  })
  it('supports the flywheel shaft in a sleeve outside the moving wheel plane',async()=>{
    const model=await load('factory'),motion=createBuildingMotion(model)!,parts=nodes(model,'buildStart'),bearing=parts.find((o)=>o.name==='FrontBearing')!,wheel=parts.find((o)=>o.name==='Flywheel')!
    settle(motion,1);model.updateMatrixWorld(true)
    const support=new Box3().setFromObject(bearing,true),rotor=new Box3().setFromObject(wheel,true)
    expect(support.min.y).toBeCloseTo(.22,5);expect(support.max.y).toBeGreaterThan(1.1)
    expect(support.intersectsBox(rotor)).toBe(false)
    const axial=new Raycaster(new Vector3(-1.35,1.1,2),new Vector3(0,0,-1),0,.7)
    expect(axial.intersectObjects(meshes(bearing),false)).toHaveLength(0)
    const rim=new Raycaster(new Vector3(-1.35,1.21,2),new Vector3(0,0,-1),0,.7)
    expect(rim.intersectObjects(meshes(bearing),false).length).toBeGreaterThan(0)
  })
  it('fits the actual locomotive and freight wagon between the platform and signal along the complete track',async()=>{
    const station=await load('train-station'),motion=createBuildingMotion(station)!
    settle(motion,1,2);station.updateMatrixWorld(true)
    const obstructions=nodes(station,'buildStart').filter((o)=>o.visible&&!o.name.startsWith('Track')&&!o.name.startsWith('Rail'))
    for(const id of ['steam-locomotive','freight-wagon']){
      const vehicle=await load(id)
      for(const z of [-2.8,-1.4,0,1.4,2.8]){
        vehicle.position.set(1.4,.28,z);vehicle.updateMatrixWorld(true)
        const envelope=new Box3().setFromObject(vehicle,true)
        for(const part of obstructions){
          const box=new Box3().setFromObject(part,true)
          expect(envelope.intersectsBox(box),`${id} hits ${part.name} at ${z}`).toBe(false)
        }
      }
    }
  })
  it('provides a continuous ramp and clear boarding path rather than a step hidden under paving',async()=>{
    const model=await load('train-station'),motion=createBuildingMotion(model)!
    settle(motion,1,2);model.updateMatrixWorld(true);const objects=active(model)
    let height=.2
    for(let i=0;i<=25;i++){
      const z=3.79-i*3.79/25
      const hit=new Raycaster(new Vector3(.25,1.7,z),new Vector3(0,-1,0)).intersectObjects(objects,false)[0]
      expect(hit).toBeDefined();expect(hit.point.y).toBeGreaterThanOrEqual(height-.001);expect(hit.point.y-height).toBeLessThan(.06);height=hit.point.y
      expect(new Raycaster(new Vector3(.25,1.2,z),new Vector3(1,0,0),0,.42).intersectObjects(objects,false)).toHaveLength(0)
    }
  })
  it('drives separate clock hands at twelve-to-one speed and keeps their centers fixed',async()=>{
    const model=await load('train-station'),motion=createBuildingMotion(model)!,parts=nodes(model,'buildStart'),minute=parts.find((o)=>o.name==='MinuteHand')!,hour=parts.find((o)=>o.name==='HourHand')!
    motion.update(0,true);const mq=minute.quaternion.clone(),hq=hour.quaternion.clone(),p=minute.position.clone()
    motion.update(.5,true)
    expect(mq.angleTo(minute.quaternion)/hq.angleTo(hour.quaternion)).toBeCloseTo(12,5);expect(minute.position).toEqual(p)
  })
  it('leaves a real cargo opening from the upgraded dock into the factory',async()=>{
    const model=await load('factory'),motion=createBuildingMotion(model)!
    settle(motion,1,2);model.updateMatrixWorld(true)
    const port=nodes(model,'connectionKind').find((o)=>o.userData.connectionKind==='cargo')!,point=port.getWorldPosition(new Vector3()),objects=active(model)
    expect(point.z).toBeCloseTo(.22,5)
    for(const height of [.60,.95,1.40])for(const offset of [-.18,0,.18]){
      const ray=new Raycaster(new Vector3(point.x,height,point.z+offset),new Vector3(1,0,0),0,1.75)
      expect(ray.intersectObjects(objects,false).map((hit)=>hit.object.name)).toEqual([])
    }
  })
  it('changes semaphore aspect smoothly, freezes it and resets it before construction',async()=>{
    const model=await load('train-station'),motion=createBuildingMotion(model)!,arm=nodes(model,'buildStart').find((o)=>o.userData.buildingMotion==='semaphore')!
    motion.update(0,true);const closed=arm.quaternion.clone(),position=arm.position.clone()
    motion.setSettings({...defaultBuildingSettings,gateOpen:true});motion.update(.1,true)
    expect(motion.state.access).toBeGreaterThan(0);expect(motion.state.access).toBeLessThan(1)
    const paused=snap(model);motion.update(1,false);expect(snap(model)).toBe(paused)
    for(let i=0;i<400;i++)motion.update(1/60,true)
    expect(motion.state.access).toBe(1);expect(closed.angleTo(arm.quaternion)).toBeCloseTo(Math.PI/4,5);expect(arm.position).toEqual(position)
    motion.setSettings({...defaultBuildingSettings,gateOpen:false});for(let i=0;i<400;i++)motion.update(1/60,true)
    expect(motion.state.access).toBe(0);expect(closed.angleTo(arm.quaternion)).toBeLessThan(1e-6)
    settle(motion,.5);expect(motion.state.access).toBe(0)
  })
  it('grounds front platform supports and seats stacked crates on the loading pallet',async()=>{
    const station=await load('train-station'),factory=await load('factory')
    for(const model of [station,factory]){settle(createBuildingMotion(model)!,1,2);model.updateMatrixWorld(true)}
    const parts=nodes(station,'buildStart'),mast=parts.find((o)=>o.name==='SignalMast')!
    expect(new Box3().setFromObject(mast,true).min.y).toBeCloseTo(0,5)
    for(const [name,minZ]of [['PlatformCanopyFrame',2.9],['PlatformAmenities',2.4]] as const){
      const points=meshes(parts.find((o)=>o.name===name)!).flatMap((mesh)=>{
        const p=mesh.geometry.getAttribute('position');return Array.from({length:p.count},(_,i)=>new Vector3().fromBufferAttribute(p,i).applyMatrix4(mesh.matrixWorld))
      }).filter((p)=>p.z>minZ)
      expect(points.length).toBeGreaterThan(10);expect(Math.min(...points.map((p)=>p.y))).toBeCloseTo(.20,5)
    }
    const dock=nodes(factory,'buildStart').find((o)=>o.name==='LoadingDock')!,crates=meshes(dock).filter((m)=>!Array.isArray(m.material)&&m.material.name==='wood')
    expect(crates.length).toBeGreaterThan(0)
    const bounds=new Box3();for(const mesh of crates)bounds.union(new Box3().setFromObject(mesh,true))
    expect(bounds.min.y).toBeCloseTo(.43,5);expect(bounds.max.y).toBeCloseTo(1.31,5)
  })
})
