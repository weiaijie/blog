import { readFileSync } from 'node:fs'
import { Box3, Group, Mesh, MeshStandardMaterial, Object3D, Raycaster, Vector3 } from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { describe, expect, it } from 'vitest'
import { createTerrainMotion, defaultTerrainSettings } from '../../src/render/visuals/mapElementTerrain'

const half=1.75*Math.sqrt(3)/2,ids=['waterfall','lake-shore']
async function load(id:string) {const b=readFileSync(new URL(`../../src/render/assets/elements/${id}.glb`,import.meta.url));return (await new GLTFLoader().parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'')).scene}
function nodes(root:Object3D,key:string) {const a:Object3D[]=[];root.traverse((o)=>{if(o.userData[key]!==undefined)a.push(o)});return a}
function meshes(root:Object3D) {const a:Mesh[]=[];root.traverse((o)=>{if(o instanceof Mesh)a.push(o)});return a}
function groupMeshes(root:Object3D,key:string) {return nodes(root,key).flatMap(meshes)}
function height(model:Group,key:string,x:number,z:number) {
  model.updateMatrixWorld(true)
  const hit=new Raycaster(new Vector3(x,3,z),new Vector3(0,-1,0)).intersectObjects(groupMeshes(model,key),false)[0]
  expect(hit,`${key} (${x},${z})`).toBeDefined();return hit.point.y
}
function snapshot(model:Group) {return groupMeshes(model,'hydroscapeWater').map((m)=>[...m.geometry.attributes.position.array,...m.geometry.attributes.color.array])}
type Motion=NonNullable<ReturnType<typeof createTerrainMotion>>
function settle(m:Motion,id:string,snow:number) {m.setSettings({...defaultTerrainSettings(id),snow,wind:0});for(let i=0;i<180;i++)m.update(1/60,false)}

describe('waterfall and lake shore geometry and motion',()=>{
  it('has a real 1.10 m drop and a plunge pool below the downstream bed',async()=>{
    const model=await load('waterfall')
    expect(height(model,'hydroscapeWater',0,-half+.001)-height(model,'hydroscapeWater',0,half-.001)).toBeCloseTo(1.10,4)
    expect(height(model,'hydroscapeGround',0,.40)).toBeLessThan(-.18)
    expect(height(model,'hydroscapeWater',0,0)-height(model,'hydroscapeGround',0,0)).toBeGreaterThan(.35)
    expect(nodes(model,'cascadeSpray')).toHaveLength(18)
    for(const x of [-1.2,-.9,.9,1.2]) {
      const hit=new Raycaster(new Vector3(x,3,0),new Vector3(0,-1,0)).intersectObjects(groupMeshes(model,'hydroscapeWater'),false)
      expect(hit,`dry cliff side ${x}`).toHaveLength(0)
    }
  })
  it('matches the actual old river-bed sections at both ends after applying the upper elevation',async()=>{
    const model=await load('waterfall'),old=await load('river-bend')
    const ports=nodes(model,'edgeIndex').filter((o)=>o.userData.profile==='hex-river-080-v1')
    expect(ports.map((o)=>o.userData.edgeIndex).sort()).toEqual([1,4])
    for(const sign of [-1,1])for(let i=0;i<=80;i++) {
      const x=-.84+i*.021,z=sign*(half-.000001),lift=sign<0?1.10:0
      expect(height(model,'hydroscapeGround',x,z)-lift,`bed ${sign}/${x}`).toBeCloseTo(height(old,'riparianGround',x,z),4)
      if(Math.abs(x)<.395)expect(height(model,'hydroscapeWater',x,z)-lift).toBeCloseTo(.04,5)
    }
    expect(nodes(model,'edgeIndex').filter((o)=>o.userData.profile==='hex-drop-110-side-v1')).toHaveLength(4)
  })
  it('distinguishes dry land, shallow shore and deep lake with matched north/south shore sections',async()=>{
    const model=await load('lake-shore')
    expect(height(model,'hydroscapeGround',-1,0)).toBeGreaterThan(.08)
    expect(height(model,'hydroscapeGround',.2,0)).toBeGreaterThan(-.08)
    expect(height(model,'hydroscapeGround',1,0)).toBeCloseTo(-.16,5)
    for(let i=0;i<=70;i++) {
      const x=-.84+i*.024
      expect(height(model,'hydroscapeGround',x,half-.000001)).toBeCloseTo(height(model,'hydroscapeGround',x,-half+.000001),4)
    }
    const ports=nodes(model,'edgeIndex')
    expect(ports.filter((o)=>o.userData.profile==='hex-lake-shore-v1')).toHaveLength(2)
    expect(ports.filter((o)=>o.userData.profile==='hex-lake-deep-v1')).toHaveLength(2)
    const grass=await load('grassland');grass.updateMatrixWorld(true)
    for(const edge of ports.filter((o)=>o.userData.profile==='hex-flat-3.5-v1')) {
      const normal=new Vector3().fromArray(edge.userData.normalGltf),tangent=new Vector3(-normal.z,0,normal.x)
      for(let i=-8;i<=8;i++) {
        const p=normal.clone().multiplyScalar(half-.00001).addScaledVector(tangent,i*.10)
        expect(height(model,'hydroscapeGround',p.x,p.z)).toBeCloseTo(.08,5)
        const soil=meshes(grass).filter((o)=>!(Array.isArray(o.material)?o.material:[o.material]).some((m)=>m.name==='ground_snow'))
        const hit=new Raycaster(new Vector3(p.x,2,p.z),new Vector3(0,-1,0)).intersectObjects(soil,false)[0]
        expect(hit.point.y).toBeCloseTo(.08,5)
      }
    }
  })
  it('places real river neighbors against both waterfall ports in all six rotations',async()=>{
    const model=await load('waterfall'),neighbor=await load('river-bend'),axis=new Vector3(0,1,0)
    for(let turn=0;turn<6;turn++)for(const sign of [-1,1]) {
      const angle=turn*Math.PI/3,lift=sign<0?1.10:0
      model.rotation.y=angle;neighbor.rotation.y=angle
      neighbor.position.copy(new Vector3(0,lift,sign*2*half).applyAxisAngle(axis,angle))
      for(let i=-4;i<=4;i++) {
        const a=new Vector3(i*.18,0,sign*(half-.000001)).applyAxisAngle(axis,angle)
        const b=new Vector3(i*.18,0,sign*(half+.000001)).applyAxisAngle(axis,angle)
        expect(height(model,'hydroscapeGround',a.x,a.z)).toBeCloseTo(height(neighbor,'riparianGround',b.x,b.z),4)
        if(Math.abs(i*.18)<.395)expect(height(model,'hydroscapeWater',a.x,a.z)).toBeCloseTo(height(neighbor,'riparianWater',b.x,b.z),5)
      }
    }
  })
  for(const id of ids) {
    it(`${id} covers all six edges with contiguous ground faces`,async()=>{
      const model=await load(id);model.updateMatrixWorld(true)
      for(const edge of nodes(model,'edgeIndex')) {
        const normal=new Vector3().fromArray(edge.userData.normalGltf),lengths:number[]=[]
        for(const mesh of groupMeshes(model,'hydroscapeGround')) {
          const p=mesh.geometry.attributes.position,index=mesh.geometry.index
          for(let i=0;i<(index?.count??p.count);i+=3) {
            const ends=[0,1,2].map((j)=>new Vector3().fromBufferAttribute(p,index?index.getX(i+j):i+j).applyMatrix4(mesh.matrixWorld)).filter((v)=>Math.abs(v.dot(normal)-half)<1e-5)
            if(ends.length===2)lengths.push(Math.hypot(ends[0].x-ends[1].x,ends[0].z-ends[1].z))
          }
        }
        expect(lengths).toHaveLength(20);expect(lengths.reduce((a,b)=>a+b,0)).toBeCloseTo(1.75,5)
      }
    })
    it(`${id} clips to the real bed and contains one connected water sheet`,async()=>{
      const model=await load(id);model.updateMatrixWorld(true)
      const adjacency=new Map<string,Set<string>>(),key=(p:Vector3)=>p.toArray().map((v)=>v.toFixed(5)).join(',')
      for(const mesh of groupMeshes(model,'hydroscapeWater')) {
        const p=mesh.geometry.attributes.position,uv=mesh.geometry.attributes.uv,index=mesh.geometry.index
        for(let i=0;i<p.count;i+=13) {
          const v=new Vector3().fromBufferAttribute(p,i).applyMatrix4(mesh.matrixWorld)
          if(Math.abs(v.z)>half-.001)continue
          const depth=v.y-height(model,'hydroscapeGround',v.x,v.z)
          expect(depth).toBeGreaterThan(-1e-5);expect((1-uv.getY(i))*1.5).toBeCloseTo(depth,4)
        }
        for(let i=0;i<(index?.count??p.count);i+=3) {
          const face=[0,1,2].map((j)=>key(new Vector3().fromBufferAttribute(p,index?index.getX(i+j):i+j)))
          for(const a of face) {if(!adjacency.has(a))adjacency.set(a,new Set());for(const b of face)adjacency.get(a)!.add(b)}
        }
      }
      const queue=[adjacency.keys().next().value!],visited=new Set(queue)
      while(queue.length)for(const next of adjacency.get(queue.pop()!)!)if(!visited.has(next)){visited.add(next);queue.push(next)}
      expect(visited.size).toBe(adjacency.size)
    })
    it(`${id} moves internally without cracks, shoreline drift, boundary waves or root motion`,async()=>{
      const model=await load(id),m=createTerrainMotion(model)!,roots=nodes(model,'terrainTuft').map((o)=>o.position.toArray())
      settle(m,id,0);const initial=snapshot(model)
      const base=groupMeshes(model,'hydroscapeWater').map((mesh)=>Float32Array.from(mesh.geometry.attributes.position.array))
      for(let frame=0;frame<24;frame++) {
        m.update(.1,true)
        for(const [mi,mesh]of groupMeshes(model,'hydroscapeWater').entries()) {
          const p=mesh.geometry.attributes.position,uv=mesh.geometry.attributes.uv,duplicates=new Map<string,Vector3>()
          for(let i=0;i<p.count;i++) {
            const rest=new Vector3().fromArray(base[mi],i*3),now=new Vector3().fromBufferAttribute(p,i),x=rest.x,y=-rest.z
            const edge=Math.max(Math.abs(x/1.75-y/(Math.sqrt(3)*1.75)),Math.abs(y/half),Math.abs(x/1.75+y/(Math.sqrt(3)*1.75)))
            expect(now.distanceTo(rest)).toBeLessThan(.0141)
            if(edge>1-1e-6||(1-uv.getY(i))*1.5<1e-6)expect(now.distanceTo(rest)).toBeLessThan(1e-6)
            const key=rest.toArray().map((v)=>v.toFixed(6)).join(',')
            if(duplicates.has(key))expect(now.distanceTo(duplicates.get(key)!)).toBeLessThan(2e-6)
            else duplicates.set(key,now)
          }
        }
      }
      expect(snapshot(model)).not.toEqual(initial);expect(nodes(model,'terrainTuft').map((o)=>o.position.toArray())).toEqual(roots)
      const paused=snapshot(model);m.update(2,false);expect(snapshot(model)).toEqual(paused)
      m.setSettings({...defaultTerrainSettings(id),activity:0,wind:0});m.update(1,true)
      const calm=snapshot(model);m.update(2,true);expect(snapshot(model)).toEqual(calm)
      expect(model.scale.toArray()).toEqual([1,1,1])
    })
    it(`${id} freezes in five zones then thaws, including finite spray and seasonal grass`,async()=>{
      const model=await load(id),m=createTerrainMotion(model)!,ice=nodes(model,'hydroscapeIce'),spray=nodes(model,'cascadeSpray')
      expect(ice).toHaveLength(5);settle(m,id,0);expect(ice.every((o)=>!o.visible)).toBe(true)
      settle(m,id,.8);expect(ice.some((o)=>o.visible)&&ice.some((o)=>!o.visible)).toBe(true)
      settle(m,id,1);expect(ice.every((o)=>o.visible)).toBe(true);expect(spray.every((o)=>!o.visible)).toBe(true)
      const frozen=snapshot(model);m.update(3,true);expect(snapshot(model)).toEqual(frozen)
      settle(m,id,0);expect(ice.every((o)=>!o.visible)).toBe(true);m.update(1,true);expect(snapshot(model)).not.toEqual(frozen)
      const greens=meshes(model).flatMap((o)=>Array.isArray(o.material)?o.material:[o.material]).filter((o)=>o.name.startsWith('ground_grass')) as MeshStandardMaterial[]
      const summer=greens.map((o)=>o.color.getHex());m.setSettings({...defaultTerrainSettings(id),phase:.5,wind:0})
      for(let i=0;i<180;i++)m.update(1/60,false)
      expect(greens.map((o)=>o.color.getHex())).not.toEqual(summer)
    })
  }
  it('uses bounded ballistic droplets that stay above water, fade and freeze on pause',async()=>{
    const model=await load('waterfall'),m=createTerrainMotion(model)!;settle(m,'waterfall',0)
    const spray=nodes(model,'cascadeSpray'),root=nodes(model,'terrainType')[0]
    const bounds=new Box3(new Vector3().fromArray(root.userData.animationBoundsMin),new Vector3().fromArray(root.userData.animationBoundsMax))
    for(let i=0;i<120;i++) {
      m.update(1/60,true);model.updateMatrixWorld(true)
      for(const p of spray) {
        expect(p.position.y).toBeGreaterThanOrEqual(.0549)
        expect(bounds.containsBox(new Box3().setFromObject(p,true))).toBe(true)
      }
    }
    const before=spray.map((o)=>o.position.toArray());m.update(1,false);expect(spray.map((o)=>o.position.toArray())).toEqual(before)
    m.setSettings({...defaultTerrainSettings('waterfall'),activity:0,wind:0});m.update(1,true)
    expect(spray.every((o)=>!o.visible)).toBe(true)
  })
})
