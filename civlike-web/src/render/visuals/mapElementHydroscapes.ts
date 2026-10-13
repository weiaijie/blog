import { BufferAttribute, Color, Group, Mesh, MeshStandardMaterial, Object3D, Vector3 } from 'three'

const radius=1.75,half=radius*Math.sqrt(3)/2
function smooth(v:number) {const t=Math.max(0,Math.min(1,v));return t*t*(3-2*t)}

export function createHydroscapeWater(model:Group) {
  const surfaces:{mesh:Mesh;base:Float32Array;colors:BufferAttribute;tint:Color;depthScale:number;fall:boolean}[]=[]
  const spray:{object:Object3D;base:Vector3;velocity:Vector3;life:number;phase:number;materials:MeshStandardMaterial[]}[]=[]
  model.traverse((node)=>{
    if(node.userData.hydroscapeWater)node.traverse((child)=>{
      if(!(child instanceof Mesh))return
      child.geometry=child.geometry.clone()
      const base=Float32Array.from(child.geometry.attributes.position.array),colors=new BufferAttribute(new Float32Array(base.length).fill(1),3)
      const tint=((Array.isArray(child.material)?child.material[0]:child.material) as MeshStandardMaterial).color.clone()
      child.geometry.setAttribute('color',colors)
      const copies=(Array.isArray(child.material)?child.material:[child.material]).map((m)=>{
        const copy=(m as MeshStandardMaterial).clone();copy.color.setRGB(1,1,1);copy.vertexColors=true;copy.roughness=.30;copy.metalness=.06;return copy
      })
      child.material=Array.isArray(child.material)?copies:copies[0]
      surfaces.push({mesh:child,base,colors,tint,depthScale:Number(node.userData.depthScale),fall:node.userData.hydroscapeWater==='waterfall'})
    })
    if(node.userData.cascadeSpray) {
      const materials:MeshStandardMaterial[]=[]
      node.traverse((child)=>{
        if(!(child instanceof Mesh))return
        const copies=(Array.isArray(child.material)?child.material:[child.material]).map((m)=>{
          const copy=(m as MeshStandardMaterial).clone();copy.transparent=true;copy.depthWrite=false;materials.push(copy);return copy
        });child.material=Array.isArray(child.material)?copies:copies[0]
      })
      spray.push({object:node,base:node.position.clone(),velocity:new Vector3().fromArray(node.userData.sprayVelocityGltf),life:Number(node.userData.sprayLifetime),phase:Number(node.userData.sprayPhase),materials})
    }
  })
  let time=0
  return {
    update(delta:number,playing:boolean,wind:number,activity:number,snow:number) {
      const liquid=1-smooth((snow-.60)/.10)
      if(playing)time+=delta*activity*liquid
      for(const {mesh,base,colors,tint,depthScale,fall} of surfaces) {
        const position=mesh.geometry.attributes.position,uv=mesh.geometry.attributes.uv
        for(let i=0;i<position.count;i++) {
          const x=base[3*i],y=-base[3*i+2],depth=Math.max(0,(1-uv.getY(i))*depthScale)
          const edgeNorm=Math.max(Math.abs(x/radius-y/(Math.sqrt(3)*radius)),Math.abs(y/half),Math.abs(x/radius+y/(Math.sqrt(3)*radius)))
          const mask=smooth(depth/.05)*smooth((1-edgeNorm)/.10)
          const t=uv.getX(i),drop=Math.max(0,Math.min(1,(y+.12)/.28)),slope=fall?1.1/.28*6*drop*(1-drop):0
          const direction=1/Math.sqrt(1+slope*slope)
          const phase=fall?t*45+time*6:x*15+time*1.65+Math.sin(y*4)*.6
          const crest=Math.sin(phase)+wind*.25*Math.sin(y*24+x*9-time*2)
          const wave=crest*.007*mask*activity*liquid
          position.setXYZ(i,x,base[3*i+1]+wave*direction,base[3*i+2]+wave*slope*direction)
          const shallow=1-Math.min(1,depth/.18)
          const impact=fall?Math.exp(-((x/.43)**2+((y+.30)/.24)**2)):0
          const rings=.5+.5*Math.sin(Math.hypot(x,y+.27)*36-time*8)
          const foam=(fall?Math.min(.55,slope*.07)*(.5+.5*Math.sin(x*33+t*25+time*6)) + impact*(.30+.25*rings):0)*mask*activity*liquid
          const glint=Math.max(0,Math.sin(phase))**10*.16*mask*activity*liquid
          colors.setXYZ(i,tint.r*(.62+.25*shallow)*(1-foam)+glint*.3+foam*.72,tint.g*(.84+.10*shallow)*(1-foam)+glint*.4+foam*.89,tint.b*(.92+.05*shallow)*(1-foam)+glint*.45+foam*.92)
        }
        position.needsUpdate=true;colors.needsUpdate=true;mesh.geometry.computeVertexNormals()
      }
      for(const p of spray) {
        const phase=(time/p.life+p.phase)%1,t=phase*p.life
        p.object.visible=liquid>.01&&activity>.01
        p.object.position.copy(p.base).addScaledVector(p.velocity,t)
        p.object.position.y-=1.8*t*t
        for(const material of p.materials)material.opacity=Math.sin(Math.PI*phase)*liquid*activity*.65
      }
    },
  }
}
