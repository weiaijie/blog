import { AnimationClip, AnimationMixer, Group } from 'three'

export type SkeletalSettings = { clip: string; speed: number }
export type SkeletalState = { clip: string; clips: string[]; time: number; duration: number }
export const defaultSkeletalSettings: SkeletalSettings = { clip: '', speed: 1 }
const labels: Record<string,string> = { Idle:'待机', Walk:'行走', Run:'跑步', Wave:'招手', Interact:'互动', Eating:'采食', Gallop:'奔跑',
  Gallop_Jump:'奔跑跳跃', Jump_toIdle:'跳跃落地', Idle_2:'待机变化', Idle_Headlow:'低头休息', Death:'倒下',
  Attack_Headbutt:'顶撞', Attack_Kick:'后踢', Idle_Neutral:'自然站姿', Idle_HitReact1:'受惊', Idle_HitReact2:'受惊变化' }
export function skeletalClipLabel(name: string) { return labels[name] ?? name.replace(/_/g,' ') }

export function createSkeletalMotion(model: Group, clips: AnimationClip[]) {
  let licensed = false
  model.traverse((object)=>{if(object.userData.licensedAsset)licensed=true})
  if(!licensed)return undefined
  if(!clips.length)throw new Error('Licensed model has no animation clips')
  const mixer = new AnimationMixer(model)
  const actions = new Map(clips.map((clip)=>[clip.name,mixer.clipAction(clip)]))
  let current=actions.get('Idle') ?? actions.values().next().value!
  let settings={...defaultSkeletalSettings,clip:current.getClip().name}
  current.play()
  return {
    setSettings(next: SkeletalSettings) {
      const name=next.clip || current.getClip().name,action=actions.get(name)
      if(!action)throw new Error(`Missing animation: ${name}`)
      if(action!==current){const previous=current;current=action;current.reset().setEffectiveWeight(1).setEffectiveTimeScale(1).play().crossFadeFrom(previous,.25,false)}
      settings={clip:name,speed:Math.max(0,Math.min(2,next.speed))}
    },
    update(delta: number, playing: boolean): SkeletalState {
      mixer.update(playing ? delta*settings.speed : 0)
      return {clip:settings.clip,clips:[...actions.keys()],time:current.time,duration:current.getClip().duration}
    },
    destroy(){mixer.stopAllAction();mixer.uncacheRoot(model)},
  }
}
