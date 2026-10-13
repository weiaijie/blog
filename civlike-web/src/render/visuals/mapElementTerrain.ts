import { Color, Group, Mesh, MeshStandardMaterial, Object3D, Quaternion, Vector3 } from 'three'
import { createGeodynamics } from './mapElementGeodynamics'
import { createRiparianWater } from './mapElementRiparian'

export type TerrainSettings = { phase:number; snow:number; wind:number; automatic:boolean; activity:number }
export type TerrainState = { phase:number; snow:number }
export const terrainSeasons = ['春','夏','秋','冬']
export const aridTerrains = new Set(['volcano','lava-field','sand-dunes','desert-oasis'])
export const riparianTerrains = new Set(['wetland','river-bend'])

function smooth(value:number) {const t=Math.max(0,Math.min(1,value));return t*t*(3-2*t)}
function wrap(value:number) {return ((value%1)+1)%1}
function blend(values:number[],phase:number) {
  const p=wrap(phase)*4,i=Math.floor(p)
  return values[i]+(values[(i+1)%4]-values[i])*smooth(p-i)
}
export function terrainSnow(kind:string,phase:number) {
  if(aridTerrains.has(kind))return 0
  return blend(kind==='snow-peak' ? [.62,.42,.54,.96] : [.12,0,.04,.94],phase)
}
export function defaultTerrainSettings(kind:string):TerrainSettings {
  return {phase:.25,snow:terrainSnow(kind,.25),wind:.45,automatic:false,activity:1}
}

export function createTerrainMotion(model:Group) {
  let kind:string|undefined
  model.traverse((o)=>{if(typeof o.userData.terrainType==='string')kind=o.userData.terrainType})
  if(!kind)return undefined
  const geodynamics=createGeodynamics(model)
  const riparian=createRiparianWater(model)
  const tufts:{object:Object3D;rotation:Quaternion;phase:number;altitude:number}[]=[]
  const snow:{object:Object3D;threshold:number;materials:MeshStandardMaterial[]}[]=[]
  const greens=new Map<MeshStandardMaterial,Color[]>()
  model.traverse((o)=>{
    if(o.userData.terrainTuft)tufts.push({object:o,rotation:o.quaternion.clone(),phase:Number(o.userData.windPhase),altitude:Number(o.userData.snowAltitude)})
    if(typeof o.userData.snowThreshold==='number') {
      const materials:MeshStandardMaterial[]=[]
      o.traverse((child)=>{if(child instanceof Mesh) {
        const clone=(material:MeshStandardMaterial)=>{
          const copy=material.clone();copy.transparent=true;copy.depthWrite=false;materials.push(copy);return copy
        }
        child.material=Array.isArray(child.material) ? child.material.map((m)=>clone(m as MeshStandardMaterial)) : clone(child.material as MeshStandardMaterial)
      }})
      snow.push({object:o,threshold:o.userData.snowThreshold,materials})
    }
    if(o instanceof Mesh)for(const m of Array.isArray(o.material)?o.material:[o.material]) {
      if(m instanceof MeshStandardMaterial && m.name.startsWith('ground_grass'))greens.set(m,[m.color.clone().lerp(new Color('#94AD70'),.4),m.color.clone(),new Color('#B5A163'),new Color('#879084')])
    }
  })
  let settings=defaultTerrainSettings(kind),phase=settings.phase,coverage=settings.snow,elapsed=0
  const rotation=new Quaternion(),axis=new Vector3(1,0,.35).normalize()
  return {
    kind,
    setSettings(value:TerrainSettings) {settings={...value,phase:wrap(value.phase),snow:Math.max(0,Math.min(1,value.snow)),wind:Math.max(0,Math.min(1,value.wind)),activity:Math.max(0,Math.min(1,value.activity))}},
    update(delta:number,playing:boolean):TerrainState {
      geodynamics.update(delta,playing,settings.wind,settings.activity)
      if(playing) {
        elapsed+=delta
        if(settings.automatic){phase=wrap(phase+delta/90);settings.phase=phase;settings.snow=terrainSnow(kind!,phase)}
      }
      if(playing || !settings.automatic) {
        if(!settings.automatic) {
          const difference=wrap(settings.phase-phase+.5)-.5
          phase=Math.abs(difference)<.0001 ? settings.phase : wrap(phase+difference*(1-Math.exp(-delta*6)))
        }
        coverage+= (settings.snow-coverage)*(1-Math.exp(-delta*6))
        if(Math.abs(coverage-settings.snow)<.0001)coverage=settings.snow
      }
      for(const [material,seasons] of greens) {
        const p=wrap(phase)*4,i=Math.floor(p)
        material.color.copy(seasons[i]).lerp(seasons[(i+1)%4],smooth(p-i))
      }
      riparian.update(delta,playing,settings.wind,settings.activity,coverage)
      for(const zone of snow) {
        const opacity=smooth((coverage-zone.threshold)/.13)
        zone.object.visible=opacity>.005
        for(const material of zone.materials)material.opacity=opacity
      }
      for(const tuft of tufts) {
        const bend=(Math.sin(elapsed*1.6+tuft.phase)+.2*Math.sin(elapsed*3.4+tuft.phase))*settings.wind*.20
        tuft.object.quaternion.copy(tuft.rotation).multiply(rotation.setFromAxisAngle(axis,bend))
        tuft.object.visible=coverage<.89-.18*tuft.altitude
      }
      return {phase,snow:coverage}
    },
  }
}
