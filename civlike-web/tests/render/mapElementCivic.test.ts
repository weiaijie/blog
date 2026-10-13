import { readFileSync } from 'node:fs'
import { Box3, Group, Mesh, Object3D, Raycaster, SkinnedMesh, Vector3 } from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { describe, expect, it } from 'vitest'
import { createBuildingMotion, defaultBuildingSettings } from '../../src/render/visuals/mapElementBuildings'
import { createHumanMotion } from '../../src/render/visuals/mapElementPeople'

async function load(id:string){const b=readFileSync(new URL(`../../src/render/assets/elements/${id}.glb`,import.meta.url));return (await new GLTFLoader().parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'')).scene}
function nodes(root:Object3D,key:string){const list:Object3D[]=[];root.traverse((o)=>{if(o.userData[key]!==undefined)list.push(o)});return list}
function meshes(root:Object3D){const list:Mesh[]=[];root.traverse((o)=>{if(o instanceof Mesh)list.push(o)});return list}
function vertices(root:Object3D){root.updateWorldMatrix(true,true);return meshes(root).flatMap((m)=>{const p=m.geometry.getAttribute('position');return Array.from({length:p.count},(_,i)=>new Vector3().fromBufferAttribute(p,i).applyMatrix4(m.matrixWorld))})}
type Motion=NonNullable<ReturnType<typeof createBuildingMotion>>
function advance(m:Motion,seconds:number,playing=true){for(let i=0;i<seconds*60;i++)m.update(1/60,playing)}
function settle(m:Motion,progress:number,tier:1|2=1){m.setSettings({...defaultBuildingSettings,progress,tier});advance(m,3,false)}
function snapshot(model:Group){return JSON.stringify(nodes(model,'buildStart').map((p)=>[p.visible,...p.position.toArray(),...p.quaternion.toArray()]))}
function named(root:Object3D,name:string){return nodes(root,'buildStart').find((p)=>p.name===name)!}

describe('gallery inn and chapel',()=>{
  for(const id of ['inn','chapel']){
    it(`${id} constructs distinct stages and upgrades, without scaling the whole building`,async()=>{
      const model=await load(id),m=createBuildingMotion(model)!,parts=nodes(model,'buildStart'),counts=[]
      const ports=nodes(model,'connectionKind'),anchors=ports.map((p)=>p.position.toArray())
      for(const progress of [0,.30,.52,.78,1]){
        settle(m,progress);counts.push(parts.filter((p)=>p.visible).length)
        expect(ports.map((p)=>p.position.toArray())).toEqual(anchors);expect(model.scale.toArray()).toEqual([1,1,1])
      }
      expect(new Set(counts).size).toBe(5)
      const upgrade=parts.filter((p)=>p.userData.buildingTier===2);expect(upgrade.length).toBeGreaterThan(0)
      expect(upgrade.every((p)=>!p.visible)).toBe(true);settle(m,1,2);expect(upgrade.every((p)=>p.visible)).toBe(true)
      expect(parts.filter((p)=>p.userData.buildingTemporary).every((p)=>!p.visible)).toBe(true)
      settle(m,0);m.setSettings({...defaultBuildingSettings,automatic:true,progress:0});advance(m,2)
      const paused=snapshot(model);advance(m,1,false);expect(snapshot(model)).toBe(paused)
      advance(m,34);expect(m.state.progress).toBe(1)
    })
    it(`${id} moves functional parts, freezes exactly, and preserves the cutaway`,async()=>{
      const model=await load(id),m=createBuildingMotion(model)!,covers=nodes(model,'inspectionCover')
      expect(covers.length).toBeGreaterThanOrEqual(6);covers.forEach((p)=>{p.visible=false})
      const initial=snapshot(model);advance(m,.75);expect(snapshot(model)).not.toBe(initial)
      const paused=snapshot(model);advance(m,1,false);expect(snapshot(model)).toBe(paused)
      m.setSettings({...defaultBuildingSettings,speed:0});advance(m,1);expect(snapshot(model)).toBe(paused)
      m.setSettings({...defaultBuildingSettings,working:false});advance(m,1);expect(snapshot(model)).toBe(paused)
      expect(covers.every((p)=>!p.visible)).toBe(true)
      const root=model.getObjectByName('BuildingRoot')!,bounds=new Box3(new Vector3().fromArray(root.userData.animationBoundsMin),new Vector3().fromArray(root.userData.animationBoundsMax))
      m.setSettings({...defaultBuildingSettings,tier:2,speed:1})
      for(let i=0;i<120;i++){
        m.update(.10,true);model.updateMatrixWorld(true)
        const escaped=partsWithoutScaffolds(model).filter((p)=>!bounds.containsPoint(p))
        expect(escaped,`${id}: frame ${i} outside framing bounds`).toHaveLength(0)
      }
    })
    it(`${id} has real entrance and side window openings in the wall mesh`,async()=>{
      const model=await load(id),m=createBuildingMotion(model)!;settle(m,1);model.updateMatrixWorld(true)
      const walls=nodes(model,'buildStart').filter((p)=>/^(Front|Side)WallCourse/.test(p.name)).flatMap(meshes)
      expect(walls.length).toBeGreaterThan(0)
      const d=id==='inn'?3.6:5.2,w=id==='inn'?4.8:3.8
      for(const x of [-.4,0,.4])for(const y of [.5,1.5])expect(new Raycaster(new Vector3(x,y,d/2+.3),new Vector3(0,0,-1),0,.6).intersectObjects(walls,false)).toHaveLength(0)
      for(const sourceY of id==='inn'?[-.95,.95]:[-1.5,.2,1.75]){
        expect(new Raycaster(new Vector3(w/2+.3,id==='inn'?1.3:1.68,-sourceY),new Vector3(-1,0,0),0,.6).intersectObjects(walls,false)).toHaveLength(0)
      }
    })
  }
  it('connects every inn stair tread to the upper gallery with an unobstructed landing',async()=>{
    const model=await load('inn'),m=createBuildingMotion(model)!;settle(m,1,2);model.updateMatrixWorld(true)
    const stairs=meshes(named(model,'ExternalStair')),gallery=meshes(named(model,'Gallery'))
    for(let i=0;i<12;i++){
      const y=1.47-i*.29,height=(i+1)*2.55/12
      const hit=new Raycaster(new Vector3(3.16,height+.15,-y),new Vector3(0,-1,0)).intersectObjects(stairs,false)[0]
      expect(hit).toBeDefined();expect(hit.point.y).toBeCloseTo(height,4)
    }
    for(const x of [3.16,2.50,2.42,2.2]){
      const hit=new Raycaster(new Vector3(x,2.8,2.22),new Vector3(0,-1,0)).intersectObjects([...stairs,...gallery],false)[0]
      expect(hit.point.y).toBeCloseTo(2.55,4)
    }
    for(const y of [2.8,3.2])expect(new Raycaster(new Vector3(3.16,y,2.22),new Vector3(-1,0,0),0,1.0).intersectObjects([...stairs,...gallery],false)).toHaveLength(0)
    const doors=nodes(model,'buildStart').filter((p)=>p.name.startsWith('Guest')&&p.name.includes('Door'))
    expect(doors).toHaveLength(3);expect(doors.every((p)=>Math.abs(p.position.y-2.55)<1e-5)).toBe(true)
    m.setSettings({...defaultBuildingSettings,speed:1,tier:2})
    for(let i=0;i<120;i++){m.update(.10,true);expect(Math.max(...doors.flatMap(vertices).map((p)=>p.z))).toBeLessThan(1.98)}
  })
  it('keeps the chapel aisle open between pews and supports the belfry on masonry',async()=>{
    const model=await load('chapel');settle(createBuildingMotion(model)!,1);model.updateMatrixWorld(true)
    const pews=meshes(named(model,'Pews'))
    for(const x of [-.45,0,.45])expect(new Raycaster(new Vector3(x,.6,1.8),new Vector3(0,0,-1),0,3.2).intersectObjects(pews,false)).toHaveLength(0)
    const gable=meshes(named(model,'Gables'))
    for(const x of [-.68,.68]){
      const hit=new Raycaster(new Vector3(x,3.6,2.60),new Vector3(0,-1,0)).intersectObjects(gable,false)[0]
      expect(hit).toBeDefined();expect(hit.point.y).toBeGreaterThan(3.40)
    }
  })
  it('has a hollow bell and a separately hinged clapper that stays inside its mouth',async()=>{
    const model=await load('chapel'),m=createBuildingMotion(model)!,bell=named(model,'SwingingBell'),clapper=named(model,'BellClapper')
    m.update(0,false);model.updateMatrixWorld(true)
    expect(clapper.parent).toBe(bell)
    const shell=meshes(bell).filter((p)=>!meshes(clapper).includes(p))
    expect(new Raycaster(new Vector3(.20,4.10,2.48),new Vector3(0,1,0),0,.32).intersectObjects(shell,false)).toHaveLength(0)
    const rest=clapper.quaternion.clone(),bellRest=bell.quaternion.clone()
    m.setSettings({...defaultBuildingSettings,speed:1});advance(m,.50)
    expect(bell.quaternion.angleTo(bellRest)).toBeGreaterThan(.1);expect(clapper.quaternion.angleTo(rest)).toBeGreaterThan(.05)
    for(let i=0;i<120;i++){
      m.update(.05,true);model.updateMatrixWorld(true)
      const local=vertices(clapper).map((p)=>bell.worldToLocal(p.clone()))
      expect(local.every((p)=>Math.hypot(p.x,p.z)<.24&&p.y>-.75&&p.y<-.08)).toBe(true)
      const belfryBounds=new Box3(new Vector3(-.55,4.10,1.80),new Vector3(.55,5.11,3.16))
      const bellOnly=vertices(bell).filter((p)=>Math.abs(p.x)<.50)
      expect(bellOnly.every((p)=>belfryBounds.containsPoint(p))).toBe(true)
    }
  })
  it('fits the actual unscaled walking workers through ground and guest room entrances',async()=>{
    const inn=await load('inn'),chapel=await load('chapel')
    for(const model of [inn,chapel]){
      const motion=createBuildingMotion(model)!;settle(motion,1)
      motion.setSettings({...defaultBuildingSettings,speed:1});motion.update(Math.PI*2,true);model.updateMatrixWorld(true)
    }
    const passages=[{model:inn,x:0,y:.2,z:1.85,approach:1.40},{model:chapel,x:0,y:.2,z:2.65,approach:.85},...[-1.5,0,1.5].map((x)=>({model:inn,x,y:2.55,z:1.85,approach:.24}))]
    const solids=new Map([inn,chapel].map((model)=>[model,meshes(model).filter(visible)]))
    for(const id of ['farmer','merchant','fisher','woodcutter']){
      const b=readFileSync(new URL(`../../src/render/assets/elements/${id}.glb`,import.meta.url)),{scene,animations}=await new GLTFLoader().parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'')
      const human=createHumanMotion(scene,animations)!;human.setSettings({mode:'Walk',speed:1});human.update(1,true)
      for(let frame=0;frame<24;frame++){
        human.update(.125,true);scene.updateMatrixWorld(true)
        const points=meshes(scene).filter(visible).flatMap((mesh)=>{
          if(mesh instanceof SkinnedMesh)mesh.skeleton.update()
          return Array.from({length:mesh.geometry.attributes.position.count},(_,i)=>mesh.getVertexPosition(i,new Vector3()).applyMatrix4(mesh.matrixWorld))
        })
        const bounds=new Box3().setFromPoints(points)
        expect(bounds.max.y).toBeLessThan(2.17);expect(Math.max(Math.abs(bounds.min.x),Math.abs(bounds.max.x))).toBeLessThan(.54)
        for(const passage of passages){
          // Sweep the walking silhouette through the short portal, including open door leaves and frames.
          for(const x of [bounds.min.x,0,bounds.max.x])for(const y of [.04,bounds.max.y/2,bounds.max.y]){
            const ray=new Raycaster(new Vector3(passage.x+x,passage.y+y,passage.z+passage.approach),new Vector3(0,0,-1),0,passage.approach+.24)
            const hits=ray.intersectObjects(solids.get(passage.model)!,false).map((hit)=>({part:hit.object.name,parent:hit.object.parent?.name,point:hit.point.toArray()}))
            expect(hits,`${id} at ${passage.x}/${passage.y} sample ${x}/${y} frame ${frame}`).toEqual([])
          }
        }
        for(const z of [2.54-bounds.max.x,2.54,2.54-bounds.min.x])for(const y of [.04,bounds.max.y/2,bounds.max.y]){
          const ray=new Raycaster(new Vector3(2.24,2.55+y,z),new Vector3(-1,0,0),0,3.84)
          expect(ray.intersectObjects(solids.get(inn)!,false).map((hit)=>hit.object.name),`${id}: gallery circulation`).toEqual([])
        }
      }
      expect(scene.scale.toArray()).toEqual([1,1,1]);human.destroy()
    }
  })
})

function partsWithoutScaffolds(model:Group){return nodes(model,'buildStart').filter((p)=>p.visible&&!p.userData.buildingTemporary&&p.name!=='BellClapper').flatMap(vertices)}
function visible(node:Object3D){for(let p:Object3D|null=node;p;p=p.parent)if(!p.visible)return false;return true}
