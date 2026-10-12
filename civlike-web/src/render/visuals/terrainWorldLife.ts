import * as THREE from 'three'
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js'
import { WATER_LEVEL, createWorldTiles, seededRandom, type GroundPoint } from './terrainWorld'
import { civilizationOccupies, type CivilizationPlan, type SurfaceSampler } from './terrainWorldCivilization'

export type LifeKind = 'traveler' | 'cart' | 'deer' | 'sheep' | 'bird'
export type LifePoint = GroundPoint & { height: number }
export type WorldActor = {kind: LifeKind; path: LifePoint[]; lengths: number[]; length: number; speed: number; phase: number; wait: number; from: string; to: string}

function actor(kind: LifeKind,path: LifePoint[],phase: number,from='',to=''): WorldActor {
  const lengths=[0]
  for(let i=1;i<path.length;i++) lengths.push(lengths[i-1]+Math.hypot(path[i].x-path[i-1].x,path[i].z-path[i-1].z))
  return {kind,path,lengths,length:lengths[lengths.length-1],phase,speed:kind==='bird'?0.55:kind==='cart'?0.19:kind==='traveler'?0.24:0.085,wait:kind==='bird'?0:kind==='traveler'||kind==='cart'?4:7,from,to}
}

export function sampleActorMotion(a: WorldActor, time: number) {
  const travel=a.length/a.speed,cycle=2*(travel+a.wait)
  const period=a.kind==='bird'?travel:cycle
  const clock=((time+a.phase)%period+period)%period
  const back=a.kind!=='bird' && clock>=travel+a.wait, leg=back?clock-travel-a.wait:clock
  const moving=leg<travel, distance=(back?1-Math.min(1,leg/travel):Math.min(1,leg/travel))*a.length
  let index=1
  while(index<a.lengths.length-1 && a.lengths[index]<distance) index++
  const p=a.path[index-1],q=a.path[index],t=(distance-a.lengths[index-1])/(a.lengths[index]-a.lengths[index-1]||1)
  return {x:p.x+(q.x-p.x)*t,z:p.z+(q.z-p.z)*t,height:p.height+(q.height-p.height)*t,
    heading:Math.atan2(q.x-p.x,q.z-p.z)+(back?Math.PI:0),moving,
    state:moving?'traveling':back?'loading':'unloading',destination:back?a.from:a.to}
}

export function createLifePlan(seed: number,plan: CivilizationPlan,sample: SurfaceSampler) {
  const random=seededRandom(seed^0x27ad942),actors: WorldActor[]=[]
  const routes=new Map<string,LifePoint[]>()
  for(const road of plan.roads) {
    if(road.to==='dock') continue
    const key=`${road.from}:${road.to}`,path=routes.get(key)??[]
    for(let i=1;i<road.points.length;i++) {
      const p=road.points[i-1],q=road.points[i],count=Math.ceil(Math.hypot(q.x-p.x,q.z-p.z)/0.08)
      for(let j=path.length?1:0;j<=count;j++) {
        const t=j/count,x=p.x+(q.x-p.x)*t,z=p.z+(q.z-p.z)*t
        const height=road.bridge?p.height*(1-t)+q.height*t+0.035+Math.sin(t*Math.PI)*0.22:(sample(x,z)?.height??p.height)+0.035
        path.push({x,z,height})
      }
    }
    routes.set(key,path)
  }
  for(const [key,path] of routes) {
    if(path.length<2) continue
    const [from,to]=key.split(':')
    for(let i=0;i<3;i++) actors.push(actor(i===2?'cart':'traveler',path,random()*180,from,to))
  }
  const tiles=createWorldTiles()
  for(const kind of ['deer','sheep'] as const) {
    const habitat=tiles.map((t)=>sample(t.center.x,t.center.z)).filter((p)=>p && p.height>WATER_LEVEL+0.12 && p.shore>1
      && p.rock<0.2 && p.desert<0.4 && p.wetland<0.3 && !civilizationOccupies(plan,p)
      && (kind==='deer'?p.forest>0.3:p.forest<0.35))
    for(let herd=0;herd<Math.min(4,habitat.length);herd++) {
      const home=habitat[Math.floor(random()*habitat.length)]!
      for(let member=0;member<4;member++) {
        const angle=random()*Math.PI*2,r=0.12+random()*0.55
        const start={x:home.x+Math.cos(angle)*r,z:home.z+Math.sin(angle)*r}
        const end={x:start.x+Math.cos(angle+1.4)*0.6,z:start.z+Math.sin(angle+1.4)*0.6}
        const path=Array.from({length:25},(_,i)=>sample(start.x+(end.x-start.x)*i/24,start.z+(end.z-start.z)*i/24))
        if(path.some((p)=>!p || p.height<WATER_LEVEL+0.08 || p.shore<0.5 || p.rock>0.25 || civilizationOccupies(plan,p))) continue
        actors.push(actor(kind,path.map((p)=>({...p!,height:p!.height+0.015})),random()*80))
      }
    }
  }
  for(let i=0;i<8;i++) {
    const center=plan.places[i%plan.places.length]?.center??{x:0,z:0},path: LifePoint[]=[]
    for(let j=0;j<=48;j++) {
      const a=j/48*Math.PI*2,r=1.2+i*0.12,x=center.x+Math.cos(a)*r,z=center.z+Math.sin(a)*r
      path.push({x,z,height:Math.max(0.3,sample(x,z)?.height??0)+1.2})
    }
    actors.push(actor('bird',path,random()*30))
  }
  return actors
}

export function createWorldLife(seed: number, plan: CivilizationPlan,sample: SurfaceSampler) {
  const actors=createLifePlan(seed,plan,sample),group=new THREE.Group()
  group.name='world-residents-and-wildlife'
  const material=new THREE.MeshStandardMaterial({vertexColors:true,roughness:1,flatShading:true})
  const matrix=new THREE.Object3D()
  const updates: ((time:number)=>void)[]=[]
  function colored(geometry:THREE.BufferGeometry,color:string) {
    const geo=geometry.index?geometry.toNonIndexed():geometry
    if(geo!==geometry) geometry.dispose()
    geo.deleteAttribute('uv')
    const c=new THREE.Color(color),count=geo.getAttribute('position').count
    geo.setAttribute('color',new THREE.Float32BufferAttribute(Array.from({length:count},()=>[c.r,c.g,c.b]).flat(),3))
    return geo
  }
  const box=(x:number,y:number,z:number,w:number,h:number,d:number,color:string)=>colored(new THREE.BoxGeometry(w,h,d).translate(x,y,z),color)
  const ball=(x:number,y:number,z:number,r:number,sx:number,sy:number,sz:number,color:string)=>colored(new THREE.IcosahedronGeometry(r,0).scale(sx,sy,sz).translate(x,y,z),color)
  function batch(parts:THREE.BufferGeometry[],list:WorldActor[],pose:(a:WorldActor,time:number,index:number)=>void) {
    if(!list.length) {parts.forEach((p)=>p.dispose());return}
    const geo=mergeGeometries(parts)!,mesh=new THREE.InstancedMesh(geo,material,list.length)
    parts.forEach((p)=>p.dispose());mesh.castShadow=true;mesh.receiveShadow=true;mesh.frustumCulled=false;group.add(mesh)
    updates.push((time)=> {
      list.forEach((a,index)=>{matrix.position.set(0,0,0);matrix.rotation.set(0,0,0);matrix.scale.setScalar(1);pose(a,time,index);matrix.updateMatrix();mesh.setMatrixAt(index,matrix.matrix)})
      mesh.instanceMatrix.needsUpdate=true
    })
  }
  function root(a:WorldActor,time:number) {
    const p=sampleActorMotion(a,time)
    matrix.position.set(p.x,p.height,p.z);matrix.rotation.y=p.heading
    return p
  }
  for(const kind of ['traveler','cart','deer','sheep','bird'] as const) {
    const list=actors.filter((a)=>a.kind===kind)
    if(kind==='bird') {
      batch([ball(0,0,0,0.025,0.8,0.7,2,'#f3efe0')],list,(a,t)=>{root(a,t)})
      for(const side of [-1,1]) batch([box(side*0.055,0,0,0.1,0.006,0.027,'#e7e7d9')],list,(a,t)=>{root(a,t);matrix.rotation.z=Math.sin(t*5+a.phase)*0.42*side})
      continue
    }
    const human=kind==='traveler'||kind==='cart',sheep=kind==='sheep'
    const body=human?[
      box(0,0.095,0,0.046,0.071,0.037,kind==='cart'?'#b88949':'#3e7d91'),ball(0,0.148,0.004,0.028,0.8,1,0.85,'#d3ad84'),
      box(0,0.17,0,0.062,0.014,0.054,'#846448'),box(0,0.097,-0.026,0.038,0.048,0.025,'#906e4b'),
    ]:[ball(0,0.092,0,0.07,0.78,sheep?0.9:0.7,1.6,sheep?'#e9e3cb':'#af8556'),ball(0,0.135,0.094,0.033,0.7,1,1.15,sheep?'#514f45':'#b48f64')]
    if(kind==='deer') for(const side of [-1,1]) {
      body.push(box(side*0.018,0.19,0.09,0.009,0.09,0.009,'#735a42'),box(side*0.03,0.22,0.09,0.035,0.007,0.008,'#735a42'))
    }
    if(kind==='cart') body.push(box(0,0.07,-0.19,0.14,0.025,0.18,'#987951'),box(0,0.116,-0.19,0.11,0.075,0.13,'#c3ae77'),box(0,0.052,-0.09,0.08,0.014,0.13,'#745b41'))
    batch(body,list,(a,t)=>{const p=root(a,t);matrix.position.y+=p.moving?Math.sin(t*12+a.phase)*0.003:0})
    for(const side of [-1,1]) {
      batch([box(side*0.016,0.028,human?0:0.055,0.013,0.055,0.013,'#514b3d'),...(!human?[box(side*0.038,0.028,-0.058,0.013,0.055,0.013,'#514b3d')]:[])],list,(a,t)=> {
        const p=root(a,t);matrix.rotation.x=p.moving?Math.sin(t*(human?12:7)+a.phase)*0.28*side:0
      })
      if(kind==='cart') batch([colored(new THREE.CylinderGeometry(0.041,0.041,0.015,10).rotateZ(Math.PI/2).translate(side*0.079,0.039,-0.19),'#554b3e')],list,(a,t)=>{root(a,t)})
    }
  }
  updates.forEach((update)=>update(0))
  return {group,actors,animate:(time:number)=>updates.forEach((update)=>update(time)),position:(kind:LifeKind,time:number)=> {
    const a=actors.find((item)=>item.kind===kind)
    return a?sampleActorMotion(a,time):null
  }}
}
