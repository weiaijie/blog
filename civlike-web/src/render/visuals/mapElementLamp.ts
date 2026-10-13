import { Group, Mesh, MeshStandardMaterial, PointLight } from 'three'

function smooth(value:number){const t=Math.max(0,Math.min(1,value));return t*t*(3-2*t)}
export function lampNightFactor(hour:number){return 1-smooth((hour-5)/2)+smooth((hour-17)/2)}
export type LampState={hour:number;night:number;power:number}

export function createLampLighting(model:Group){
  const emitters:{light:PointLight;materials:MeshStandardMaterial[];power:number}[]=[]
  model.traverse((node)=>{
    if(!node.userData.lampEmitter)return
    const materials:MeshStandardMaterial[]=[]
    node.traverse((child)=>{
      if(!(child instanceof Mesh))return
      const copy=(material:MeshStandardMaterial)=>{const result=material.clone();materials.push(result);return result}
      child.material=Array.isArray(child.material)?child.material.map((m)=>copy(m as MeshStandardMaterial)):copy(child.material as MeshStandardMaterial)
    })
    const light=new PointLight(0xffd496,0,Number(node.userData.lampRange),2)
    light.name='StreetLampLight';node.add(light)
    emitters.push({light,materials,power:Number(node.userData.lampPower)})
  })
  if(!emitters.length)return undefined
  let hour=18,requestedHour=18
  const state:LampState={hour,night:lampNightFactor(hour),power:0}
  return {
    state,
    update(delta:number,playing:boolean,settings:{hour:number;automatic:boolean;on:boolean}){
      if(!settings.automatic||settings.hour!==requestedHour)hour=((settings.hour%24)+24)%24
      requestedHour=settings.hour
      if(playing&&settings.automatic)hour=(hour+delta*.4)%24
      state.hour=hour;state.night=lampNightFactor(hour);state.power=settings.on?state.night:0
      for(const emitter of emitters){
        emitter.light.intensity=emitter.power*state.power
        for(const material of emitter.materials)material.emissiveIntensity=state.power*3.5
      }
      return state
    },
  }
}
