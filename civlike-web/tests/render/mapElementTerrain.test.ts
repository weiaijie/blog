import { readFileSync } from 'node:fs'
import { Box3, Group, Mesh, MeshStandardMaterial, Object3D, Vector3 } from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { describe, expect, it } from 'vitest'
import { createTerrainMotion, defaultTerrainSettings, terrainSnow } from '../../src/render/visuals/mapElementTerrain'

const ids=['grassland','rolling-hills','rocky-mountain','snow-peak']
async function load(id:string) {
  const b=readFileSync(new URL(`../../src/render/assets/elements/${id}.glb`,import.meta.url))
  return (await new GLTFLoader().parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'')).scene
}
function nodes(model:Object3D,key:string) {const result:Object3D[]=[];model.traverse((o)=>{if(o.userData[key]!==undefined)result.push(o)});return result}
function settle(motion:NonNullable<ReturnType<typeof createTerrainMotion>>,kind:string,phase:number,snow=terrainSnow(kind,phase)) {
  motion.setSettings({...defaultTerrainSettings(kind),phase,snow,wind:0})
  for(let i=0;i<180;i++)motion.update(1/60,false)
}
function border(model:Group) {
  const points:Vector3[]=[];model.updateMatrixWorld(true)
  model.traverse((o)=>{
    if(!(o instanceof Mesh))return
    const p=o.geometry.getAttribute('position')
    for(let i=0;i<p.count;i++) {
      const v=new Vector3().fromBufferAttribute(p,i).applyMatrix4(o.matrixWorld)
      const norm=Math.max(Math.abs(v.x/1.75+v.z/(Math.sqrt(3)*1.75)),Math.abs(2*v.z/(Math.sqrt(3)*1.75)),Math.abs(v.x/1.75-v.z/(Math.sqrt(3)*1.75)))
      if(Math.abs(norm-1)<1e-5 && Math.abs(v.y-.08)<1e-5 && !points.some((p)=>p.distanceTo(v)<1e-5))points.push(v)
    }
  });return points
}
function triangles(model:Group) {
  const result:Vector3[][]=[];model.updateMatrixWorld(true)
  model.traverse((o)=>{
    if(!(o instanceof Mesh))return
    const p=o.geometry.getAttribute('position'),index=o.geometry.getIndex()
    for(let i=0;i<(index?.count??p.count);i+=3)result.push([0,1,2].map((j)=>new Vector3().fromBufferAttribute(p,index?index.getX(i+j):i+j).applyMatrix4(o.matrixWorld)))
  });return result
}
describe('hex landforms and seasonal surfaces',()=>{
  it('has four distinct elevations rather than recolored copies',async()=>{
    const heights=[]
    for(const id of ids) {
      const model=await load(id),box=new Box3().setFromObject(model)
      heights.push(box.max.y)
      expect(box.min.x).toBeCloseTo(-1.75,4);expect(box.max.x).toBeCloseTo(1.75,4)
      expect(nodes(model,'terrainType')[0].userData.terrainType).toBe(id)
    }
    expect(heights[0]).toBeLessThan(.4)
    for(let i=1;i<heights.length;i++)expect(heights[i]-heights[i-1]).toBeGreaterThan(.4)
  })
  it('matches actual border vertices and anchors across all six edges of every terrain pair',async()=>{
    const models=await Promise.all(ids.map(load)),borders=models.map(border)
    for(const points of borders)expect(points).toHaveLength(90)
    for(let a=0;a<models.length;a++)for(let b=0;b<models.length;b++) {
      const edges=nodes(models[a],'edgeIndex'),other=nodes(models[b],'edgeIndex')
      expect(edges).toHaveLength(6)
      for(const edge of edges) {
        const normal=new Vector3().fromArray(edge.userData.normalGltf),offset=new Vector3().fromArray(edge.userData.neighborOffsetGltf)
        const opposite=other.find((o)=>o.userData.edgeIndex===(edge.userData.edgeIndex+3)%6)!
        expect(edge.userData.profile).toBe('hex-flat-3.5-v1')
        expect(edge.getWorldPosition(new Vector3()).distanceTo(opposite.getWorldPosition(new Vector3()).add(offset))).toBeLessThan(1e-5)
        const seam=borders[a].filter((p)=>Math.abs(p.dot(normal)-1.75*Math.sqrt(3)/2)<1e-5)
        expect(seam).toHaveLength(16)
        for(const p of seam)expect(Math.min(...borders[b].map((q)=>p.distanceTo(q.clone().add(offset))))).toBeLessThan(1e-5)
      }
    }
  })
  it('has continuous top triangles on every edge and a closed underside',async()=>{
    for(const id of ids) {
      const model=await load(id),faces=triangles(model)
      for(const edge of nodes(model,'edgeIndex')) {
        const normal=new Vector3().fromArray(edge.userData.normalGltf),segments:number[]=[]
        for(const face of faces) {
          if(face.some((p)=>p.y<.08-1e-5))continue
          const ends=face.filter((p)=>Math.abs(p.y-.08)<1e-5 && Math.abs(p.dot(normal)-1.75*Math.sqrt(3)/2)<1e-5)
          if(ends.length===2)segments.push(ends[0].distanceTo(ends[1]))
        }
        expect(segments).toHaveLength(15)
        expect(segments.reduce((a,b)=>a+b,0)).toBeCloseTo(1.75,4)
      }
      expect(faces.filter((face)=>face.every((p)=>Math.abs(p.y+.16)<1e-5))).toHaveLength(90)
    }
  })
  for(const id of ids)it(`${id} accumulates snow independently, restores summer and pauses wind and season time`,async()=>{
    const model=await load(id),motion=createTerrainMotion(model)!,zones=nodes(model,'snowThreshold'),tufts=nodes(model,'terrainTuft')
    expect(zones.length).toBeGreaterThan(5);expect(tufts.length).toBeGreaterThan(20)
    settle(motion,id,.25,0);expect(zones.some((z)=>z.visible)).toBe(false)
    const green:MeshStandardMaterial[]=[]
    model.traverse((o)=>{if(o instanceof Mesh)for(const m of Array.isArray(o.material)?o.material:[o.material])if(m instanceof MeshStandardMaterial && m.name==='ground_grass')green.push(m)})
    const summer=green[0].color.clone(),base=new Box3().setFromObject(model).getSize(new Vector3())
    settle(motion,id,.5,.4)
    expect(zones.filter((z)=>z.visible).length).toBeGreaterThan(0)
    expect(zones.filter((z)=>z.visible).length).toBeLessThan(zones.length)
    expect(green[0].color.equals(summer)).toBe(false)
    const opacities:number[]=[]
    for(const zone of zones)zone.traverse((o)=>{if(o instanceof Mesh)opacities.push((o.material as MeshStandardMaterial).opacity)})
    expect(new Set(opacities.map((o)=>o.toFixed(3))).size).toBeGreaterThan(1)
    settle(motion,id,.75,1);expect(zones.every((z)=>z.visible)).toBe(true)
    expect(tufts.some((t)=>t.visible)).toBe(false)
    expect(model.scale.toArray()).toEqual([1,1,1])
    expect(new Box3().setFromObject(model).getSize(new Vector3()).distanceTo(base)).toBeLessThan(1e-7)
    settle(motion,id,.25,0);expect(green[0].color.equals(summer)).toBe(true)
    const still=tufts.map((o)=>o.quaternion.toArray())
    motion.update(2,true);expect(tufts.map((o)=>o.quaternion.toArray())).toEqual(still)
    motion.setSettings({...defaultTerrainSettings(id),automatic:true,wind:.8})
    const active=motion.update(5,true);expect(active.phase).toBeGreaterThan(.25)
    expect(tufts.map((o)=>o.quaternion.toArray())).not.toEqual(still)
    const wind=tufts.map((o)=>o.quaternion.toArray())
    expect(motion.update(20,false)).toEqual(active);expect(tufts.map((o)=>o.quaternion.toArray())).toEqual(wind)
    const wrapped=motion.update(95,true);expect(wrapped.phase).toBeGreaterThanOrEqual(0);expect(wrapped.phase).toBeLessThan(1)
    motion.setSettings({...defaultTerrainSettings(id),...wrapped,automatic:false,wind:0})
    const kept=motion.update(3,false);expect(kept).toEqual(wrapped)
  })
  it('does not attach seasonal controls to non-terrain models',()=>expect(createTerrainMotion(new Group())).toBeUndefined())
})
