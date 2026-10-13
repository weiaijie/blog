import { BufferAttribute, Group, Matrix4, Mesh, MeshStandardMaterial, Vector3 } from 'three'

// Preview hydraulics: travelling ripples and a delayed downstream pool, not a fluid solver.
export function createChannelWater(model:Group){
  const surfaces:{mesh:Mesh;points:Vector3[];toMesh:Matrix4;colors:BufferAttribute;role:string;bed:number;width:number;extent:number[]}[]=[]
  model.updateMatrixWorld(true)
  model.traverse((part)=>{
    if(!part.userData.channelWater)return
    part.traverse((node)=>{
      if(!(node instanceof Mesh))return
      node.geometry=node.geometry.clone()
      const toPart=new Matrix4().copy(part.matrixWorld).invert().multiply(node.matrixWorld),p=node.geometry.getAttribute('position')
      const points=Array.from({length:p.count},(_,i)=>new Vector3().fromBufferAttribute(p,i).applyMatrix4(toPart))
      const colors=new BufferAttribute(new Float32Array(p.count*3).fill(1),3);node.geometry.setAttribute('color',colors)
      const clone=(m:MeshStandardMaterial)=>{const copy=m.clone();copy.vertexColors=true;return copy}
      node.material=Array.isArray(node.material)?node.material.map((m)=>clone(m as MeshStandardMaterial)):clone(node.material as MeshStandardMaterial)
      surfaces.push({mesh:node,points,toMesh:toPart.invert(),colors,role:part.userData.channelWater,bed:Number(part.userData.channelBed),width:Number(part.userData.channelWidth),extent:part.userData.channelExtent})
    })
  })
  let pool=0,time=0
  const point=new Vector3()
  return {
    update(delta:number,operating:boolean,access:number,constructed:boolean){
      if(!constructed){pool=0;time=0}
      if(operating){time+=delta;pool+=(access-pool)*(1-Math.exp(-delta*1.4));if(Math.abs(pool-access)<.00001)pool=access}
      for(const {mesh,points,toMesh,colors,role,bed,width,extent} of surfaces){
        const downstream=role==='downstream',flow=role==='free'?1:downstream?pool:access
        const depth=downstream?.025+.155*pool:role==='upstream'?.18+.025*(1-access):.18
        const p=mesh.geometry.getAttribute('position')
        for(let i=0;i<points.length;i++){
          const base=points[i],bank=Math.max(0,1-(2*base.x/width)**4),end=Math.min(1,Math.max(0,Math.min(base.z-extent[0],extent[1]-base.z)*6))
          const wave=Math.sin(base.z*12-time*3.6)+.35*Math.sin(base.z*21-base.x*9-time*2.4)
          const weight=Math.max(0,Math.min(1,(base.y-bed)/.18)),amplitude=(.002+.008*flow)*bank*end
          point.set(base.x,bed+(depth+wave*amplitude)*weight,base.z).applyMatrix4(toMesh);p.setXYZ(i,point.x,point.y,point.z)
          const crest=Math.max(0,Math.sin(base.z*12-time*3.6))**10*flow*bank*end
          const light=(.76+.20*bank+.32*crest)*(.78+.22*weight);colors.setXYZ(i,light,light,light)
        }
        p.needsUpdate=true;colors.needsUpdate=true;mesh.geometry.computeVertexNormals();mesh.geometry.computeBoundingBox();mesh.geometry.computeBoundingSphere()
      }
      return pool
    },
  }
}
