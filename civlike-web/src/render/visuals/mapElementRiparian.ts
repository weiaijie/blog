import { BufferAttribute, Group, Mesh, MeshStandardMaterial } from 'three'

function smooth(v:number) {const t=Math.max(0,Math.min(1,v));return t*t*(3-2*t)}

export function createRiparianWater(model:Group) {
  const surfaces:{mesh:Mesh;base:Float32Array;colors:BufferAttribute;depthScale:number;slow:boolean}[]=[]
  model.traverse((node)=>{
    if(!node.userData.riparianWater)return
    node.traverse((child)=>{
      if(!(child instanceof Mesh))return
      child.geometry=child.geometry.clone()
      const base=Float32Array.from(child.geometry.attributes.position.array)
      const colors=new BufferAttribute(new Float32Array(base.length).fill(1),3)
      child.geometry.setAttribute('color',colors)
      const materials=(Array.isArray(child.material)?child.material:[child.material]).map((source)=>{
        const material=(source as MeshStandardMaterial).clone()
        material.vertexColors=true;material.roughness=.32;material.metalness=.08
        return material
      })
      child.material=Array.isArray(child.material)?materials:materials[0]
      surfaces.push({mesh:child,base,colors,depthScale:Number(node.userData.depthScale),slow:node.userData.flowKind==='wetland'})
    })
  })
  let time=0
  return {
    update(delta:number,playing:boolean,wind:number,activity:number,snow:number) {
      const liquid=1-smooth((snow-.60)/.10)
      if(playing)time+=delta*activity*liquid
      for(const {mesh,base,colors,depthScale,slow} of surfaces) {
        const position=mesh.geometry.attributes.position,uv=mesh.geometry.attributes.uv
        for(let i=0;i<position.count;i++) {
          const t=uv.getX(i),depth=Math.max(0,(1-uv.getY(i))*depthScale)
          // GLB flips V. Depth is encoded before export; shore and both ports remain pinned.
          const edge=smooth(depth/.04)*Math.sin(Math.PI*t)**2
          const across=base[i*3],flow=t*35-time*(slow?.55:2.8)
          const crest=Math.sin(flow+across*3)+wind*.35*Math.sin(across*37+t*11-time*1.7)
          position.setY(i,base[i*3+1]+crest*.005*edge*activity*liquid)
          const shallow=1-Math.min(1,depth/.10),glint=Math.max(0,Math.sin(flow+across*3))**8*.10*edge*activity*liquid
          colors.setXYZ(i,.67+shallow*.29+glint,.84+shallow*.12+glint,.91+shallow*.06+glint)
        }
        position.needsUpdate=true;colors.needsUpdate=true;mesh.geometry.computeVertexNormals()
      }
    },
  }
}
