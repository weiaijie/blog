import { Group, Material, Mesh, Object3D, Vector3 } from 'three'

export function createSteamMotion(model:Group){
  let root:Object3D|undefined
  const anchors=new Map<string,Object3D>(),crossheads:Object3D[]=[],rods:Object3D[]=[],puffs:{object:Object3D;materials:Material[]}[]=[]
  model.traverse((o)=>{
    if(o.userData.vehicleKind==='steam-locomotive')root=o
    if(o.userData.steamAnchor)anchors.set(o.userData.steamAnchor,o)
    if(o.userData.steamCrosshead)crossheads.push(o)
    if(o.userData.steamRod)rods.push(o)
    if(typeof o.userData.steamPuff==='number'){
      const materials:Material[]=[]
      o.traverse((child)=>{if(child instanceof Mesh){
        const copy=(m:Material)=>{const c=m.clone();c.transparent=true;c.depthWrite=false;materials.push(c);return c}
        child.material=Array.isArray(child.material)?child.material.map(copy):copy(child.material)
      }})
      puffs.push({object:o,materials})
    }
  })
  if(!root)return undefined
  let time=0
  const a=new Vector3(),b=new Vector3(),direction=new Vector3(),up=new Vector3(0,1,0)
  const local=(o:Object3D,target:Vector3)=>root!.worldToLocal(o.getWorldPosition(target))
  return {
    update(delta:number,power:number){
      time+=delta*Math.abs(power)
      root!.updateWorldMatrix(true,true)
      for(const cross of crossheads){
        const pin=local(anchors.get(`pin${cross.userData.steamCrosshead}_0`)!,a),length=Number(cross.userData.connectingLength)
        cross.position.set(pin.x,.27,pin.z+Math.sqrt(length*length-(pin.y-.27)**2))
      }
      root!.updateWorldMatrix(true,true)
      for(const rod of rods){
        const [from,to]=rod.userData.steamRod
        local(anchors.get(from)!,a);local(anchors.get(to)!,b);direction.copy(b).sub(a)
        rod.position.copy(a);rod.scale.set(1,direction.length(),1);rod.quaternion.setFromUnitVectors(up,direction.normalize())
      }
      for(const {object,materials}of puffs){
        const phase=(time*.6+object.userData.steamPuff/10)%1
        object.position.set(Math.sin(phase*3+object.userData.steamPuff)*.06*phase,1.53+phase*.70,.91-phase*.25)
        object.scale.setScalar(.55+phase*.80);object.visible=phase<.92
        for(const material of materials)material.opacity=Math.sin(phase*Math.PI)**1.3*.52
      }
    },
  }
}
