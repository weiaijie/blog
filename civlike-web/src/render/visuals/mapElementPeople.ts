import { AnimationClip, AnimationMixer, Group, Object3D } from 'three'

export type HumanMode='Idle'|'Walk'|'Work'
export type HumanSettings={mode:HumanMode;speed:number}
export type HumanState={mode:HumanMode;time:number;duration:number}
export const defaultHumanSettings:HumanSettings={mode:'Work',speed:1}
export const humanModes:[HumanMode,string][]=[['Idle','待机'],['Walk','行走'],['Work','工作']]

export function createHumanMotion(model:Group,clips:AnimationClip[]) {
  let profession:string|undefined
  const props:Object3D[]=[]
  model.traverse((o)=>{if(o.userData.humanProfession)profession=o.userData.humanProfession;if(o.userData.humanWorkProp)props.push(o)})
  if(!profession)return undefined
  const mixer=new AnimationMixer(model)
  const actions=new Map(humanModes.map(([mode])=>{
    const clip=clips.find((c)=>c.name===mode)
    if(!clip)throw new Error(`${profession}: missing ${mode} animation`)
    return [mode,mixer.clipAction(clip)] as const
  }))
  let settings={...defaultHumanSettings},current=actions.get(settings.mode)!
  current.play()
  return {
    profession,
    setSettings(next:HumanSettings) {
      if(next.mode!==settings.mode){
        const previous=current;current=actions.get(next.mode)!
        current.reset().setEffectiveTimeScale(1).setEffectiveWeight(1).play().crossFadeFrom(previous,.3,false)
      }
      settings={...next,speed:Math.max(0,Math.min(2,next.speed))}
      for(const p of props)p.visible=settings.mode==='Work'
    },
    update(delta:number,playing:boolean):HumanState {
      mixer.update(playing ? delta*settings.speed : 0)
      return {mode:settings.mode,time:current.time,duration:current.getClip().duration}
    },
    destroy(){mixer.stopAllAction();mixer.uncacheRoot(model)},
  }
}
