import { readFileSync } from 'node:fs'
import { Group, Mesh, Object3D, Raycaster, Vector3 } from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { describe, expect, it } from 'vitest'
import { createBuildingMotion, defaultBuildingSettings } from '../../src/render/visuals/mapElementBuildings'

async function load(id:string){const b=readFileSync(new URL(`../../src/render/assets/elements/${id}.glb`,import.meta.url));return (await new GLTFLoader().parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'')).scene}
function nodes(root:Object3D,key:string){const list:Object3D[]=[];root.traverse((o)=>{if(o.userData[key]!==undefined)list.push(o)});return list}
function meshes(root:Object3D){const list:Mesh[]=[];root.traverse((o)=>{if(o instanceof Mesh)list.push(o)});return list}
function vertices(root:Object3D){root.updateWorldMatrix(true,true);return meshes(root).flatMap((m)=>{const p=m.geometry.getAttribute('position');return Array.from({length:p.count},(_,i)=>new Vector3().fromBufferAttribute(p,i).applyMatrix4(m.matrixWorld))})}
type Motion=NonNullable<ReturnType<typeof createBuildingMotion>>
function advance(m:Motion,seconds:number,playing=true){for(let i=0;i<seconds*60;i++)m.update(1/60,playing)}
function settle(m:Motion,progress:number,tier:1|2=1){m.setSettings({...defaultBuildingSettings,progress,tier});advance(m,3,false)}
function snapshot(model:Group){return JSON.stringify(nodes(model,'buildStart').map((p)=>[p.visible,...p.position.toArray(),...p.quaternion.toArray(),...meshes(p).flatMap((m)=>Array.from(m.geometry.attributes.position.array))]))}
function waterLevel(part:Object3D){const z=(part.userData.channelExtent as number[])[1];return Math.max(...vertices(part).filter((p)=>Math.abs(p.x)<.01&&Math.abs(p.z-z)<1e-5).map((p)=>p.y))}

describe('water infrastructure',()=>{
  for(const id of ['aqueduct','irrigation-channel']){
    it(`${id} constructs real pieces, upgrades and preserves its channel anchors`,async()=>{
      const model=await load(id),m=createBuildingMotion(model)!,parts=nodes(model,'buildStart'),ports=nodes(model,'connectionKind'),positions=ports.map((p)=>p.position.toArray())
      const counts=[]
      for(const progress of [0,.3,.52,.78,1]){settle(m,progress);counts.push(parts.filter((p)=>p.visible).length);expect(ports.map((p)=>p.position.toArray())).toEqual(positions);expect(model.scale.toArray()).toEqual([1,1,1])}
      expect(new Set(counts).size).toBe(5);expect(counts.every((n,i)=>i===0||n>counts[i-1])).toBe(true)
      const upgrade=parts.filter((p)=>p.userData.buildingTier===2);expect(upgrade.length).toBeGreaterThan(0);expect(upgrade.every((p)=>!p.visible)).toBe(true)
      settle(m,1,2);expect(upgrade.every((p)=>p.visible)).toBe(true)
      settle(m,0);m.setSettings({...defaultBuildingSettings,progress:0,automatic:true});advance(m,2)
      const paused=snapshot(model);advance(m,1,false);expect(snapshot(model)).toBe(paused);advance(m,34);expect(m.state.progress).toBe(1)
    })
    it(`${id} has nonflat travelling water contained by the channel, with exact pause`,async()=>{
      const model=await load(id),m=createBuildingMotion(model)!,water=nodes(model,'channelWater')
      m.update(0,true);const before=snapshot(model);advance(m,.45);expect(snapshot(model)).not.toBe(before)
      const paused=snapshot(model);advance(m,1,false);expect(snapshot(model)).toBe(paused)
      m.setSettings({...defaultBuildingSettings,speed:0});advance(m,1);expect(snapshot(model)).toBe(paused)
      m.setSettings({...defaultBuildingSettings,working:false});advance(m,1);expect(snapshot(model)).toBe(paused)
      for(const part of water){
        const points=vertices(part),bed=Number(part.userData.channelBed),top=points.filter((p)=>p.y>bed+.01)
        expect(top.length).toBeGreaterThan(100)
        expect(Math.max(...top.map((p)=>p.y))-Math.min(...top.map((p)=>p.y))).toBeGreaterThan(.003)
        expect(points.every((p)=>Number.isFinite(p.x)&&Number.isFinite(p.y)&&Number.isFinite(p.z)&&Math.abs(p.x)<.321&&p.y>=bed-1e-5&&p.y<bed+.24)).toBe(true)
        expect(points.filter((p)=>Math.abs(p.y-bed)<1e-5).length).toBeGreaterThan(20)
      }
    })
    it(`${id} has a solid bed at both ports rather than a blocked or unsupported outlet`,async()=>{
      const model=await load(id),m=createBuildingMotion(model)!,waterMeshes=new Set(nodes(model,'channelWater').flatMap(meshes))
      settle(m,1);model.updateMatrixWorld(true)
      const solid=meshes(model).filter((p)=>!waterMeshes.has(p)),ports=nodes(model,'connectionKind')
      expect(ports).toHaveLength(2)
      for(const port of ports){
        const center=port.getWorldPosition(new Vector3()),normal=new Vector3().fromArray(port.userData.normalGltf)
        expect(port.userData.profile).toBe('open-channel-064-v1')
        for(const x of [-.29,0,.29]){
          const origin=center.clone().addScaledVector(normal,-.005);origin.x=x;origin.y+=.30
          const hit=new Raycaster(origin,new Vector3(0,-1,0)).intersectObjects(solid,false)[0]
          expect(hit).toBeDefined();expect(hit.point.y).toBeCloseTo(center.y,5)
          origin.y=center.y+.20;expect(new Raycaster(origin,normal,0,.1).intersectObjects(solid,false)).toHaveLength(0)
        }
      }
    })
  }
  it('keeps three real arch openings below the elevated trough',async()=>{
    const model=await load('aqueduct');settle(createBuildingMotion(model)!,1,2);model.updateMatrixWorld(true)
    for(const z of [-2.5,0,2.5])for(const offset of [-.4,0,.4])expect(new Raycaster(new Vector3(-2,1,z+offset),new Vector3(1,0,0),0,4).intersectObjects(meshes(model),false)).toHaveLength(0)
  })
  it('lifts the sluice with a stationary handwheel and delayed downstream filling and draining',async()=>{
    const model=await load('irrigation-channel'),m=createBuildingMotion(model)!,parts=nodes(model,'buildStart'),gate=parts.find((p)=>p.userData.buildingMotion==='hydro-gate')!,wheel=parts.find((p)=>p.userData.buildingMotion==='hydro-wheel')!,water=nodes(model,'channelWater'),down=water.find((p)=>p.userData.channelWater==='downstream')!,up=water.find((p)=>p.userData.channelWater==='upstream')!
    m.update(0,false);expect(waterLevel(down)).toBeCloseTo(.145,5);expect(waterLevel(up)).toBeCloseTo(.325,5)
    const gateY=gate.position.y,wheelPosition=wheel.position.clone(),q=wheel.quaternion.clone()
    m.setSettings({...defaultBuildingSettings,gateOpen:true});advance(m,.30)
    expect(gate.position.y).toBeGreaterThan(gateY);expect(wheel.quaternion.angleTo(q)).toBeGreaterThan(.1);expect(wheel.position).toEqual(wheelPosition)
    expect(waterLevel(down)).toBeGreaterThan(.145);expect(waterLevel(down)).toBeLessThan(.145+.155*m.state.access)
    const paused=snapshot(model);advance(m,.7,false);expect(snapshot(model)).toBe(paused)
    advance(m,16);expect(m.state.access).toBe(1);expect(gate.position.y-gateY).toBeCloseTo(.36,6);expect(waterLevel(down)).toBeCloseTo(.30,4);expect(waterLevel(up)).toBeCloseTo(.30,5)
    const gateBottom=Math.min(...vertices(gate).map((p)=>p.y));expect(gateBottom).toBeGreaterThan(.44)
    m.setSettings({...defaultBuildingSettings,gateOpen:false});advance(m,.4)
    expect(waterLevel(down)).toBeLessThan(.30);expect(waterLevel(down)).toBeGreaterThan(.145+.155*m.state.access)
    advance(m,16);expect(m.state.access).toBe(0);expect(waterLevel(down)).toBeCloseTo(.145,4)
    m.setSettings({...defaultBuildingSettings,gateOpen:true});advance(m,16);settle(m,.52);expect(m.state.access).toBe(0);expect(down.visible).toBe(false)
    settle(m,1);expect(waterLevel(down)).toBeCloseTo(.145,4)
  })
  it('leaves open U-section guides for the sliding gate rather than intersecting solid posts',async()=>{
    const model=await load('irrigation-channel'),m=createBuildingMotion(model)!,frame=nodes(model,'buildStart').find((p)=>p.name==='SluiceFrame')!
    settle(m,1);model.updateMatrixWorld(true)
    for(const x of [-.345,.345])for(const y of [-.041,.041]){
      expect(new Raycaster(new Vector3(x,.2,y),new Vector3(0,1,0),0,.75).intersectObjects(meshes(frame),false)).toHaveLength(0)
    }
  })
  it('aligns actual water and bed end faces between high and low channel modules',async()=>{
    const aqueduct=await load('aqueduct'),irrigation=await load('irrigation-channel'),a=createBuildingMotion(aqueduct)!,b=createBuildingMotion(irrigation)!
    a.update(0,false);b.setSettings({...defaultBuildingSettings,gateOpen:true});advance(b,16)
    const out=nodes(aqueduct,'connectionKind').find((p)=>p.userData.flowRole==='outlet')!,inlet=nodes(irrigation,'connectionKind').find((p)=>p.userData.flowRole==='inlet')!
    expect(out.userData.profile).toBe(inlet.userData.profile)
    expect(new Vector3().fromArray(out.userData.normalGltf).dot(new Vector3().fromArray(inlet.userData.normalGltf))).toBe(-1)
    irrigation.position.copy(out.position).sub(inlet.position);irrigation.updateMatrixWorld(true);aqueduct.updateMatrixWorld(true)
    expect(out.getWorldPosition(new Vector3()).distanceTo(inlet.getWorldPosition(new Vector3()))).toBeLessThan(1e-5)
    const join=out.getWorldPosition(new Vector3()),objects=[...meshes(aqueduct),...meshes(irrigation)]
    for(const z of [join.z-.01,join.z+.01])for(const x of [-.25,0,.25]){
      const hit=new Raycaster(new Vector3(x,3,z),new Vector3(0,-1,0)).intersectObjects(objects,false)[0]
      expect(hit.point.y).toBeCloseTo(join.y+.18,3)
    }
  })
})
