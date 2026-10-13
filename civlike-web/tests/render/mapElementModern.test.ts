import { readFileSync } from 'node:fs'
import { Box3, Group, Mesh, Object3D, Raycaster, Vector3 } from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { describe, expect, it } from 'vitest'
import { createBuildingMotion, defaultBuildingSettings } from '../../src/render/visuals/mapElementBuildings'

async function load(id:string) {const b=readFileSync(new URL(`../../src/render/assets/elements/${id}.glb`,import.meta.url));return (await new GLTFLoader().parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'')).scene}
function nodes(root:Object3D,key:string) {const result:Object3D[]=[];root.traverse((o)=>{if(o.userData[key]!==undefined)result.push(o)});return result}
function meshes(root:Object3D) {const result:Mesh[]=[];root.traverse((o)=>{if(o instanceof Mesh)result.push(o)});return result}
function visible(node:Object3D) {for(let p:Object3D|null=node;p;p=p.parent)if(!p.visible)return false;return true}
type Motion=NonNullable<ReturnType<typeof createBuildingMotion>>
function advance(m:Motion,seconds:number,playing=true) {for(let i=0;i<seconds*60;i++)m.update(1/60,playing)}
function settle(m:Motion,progress:number,tier:1|2=1) {m.setSettings({...defaultBuildingSettings,progress,tier});advance(m,3,false)}
function snapshot(root:Group) {return JSON.stringify(nodes(root,'buildStart').map((p)=>[p.visible,...p.position.toArray(),...p.quaternion.toArray()]))}
function points(root:Object3D) {root.updateWorldMatrix(true,true);return meshes(root).filter(visible).flatMap((mesh)=>{const p=mesh.geometry.getAttribute('position');return Array.from({length:p.count},(_,i)=>new Vector3().fromBufferAttribute(p,i).applyMatrix4(mesh.matrixWorld))})}

describe('modern housing and hospital',()=>{
  for(const id of ['apartment','hospital']) {
    it(`${id} assembles distinct floors, upgrades and scaffolds without scaling`,async()=>{
      const model=await load(id),m=createBuildingMotion(model)!,parts=nodes(model,'buildStart'),counts=[]
      const port=nodes(model,'connectionKind')[0],anchor=port.position.clone()
      for(const progress of [0,.30,.52,.78,1]) {
        settle(m,progress);counts.push(parts.filter((p)=>p.visible).length)
        expect(port.position.equals(anchor)).toBe(true)
        expect(model.getObjectByName('BuildingRoot')!.scale.toArray()).toEqual([1,1,1])
      }
      expect(new Set(counts).size).toBe(5)
      const upgrades=parts.filter((p)=>p.userData.buildingTier===2)
      expect(upgrades.length).toBeGreaterThan(0);expect(upgrades.every((p)=>!p.visible)).toBe(true)
      settle(m,1,2);expect(upgrades.every((p)=>p.visible)).toBe(true)
      expect(parts.filter((p)=>p.userData.buildingTemporary).every((p)=>!p.visible)).toBe(true)
      settle(m,0);m.setSettings({...defaultBuildingSettings,progress:0,automatic:true});advance(m,2)
      const stopped=snapshot(model);advance(m,1,false);expect(snapshot(model)).toBe(stopped)
      advance(m,34);expect(m.state.progress).toBe(1)
    })
    it(`${id} operates within authored bounds and preserves roof inspection while paused/stopped`,async()=>{
      const model=await load(id),m=createBuildingMotion(model)!,covers=nodes(model,'inspectionCover')
      expect(covers.length).toBeGreaterThan(2);covers.forEach((p)=>{p.visible=false})
      const initial=snapshot(model);advance(m,.7);expect(snapshot(model)).not.toBe(initial)
      const paused=snapshot(model);advance(m,1,false);expect(snapshot(model)).toBe(paused)
      m.setSettings({...defaultBuildingSettings,speed:0});advance(m,1);expect(snapshot(model)).toBe(paused)
      m.setSettings({...defaultBuildingSettings,working:false});advance(m,1);expect(snapshot(model)).toBe(paused)
      expect(covers.every((p)=>!p.visible)).toBe(true)
      covers.forEach((p)=>{p.visible=true})
      m.setSettings({...defaultBuildingSettings,speed:1,tier:2})
      const root=model.getObjectByName('BuildingRoot')!,bounds=new Box3(new Vector3().fromArray(root.userData.animationBoundsMin),new Vector3().fromArray(root.userData.animationBoundsMax))
      for(let frame=0;frame<120;frame++) {m.update(.1,true);expect(points(model).every((p)=>bounds.containsPoint(p)),`frame ${frame}`).toBe(true)}
    })
    it(`${id} keeps real wall openings and a continuous approach ramp`,async()=>{
      const model=await load(id),m=createBuildingMotion(model)!;settle(m,1);model.updateMatrixWorld(true)
      const walls=nodes(model,'buildStart').filter((p)=>p.name.startsWith('FrontWall')).flatMap(meshes)
      const front=id==='hospital'?3.4:3.3
      for(const x of [-.5,0,.5])for(const y of [.25,1.2,2.36]) {
        expect(new Raycaster(new Vector3(x,y,front+.3),new Vector3(0,0,-1),0,.6).intersectObjects(walls,false)).toHaveLength(0)
      }
      const ramps=nodes(model,'buildStart').filter((p)=>p.name==='EntranceRamp').flatMap(meshes)
      for(const t of [.02,.25,.5,.75,.98]) {
        const hit=new Raycaster(new Vector3(0,.4,front+2.4*(1-t)),new Vector3(0,-1,0)).intersectObjects(ramps,false)[0]
        expect(hit).toBeDefined();expect(hit.point.y).toBeCloseTo(.2*t,5)
      }
    })
    it(`${id} connects each stair tread to half and upper landings`,async()=>{
      const model=await load(id),m=createBuildingMotion(model)!;settle(m,1);model.updateMatrixWorld(true)
      const stairs=nodes(model,'buildStart').filter((p)=>p.name.startsWith('SwitchbackStair')).flatMap(meshes)
      const hospital=id==='hospital',count=hospital?8:9,storey=hospital?2.85:2.7,shift=hospital?6.2:0,first=hospital?-1.6:-1.88
      for(let level=0;level<(hospital?1:2);level++)for(let flight=0;flight<2;flight++)for(let step=0;step<count;step++) {
        const x=flight===0?-.62:.62,sourceY=shift+(flight===0?first+step*.28:.36-step*.28),height=.2+level*storey+flight*storey/2+(step+1)*storey/(2*count)
        const hit=new Raycaster(new Vector3(x,height+.02,-sourceY),new Vector3(0,-1,0),0,.08).intersectObjects(stairs,false)[0]
        expect(hit,`tread ${level}/${flight}/${step}`).toBeDefined();expect(hit.point.y).toBeCloseTo(height,5)
      }
      const all=meshes(model).filter(visible),height=.2+storey
      for(const sourceY of hospital?[3.28,3.45,4.30,4.47]:[-2.9,-2.2,-2.04,-2.0]) {
        const hit=new Raycaster(new Vector3(.62,height+.03,-sourceY),new Vector3(0,-1,0),0,.09).intersectObjects(all,false)[0]
        expect(hit,`landing ${sourceY}`).toBeDefined();expect(hit.point.y).toBeCloseTo(height,5)
      }
    })
  }
  it('opens the hospital sliding doors symmetrically, dwells and leaves both corridors unobstructed',async()=>{
    const model=await load('hospital'),m=createBuildingMotion(model)!,doors=nodes(model,'buildStart').filter((p)=>p.userData.buildingMotion==='sliding-door')
    expect(doors).toHaveLength(6)
    const rest=doors.map((p)=>p.position.clone())
    m.setSettings({...defaultBuildingSettings,speed:1});m.update(3,true)
    doors.forEach((p,i)=>expect(Math.abs(p.position.x-rest[i].x)).toBeCloseTo(.43,5))
    m.update(2,true);const opened=doors.map((p)=>p.position.clone())
    doors.forEach((p,i)=>expect(Math.abs(p.position.x-rest[i].x)).toBeCloseTo(.86,5))
    m.update(1,true);expect(doors.every((p,i)=>p.position.equals(opened[i]))).toBe(true)
    model.updateMatrixWorld(true);const solids=meshes(model).filter(visible)
    for(const floor of [.2,3.05])for(const x of [-.53,0,.53])for(const y of [.04,1.05,2.17]) {
      const start=floor===.2?3.75:3.02,length=floor===.2?7.42:6.69
      const hits=new Raycaster(new Vector3(x,floor+y,start),new Vector3(0,0,-1),0,length).intersectObjects(solids,false)
      expect(hits.map((hit)=>hit.object.name),`corridor ${floor}/${x}/${y}`).toEqual([])
    }
    m.update(3,true);expect(doors.every((p,i)=>p.position.equals(rest[i]))).toBe(true)
  })
  it('keeps apartment balcony doors away from the sofas at full opening',async()=>{
    const model=await load('apartment'),m=createBuildingMotion(model)!
    m.setSettings({...defaultBuildingSettings,speed:1});m.update(Math.PI*2,true);model.updateMatrixWorld(true)
    const doors=nodes(model,'buildStart').filter((p)=>p.name.startsWith('BalconyDoor'))
    expect(doors).toHaveLength(4)
    for(const door of doors) {
      const bounds=new Box3().setFromObject(door,true)
      expect(Math.max(Math.abs(bounds.min.x),Math.abs(bounds.max.x))).toBeLessThan(2.30)
    }
    const walls=nodes(model,'buildStart').filter((p)=>p.name.startsWith('FrontWall')).flatMap(meshes)
    for(const floor of [2.9,5.6])for(const x of [-2.75,2.75])for(const y of [.05,2.17]) {
      expect(new Raycaster(new Vector3(x,floor+y,3.55),new Vector3(0,0,-1),0,.5).intersectObjects(walls,false)).toHaveLength(0)
    }
  })
})
