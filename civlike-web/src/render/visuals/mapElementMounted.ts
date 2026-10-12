import { Group, Mesh, Object3D, Quaternion, Vector3 } from 'three'
import { createAnimalMotion, defaultAnimalSettings } from './mapElementAnimals'

export type MountedSettings={speed:number;load:number}
export type MountedState={distance:number;speed:number;cargo:number;stride:number}
export const defaultMountedSettings:MountedSettings={speed:.7,load:1}

export function createMountedMotion(model:Group){
  let root:Object3D|undefined
  const anchors=new Map<string,Object3D>(),wheels:Object3D[]=[],cargo:Object3D[]=[],torsos:{object:Object3D;base:Quaternion}[]=[]
  const cables:{mesh:Mesh;a:string;b:string;sag:number;bulge:number;radius:number;vertices:number[]}[]=[]
  model.traverse((o)=>{
    if(o.userData.mountKind)root=o
    if(o.userData.mountAnchor)anchors.set(o.userData.mountAnchor,o)
    if(o.userData.mountWheelRadius)wheels.push(o)
    if(typeof o.userData.mountCargo==='number')cargo.push(o)
    if(o.userData.mountTorso)torsos.push({object:o,base:o.quaternion.clone()})
    if(o instanceof Mesh&&o.parent?.userData.mountCable){
      const d=o.parent.userData
      // Export may split material primitives. Each cable is a single material and tube.
      cables.push({mesh:o,a:d.mountCable[0],b:d.mountCable[1],sag:d.cableSag,bulge:d.cableBulge,radius:d.cableRadius,vertices:[]})
    }
  })
  if(!root)return undefined
  // glTF can duplicate/reorder tube vertices at hard normals. Bind by authored position.
  model.updateMatrixWorld(true)
  for(const cable of cables){
    const {mesh}=cable,a=mesh.worldToLocal(anchors.get(cable.a)!.getWorldPosition(new Vector3())),b=mesh.worldToLocal(anchors.get(cable.b)!.getWorldPosition(new Vector3()))
    const tangent=b.clone().sub(a).normalize(),across=tangent.clone().cross(new Vector3(0,1,0)).normalize(),normal=tangent.clone().cross(across).normalize()
    const samples:Vector3[]=[]
    for(let row=0;row<13;row++)for(let side=0;side<6;side++){
      const t=row/12,s=Math.sin(Math.PI*t),angle=side*Math.PI/3
      const p=a.clone().lerp(b,t).add(new Vector3(cable.bulge*s,-cable.sag*s,0))
      samples.push(p.addScaledVector(across,Math.cos(angle)*cable.radius).addScaledVector(normal,Math.sin(angle)*cable.radius))
    }
    const p=mesh.geometry.getAttribute('position'),v=new Vector3()
    for(let i=0;i<p.count;i++){
      v.fromBufferAttribute(p,i);let nearest=0
      for(let j=1;j<samples.length;j++)if(v.distanceToSquared(samples[j])<v.distanceToSquared(samples[nearest]))nearest=j
      if(v.distanceTo(samples[nearest])>.001)throw new Error('Harness geometry does not match authored cable')
      cable.vertices.push(nearest)
    }
  }
  const horse=createAnimalMotion(model,true)!
  horse.setSettings({...defaultAnimalSettings,behavior:'walk'})
  const stride=Number(root.userData.strideMeters),state:MountedState={distance:0,speed:.7,cargo:cargo.length,stride:0}
  let settings={...defaultMountedSettings},distance=0,initialized=false
  const x=new Vector3(1,0,0),up=new Vector3(0,1,0),q=new Quaternion()
  const a=new Vector3(),b=new Vector3(),center=new Vector3(),tangent=new Vector3(),across=new Vector3(),normal=new Vector3()
  return {
    setSettings(next:MountedSettings){settings={speed:Math.max(0,Math.min(1.4,next.speed)),load:Math.max(0,Math.min(1,next.load))}},
    update(delta:number,playing:boolean){
      const step=playing ? delta*settings.speed : 0
      distance+=step
      const count=Math.round(settings.load*cargo.length)
      for(const item of cargo)item.visible=item.userData.mountCargo<count
      Object.assign(state,{distance,speed:settings.speed,cargo:count,stride:distance/stride%1})
      if(initialized&&step===0)return state
      // The reused stance travels 0.38 m in 62% of a cycle at 1.15 cycles/s.
      horse.update(step/(stride*1.15),playing&&settings.speed>0)
      for(const wheel of wheels)wheel.quaternion.setFromAxisAngle(x,(distance/wheel.userData.mountWheelRadius)%(Math.PI*2))
      for(const {object,base}of torsos)object.quaternion.copy(base).multiply(q.setFromAxisAngle(x,.017*Math.sin(distance/stride*Math.PI*4)))
      model.updateMatrixWorld(true)
      for(const cable of cables){
        const {mesh}=cable,p=mesh.geometry.getAttribute('position')
        mesh.worldToLocal(anchors.get(cable.a)!.getWorldPosition(a));mesh.worldToLocal(anchors.get(cable.b)!.getWorldPosition(b))
        for(let index=0;index<p.count;index++){
          const row=Math.floor(cable.vertices[index]/6),side=cable.vertices[index]%6
          const t=row/12,s=Math.sin(Math.PI*t)
          center.copy(a).lerp(b,t);center.x+=cable.bulge*s;center.y-=cable.sag*s
          tangent.copy(b).sub(a);tangent.x+=cable.bulge*Math.PI*Math.cos(Math.PI*t);tangent.y-=cable.sag*Math.PI*Math.cos(Math.PI*t);tangent.normalize()
          across.crossVectors(tangent,up).normalize();normal.crossVectors(tangent,across).normalize()
          const angle=side*Math.PI/3,c=Math.cos(angle)*cable.radius,sn=Math.sin(angle)*cable.radius
          p.setXYZ(index,center.x+across.x*c+normal.x*sn,center.y+across.y*c+normal.y*sn,center.z+across.z*c+normal.z*sn)
        }
        p.needsUpdate=true;mesh.geometry.computeVertexNormals();mesh.geometry.computeBoundingBox();mesh.geometry.computeBoundingSphere()
      }
      initialized=true
      return state
    },
  }
}
