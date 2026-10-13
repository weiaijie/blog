import { readFileSync } from 'node:fs'
import { Box3, Group, Mesh, Object3D, Raycaster, Vector3 } from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { describe, expect, it } from 'vitest'
import { buildingStage, createBuildingMotion, defaultBuildingSettings } from '../../src/render/visuals/mapElementBuildings'

async function load(id:string) {const b=readFileSync(new URL(`../../src/render/assets/elements/${id}.glb`,import.meta.url));return (await new GLTFLoader().parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'')).scene}
function nodes(root:Object3D,key:string) {const result:Object3D[]=[];root.traverse((o)=>{if(o.userData[key]!==undefined)result.push(o)});return result}
function meshes(root:Object3D) {const result:Mesh[]=[];root.traverse((o)=>{if(o instanceof Mesh)result.push(o)});return result}
function visible(node:Object3D) {for(let p:Object3D|null=node;p;p=p.parent)if(!p.visible)return false;return true}
type Motion=NonNullable<ReturnType<typeof createBuildingMotion>>
function advance(m:Motion,seconds:number,playing=true) {for(let i=0;i<seconds*60;i++)m.update(1/60,playing)}
function settle(m:Motion,progress:number,tier:1|2=1) {m.setSettings({...defaultBuildingSettings,progress,tier});advance(m,3,false)}
function snapshot(root:Group) {return JSON.stringify([nodes(root,'buildStart').map((p)=>[p.visible,...p.position.toArray(),...p.quaternion.toArray()]),meshes(root).map((p)=>Array.from(p.geometry.attributes.position.array))])}
function points(root:Object3D) {root.updateWorldMatrix(true,true);return meshes(root).filter(visible).flatMap((mesh)=>{const p=mesh.geometry.getAttribute('position');return Array.from({length:p.count},(_,i)=>new Vector3().fromBufferAttribute(p,i).applyMatrix4(mesh.matrixWorld))})}

describe('civic hall and oval public arena',()=>{
  for(const id of ['town-hall','amphitheater']) {
    it(`${id} has distinct construction stages, reversible upgrades and a stable root`,async()=>{
      const model=await load(id),m=createBuildingMotion(model)!,parts=nodes(model,'buildStart'),counts=[]
      const ports=nodes(model,'connectionKind'),anchors=ports.map((p)=>p.position.clone())
      for(const progress of [0,.30,.52,.78,1]) {
        settle(m,progress);counts.push(parts.filter((p)=>p.visible).length)
        expect(ports.every((p,i)=>p.position.equals(anchors[i]))).toBe(true)
        expect(model.getObjectByName('BuildingRoot')!.scale.toArray()).toEqual([1,1,1])
      }
      expect(new Set(counts).size).toBe(5)
      const upgrades=parts.filter((p)=>p.userData.buildingTier===2)
      expect(upgrades.length).toBeGreaterThan(0);expect(upgrades.every((p)=>!p.visible)).toBe(true)
      settle(m,1,2);expect(upgrades.every((p)=>p.visible)).toBe(true)
      expect(parts.filter((p)=>p.userData.buildingTemporary).every((p)=>!p.visible)).toBe(true)
      settle(m,.30);expect(parts.some((p)=>p.userData.buildingTemporary&&p.visible)).toBe(true)
      settle(m,0);m.setSettings({...defaultBuildingSettings,progress:0,automatic:true});advance(m,2)
      const stopped=snapshot(model);advance(m,1,false);expect(snapshot(model)).toBe(stopped)
      advance(m,34);expect(m.state.progress).toBe(1)
    })
    it(`${id} freezes functional motion and keeps animated vertices inside preview bounds`,async()=>{
      const model=await load(id),m=createBuildingMotion(model)!;settle(m,1,2)
      const before=snapshot(model);advance(m,.7);expect(snapshot(model)).not.toBe(before)
      const paused=snapshot(model);advance(m,1,false);expect(snapshot(model)).toBe(paused)
      m.setSettings({...defaultBuildingSettings,speed:0,tier:2});advance(m,1);expect(snapshot(model)).toBe(paused)
      m.setSettings({...defaultBuildingSettings,working:false,tier:2});advance(m,1);expect(snapshot(model)).toBe(paused)
      m.setSettings({...defaultBuildingSettings,speed:1,tier:2})
      const root=model.getObjectByName('BuildingRoot')!,bounds=new Box3(new Vector3().fromArray(root.userData.animationBoundsMin),new Vector3().fromArray(root.userData.animationBoundsMax))
      for(let frame=0;frame<120;frame++) {m.update(.1,true);expect(points(model).every((p)=>bounds.containsPoint(p)),`frame ${frame}`).toBe(true)}
    })
  }
  it('keeps four ground-level arena entrances traversable under real arches',async()=>{
    const model=await load('amphitheater'),m=createBuildingMotion(model)!;settle(m,1,2);model.updateMatrixWorld(true)
    const solids=meshes(model).filter(visible),ports=nodes(model,'connectionKind')
    expect(ports).toHaveLength(4)
    for(const port of ports){
      const normal=new Vector3().fromArray(port.userData.normalGltf),tangent=new Vector3(-normal.z,0,normal.x)
      expect(normal.length()).toBeCloseTo(1,6);expect(port.userData.clearWidth).toBe(1.4)
      for(const offset of [-.53,0,.53])for(const height of [.05,1.10,2.17]){
        const start=port.getWorldPosition(new Vector3()).addScaledVector(normal,.05).addScaledVector(tangent,offset);start.y+=height
        const hits=new Raycaster(start,normal.clone().negate(),0,6.2).intersectObjects(solids,false)
        expect(hits.map((hit)=>hit.object.name),`${port.name}/${offset}/${height}`).toEqual([])
      }
    }
  })
  it('joins every arena aisle tread to the upper promenade at its actual height',async()=>{
    const model=await load('amphitheater'),m=createBuildingMotion(model)!;settle(m,1);model.updateMatrixWorld(true)
    const stairs=nodes(model,'buildStart').filter((p)=>p.name==='AisleStairs').flatMap(meshes)
    const walk=nodes(model,'buildStart').filter((p)=>p.name==='Promenade').flatMap(meshes)
    for(let q=0;q<4;q++){
      const a=q*Math.PI/2+Math.PI/4
      for(let step=0;step<10;step++) {
        const r=3.6+(step+.5)*.29,height=.12+(step+1)*.20
        const hit=new Raycaster(new Vector3(1.24*r*Math.cos(a),height+.02,-r*Math.sin(a)),new Vector3(0,-1,0),0,.05).intersectObjects(stairs,false)[0]
        expect(hit).toBeDefined();expect(hit.point.y).toBeCloseTo(height,5)
      }
      for(const r of [6.49,6.51,6.9]){
        const hit=new Raycaster(new Vector3(1.24*r*Math.cos(a),2.14,-r*Math.sin(a)),new Vector3(0,-1,0),0,.05).intersectObjects([...stairs,...walk],false)[0]
        expect(hit,`promenade ${q}/${r}`).toBeDefined();expect(hit.point.y).toBeCloseTo(2.12,5)
      }
    }
    expect(buildingStage(.51,'amphitheater')).toBe('阶梯与拱廊')
  })
  it('pins all four velarium edges while deforming the interior without cumulative drift',async()=>{
    const model=await load('amphitheater'),m=createBuildingMotion(model)!
    settle(m,1,2)
    const cloth=nodes(model,'buildStart').filter((p)=>p.userData.buildingMotion==='velarium').flatMap(meshes)
    expect(cloth).toHaveLength(8)
    const authored=await load('amphitheater'),original=nodes(authored,'buildStart').filter((p)=>p.userData.buildingMotion==='velarium').flatMap(meshes)
    let moving=0,pinned=0
    for(let frame=0;frame<40;frame++){
      m.update(.17,true)
      cloth.forEach((mesh,index)=>{
        const p=mesh.geometry.attributes.position,base=original[index].geometry.attributes.position,uv=mesh.geometry.attributes.uv
        for(let i=0;i<p.count;i++){
          expect(p.getX(i)).toBe(base.getX(i));expect(p.getZ(i)).toBe(base.getZ(i))
          const delta=Math.abs(p.getY(i)-base.getY(i)),u=uv.getX(i),v=uv.getY(i)
          if(u<.001||u>.999||v<.001||v>.999){expect(delta).toBeLessThan(1e-6);pinned++}
          else {expect(delta).toBeLessThan(.045001);if(delta>.003)moving++}
        }
      })
    }
    expect(moving).toBeGreaterThan(500);expect(pinned).toBeGreaterThan(100)
  })
  it('supports each pinned cloth edge with a spar or rope and leaves recesses behind the arcade',async()=>{
    const model=await load('amphitheater');model.updateMatrixWorld(true)
    const supports=nodes(model,'buildStart').filter((p)=>p.name==='CanopyMasts').flatMap(meshes)
    const cloth=nodes(model,'buildStart').filter((p)=>p.userData.buildingMotion==='velarium').flatMap(meshes)
    for(const mesh of cloth){
      const p=mesh.geometry.attributes.position,uv=mesh.geometry.attributes.uv
      for(let i=0;i<p.count;i++){
        const u=uv.getX(i),v=uv.getY(i)
        if(u>.001&&u<.999&&v>.001&&v<.999)continue
        const point=new Vector3().fromBufferAttribute(p,i).applyMatrix4(mesh.matrixWorld)
        const hit=new Raycaster(point.clone().add(new Vector3(0,.08,0)),new Vector3(0,-1,0),0,.16).intersectObjects(supports,false)[0]
        expect(hit,`cloth edge ${mesh.name}/${u}/${v}`).toBeDefined()
      }
    }
    const walk=nodes(model,'buildStart').filter((p)=>p.name==='Promenade').flatMap(meshes)
    for(const mesh of walk){
      const p=mesh.geometry.attributes.position
      for(let i=0;i<p.count;i++)expect(new Vector3().fromBufferAttribute(p,i).applyMatrix4(mesh.matrixWorld).y).toBeGreaterThanOrEqual(1.94999)
    }
  })
  it('keeps the civic entrance and center aisle clear with fully open doors',async()=>{
    const model=await load('town-hall'),m=createBuildingMotion(model)!
    m.setSettings({...defaultBuildingSettings,speed:1,tier:2});m.update(2*Math.PI,true);model.updateMatrixWorld(true)
    const solids=meshes(model).filter(visible)
    for(const x of [-.53,0,.53])for(const height of [.05,1.05,2.17]){
      const hits=new Raycaster(new Vector3(x,.3+height,4.55),new Vector3(0,0,-1),0,6.2).intersectObjects(solids,false)
      expect(hits.map((hit)=>hit.object.name),`aisle ${x}/${height}`).toEqual([])
    }
    for(const [z,height] of [[5.15,.15],[4.75,.30],[4.1,.30],[3.1,.30],[2.7,.30]]){
      const hit=new Raycaster(new Vector3(0,height+.03,z),new Vector3(0,-1,0),0,.06).intersectObjects(solids,false)[0]
      expect(hit).toBeDefined();expect(hit.point.y).toBeCloseTo(height,5)
    }
  })
  it('drives civic clock hands at 12:1 and preserves the roof inspection state',async()=>{
    const model=await load('town-hall'),m=createBuildingMotion(model)!,minute=model.getObjectByName('MinuteHand')!,hour=model.getObjectByName('HourHand')!
    const minuteBase=minute.quaternion.clone(),hourBase=hour.quaternion.clone(),covers=nodes(model,'inspectionCover')
    expect(covers.length).toBeGreaterThan(4);covers.forEach((p)=>{p.visible=false})
    m.setSettings({...defaultBuildingSettings,speed:1});m.update(1,true)
    expect(minute.quaternion.angleTo(minuteBase)).toBeCloseTo(1.2,5)
    expect(hour.quaternion.angleTo(hourBase)).toBeCloseTo(.1,5)
    expect(covers.every((p)=>!p.visible)).toBe(true)
  })
  it('keeps the civic roof continuous outside the exact clock-tower footprint',async()=>{
    const model=await load('town-hall'),m=createBuildingMotion(model)!;settle(m,1);model.updateMatrixWorld(true)
    const roof=nodes(model,'buildStart').filter((p)=>p.name.startsWith('RoofCourse')).flatMap(meshes)
    for(const x of [-4,-2,0,2,4])for(const y of [-3.22,-3.10,-2.70,-1.60,-1.38,-1.11,-.01,.3,2.7,3.2]){
      const inside=Math.abs(x)<1.02&&y>=-3.04&&y<=-1.40
      const hit=new Raycaster(new Vector3(x,6,-y),new Vector3(0,-1,0),0,3).intersectObjects(roof,false)[0]
      if(inside)expect(hit).toBeUndefined()
      else {expect(hit,`roof ${x}/${y}`).toBeDefined();expect(hit.point.y).toBeCloseTo(3.40+1.28*(1-Math.abs(y)/3.28),5)}
    }
  })
  it('closes the civic gable and eave junctions directly below the sloped roof',async()=>{
    const model=await load('town-hall'),m=createBuildingMotion(model)!;settle(m,1);model.updateMatrixWorld(true)
    const solids=meshes(model).filter(visible)
    for(const side of [-1,1])for(const sourceY of [0,.8,1.8,2.6]){
      const height=3.34+1.28*(1-sourceY/3.28)-.025
      const hits=new Raycaster(new Vector3(side*4.35,height,-sourceY),new Vector3(-side,0,0),0,.3).intersectObjects(solids,false)
      expect(hits.length,`gable closure ${side}/${sourceY}`).toBeGreaterThan(0)
    }
    for(const side of [-1,1])for(const x of [-2.4,2.4]){
      const hits=new Raycaster(new Vector3(x,3.43,side*3.3),new Vector3(0,0,-side),0,.5).intersectObjects(solids,false)
      expect(hits.length,`eave closure ${side}/${x}`).toBeGreaterThan(0)
    }
  })
})
