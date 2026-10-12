import { Group, Mesh, Object3D, Quaternion, Vector3 } from 'three'

export type BuildingSettings = { progress: number; automatic: boolean; working: boolean; speed: number; tier: 1 | 2; gateOpen: boolean }
export type BuildingState = { progress: number; visible: number; operating: boolean; tier: 1 | 2; access: number }
export const defaultBuildingSettings: BuildingSettings = { progress: 1, automatic: false, working: true, speed: .6, tier: 1, gateOpen:false }
export function buildingStage(progress: number) {
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
  for (const part of parts.filter((part) => part.motion==='banner' || part.motion==='chain')) {
    part.object.traverse((node) => {
      if (!(node instanceof Mesh)) return
      node.geometry=node.geometry.clone()
      node.geometry.computeBoundingBox()
      const bounds=node.geometry.boundingBox!
      surfaces.push({ mesh:node,base:Float32Array.from(node.geometry.attributes.position.array),motion:part.motion,
        min:part.motion==='banner' ? bounds.min.x : bounds.min.y,span:part.motion==='banner' ? bounds.max.x-bounds.min.x : bounds.max.y-bounds.min.y })
    })
  }
  let settings={ ...defaultBuildingSettings }, progress=1, elapsed=0, access=0
  const hasGate=parts.some((part) => part.motion==='lift')
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
          } else {
            const t=1-(y-min)/span
            attribute.setXYZ(i,x,y+t*2.5*(Math.cos(bridgeAngle)-1),z+t*2.5*Math.sin(bridgeAngle))
          }
        }
        attribute.needsUpdate=true
        mesh.geometry.computeVertexNormals()
        mesh.geometry.computeBoundingSphere()
      }
      return state
    },
  }
}
