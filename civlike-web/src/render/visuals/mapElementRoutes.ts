import { Group, Object3D, Quaternion, Vector3 } from 'three'

export type RouteShape='straight'|'bend'|'junction'
export type RouteSettings={shape:RouteShape;progress:number;automatic:boolean;wind:number;diverted:boolean;connected:boolean}
export type RouteState={shape:RouteShape;progress:number;ports:number[];switchPosition:number;visible:number}
export const defaultRouteSettings:RouteSettings={shape:'straight',progress:1,automatic:false,wind:.6,diverted:false,connected:false}
export function routeStage(progress:number){return progress<.3 ? '基层' : progress<.75 ? '铺装' : progress<.99 ? '收尾' : '通行'}

export function createRouteMotion(model:Group){
  let kind=''
  const shapes:Object3D[]=[],parts:{object:Object3D;base:Vector3}[]=[],tufts:{object:Object3D;rotation:Quaternion;phase:number}[]=[]
  const switches:{object:Object3D;base:Vector3;travel:Vector3}[]=[],indicators:{object:Object3D;rotation:Quaternion}[]=[]
  model.traverse((o)=>{
    if(o.userData.routeKind)kind=o.userData.routeKind
    if(o.userData.routeShape)shapes.push(o)
    if(typeof o.userData.routeStart==='number')parts.push({object:o,base:o.position.clone()})
    if(typeof o.userData.routeWind==='number')tufts.push({object:o,rotation:o.quaternion.clone(),phase:o.userData.routeWind})
    if(o.userData.routeSwitch)switches.push({object:o,base:o.position.clone(),travel:new Vector3().fromArray(o.userData.switchTravel)})
    if(o.userData.routeIndicator)indicators.push({object:o,rotation:o.quaternion.clone()})
  })
  if(!kind)return undefined
  let settings={...defaultRouteSettings},progress=1,elapsed=0,switchPosition=0
  const q=new Quaternion(),axis=new Vector3(0,0,1),up=new Vector3(0,1,0)
  const state:RouteState={shape:'straight',progress:1,ports:[0,3],switchPosition:0,visible:0}
  return {
    kind,
    setSettings(next:RouteSettings){settings={...next,progress:Math.max(0,Math.min(1,next.progress)),wind:Math.max(0,Math.min(1,next.wind))}},
    update(delta:number,playing:boolean){
      if(playing){elapsed+=delta*settings.wind;if(settings.automatic)settings.progress=Math.min(1,settings.progress+delta/24)}
      if(playing||!settings.automatic){const d=settings.progress-progress;progress=Math.abs(d)<.0001 ? settings.progress : progress+d*(1-Math.exp(-delta*10))}
      const active=shapes.find((o)=>o.userData.routeShape===settings.shape)!
      for(const shape of shapes)shape.visible=shape===active
      let visible=0
      for(const {object,base}of parts){
        const t=Math.max(0,Math.min(1,(progress-object.userData.routeStart)/(object.userData.routeFull-object.userData.routeStart)))
        object.visible=t>.001;object.position.copy(base);object.position.y+=(1-t*t*(3-2*t))*.06
        if(object.visible&&object.parent===active)visible++
      }
      for(const {object,rotation,phase}of tufts)object.quaternion.copy(rotation).multiply(q.setFromAxisAngle(axis,settings.wind*.08*Math.sin(elapsed*2.4+phase)))
      if(progress<.99)switchPosition=0
      else if(playing)switchPosition+=(Number(settings.diverted)-switchPosition)*(1-Math.exp(-delta*6))
      for(const {object,base,travel}of switches){object.visible=progress>=.99;object.position.copy(base).addScaledVector(travel,switchPosition)}
      for(const {object,rotation}of indicators){object.visible=progress>=.99;object.quaternion.copy(rotation).multiply(q.setFromAxisAngle(up,switchPosition*Math.PI/2))}
      Object.assign(state,{shape:settings.shape,progress,switchPosition,visible,ports:progress<.99 ? [] : kind==='rail-track'&&settings.shape==='junction' ? [0,switchPosition>.99 ? 2 : switchPosition<.01 ? 3 : -1].filter((p)=>p>=0) : [...active.userData.ports]})
      return state
    },
  }
}
