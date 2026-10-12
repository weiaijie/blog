import { Group, Mesh, Object3D, Quaternion, Vector3 } from 'three'

export type TransportSettings={speed:number;steering:number;access:boolean;load:number}
export type TransportState={distance:number;speed:number;steering:number;access:number;cargo:number}
export const defaultTransportSettings:TransportSettings={speed:.7,steering:0,access:false,load:1}
export const transportAccessLabels:Record<string,string>={rickshaw:'收起车篷','early-car':'打开车门','freight-wagon':'放下侧板'}
export function steeringAngle(angle:number,side:number,track:number,wheelbase:number){
  if(Math.abs(angle)<1e-6||track===0)return angle
  const radius=wheelbase/Math.tan(Math.abs(angle))
  return Math.sign(angle)*Math.atan(wheelbase/(radius-Math.sign(angle)*side*track/2))
}

export function createTransportMotion(model:Group){
  let root:Object3D|undefined
  model.traverse((o)=>{if(o.userData.vehicleKind)root=o})
  if(!root)return undefined
  const data=root.userData,kind=String(data.vehicleKind),rotating:{object:Object3D;base:Quaternion}[]=[],cargo:Object3D[]=[]
  const cloth:{mesh:Mesh;rest:Float32Array}[]=[],links:Object3D[]=[]
  model.traverse((o)=>{
    if(o.userData.vehicleWheel||o.userData.vehicleCrank||o.userData.vehiclePedal||o.userData.vehicleSteer||o.userData.vehicleSteeringWheel||o.userData.vehicleAccess||typeof o.userData.vehicleCanopy==='number')rotating.push({object:o,base:o.quaternion.clone()})
    if(typeof o.userData.vehicleCargo==='number')cargo.push(o)
    if(typeof o.userData.vehicleChain==='number')links.push(o)
    if(o instanceof Mesh&&o.parent?.userData.vehicleCanopySurface)cloth.push({mesh:o,rest:new Float32Array(o.geometry.getAttribute('position').array)})
  })
  const path:Vector3[]=(data.chainPath??[]).map((p:number[])=>new Vector3().fromArray(p)),lengths=[0]
  for(let i=0;i<path.length;i++)lengths.push(lengths[i]+path[i].distanceTo(path[(i+1)%path.length]))
  const chainLength=lengths[lengths.length-1],x=new Vector3(1,0,0),up=new Vector3(0,1,0),q=new Quaternion(),axis=new Vector3(),tangent=new Vector3()
  let settings={...defaultTransportSettings},distance=0,steering=0,access=0
  const state:TransportState={distance:0,speed:.7,steering:0,access:0,cargo:cargo.length}
  return {
    kind,
    setSettings(next:TransportSettings){settings={speed:Math.max(-1,Math.min(2,next.speed)),steering:Math.max(-.42,Math.min(.42,next.steering)),access:next.access,load:Math.max(0,Math.min(1,next.load))}},
    update(delta:number,playing:boolean){
      const canSteer=kind==='bicycle'||kind==='early-car'
      const targetAccess=settings.access&&Math.abs(settings.speed)<.001 ? 1 : 0
      if(playing){
        steering+=(Number(canSteer)*settings.steering-steering)*(1-Math.exp(-delta*8))
        access+=(targetAccess-access)*(1-Math.exp(-delta*5))
        if(Math.abs(access-targetAccess)<1e-5)access=targetAccess
      }
      const speed=access>.001||targetAccess ? 0 : settings.speed
      if(playing)distance+=delta*speed
      let crankAngle=0
      for(const {object}of rotating)if(object.userData.vehicleCrank)crankAngle=distance/.30/object.userData.gearRatio
      for(const {object,base}of rotating){
        const d=object.userData;let angle=0;axis.copy(x)
        if(d.vehicleWheel)angle=distance/d.wheelRadius
        else if(d.vehicleCrank)angle=crankAngle
        else if(d.vehiclePedal)angle=-crankAngle
        else if(d.vehicleSteer){axis.copy(up);angle=steeringAngle(steering,d.steerSide,data.track,data.wheelbase)}
        else if(d.vehicleSteeringWheel){axis.copy(up);angle=steering*5}
        else if(d.vehicleAccess){axis.fromArray(d.accessAxis);angle=access*d.accessAngle}
        else if(typeof d.vehicleCanopy==='number')angle=access*(d.vehicleCanopy-(.35+.12*(d.vehicleCanopy+1.2)/1.4))
        object.quaternion.copy(base).multiply(q.setFromAxisAngle(axis,angle%(Math.PI*2)))
      }
      for(const {mesh,rest}of cloth){
        const position=mesh.geometry.getAttribute('position')
        for(let i=0;i<position.count;i++){
          const y=rest[i*3+1],z=rest[i*3+2],a=Math.atan2(-z,y),phase=(a+1.2)/1.4
          const r=Math.hypot(y,z)+.018*access*Math.sin(phase*Math.PI*8)**2
          const folded=.35+.12*phase,angle=a+(folded-a)*access
          position.setXYZ(i,rest[i*3],Math.cos(angle)*r,-Math.sin(angle)*r)
        }
        position.needsUpdate=true;mesh.geometry.computeVertexNormals();mesh.geometry.computeBoundingSphere();mesh.geometry.computeBoundingBox()
      }
      for(const link of links){
        const traveled=distance/.30*Number(data.rearSprocketRadius),d=((link.userData.vehicleChain*chainLength+traveled)%chainLength+chainLength)%chainLength
        let segment=0;while(segment<path.length-1&&lengths[segment+1]<d)segment++
        const a=path[segment],b=path[(segment+1)%path.length],t=(d-lengths[segment])/(lengths[segment+1]-lengths[segment])
        link.position.copy(a).lerp(b,t);tangent.copy(b).sub(a).normalize();link.quaternion.setFromUnitVectors(up,tangent)
      }
      const visible=Math.round(settings.load*cargo.length)
      for(const object of cargo)object.visible=object.userData.vehicleCargo<visible
      Object.assign(state,{distance,speed,steering,access,cargo:visible})
      return state
    },
  }
}
