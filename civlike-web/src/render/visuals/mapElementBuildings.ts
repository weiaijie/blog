import { Group, Matrix4, Mesh, MeshStandardMaterial, Object3D, Quaternion, Vector3 } from 'three'
import { createChannelWater } from './mapElementHydraulics'

export type BuildingSettings = { progress: number; automatic: boolean; working: boolean; speed: number; tier: 1 | 2; gateOpen: boolean }
export type BuildingState = { progress: number; visible: number; operating: boolean; tier: 1 | 2; access: number }
export const defaultBuildingSettings: BuildingSettings = { progress: 1, automatic: false, working: true, speed: .6, tier: 1, gateOpen:false }
export function buildingStage(progress: number, kind?: string) {
  if(kind==='irrigation-channel')return progress<.15 ? '基础' : progress<.42 ? '渠床' : progress<.62 ? '渠壁' : progress<.90 ? '水闸与附件' : progress<.99 ? '注水' : '竣工'
  if(kind==='aqueduct')return progress<.15 ? '基础' : progress<.42 ? '桥墩' : progress<.62 ? '承重结构' : progress<.90 ? '渠槽与附件' : progress<.99 ? '注水' : '竣工'
  if(kind==='stone-bridge'||kind==='steel-bridge')return progress<.15 ? '基础' : progress<.42 ? '桥墩' : progress<.62 ? '拱圈与承重' : progress<.90 ? '桥面与护栏' : progress<.99 ? '收尾' : '竣工'
  return progress<.15 ? '地基' : progress<.42 ? '墙体' : progress<.62 ? '结构' : progress<.90 ? '屋顶与部件' : progress<.99 ? '收尾' : '竣工'
}
function smooth(value: number) { const t=Math.max(0,Math.min(1,value)); return t*t*(3-2*t) }

export function createBuildingMotion(model: Group) {
  const parts: { object: Object3D; position: Vector3; rotation: Quaternion; start: number; full: number; tier: number; temporary: boolean; motion: string; axis: Vector3; rate: number }[]=[]
  model.traverse((object) => {
    if (typeof object.userData.buildStart!=='number') return
    parts.push({ object,position:object.position.clone(),rotation:object.quaternion.clone(),start:object.userData.buildStart,full:object.userData.buildFull,
      tier:object.userData.buildingTier,temporary:Boolean(object.userData.buildingTemporary),motion:String(object.userData.buildingMotion),
      axis:new Vector3().fromArray(object.userData.motionAxis).normalize(),rate:Number(object.userData.motionRate) })
  })
  if (!parts.length) return undefined
  const surfaces: { mesh: Mesh; base: Float32Array; motion: string; min: number; span: number }[]=[]
  for (const part of parts.filter((part) => part.motion==='banner' || part.motion==='chain' || part.motion==='awning')) {
    part.object.traverse((node) => {
      if (!(node instanceof Mesh)) return
      node.geometry=node.geometry.clone()
      node.geometry.computeBoundingBox()
      const bounds=node.geometry.boundingBox!
      surfaces.push({ mesh:node,base:Float32Array.from(node.geometry.attributes.position.array),motion:part.motion,
        min:part.motion==='banner' ? bounds.min.x : part.motion==='awning' ? bounds.min.z : bounds.min.y,
        span:part.motion==='banner' ? bounds.max.x-bounds.min.x : part.motion==='awning' ? bounds.max.z-bounds.min.z : bounds.max.y-bounds.min.y })
    })
  }
  const bellows:{mesh:Mesh;local:Vector3[];toMesh:Matrix4}[]=[],embers:MeshStandardMaterial[]=[]
  model.updateMatrixWorld(true)
  // Imported material splits may carry their own transforms; deform in the leaf hinge's coordinates.
  for(const part of parts){
    if(part.motion==='bellows-skin')part.object.traverse((node)=>{
      if(!(node instanceof Mesh))return
      node.geometry=node.geometry.clone()
      const toPart=new Matrix4().copy(part.object.matrixWorld).invert().multiply(node.matrixWorld),position=node.geometry.getAttribute('position')
      bellows.push({mesh:node,local:Array.from({length:position.count},(_,i)=>new Vector3().fromBufferAttribute(position,i).applyMatrix4(toPart)),toMesh:toPart.clone().invert()})
    })
    if(part.motion==='ember')part.object.traverse((node)=>{
      if(!(node instanceof Mesh))return
      const clone=(material:MeshStandardMaterial)=>{const copy=material.clone();embers.push(copy);return copy}
      node.material=Array.isArray(node.material)?node.material.map((m)=>clone(m as MeshStandardMaterial)):clone(node.material as MeshStandardMaterial)
    })
  }
  let settings={ ...defaultBuildingSettings }, progress=1, elapsed=0, access=0
  const water=createChannelWater(model)
  const hasGate=parts.some((part) => part.motion==='lift' || part.motion==='semaphore' || part.motion==='bascule' || part.motion==='hydro-gate')
  const rotation=new Quaternion()
  const state: BuildingState={ progress,visible:0,operating:false,tier:1,access:0 }
  return {
    state,
    setSettings(next: BuildingSettings) { settings={ ...next,progress:Math.max(0,Math.min(1,next.progress)),speed:Math.max(0,Math.min(1,next.speed)) } },
    update(delta: number, playing: boolean) {
      if (playing && settings.automatic) settings.progress=Math.min(1,settings.progress+delta/30)
      if (playing || !settings.automatic) {
        const difference=settings.progress-progress
        progress=Math.abs(difference)<.0001 ? settings.progress : progress+difference*(1-Math.exp(-delta*8))
      }
      const operating=progress>=.99 && settings.working && settings.speed>0
      if (playing && operating) elapsed+=delta*settings.speed
      if (progress<.99) access=0
      else if (hasGate && playing && operating) {
        const target=settings.gateOpen ? 1 : 0
        access=Math.abs(target-access)<.0001 ? target : access+(target-access)*(1-Math.exp(-delta*settings.speed*4))
      }
      const bridgeAngle=smooth(access/.55)*Math.PI/2
      const gateLift=smooth((access-.45)/.55)
      const bellowsAngle=.10+(1+Math.sin(elapsed*2.4))*.10
      state.progress=progress; state.visible=0; state.operating=operating && playing; state.tier=settings.tier; state.access=access
      for (const part of parts) {
        const { object }=part
        const assembled=smooth((progress-part.start)/(part.full-part.start))
        object.visible=part.tier<=settings.tier && (part.start===0 || assembled>.001) && (!part.temporary || progress<.95)
        if (!object.visible) continue
        state.visible++
        object.position.copy(part.position)
        object.quaternion.copy(part.rotation)
        // Individually placed courses settle onto their authored anchors; the building root never scales.
        if (!part.temporary && part.start>0) object.position.y+=(1-assembled)*.18
        if (part.motion==='spin') object.quaternion.multiply(rotation.setFromAxisAngle(part.axis,elapsed*part.rate))
        if (part.motion==='door') object.quaternion.multiply(rotation.setFromAxisAngle(part.axis,(.05+(1-Math.cos(elapsed*.65))*.32)*part.rate))
        if (part.motion==='sway') object.quaternion.multiply(rotation.setFromAxisAngle(part.axis,Math.sin(elapsed*.8)*.22))
        if (part.motion==='sign-swing') object.quaternion.multiply(rotation.setFromAxisAngle(part.axis,Math.sin(elapsed*1.4)*.13))
        if (part.motion==='bell-swing') object.quaternion.multiply(rotation.setFromAxisAngle(part.axis,Math.sin(elapsed*2.4)*.32))
        if (part.motion==='bell-clapper') object.quaternion.multiply(rotation.setFromAxisAngle(part.axis,Math.sin(elapsed*2.4-.6)*-.24))
        if (part.motion==='entry-door') object.quaternion.multiply(rotation.setFromAxisAngle(part.axis,(.5-.5*Math.cos(elapsed*.5))*Number(object.userData.doorAngle)))
        if (part.motion==='sliding-door') {
          const phase=elapsed%12
          const open=phase<2 ? 0 : phase<4 ? smooth((phase-2)/2) : phase<7 ? 1 : phase<9 ? 1-smooth((phase-7)/2) : 0
          object.position.addScaledVector(part.axis,open*Number(object.userData.slideTravel))
        }
        if (part.motion==='bellows') object.quaternion.multiply(rotation.setFromAxisAngle(part.axis,bellowsAngle))
        if (part.motion==='semaphore') object.quaternion.multiply(rotation.setFromAxisAngle(part.axis,smooth(access)*Math.PI/4))
        if (part.motion==='bascule') object.quaternion.multiply(rotation.setFromAxisAngle(part.axis,smooth((access-.2)/.8)*Number(object.userData.basculeAngle)))
        if (part.motion==='road-barrier') object.quaternion.multiply(rotation.setFromAxisAngle(part.axis,(1-smooth(access/.2))*Math.PI/2))
        if (part.motion==='hydro-gate') object.position.y+=smooth(access)*Number(object.userData.gateTravel)
        if (part.motion==='hydro-wheel') object.quaternion.multiply(rotation.setFromAxisAngle(part.axis,smooth(access)*Math.PI*2*Number(object.userData.screwTurns)))
        if (part.motion==='belt-loop') {
          const data=object.userData,[left,right]=data.beltCenters as number[],r=Number(data.beltRadius),span=right-left,arc=Math.PI*r,length=2*span+2*arc
          let distance=((Number(data.beltPhase)*length-elapsed*Number(data.beltSpeed))%length+length)%length
          let x:number,y:number,angle:number
          if(distance<arc){angle=-Math.PI/2+distance/r;x=right+r*Math.cos(angle);y=r*Math.sin(angle);angle+=Math.PI/2}
          else if((distance-=arc)<span){x=right-distance;y=r;angle=Math.PI}
          else if((distance-=span)<arc){angle=Math.PI/2+distance/r;x=left+r*Math.cos(angle);y=r*Math.sin(angle);angle+=Math.PI/2}
          else {distance-=arc;x=left+distance;y=-r;angle=0}
          object.position.set(x,Number(data.beltHeight)+y+(1-assembled)*.18,Number(data.beltDepth))
          object.quaternion.setFromAxisAngle(new Vector3(0,0,1),angle)
        }
        if (part.motion==='flow') object.position.addScaledVector(part.axis,((elapsed*.18+Number(object.userData.flowPhase))%1-.5)*5.0)
        if (part.motion==='lift') object.position.y+=gateLift*Number(object.userData.gateTravel)
        if (part.motion==='bridge') object.quaternion.multiply(rotation.setFromAxisAngle(part.axis,bridgeAngle))
      }
      for (const surface of surfaces) {
        const { mesh,base,motion,min,span }=surface
        const attribute=mesh.geometry.attributes.position
        for (let i=0;i<attribute.count;i++) {
          const x=base[i*3],y=base[i*3+1],z=base[i*3+2]
          if (motion==='banner') {
            const t=(x-min)/span
            attribute.setXYZ(i,x,y,z+.09*t*Math.sin(elapsed*3.5-t*7+y*1.2))
          } else if(motion==='awning') {
            const t=(z-min)/span
            attribute.setXYZ(i,x,y+.055*4*t*(1-t)*Math.sin(elapsed*3-x*2-t*5),z)
          } else {
            const t=1-(y-min)/span
            attribute.setXYZ(i,x,y+t*2.5*(Math.cos(bridgeAngle)-1),z+t*2.5*Math.sin(bridgeAngle))
          }
        }
        attribute.needsUpdate=true
        mesh.geometry.computeVertexNormals()
        mesh.geometry.computeBoundingSphere()
      }
      for(const {mesh,local,toMesh}of bellows){
        const p=mesh.geometry.getAttribute('position'),point=new Vector3()
        for(let i=0;i<p.count;i++){
          const base=local[i],weight=Math.max(0,Math.min(1,(base.y+.15)/.15))
          point.set(base.x,base.y-base.z*Math.sin(bellowsAngle)*weight,base.z+(Math.cos(bellowsAngle)-1)*base.z*weight).applyMatrix4(toMesh)
          p.setXYZ(i,point.x,point.y,point.z)
        }
        p.needsUpdate=true;mesh.geometry.computeVertexNormals();mesh.geometry.computeBoundingBox();mesh.geometry.computeBoundingSphere()
      }
      for(const material of embers)material.emissiveIntensity=1.25+.35*Math.sin(elapsed*2.4-.4)+.10*Math.sin(elapsed*7)
      water.update(delta*settings.speed,playing&&operating,access,progress>=.93)
      return state
    },
  }
}
