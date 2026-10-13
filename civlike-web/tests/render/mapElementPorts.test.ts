import { readFileSync } from 'node:fs'
import { Box3, Mesh, Object3D, Quaternion, Raycaster, Vector3 } from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { describe, expect, it } from 'vitest'
import { buildingStage, createBuildingMotion, defaultBuildingSettings } from '../../src/render/visuals/mapElementBuildings'

async function load(id:string) {const b=readFileSync(new URL(`../../src/render/assets/elements/${id}.glb`,import.meta.url));return (await new GLTFLoader().parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'')).scene}
function nodes(root:Object3D,key:string,value?:unknown) {const result:Object3D[]=[];root.traverse((o)=>{if(value===undefined ? o.userData[key]!==undefined : o.userData[key]===value)result.push(o)});return result}
function visible(o:Object3D) {for(let p:Object3D|null=o;p;p=p.parent)if(!p.visible)return false;return true}
function meshes(root:Object3D) {const result:Mesh[]=[];root.traverse((o)=>{if(o instanceof Mesh&&visible(o))result.push(o)});return result}
type Motion=NonNullable<ReturnType<typeof createBuildingMotion>>
function advance(m:Motion,time:number,playing=true) {for(let i=0;i<time*60;i++)m.update(1/60,playing)}
function settle(m:Motion,progress:number,tier:1|2=1) {m.setSettings({...defaultBuildingSettings,progress,tier});advance(m,3,false)}
function snapshot(root:Object3D) {return nodes(root,'buildStart').map((o)=>[o.visible,...o.position.toArray(),...o.quaternion.toArray(),...o.scale.toArray()])}

describe('warehouse quay and pile-supported jetty',()=>{
  for(const id of ['harbor','dock']) {
    it(`${id} assembles five stages, preserves sockets and reverses upgrades`,async()=>{
      const model=await load(id),m=createBuildingMotion(model)!,parts=nodes(model,'buildStart'),ports=nodes(model,'connectionKind')
      const origins=ports.map((o)=>o.position.clone()),counts=[]
      for(const progress of [0,.30,.52,.78,1]) {
        settle(m,progress);counts.push(parts.filter(visible).length)
        expect(ports.every((p,i)=>p.position.equals(origins[i]))).toBe(true)
        expect(model.getObjectByName('BuildingRoot')!.scale.toArray()).toEqual([1,1,1])
      }
      expect(new Set(counts).size).toBe(5)
      const upgrades=parts.filter((o)=>o.userData.buildingTier===2)
      expect(upgrades.length).toBeGreaterThan(0);expect(upgrades.every((o)=>!o.visible)).toBe(true)
      settle(m,1,2);expect(upgrades.every(visible)).toBe(true)
      expect(parts.filter((o)=>o.userData.buildingTemporary).every((o)=>!o.visible)).toBe(true)
      settle(m,.30);expect(parts.some((o)=>o.userData.buildingTemporary&&o.visible)).toBe(true)
      settle(m,0);m.setSettings({...defaultBuildingSettings,progress:0,automatic:true});advance(m,2)
      const paused=snapshot(model);advance(m,1,false);expect(snapshot(model)).toEqual(paused)
      advance(m,34);expect(m.state.progress).toBe(1)
    })
    it(`${id} synchronizes actual cable endpoints, suspended cargo and wheel arc lengths`,async()=>{
      const model=await load(id),m=createBuildingMotion(model)!;settle(m,1,2)
      m.setSettings({...defaultBuildingSettings,speed:1,tier:2})
      const cable=nodes(model,'buildingMotion','hoist-cable')[0],cargo=nodes(model,'buildingMotion','hoist-load')[0]
      const wheels=nodes(model,'buildingMotion','hoist-wheel'),top=cable.position.clone(),bottom=cargo.position.clone()
      const rotations=wheels.map((o)=>o.quaternion.clone().normalize()),positions=wheels.map((o)=>o.position.clone())
      const root=model.getObjectByName('BuildingRoot')!,bounds=new Box3(new Vector3().fromArray(root.userData.animationBoundsMin),new Vector3().fromArray(root.userData.animationBoundsMax))
      let maximum=0,minimum=Infinity
      for(let frame=0;frame<110;frame++) {
        m.update(.1,true);model.updateMatrixWorld(true)
        const lift=cargo.position.y-bottom.y,rope=new Box3().setFromObject(cable,true)
        maximum=Math.max(maximum,lift);minimum=Math.min(minimum,lift)
        expect(cable.position.distanceTo(top)).toBeLessThan(.00001)
        expect(rope.max.y).toBeCloseTo(top.y,5)
        expect(rope.min.y).toBeCloseTo(cargo.position.y,5)
        expect(rope.max.y-rope.min.y+lift).toBeCloseTo(cable.userData.hoistLength,5)
        expect(cable.scale.x).toBe(1);expect(cable.scale.z).toBe(1);expect(cable.scale.y).toBeGreaterThan(.25)
        for(const [i,wheel]of wheels.entries()) {
          expect(wheel.position.equals(positions[i])).toBe(true)
          const expected=rotations[i].clone().multiply(new Quaternion().setFromAxisAngle(new Vector3().fromArray(wheel.userData.motionAxis),lift/wheel.userData.hoistRadius)).normalize()
          expect(wheel.quaternion.clone().normalize().angleTo(expected)).toBeLessThan(.00001)
        }
        for(const mesh of meshes(model)) {
          const box=new Box3().setFromObject(mesh,true)
          expect(bounds.containsBox(box),`${id}/${mesh.name}/${frame}`).toBe(true)
        }
      }
      expect(maximum).toBeGreaterThan(cargo.userData.hoistTravel*.99)
      expect(minimum).toBeLessThan(.002)
    })
    it(`${id} freezes the entire mechanism on pause, zero speed and disabled operation`,async()=>{
      const model=await load(id),m=createBuildingMotion(model)!;settle(m,1,2)
      const start=snapshot(model);advance(m,2);expect(snapshot(model)).not.toEqual(start)
      const stopped=snapshot(model);advance(m,2,false);expect(snapshot(model)).toEqual(stopped)
      m.setSettings({...defaultBuildingSettings,speed:0,tier:2});advance(m,2);expect(snapshot(model)).toEqual(stopped)
      m.setSettings({...defaultBuildingSettings,working:false,tier:2});advance(m,2);expect(snapshot(model)).toEqual(stopped)
    })
    it(`${id} connects its land socket to a continuous ramp and actual deck surface`,async()=>{
      const model=await load(id),m=createBuildingMotion(model)!;settle(m,1,2);model.updateMatrixWorld(true)
      const entry=model.getObjectByName('LandEntrance')!,x=entry.position.x,start=-entry.position.z
      const deck=meshes(model)
      for(const offset of [-.50,0,.50])for(let step=0;step<=20;step++) {
        const y=start+.01+step*.098,height=.08+(y-start)*.20
        const hit=new Raycaster(new Vector3(x+offset,height+.025,-y),new Vector3(0,-1,0),0,.055).intersectObjects(deck,false)[0]
        expect(hit,`${id} ramp ${offset}/${step}`).toBeDefined()
        expect(hit.point.y).toBeCloseTo(height,4)
      }
      const joined=new Raycaster(new Vector3(x,.51,-(start+2.04)),new Vector3(0,-1,0),0,.05).intersectObjects(deck,false)[0]
      expect(joined).toBeDefined();expect(joined.point.y).toBeCloseTo(.48,5)
    })
    it(`${id} provides two hull-clear berths compatible with the real river barge dimensions`,async()=>{
      const model=await load(id),m=createBuildingMotion(model)!;settle(m,1,2);model.updateMatrixWorld(true)
      const barge=await load('river-barge'),shipRoot=nodes(barge,'vesselKind')[0],shipBox=new Box3().setFromObject(barge,true),size=shipBox.getSize(new Vector3())
      const berths=nodes(model,'connectionKind','berth'),solids=meshes(model)
      expect(berths).toHaveLength(2)
      for(const berth of berths) {
        expect(berth.userData.profile).toBe(shipRoot.userData.routeProfile)
        expect(berth.userData.waterline).toBe(shipRoot.userData.waterline)
        expect(berth.userData.berthLength).toBeGreaterThan(size.z+.20)
        expect(berth.userData.clearWidth).toBeGreaterThan(size.x+.10)
        expect(berth.userData.waterDepth).toBeGreaterThan(-shipBox.min.y+.10)
        const center=new Vector3().fromArray(berth.userData.vesselCenterGltf),normal=new Vector3().fromArray(berth.userData.normalGltf)
        const along=new Vector3(0,0,1).applyAxisAngle(new Vector3(0,1,0),berth.userData.vesselYaw)
        // Sample the lower-hull envelope through real piles, fenders and quay triangles.
        for(const length of [-1.95,-1.3,0,1.3,1.95])for(const height of [-.45,-.20,.05,.30]) {
          const origin=center.clone().addScaledVector(along,length).addScaledVector(normal,-.77);origin.y=height
          const hits=new Raycaster(origin,normal,0,1.54).intersectObjects(solids,false)
          expect(hits.map((hit)=>hit.object.name),`${id}/${berth.name}/${length}/${height}`).toEqual([])
        }
      }
    })
  }
  it('opens a real warehouse loading passage and keeps the interior available for cutaway',async()=>{
    const model=await load('harbor'),m=createBuildingMotion(model)!;settle(m,1,2)
    m.setSettings({...defaultBuildingSettings,speed:1,tier:2});advance(m,5);model.updateMatrixWorld(true)
    const entry=model.getObjectByName('WarehouseEntrance')!,solids=meshes(model)
    for(const dx of [-.70,0,.70])for(const h of [.12,1,1.75]) {
      const p=entry.getWorldPosition(new Vector3()).add(new Vector3(dx,h,-.5))
      expect(new Raycaster(p,new Vector3(0,0,1),0,2.9).intersectObjects(solids,false)).toHaveLength(0)
    }
    const roof=nodes(model,'inspectionCover');expect(roof.length).toBeGreaterThan(0)
    for(const mesh of roof)mesh.visible=false
    advance(m,2)
    expect(roof.every((o)=>!o.visible)).toBe(true)
    expect(buildingStage(.5,'dock')).toBe('桥面')
    expect(buildingStage(.5,'harbor')).toBe('库房')
  })
})
