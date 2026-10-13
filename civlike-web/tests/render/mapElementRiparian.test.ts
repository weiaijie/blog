import { readFileSync } from 'node:fs'
import { Group, Mesh, Object3D, Raycaster, Vector3 } from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { describe, expect, it } from 'vitest'
import { createTerrainMotion, defaultTerrainSettings } from '../../src/render/visuals/mapElementTerrain'

const half=1.75*Math.sqrt(3)/2,ids=['wetland','river-bend']
async function load(id:string) {const b=readFileSync(new URL(`../../src/render/assets/elements/${id}.glb`,import.meta.url));return (await new GLTFLoader().parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'')).scene}
function nodes(root:Object3D,key:string) {const list:Object3D[]=[];root.traverse((o)=>{if(o.userData[key]!==undefined)list.push(o)});return list}
function meshes(root:Object3D) {const list:Mesh[]=[];root.traverse((o)=>{if(o instanceof Mesh)list.push(o)});return list}
function points(root:Object3D) {root.updateWorldMatrix(true,true);return meshes(root).flatMap((m)=>Array.from({length:m.geometry.attributes.position.count},(_,i)=>new Vector3().fromBufferAttribute(m.geometry.attributes.position,i).applyMatrix4(m.matrixWorld)))}
function ground(model:Group) {return meshes(nodes(model,'riparianGround')[0])}
function bed(model:Group,x:number,z:number) {model.updateMatrixWorld(true);const hits=new Raycaster(new Vector3(x,2,z),new Vector3(0,-1,0)).intersectObjects(ground(model),false);expect(hits.length).toBeGreaterThan(0);return hits[0].point.y}
function water(model:Group) {return meshes(nodes(model,'riparianWater')[0])}
function waterSnapshot(model:Group) {return water(model).map((m)=>Array.from(m.geometry.attributes.position.array))}
function settle(m:NonNullable<ReturnType<typeof createTerrainMotion>>,kind:string,snow:number) {m.setSettings({...defaultTerrainSettings(kind),snow});for(let i=0;i<180;i++)m.update(1/60,false)}
function area(model:Group) {
  let value=0
  for(const mesh of water(model)) {
    const p=mesh.geometry.attributes.position,index=mesh.geometry.index
    for(let i=0;i<(index?.count??p.count);i+=3) {
      const [a,b,c]=[0,1,2].map((j)=>new Vector3().fromBufferAttribute(p,index?index.getX(i+j):i+j))
      value+=b.sub(a).cross(c.sub(a)).length()/2
    }
  }
  return value
}

describe('river bends and wetland hexes',()=>{
  it('has a cut bank and point bar, with a wider wetland basin and actual hummocks',async()=>{
    const river=await load('river-bend'),wetland=await load('wetland')
    expect(bed(river,1.17,0)-bed(river,-.02,0)).toBeGreaterThan(.09)
    expect(bed(river,.58,0)).toBeLessThan(-.06)
    expect(bed(wetland,-.32,.45)).toBeGreaterThan(.04)
    expect(bed(wetland,-.06,.45)).toBeLessThan(.04)
    expect(area(wetland)).toBeGreaterThan(area(river)*1.2)
    for(const model of [river,wetland])expect(nodes(model,'terrainTuft').length).toBeGreaterThan(40)
  })
  it('matches actual bed and water vertices across both ports in all six rotations',async()=>{
    const models=await Promise.all(ids.map(load)),axis=new Vector3(0,1,0)
    for(const a of models)for(const b of models)for(let turn=0;turn<6;turn++) {
      const angle=turn*Math.PI/3,rotate=(v:Vector3)=>v.clone().applyAxisAngle(axis,angle)
      const offset=rotate(new Vector3(0,0,2*half))
      for(const key of ['riparianGround','riparianWater']) {
        const top=points(nodes(a,key)[0]).filter((p)=>Math.abs(p.z-half)<1e-5)
        const bottom=points(nodes(b,key)[0]).filter((p)=>Math.abs(p.z+half)<1e-5).map((p)=>rotate(p).add(offset))
        expect(top.length).toBeGreaterThan(10)
        if(key==='riparianWater')expect(Math.max(...top.map((p)=>p.x))-Math.min(...top.map((p)=>p.x))).toBeCloseTo(.8,5)
        for(const p of top)expect(Math.min(...bottom.map((q)=>q.distanceTo(rotate(p))))).toBeLessThan(1e-5)
      }
      const ports=nodes(a,'edgeIndex').filter((o)=>o.userData.profile==='hex-river-080-v1')
      expect(ports.map((o)=>o.userData.edgeIndex).sort()).toEqual([1,4])
      expect(ports.every((o)=>o.userData.waterWidth===.8&&o.userData.waterLevel===.04)).toBe(true)
    }
  })
  it('keeps the other four edges level with the existing grassland mesh',async()=>{
    const grass=await load('grassland'),grassPoints=points(grass)
    for(const id of ids) {
      const model=await load(id),vertices=points(nodes(model,'riparianGround')[0])
      for(const edge of nodes(model,'edgeIndex').filter((o)=>![1,4].includes(o.userData.edgeIndex))) {
        const normal=new Vector3().fromArray(edge.userData.normalGltf)
        const seam=vertices.filter((p)=>Math.abs(p.dot(normal)-half)<1e-5)
        expect(seam.length).toBeGreaterThanOrEqual(16);expect(seam.every((p)=>Math.abs(p.y-.08)<1e-5)).toBe(true)
        const old=grassPoints.filter((p)=>Math.abs(p.dot(normal)-half)<1e-5&&Math.abs(p.y-.08)<1e-5)
        for(const p of old)expect(Math.min(...seam.map((q)=>q.distanceTo(p)))).toBeLessThan(1e-5)
      }
    }
  })
  it('covers every boundary segment with a real top triangle, without sawtooth holes',async()=>{
    for(const id of ids) {
      const model=await load(id);model.updateMatrixWorld(true)
      for(const edge of nodes(model,'edgeIndex')) {
        const normal=new Vector3().fromArray(edge.userData.normalGltf),segments:number[]=[]
        for(const mesh of ground(model)) {
          const p=mesh.geometry.attributes.position,index=mesh.geometry.index
          for(let i=0;i<(index?.count??p.count);i+=3) {
            const face=[0,1,2].map((j)=>new Vector3().fromBufferAttribute(p,index?index.getX(i+j):i+j).applyMatrix4(mesh.matrixWorld))
            const ends=face.filter((v)=>Math.abs(v.dot(normal)-half)<1e-5)
            if(ends.length===2)segments.push(Math.hypot(ends[0].x-ends[1].x,ends[0].z-ends[1].z))
          }
        }
        expect(segments,`${id}: edge ${edge.userData.edgeIndex}`).toHaveLength(15)
        expect(segments.reduce((a,b)=>a+b,0)).toBeCloseTo(1.75,4)
      }
    }
  })
  for(const id of ids) {
    it(`${id} clips the water to the real bed and exports usable depth coordinates`,async()=>{
      const model=await load(id)
      for(const mesh of water(model)) {
        const p=mesh.geometry.attributes.position,uv=mesh.geometry.attributes.uv
        expect(p.count).toBeGreaterThan(1000)
        for(let i=0;i<p.count;i+=17) {
          const point=new Vector3().fromBufferAttribute(p,i).applyMatrix4(mesh.matrixWorld)
          // Endpoints are tested separately; avoid ray ambiguity at a triangle's outer boundary.
          if(Math.abs(point.z)>half-.001)continue
          const depth=.04-bed(model,point.x,point.z)
          expect(depth).toBeGreaterThanOrEqual(-1e-5)
          expect((1-uv.getY(i))*.15).toBeCloseTo(depth,4)
          expect(point.y).toBeCloseTo(.04,5)
        }
      }
    })
    it(`${id} ripples in place, pins shores and ports, pauses and respects zero flow`,async()=>{
      const model=await load(id),motion=createTerrainMotion(model)!
      settle(motion,id,0);const before=waterSnapshot(model)
      motion.setSettings({...defaultTerrainSettings(id),wind:0});motion.update(1,true)
      expect(waterSnapshot(model)).not.toEqual(before)
      for(const mesh of water(model)) {
        const p=mesh.geometry.attributes.position,uv=mesh.geometry.attributes.uv
        for(let i=0;i<p.count;i++) {
          const y=p.getY(i),t=uv.getX(i),depth=(1-uv.getY(i))*.15
          expect(Number.isFinite(y)).toBe(true);expect(Math.abs(y-.04)).toBeLessThan(.006)
          if(depth<1e-6||t<1e-6||t>1-1e-6)expect(y).toBeCloseTo(.04,5)
        }
      }
      const active=waterSnapshot(model);motion.update(5,false);expect(waterSnapshot(model)).toEqual(active)
      motion.setSettings({...defaultTerrainSettings(id),activity:0,wind:0});motion.update(1,true)
      const calm=waterSnapshot(model);motion.update(5,true);expect(waterSnapshot(model)).toEqual(calm)
      motion.setSettings({...defaultTerrainSettings(id),activity:1,wind:0});motion.update(1,true);expect(waterSnapshot(model)).not.toEqual(calm)
      expect(model.scale.toArray()).toEqual([1,1,1])
    })
    it(`${id} freezes in separate ice zones and restores open water without moving roots`,async()=>{
      const model=await load(id),motion=createTerrainMotion(model)!,tufts=nodes(model,'terrainTuft'),ice=nodes(model,'riparianIce')
      const roots=tufts.map((p)=>p.position.toArray())
      expect(ice).toHaveLength(5);settle(motion,id,0);expect(ice.every((p)=>!p.visible)).toBe(true)
      settle(motion,id,.8);expect(ice.some((p)=>p.visible)).toBe(true);expect(ice.some((p)=>!p.visible)).toBe(true)
      settle(motion,id,1);expect(ice.every((p)=>p.visible)).toBe(true)
      const frozen=waterSnapshot(model);motion.update(2,true);expect(waterSnapshot(model)).toEqual(frozen)
      settle(motion,id,0);expect(ice.every((p)=>!p.visible)).toBe(true)
      motion.update(1,true);expect(waterSnapshot(model)).not.toEqual(frozen)
      expect(tufts.map((p)=>p.position.toArray())).toEqual(roots)
    })
  }
})
