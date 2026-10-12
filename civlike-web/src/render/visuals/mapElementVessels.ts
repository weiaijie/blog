import { Group, Mesh, Object3D, Vector3 } from 'three'

export type VesselSettings={speed:number;wind:number;waves:number;rudder:number;trim:number;load:number}
export type VesselState={distance:number;speed:number;rudder:number;cargo:number;heave:number}
export const defaultVesselSettings:VesselSettings={speed:.7,wind:.65,waves:.45,rudder:0,trim:.22,load:1}

export function createVesselMotion(model:Group){
  let root:Object3D|undefined
  const rudders:Object3D[]=[],booms:Object3D[]=[],props:Object3D[]=[],cargo:Object3D[]=[],helms:Object3D[]=[]
  const sails:{mesh:Mesh;rest:Float32Array;weights:number[]}[]=[]
  model.traverse((o)=>{
    if(o.userData.vesselKind)root=o
    if(o.userData.vesselRudder)rudders.push(o)
    if(o.userData.vesselBoom)booms.push(o)
    if(o.userData.vesselPropeller)props.push(o)
    if(o.userData.vesselHelm)helms.push(o)
    if(typeof o.userData.vesselCargo==='number')cargo.push(o)
    if(o instanceof Mesh&&o.parent?.userData.vesselSail){
      const [a,b,c]=o.parent.userData.sailCorners.map((p:number[])=>new Vector3().fromArray(p)),p=o.geometry.getAttribute('position'),rest=new Float32Array(p.array),weights=[]
      const determinant=(b.y-c.y)*(a.z-c.z)+(c.z-b.z)*(a.y-c.y)
      for(let i=0;i<p.count;i++){
        const u=((b.y-c.y)*(p.getZ(i)-c.z)+(c.z-b.z)*(p.getY(i)-c.y))/determinant
        const v=((c.y-a.y)*(p.getZ(i)-c.z)+(a.z-c.z)*(p.getY(i)-c.y))/determinant
        weights.push(Math.max(0,27*u*v*(1-u-v)))
      }
      sails.push({mesh:o,rest,weights})
    }
  })
  if(!root)return undefined
  const origin=root.position.clone(),restRotation=root.quaternion.clone(),sailing=root.userData.vesselKind==='sailboat'
  let settings={...defaultVesselSettings},time=0,distance=0,rudder=0,trim=.22
  const state:VesselState={distance:0,speed:.7,rudder:0,cargo:cargo.length,heave:0}
  return {
    setSettings(next:VesselSettings){settings={speed:Math.max(-1,Math.min(2,next.speed)),wind:Math.max(0,Math.min(1,next.wind)),waves:Math.max(0,Math.min(1,next.waves)),rudder:Math.max(-.44,Math.min(.44,next.rudder)),trim:Math.max(-.85,Math.min(.85,next.trim)),load:Math.max(0,Math.min(1,next.load))}},
    update(delta:number,playing:boolean){
      if(playing){time+=delta;distance+=delta*(sailing?0:settings.speed);rudder+=(settings.rudder-rudder)*(1-Math.exp(-delta*7));trim+=(settings.trim-trim)*(1-Math.exp(-delta*7))}
      root!.quaternion.copy(restRotation);root!.rotateX(Math.sin(time*.83)*.018*settings.waves);root!.rotateZ(Math.sin(time*1.17+.8)*.035*settings.waves)
      const heave=Math.sin(time*1.1)*.042*settings.waves;root!.position.copy(origin);root!.position.y+=heave
      for(const object of rudders)object.rotation.y=rudder
      for(const object of helms)object.rotation.z=rudder*3
      for(const object of booms)object.rotation.y=trim
      for(const object of props)object.rotation.z=distance*9%(Math.PI*2)
      for(const {mesh,rest,weights}of sails){
        const p=mesh.geometry.getAttribute('position')
        for(let i=0;i<p.count;i++)p.setX(i,rest[i*3]+settings.wind*.14*weights[i]*(1+.14*Math.sin(time*3+rest[i*3+1]*3)))
        p.needsUpdate=true;mesh.geometry.computeVertexNormals();mesh.geometry.computeBoundingBox();mesh.geometry.computeBoundingSphere()
      }
      const count=Math.round(settings.load*cargo.length);for(const object of cargo)object.visible=object.userData.vesselCargo<count
      Object.assign(state,{distance,speed:sailing?0:settings.speed,rudder,cargo:count,heave})
      return state
    },
    sailing,
  }
}
