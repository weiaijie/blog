import { BufferAttribute, Color, Group, Mesh, MeshStandardMaterial, Object3D, Vector3 } from 'three'

// Lightweight asset-preview effects. No terrain erosion, fluid solver or climate simulation.
export function createGeodynamics(model:Group) {
  const surfaces:{mesh:Mesh;kind:string;base:Float32Array;colors:BufferAttribute;materials:MeshStandardMaterial[]}[]=[]
  const particles:{object:Object3D;kind:string;phase:number;path:number[]}[]=[]
  model.traverse((object)=>{
    const kind=object.userData.terrainEffect as string|undefined
    if(!kind)return
    if(kind==='sand'||kind==='ash')particles.push({object,kind,phase:Number(object.userData.effectPhase),path:object.userData.driftPath??[]})
    else object.traverse((child)=>{
      if(!(child instanceof Mesh))return
      child.geometry=child.geometry.clone()
      const base=Float32Array.from(child.geometry.getAttribute('position').array)
      const colors=new BufferAttribute(new Float32Array(base.length).fill(1),3)
      child.geometry.setAttribute('color',colors)
      const materials=(Array.isArray(child.material)?child.material:[child.material]).map((m)=>{
        const copy=(m as MeshStandardMaterial).clone();copy.vertexColors=true
        if(kind==='water'){copy.roughness=.27;copy.metalness=.12}
        return copy
      })
      child.material=Array.isArray(child.material)?materials:materials[0]
      surfaces.push({mesh:child,kind,base,colors,materials})
    })
  })
  let waterTime=0,lavaTime=0,sandTime=0
  const tint=new Color(),point=new Vector3()
  return {
    update(delta:number,playing:boolean,wind:number,activity:number) {
      if(playing){waterTime+=delta*activity;lavaTime+=delta*activity;sandTime+=delta*wind}
      for(const {mesh,kind,base,colors,materials} of surfaces) {
        const position=mesh.geometry.getAttribute('position')
        for(let i=0;i<position.count;i++) {
          const x=base[i*3],y=base[i*3+1],z=base[i*3+2]
          if(kind==='water') {
            // Fade amplitude near the bank; the bank itself stays fixed.
            const r=Math.hypot((x+.18)/.62,(z-.16)/.45),edge=Math.max(0,Math.min(1,(1-r)*3))
            const wave=Math.sin(x*20+z*9-waterTime*2.4)+.45*Math.sin(z*27-x*11-waterTime*1.8)
            position.setY(i,y+.007*wave*edge*activity)
            const light=.86+.14*Math.sin(x*25+z*13-waterTime*2.1)**8*activity
            tint.setRGB(light,light,light);colors.setXYZ(i,tint.r,tint.g,tint.b)
          }else {
            const flow=.5+.5*Math.sin(y*17+x*9+z*5+lavaTime*2.2)
            const light=.54+.46*flow*activity
            tint.setRGB(light,.60+.40*flow*activity,.40+.60*flow*activity)
            colors.setXYZ(i,tint.r,tint.g,tint.b)
          }
        }
        if(kind==='water'){position.needsUpdate=true;mesh.geometry.computeVertexNormals()}
        else for(const material of materials)material.emissiveIntensity=.15+activity*(.70+.13*Math.sin(lavaTime*2))
        colors.needsUpdate=true
      }
      for(const {object,kind,phase,path} of particles) {
        if(kind==='sand') {
          const t=(phase+sandTime*.11)%1,s=t*(path.length/3-1),i=Math.floor(s),f=s-i
          point.fromArray(path,i*3)
          if(i<path.length/3-1){point.x+=(path[(i+1)*3]-point.x)*f;point.y+=(path[(i+1)*3+1]-point.y)*f;point.z+=(path[(i+1)*3+2]-point.z)*f}
          object.position.copy(point);object.visible=wind>0 && t>.04 && t<.96
        }else {
          const t=(phase+lavaTime*.27)%1
          object.position.set(Math.sin(t*7+phase*6)*.07,t*.65,Math.cos(t*5+phase*6)*.05)
          object.visible=activity>0 && t<.90
        }
      }
    },
  }
}
