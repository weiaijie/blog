import { readFileSync } from 'node:fs'
import { Group, Mesh, MeshStandardMaterial, Object3D, Raycaster, Vector3 } from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { describe, expect, it } from 'vitest'
import { createRouteMotion, defaultRouteSettings, type RouteShape } from '../../src/render/visuals/mapElementRoutes'

const ids=['dirt-road','stone-road','asphalt-road','rail-track']
async function load(id:string){const b=readFileSync(new URL(`../../src/render/assets/elements/${id}.glb`,import.meta.url));return (await new GLTFLoader().parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'')).scene}
function find(model:Group,key:string){const result:Object3D[]=[];model.traverse((o)=>{if(o.userData[key]!==undefined)result.push(o)});return result}
function advance(motion:NonNullable<ReturnType<typeof createRouteMotion>>,seconds:number,playing=true){for(let i=0;i<seconds*60;i++)motion.update(1/60,playing);return motion.update(0,playing)}

describe('route tile construction and connections',()=>{
  for(const id of ids){
    it(`${id} has distinct shapes and real surfaces at every advertised port`,async()=>{
      const model=await load(id),motion=createRouteMotion(model)!,shapes=find(model,'routeShape'),ports=find(model,'routePort')
      expect(shapes.map((o)=>o.userData.routeShape)).toEqual(['straight','bend','junction']);expect(ports).toHaveLength(6)
      model.updateMatrixWorld(true)
      const ground:Mesh[]=[]
      model.traverse((o)=>{if(o instanceof Mesh&&o.material instanceof MeshStandardMaterial&&['route_grass','route_grass_light'].includes(o.material.name)&&o.parent?.name==='RouteRoot_mesh')ground.push(o)})
      const ray=new Raycaster(),down=new Vector3(0,-1,0)
      for(let x=-1.6;x<=1.6;x+=.1)for(let z=-1.4;z<=1.4;z+=.1){
        const nx=x/1.75,ny=-z/(Math.sqrt(3)*1.75)
        if(Math.max(Math.abs(nx-ny),Math.abs(2*ny),Math.abs(nx+ny))>.98)continue
        ray.set(new Vector3(x,1,z),down);const hits=ray.intersectObjects(ground,false)
        expect(hits.length,`${id}: ground hole at ${x},${z}`).toBeGreaterThan(0)
        expect(hits[0].point.y).toBeCloseTo(.08,5)
      }
      for(const shape of shapes){
        motion.setSettings({...defaultRouteSettings,shape:shape.userData.routeShape});const state=motion.update(0,false)
        expect(shapes.filter((s)=>s.visible)).toEqual([shape]);expect(state.ports.length).toBeGreaterThanOrEqual(2)
        for(const edge of shape.userData.ports as number[]){
          const port=ports.find((p)=>p.userData.routePort===edge)!,normal=new Vector3().fromArray(port.userData.normalGltf),center=port.getWorldPosition(new Vector3())
          const lateral=new Vector3(-normal.z,0,normal.x),values:number[]=[]
          const material=id==='rail-track'?'route_steel':id==='dirt-road'?'route_dirt':id==='stone-road'?'route_paver_dark':'route_asphalt'
          shape.traverse((o)=>{if(!(o instanceof Mesh)||!(o.material instanceof MeshStandardMaterial)||o.material.name!==material)return
            const p=o.geometry.getAttribute('position'),index=o.geometry.index
            for(let j=0;j<(index?.count??p.count);j++){const v=new Vector3().fromBufferAttribute(p,index?index.getX(j):j).applyMatrix4(o.matrixWorld).sub(center)
              if(Math.abs(v.dot(normal))<1e-5&&Math.abs(v.y)<1e-5)values.push(v.dot(lateral))
            }
          })
          for(const value of id==='rail-track' ? [-.386,-.334,.334,.386] : [-.725,.725])expect(values.some((v)=>Math.abs(v-value)<1e-5)).toBe(true)
        }
      }
    })
    it(`${id} builds separate pieces, supports rollback, wind and exact pause`,async()=>{
      const model=await load(id),motion=createRouteMotion(model)!,parts=find(model,'routeStart'),tufts=find(model,'routeWind')
      expect(parts.length).toBeGreaterThan(20);expect(tufts.length).toBeGreaterThan(6)
      const visible=[]
      for(const progress of [0,.2,.5,.8,1]){motion.setSettings({...defaultRouteSettings,progress});const state=advance(motion,2);visible.push(state.visible);expect(state.progress).toBeCloseTo(progress,4);expect(state.ports.length).toBe(progress<.99?0:2)}
      expect(visible.every((n,i)=>i===0||n>=visible[i-1])).toBe(true);expect(new Set(visible).size).toBe(5)
      motion.setSettings({...defaultRouteSettings,progress:0});advance(motion,2);expect(motion.update(0,false).visible).toBe(0)
      motion.setSettings({...defaultRouteSettings,progress:0,automatic:true});advance(motion,3)
      const paused=JSON.stringify(motion.update(0,false)),rotation=tufts[0].quaternion.toArray();advance(motion,2,false)
      expect(JSON.stringify(motion.update(0,false))).toBe(paused);expect(tufts[0].quaternion.toArray()).toEqual(rotation)
      advance(motion,1);expect(tufts[0].quaternion.toArray()).not.toEqual(rotation)
      motion.setSettings({...defaultRouteSettings,wind:0});advance(motion,2);const calm=tufts[0].quaternion.toArray();advance(motion,2);expect(tufts[0].quaternion.toArray()).toEqual(calm)
      expect(model.scale.toArray()).toEqual([1,1,1])
    })
  }
  it('joins rotated road ports across styles and keeps rail incompatible',async()=>{
    const models=await Promise.all(ids.map(load))
    for(let a=0;a<models.length;a++)for(let b=0;b<models.length;b++){
      const left=find(models[a],'routePort'),right=find(models[b],'routePort')
      expect(left[0].userData.profile===right[0].userData.profile).toBe((a===3)===(b===3))
      if((a===3)!==(b===3))continue
      for(const p of left)for(const q of right){
        const theta=(p.userData.routePort+3-q.userData.routePort)*Math.PI/3
        const shift=new Vector3().fromArray(p.userData.neighborOffsetGltf)
        const pos=q.position.clone().applyAxisAngle(new Vector3(0,1,0),theta).add(shift)
        expect(pos.distanceTo(p.position)).toBeLessThan(1e-5)
        const normal=new Vector3().fromArray(q.userData.normalGltf).applyAxisAngle(new Vector3(0,1,0),theta)
        expect(normal.dot(new Vector3().fromArray(p.userData.normalGltf))).toBeCloseTo(-1,5)
      }
    }
  })
  it('moves the rail switch independently and closes its exit while moving',async()=>{
    const model=await load('rail-track'),motion=createRouteMotion(model)!,switches=find(model,'routeSwitch')
    expect(switches).toHaveLength(1)
      const root=find(model,'routeKind')[0]
      expect(root.userData.gauge).toBeCloseTo(.668,5)
      expect(root.userData.railCenterSpacing-root.userData.gauge).toBeCloseTo(.052,5)
    motion.setSettings({...defaultRouteSettings,shape:'junction'});expect(motion.update(0,false).ports).toEqual([0,3])
    const before=switches[0].position.clone();motion.setSettings({...defaultRouteSettings,shape:'junction',diverted:true})
    expect(advance(motion,.1).ports).toEqual([0]);const midway=switches[0].position.clone();advance(motion,2,false);expect(switches[0].position.equals(midway)).toBe(true)
    expect(advance(motion,2).ports).toEqual([0,2]);expect(switches[0].position.distanceTo(before)).toBeGreaterThan(.07)
    motion.setSettings({...defaultRouteSettings,shape:'junction',progress:.5});expect(advance(motion,2).ports).toEqual([]);expect(switches[0].visible).toBe(false)
    for(const shape of ['straight','bend'] as RouteShape[]){motion.setSettings({...defaultRouteSettings,shape});advance(motion,2);expect(switches[0].parent!.visible).toBe(false)}
  })
  it('does not create route controls for unrelated assets',()=>expect(createRouteMotion(new Group())).toBeUndefined())
})
