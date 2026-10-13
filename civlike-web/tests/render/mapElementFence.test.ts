import { readFileSync } from 'node:fs'
import { Box3, Mesh, Object3D, Quaternion, Raycaster, Vector3 } from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { describe, expect, it } from 'vitest'
import { buildingStage, createBuildingMotion, defaultBuildingSettings } from '../../src/render/visuals/mapElementBuildings'

async function load() { const b=readFileSync(new URL('../../src/render/assets/elements/fence.glb',import.meta.url));return (await new GLTFLoader().parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'')).scene }
function nodes(root:Object3D,key:string,value?:unknown) {const found:Object3D[]=[];root.traverse((o)=>{if(value===undefined ? o.userData[key]!==undefined : o.userData[key]===value)found.push(o)});return found}
function visible(o:Object3D) {for(let p:Object3D|null=o;p;p=p.parent)if(!p.visible)return false;return true}
function meshes(root:Object3D) {const result:Mesh[]=[];root.traverse((o)=>{if(o instanceof Mesh&&visible(o))result.push(o)});return result}
type Motion=NonNullable<ReturnType<typeof createBuildingMotion>>
function advance(m:Motion,seconds:number,playing=true) {for(let i=0;i<seconds*60;i++)m.update(1/60,playing)}
function snapshot(root:Object3D) {return nodes(root,'buildStart').map((o)=>[o.visible,...o.position.toArray(),...o.quaternion.toArray(),...o.scale.toArray()])}

describe('farm fence and gravity latch',()=>{
  it('assembles without root scaling, reverses upgrades and freezes automatic construction',async()=>{
    const model=await load(),m=createBuildingMotion(model)!,parts=nodes(model,'buildStart'),counts=[]
    for(const progress of [0,.30,.52,.78,1]) {
      m.setSettings({...defaultBuildingSettings,progress});advance(m,3,false)
      counts.push(parts.filter(visible).length)
      expect(model.getObjectByName('BuildingRoot')!.scale.toArray()).toEqual([1,1,1])
    }
    expect(new Set(counts).size).toBe(5)
    expect(buildingStage(.3,'fence')).toBe('立柱')
    const pickets=parts.filter((o)=>o.userData.buildingTier===2)
    expect(pickets).toHaveLength(16);expect(pickets.every((o)=>!visible(o))).toBe(true)
    m.setSettings({...defaultBuildingSettings,tier:2});m.update(0,false);expect(pickets.every(visible)).toBe(true)
    m.setSettings({...defaultBuildingSettings,progress:0});advance(m,3,false)
    m.setSettings({...defaultBuildingSettings,progress:0,automatic:true});advance(m,2)
    const paused=snapshot(model);advance(m,1,false);expect(snapshot(model)).toEqual(paused)
    advance(m,34);expect(m.state.progress).toBe(1)
    expect(parts.filter((o)=>o.userData.buildingTemporary).every((o)=>!visible(o))).toBe(true)
  })

  it('lifts the latch before opening and closes the gate before dropping it',async()=>{
    const model=await load(),m=createBuildingMotion(model)!,gate=nodes(model,'buildingMotion','swing-gate')[0],latch=nodes(model,'buildingMotion','gate-latch')[0]
    const hinge=gate.position.clone(),gateClosed=gate.quaternion.clone().normalize(),latchClosed=latch.quaternion.clone().normalize()
    expect(latch.parent).toBe(gate)
    m.setSettings({...defaultBuildingSettings,gateOpen:true,speed:1})
    m.update(.025,true)
    expect(m.state.access).toBeLessThan(.2)
    expect(gate.quaternion.clone().normalize().angleTo(gateClosed)).toBeLessThan(.00001)
    expect(latch.quaternion.clone().normalize().angleTo(latchClosed)).toBeGreaterThan(.1)
    advance(m,4);expect(m.state.access).toBe(1)
    const expected=gateClosed.clone().multiply(new Quaternion().setFromAxisAngle(new Vector3(0,1,0),-Math.PI/2))
    expect(gate.quaternion.clone().normalize().angleTo(expected)).toBeLessThan(.00001)
    expect(gate.position.distanceTo(hinge)).toBeLessThan(.000001)
    m.setSettings({...defaultBuildingSettings,speed:1})
    while(m.state.access>.19)m.update(.01,true)
    expect(gate.quaternion.clone().normalize().angleTo(gateClosed)).toBeLessThan(.00001)
    expect(latch.quaternion.clone().normalize().angleTo(latchClosed)).toBeGreaterThan(1)
    advance(m,4);expect(latch.quaternion.clone().normalize().angleTo(latchClosed)).toBeLessThan(.00001)
  })

  it('keeps the full moving meshes within bounds and the open pedestrian passage clear',async()=>{
    const model=await load(),m=createBuildingMotion(model)!,root=model.getObjectByName('BuildingRoot')!
    const bounds=new Box3(new Vector3().fromArray(root.userData.animationBoundsMin),new Vector3().fromArray(root.userData.animationBoundsMax))
    m.setSettings({...defaultBuildingSettings,gateOpen:true,speed:1,tier:2})
    for(let frame=0;frame<180;frame++) {
      m.update(1/60,true);model.updateMatrixWorld(true)
      for(const mesh of meshes(model))expect(bounds.containsBox(new Box3().setFromObject(mesh,true)),`${mesh.name}/${frame}`).toBe(true)
    }
    for(const x of [-.74,-.4,0,.4,.74])for(const height of [.1,.35,.75,1.1,1.5]) {
      expect(new Raycaster(new Vector3(x,height,-1.9),new Vector3(0,0,1),0,3.8).intersectObjects(meshes(model),false)).toHaveLength(0)
    }
    m.setSettings({...defaultBuildingSettings,speed:1});advance(m,4);model.updateMatrixWorld(true)
    expect(new Raycaster(new Vector3(0,.76,-1.9),new Vector3(0,0,1),0,3.8).intersectObjects(meshes(model),false).length).toBeGreaterThan(0)
  })

  it('matches actual rail ends when two modules mate, without overlapping footings',async()=>{
    const first=await load(),second=await load()
    for(const model of [first,second])createBuildingMotion(model)!.update(0,false)
    const a=first.getObjectByName('FenceEndRight')!,b=second.getObjectByName('FenceEndLeft')!
    expect(a.userData.connectionProfile).toBe(b.userData.connectionProfile)
    second.position.x=a.position.x-b.position.x;first.updateMatrixWorld(true);second.updateMatrixWorld(true)
    expect(a.getWorldPosition(new Vector3()).distanceTo(b.getWorldPosition(new Vector3()))).toBeLessThan(.00001)
    for(const height of a.userData.railHeights as number[]) {
      const left=new Raycaster(new Vector3(3.5,height,0),new Vector3(-1,0,0),0,.3).intersectObjects(meshes(first),false)[0]
      const right=new Raycaster(new Vector3(3.2,height,0),new Vector3(1,0,0),0,.3).intersectObjects(meshes(second),false)[0]
      expect(left).toBeDefined();expect(right).toBeDefined();expect(left.point.distanceTo(right.point)).toBeLessThan(.00001)
    }
    expect(new Box3().setFromObject(first.getObjectByName('Footings')!,true).intersectsBox(new Box3().setFromObject(second.getObjectByName('Footings')!,true))).toBe(false)
  })

  it('freezes access and geometry on pause, zero speed and disabled operation',async()=>{
    const model=await load(),m=createBuildingMotion(model)!
    m.setSettings({...defaultBuildingSettings,gateOpen:true,speed:1});advance(m,.2)
    const stopped=snapshot(model),access=m.state.access
    advance(m,1,false);expect(snapshot(model)).toEqual(stopped)
    m.setSettings({...defaultBuildingSettings,gateOpen:true,speed:0});advance(m,1);expect(snapshot(model)).toEqual(stopped)
    m.setSettings({...defaultBuildingSettings,gateOpen:true,working:false});advance(m,1);expect(snapshot(model)).toEqual(stopped)
    expect(m.state.access).toBe(access)
  })
})
