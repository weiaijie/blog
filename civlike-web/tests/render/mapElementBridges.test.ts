import { readFileSync } from 'node:fs'
import { Group, Mesh, Object3D, Raycaster, Vector3 } from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { describe, expect, it } from 'vitest'
import { createBuildingMotion, defaultBuildingSettings } from '../../src/render/visuals/mapElementBuildings'
import { createRouteMotion } from '../../src/render/visuals/mapElementRoutes'

async function load(id:string){const b=readFileSync(new URL(`../../src/render/assets/elements/${id}.glb`,import.meta.url));return (await new GLTFLoader().parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'')).scene}
function nodes(root:Object3D,key:string){const list:Object3D[]=[];root.traverse((o)=>{if(o.userData[key]!==undefined)list.push(o)});return list}
function meshes(root:Object3D){const list:Mesh[]=[];root.traverse((o)=>{if(o instanceof Mesh){let p:Object3D|null=o;while(p){if(!p.visible)return;p=p.parent}list.push(o)}});return list}
type Motion=NonNullable<ReturnType<typeof createBuildingMotion>>
function advance(motion:Motion,seconds:number,playing=true){for(let i=0;i<seconds*60;i++)motion.update(1/60,playing)}
function settle(motion:Motion,progress:number,tier:1|2=1){motion.setSettings({...defaultBuildingSettings,progress,tier});advance(motion,3,false)}
function snap(model:Group){return JSON.stringify(nodes(model,'buildStart').map((o)=>[o.visible,...o.position.toArray(),...o.quaternion.toArray(),...meshes(o).flatMap((m)=>Array.from(m.geometry.attributes.position.array))]))}

describe('bridge structure, connections and operating envelope',()=>{
  for(const id of ['stone-bridge','steel-bridge']){
    it(`${id} assembles its structure without scaling the river openings or ports`,async()=>{
      const model=await load(id),motion=createBuildingMotion(model)!,parts=nodes(model,'buildStart'),ports=nodes(model,'connectionKind'),anchors=ports.map((p)=>p.position.toArray())
      expect(parts.length).toBeGreaterThan(15)
      let previous=0
      for(const progress of [0,.3,.52,.78,1]){
        settle(motion,progress)
        const visible=parts.filter((p)=>p.visible&&!p.userData.buildingTemporary).length
        expect(visible).toBeGreaterThan(previous);previous=visible
        expect(nodes(model,'buildingType')[0].scale.toArray()).toEqual([1,1,1])
        expect(ports.map((p)=>p.position.toArray())).toEqual(anchors)
      }
      expect(parts.filter((p)=>p.userData.buildingTemporary).every((p)=>!p.visible)).toBe(true)
      const upgrades=parts.filter((p)=>p.userData.buildingTier===2);expect(upgrades.length).toBeGreaterThan(0)
      expect(upgrades.every((p)=>!p.visible)).toBe(true);settle(motion,1,2);expect(upgrades.every((p)=>p.visible)).toBe(true)
      const before=snap(model);advance(motion,.5);expect(snap(model)).not.toBe(before)
      const stopped=snap(model);advance(motion,1,false);expect(snap(model)).toBe(stopped)
      motion.setSettings({...defaultBuildingSettings,tier:2,speed:0});advance(motion,1);expect(snap(model)).toBe(stopped)
      motion.setSettings({...defaultBuildingSettings,tier:2,working:false});advance(motion,1);expect(snap(model)).toBe(stopped)
      settle(motion,0);motion.setSettings({...defaultBuildingSettings,progress:0,automatic:true})
      const construction=snap(model);advance(motion,1,false);expect(snap(model)).toBe(construction)
      advance(motion,35);expect(motion.state.progress).toBe(1)
    })
    it(`${id} joins actual road geometry at both ends with a traversable deck`,async()=>{
      const model=await load(id),motion=createBuildingMotion(model)!
      settle(motion,1);model.updateMatrixWorld(true)
      const ports=nodes(model,'connectionKind').filter((p)=>p.userData.connectionKind==='road')
      expect(ports).toHaveLength(2)
      for(const port of ports){
        const normal=new Vector3().fromArray(port.userData.normalGltf),center=port.getWorldPosition(new Vector3())
        expect(center.y).toBeCloseTo(.145,6)
        for(const roadId of ['dirt-road','stone-road','asphalt-road']){
          const road=await load(roadId);createRouteMotion(road)!.update(0,false)
          const routePort=nodes(road,'routePort')[0],routeNormal=new Vector3().fromArray(routePort.userData.normalGltf)
          expect(routePort.userData.profile).toBe(port.userData.profile)
          road.quaternion.setFromUnitVectors(routeNormal,normal.clone().negate())
          road.position.copy(center).sub(routePort.position.clone().applyQuaternion(road.quaternion));road.updateMatrixWorld(true)
          expect(routePort.getWorldPosition(new Vector3()).distanceTo(center)).toBeLessThan(1e-5)
          for(const distance of [-.025,.025])for(const x of [-.65,0,.65]){
            const point=center.clone().addScaledVector(normal,distance);point.x+=x;point.y=1
            const hit=new Raycaster(point,new Vector3(0,-1,0)).intersectObjects([...meshes(model),...meshes(road)],false)[0]
            expect(hit).toBeDefined();expect(Math.abs(hit.point.y-.145)).toBeLessThan(.012)
          }
        }
      }
      for(let i=0;i<100;i++)for(const x of [-.65,0,.65]){
        const z=-4.59+i*9.18/99
        if(id==='steel-bridge'&&Math.abs(z)<.02)continue
        const hit=new Raycaster(new Vector3(x,1,z),new Vector3(0,-1,0)).intersectObjects(meshes(model),false)[0]
        expect(hit).toBeDefined();expect(hit.point.y).toBeGreaterThanOrEqual(.14)
        expect(hit.point.y).toBeLessThan(.43)
      }
    })
  }
  it('uses real open arch barrels, cutwaters and a structural crown below the raised roadway',async()=>{
    const model=await load('stone-bridge');settle(createBuildingMotion(model)!,1,2);model.updateMatrixWorld(true)
    expect(nodes(model,'buildStart').filter((p)=>p.name.startsWith('ArchVoussoir'))).toHaveLength(48)
    for(const center of [-1.5,1.5])for(const offset of [-.5,0,.5])for(const height of [-1.35,-1,-.55]){
      expect(new Raycaster(new Vector3(-2,height,center+offset),new Vector3(1,0,0),0,4).intersectObjects(meshes(model),false)).toHaveLength(0)
    }
    for(const center of [-1.5,1.5]){
      const hits=new Raycaster(new Vector3(0,-1.2,center),new Vector3(0,1,0)).intersectObjects(meshes(model),false)
      expect(hits[0].point.y).toBeCloseTo(-.25,2)
    }
    expect(new Raycaster(new Vector3(-2,-1,0),new Vector3(1,0,0),0,4).intersectObjects(meshes(model),false).length).toBeGreaterThan(0)
  })
  it('lowers road barriers before opening either bascule and reverses that order on closing',async()=>{
    const model=await load('steel-bridge'),motion=createBuildingMotion(model)!,parts=nodes(model,'buildStart'),leaves=parts.filter((p)=>p.userData.buildingMotion==='bascule'),barriers=parts.filter((p)=>p.userData.buildingMotion==='road-barrier')
    expect(leaves).toHaveLength(2);expect(barriers).toHaveLength(2)
    motion.update(0,false);const closed=leaves.map((p)=>p.quaternion.clone()),raised=barriers.map((p)=>p.quaternion.clone())
    motion.setSettings({...defaultBuildingSettings,gateOpen:true})
    for(let frame=0;frame<550;frame++){
      motion.update(1/60,true)
      for(let i=0;i<2;i++){
        const angle=closed[i].angleTo(leaves[i].quaternion),gateAngle=raised[i].angleTo(barriers[i].quaternion)
        if(angle>.000001)expect(gateAngle).toBeCloseTo(Math.PI/2,5)
        if(motion.state.access<.2)expect(angle).toBeLessThan(1e-5)
      }
    }
    expect(motion.state.access).toBe(1)
    for(let i=0;i<2;i++)expect(closed[i].angleTo(leaves[i].quaternion)).toBeCloseTo(70*Math.PI/180,6)
    motion.setSettings({...defaultBuildingSettings,gateOpen:false})
    for(let frame=0;frame<550;frame++){
      motion.update(1/60,true)
      for(let i=0;i<2;i++)if(raised[i].angleTo(barriers[i].quaternion)<Math.PI/2-1e-5)expect(closed[i].angleTo(leaves[i].quaternion)).toBeLessThan(1e-5)
    }
    expect(motion.state.access).toBe(0)
    motion.setSettings({...defaultBuildingSettings,gateOpen:true});advance(motion,.3)
    const halfway=snap(model);advance(motion,1,false);expect(snap(model)).toBe(halfway)
    settle(motion,.5);expect(motion.state.access).toBe(0)
  })
  it('keeps the counterweights in their pockets and opens a real central navigation corridor',async()=>{
    const model=await load('steel-bridge'),motion=createBuildingMotion(model)!,parts=nodes(model,'buildStart'),leaves=parts.filter((p)=>p.userData.buildingMotion==='bascule')
    motion.update(0,false);motion.setSettings({...defaultBuildingSettings,gateOpen:true})
    for(let frame=0;frame<120;frame++){
      motion.update(1/20,true);model.updateMatrixWorld(true)
      for(const leaf of leaves)for(const mesh of meshes(leaf)){
        const positions=mesh.geometry.getAttribute('position')
        for(let i=0;i<positions.count;i++){
          const p=new Vector3().fromBufferAttribute(positions,i).applyMatrix4(mesh.matrixWorld),z=Math.abs(p.z)
          // Below the approaches only the open pocket is available, not the bank masonry.
          if(p.y<-.10){expect(p.y).toBeGreaterThan(-1.58);expect(z).toBeLessThan(3.20);expect(Math.abs(p.x)).toBeLessThan(.94)}
          if(z>2.40001&&z<4.6&&Math.abs(p.x)<.725){
            const soffit=z<2.47?.12:.025
            expect(p.y<soffit-1e-5||p.y>.145+1e-5,`moving part intersects fixed approach: ${p.toArray()}`).toBe(true)
          }
          // The swept truss must not enter the fixed parapet or guard posts.
          if(p.y>.22&&Math.abs(p.x)>.72)expect(z).toBeLessThan(3.32)
        }
      }
    }
    for(const z of [-.65,0,.65])for(const height of [-1.35,-.5,.5,1.6]){
      expect(new Raycaster(new Vector3(-2,height,z),new Vector3(1,0,0),0,4).intersectObjects(meshes(model),false)).toHaveLength(0)
    }
  })
})
