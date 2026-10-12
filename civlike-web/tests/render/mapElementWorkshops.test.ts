import { readFileSync } from 'node:fs'
import { Box3, Group, Mesh, MeshStandardMaterial, Object3D, Raycaster, Vector3 } from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { describe, expect, it } from 'vitest'
import { createBuildingMotion, defaultBuildingSettings } from '../../src/render/visuals/mapElementBuildings'

async function load(id:string){const b=readFileSync(new URL(`../../src/render/assets/elements/${id}.glb`,import.meta.url));return (await new GLTFLoader().parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'')).scene}
function nodes(model:Object3D,key:string){const a:Object3D[]=[];model.traverse((o)=>{if(o.userData[key]!==undefined)a.push(o)});return a}
function meshes(model:Object3D){const a:Mesh[]=[];model.traverse((o)=>{if(o instanceof Mesh)a.push(o)});return a}
function points(model:Object3D){model.updateWorldMatrix(true,true);return meshes(model).flatMap((m)=>{const p=m.geometry.getAttribute('position');return Array.from({length:p.count},(_,i)=>new Vector3().fromBufferAttribute(p,i).applyMatrix4(m.matrixWorld))})}
function snapshot(model:Group){const a:unknown[]=[];model.traverse((o)=>{a.push([o.visible,...o.position.toArray(),...o.quaternion.toArray()]);if(o instanceof Mesh){a.push(Array.from(o.geometry.getAttribute('position').array));if(o.material instanceof MeshStandardMaterial)a.push(o.material.emissiveIntensity)}});return JSON.stringify(a)}

describe('service buildings have distinct interiors and attached working surfaces',()=>{
  for(const id of ['stable','blacksmith','market-hall']){
    it(`${id} constructs individual parts, preserves sockets and adds upgrade modules`,async()=>{
      const model=await load(id),motion=createBuildingMotion(model)!,parts=nodes(model,'buildStart'),root=nodes(model,'buildingType')[0],sockets=nodes(model,'connectionKind')
      const anchors=sockets.map((o)=>o.position.toArray())
      expect(sockets.some((o)=>o.userData.connectionKind==='road')).toBe(true)
      expect(parts.length).toBeGreaterThan(20);expect(parts.some((o)=>o.userData.buildingTier===2)).toBe(true)
      let count=0
      for(const progress of [0,.25,.5,.78,1]){
        motion.setSettings({...defaultBuildingSettings,progress,working:false})
        for(let i=0;i<180;i++)motion.update(1/60,false)
        const visible=parts.filter((o)=>o.visible&&!o.userData.buildingTemporary).length
        expect(visible).toBeGreaterThanOrEqual(count);count=visible
        if(progress===0)expect(visible).toBe(1)
        expect(root.scale.toArray()).toEqual([1,1,1]);expect(sockets.map((o)=>o.position.toArray())).toEqual(anchors)
      }
      expect(parts.filter((o)=>o.userData.buildingTemporary).every((o)=>!o.visible)).toBe(true)
      motion.setSettings({...defaultBuildingSettings,tier:2});motion.update(0,false)
      expect(parts.filter((o)=>o.userData.buildingTier===2).every((o)=>o.visible)).toBe(true)
      const covers=nodes(model,'inspectionCover');expect(covers.length).toBeGreaterThanOrEqual(6)
      for(const cover of covers)cover.visible=false
      motion.update(.1,true)
      expect(covers.every((o)=>!o.visible)).toBe(true)
    })
    it(`${id} has real working motion, pause, zero speed and automatic construction`,async()=>{
      const model=await load(id),motion=createBuildingMotion(model)!
      motion.update(0,true);const before=snapshot(model);motion.update(1,true);expect(snapshot(model)).not.toBe(before)
      const moving=snapshot(model);motion.update(1,false);expect(snapshot(model)).toBe(moving)
      motion.setSettings({...defaultBuildingSettings,speed:0});motion.update(1,true);expect(snapshot(model)).toBe(moving)
      motion.setSettings({...defaultBuildingSettings,working:false});motion.update(1,true);expect(snapshot(model)).toBe(moving)
      motion.setSettings({...defaultBuildingSettings,progress:0});for(let i=0;i<180;i++)motion.update(1/60,false)
      motion.setSettings({...defaultBuildingSettings,progress:0,automatic:true});const state={...motion.update(0,false)};motion.update(1,false);expect(motion.state).toEqual(state)
      for(let i=0;i<2100;i++)motion.update(1/60,true)
      expect(motion.state.progress).toBe(1)
    })
  }
  it('keeps leather on actual bellows leaf edges throughout the pumping cycle',async()=>{
    const model=await load('blacksmith'),motion=createBuildingMotion(model)!,parts=nodes(model,'buildStart'),skin=parts.find((o)=>o.userData.buildingMotion==='bellows-skin')!,leaf=parts.find((o)=>o.userData.buildingMotion==='bellows')!,base=parts.find((o)=>o.name.startsWith('BellowsBase'))!
    model.updateMatrixWorld(true)
    const samples=meshes(skin).map((m)=>({m,local:points(m).map((p)=>skin.worldToLocal(p.clone()))}))
    let upper=0,lower=0
    for(let frame=0;frame<50;frame++){
      motion.update(.12,true);model.updateMatrixWorld(true)
      const top=points(leaf),bottom=points(base)
      for(const {m,local}of samples){
        const p=m.geometry.getAttribute('position')
        for(let i=0;i<p.count;i++){
          const world=new Vector3().fromBufferAttribute(p,i).applyMatrix4(m.matrixWorld)
          expect(world.toArray().every(Number.isFinite)).toBe(true)
          if(Math.abs(local[i].y)<1e-5){expect(Math.min(...top.map((q)=>q.distanceTo(world)))).toBeLessThan(.026);upper++}
          if(Math.abs(local[i].y+.15)<1e-5){expect(Math.min(...bottom.map((q)=>q.distanceTo(world)))).toBeLessThan(.026);lower++}
        }
      }
    }
    expect(upper).toBeGreaterThan(100);expect(lower).toBeGreaterThan(100)
  })
  it('pins both awning rails while only the inner cloth moves',async()=>{
    const model=await load('market-hall'),motion=createBuildingMotion(model)!,part=nodes(model,'buildStart').find((o)=>o.userData.buildingMotion==='awning')!,cloth=meshes(part)
    motion.update(0,true);const before=cloth.map((m)=>Array.from(m.geometry.getAttribute('position').array))
    motion.update(.8,true);let pinned=0,moved=0
    for(let j=0;j<cloth.length;j++){
      const p=cloth[j].geometry.getAttribute('position'),zs=Array.from({length:p.count},(_,i)=>p.getZ(i)),min=Math.min(...zs),max=Math.max(...zs)
      for(let i=0;i<p.count;i++){
        expect(p.getX(i)).toBeCloseTo(before[j][i*3],6);expect(p.getZ(i)).toBeCloseTo(before[j][i*3+2],6)
        if(Math.abs(p.getZ(i)-min)<1e-5||Math.abs(p.getZ(i)-max)<1e-5){expect(p.getY(i)).toBeCloseTo(before[j][i*3+1],6);pinned++}
        else if(Math.abs(p.getY(i)-before[j][i*3+1])>.005)moved++
      }
    }
    expect(pinned).toBeGreaterThan(20);expect(moved).toBeGreaterThan(40)
  })
  it('keeps the market central aisle open through both entrances',async()=>{
    const model=await load('market-hall'),motion=createBuildingMotion(model)!
    motion.setSettings({...defaultBuildingSettings,tier:2,working:false});motion.update(0,false);model.updateMatrixWorld(true)
    const active=meshes(model).filter((m)=>{let o:Object3D|null=m;while(o){if(!o.visible)return false;o=o.parent}return true})
    for(const x of [-.4,0,.4])expect(new Raycaster(new Vector3(x,1,5),new Vector3(0,0,-1)).intersectObjects(active,false)).toHaveLength(0)
    expect(nodes(model,'connectionKind').filter((o)=>o.userData.connectionKind==='trade')).toHaveLength(4)
  })
  it('separates three stall spaces from the front passage',async()=>{
    const model=await load('stable'),motion=createBuildingMotion(model)!
    motion.update(0,false);model.updateMatrixWorld(true)
    expect(nodes(model,'connectionKind').filter((o)=>o.userData.connectionKind==='animal')).toHaveLength(3)
    const walls=nodes(model,'buildStart').filter((o)=>o.name.startsWith('WallCourse'))
    for(const x of [-1.56*1.8,0,1.56*1.8]){
      const hit=new Raycaster(new Vector3(x,1.05,4),new Vector3(0,0,-1)).intersectObjects(walls,true)[0]
      expect(hit).toBeDefined();expect(hit.point.z).toBeLessThan(-1.7)
    }
  })
  it('fits the existing adult horse between actual stall gates, manger and partition geometry',async()=>{
    const model=await load('stable'),horse=await load('horse'),motion=createBuildingMotion(model)!
    motion.setSettings({...defaultBuildingSettings,tier:2,working:false});motion.update(0,false);model.updateMatrixWorld(true)
    const parts=nodes(model,'buildStart'),gates=parts.filter((o)=>o.name.startsWith('StallGate')),mangers=parts.filter((o)=>o.name.startsWith('MangerAndHay')),loft=parts.find((o)=>o.name.startsWith('HayLoft'))!
    horse.rotation.y=Math.PI
    for(const socket of nodes(model,'connectionKind').filter((o)=>o.userData.connectionKind==='animal')){
      const slot=socket.getWorldPosition(new Vector3());horse.position.copy(slot);horse.updateMatrixWorld(true)
      const bounds=new Box3().setFromObject(horse,true),nearest=(items:Object3D[])=>items.reduce((a,b)=>Math.abs(new Box3().setFromObject(a).getCenter(new Vector3()).x-slot.x)<Math.abs(new Box3().setFromObject(b).getCenter(new Vector3()).x-slot.x)?a:b)
      const gate=new Box3().setFromObject(nearest(gates)),manger=new Box3().setFromObject(nearest(mangers))
      expect(bounds.max.z).toBeLessThan(gate.min.z)
      expect(bounds.min.z).toBeGreaterThan(manger.max.z)
      expect(bounds.min.x).toBeGreaterThan(slot.x-.69*1.8);expect(bounds.max.x).toBeLessThan(slot.x+.69*1.8)
      expect(bounds.max.y).toBeLessThan(new Box3().setFromObject(loft).min.y)
    }
  })
  it('keeps all upgraded hay bales and bindings below the actual pitched roof',async()=>{
    const model=await load('stable'),motion=createBuildingMotion(model)!
    motion.setSettings({...defaultBuildingSettings,tier:2,working:false});motion.update(0,false);model.updateMatrixWorld(true)
    const loft=nodes(model,'buildStart').find((o)=>o.name.startsWith('HayLoft'))!,roof=nodes(model,'inspectionCover').flatMap(meshes),ray=new Raycaster()
    const hayVertices=points(loft).filter((p)=>p.y>2.03*1.8)
    expect(hayVertices.length).toBeGreaterThan(50)
    for(const point of hayVertices){
      ray.set(new Vector3(point.x,10,point.z),new Vector3(0,-1,0));const hit=ray.intersectObjects(roof,false)[0]
      expect(hit).toBeDefined();expect(point.y).toBeLessThan(hit.point.y-.045*1.8)
    }
  })
})
