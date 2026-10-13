import { readFileSync } from 'node:fs'
import { Box3, Mesh, MeshStandardMaterial, Object3D, PointLight, Raycaster, Vector3 } from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { describe, expect, it } from 'vitest'
import { buildingStage, createBuildingMotion, defaultBuildingSettings } from '../../src/render/visuals/mapElementBuildings'
import { lampNightFactor } from '../../src/render/visuals/mapElementLamp'

async function load(id='street-lamp'){const b=readFileSync(new URL(`../../src/render/assets/elements/${id}.glb`,import.meta.url));return (await new GLTFLoader().parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'')).scene}
function nodes(root:Object3D,key:string){const found:Object3D[]=[];root.traverse((o)=>{if(o.userData[key]!==undefined)found.push(o)});return found}
type Motion=NonNullable<ReturnType<typeof createBuildingMotion>>
function advance(m:Motion,time:number,playing=true){for(let i=0;i<time*60;i++)m.update(1/60,playing)}
function materials(root:Object3D){const list:MeshStandardMaterial[]=[];root.traverse((o)=>{if(o instanceof Mesh)list.push(...(Array.isArray(o.material)?o.material:[o.material]) as MeshStandardMaterial[])});return list}

describe('electric street lantern',()=>{
  it('uses smooth dawn and dusk instead of periodically flashing a daytime lamp',()=>{
    for(const hour of [0,3,5,19,22,24])expect(lampNightFactor(hour)).toBe(1)
    for(const hour of [7,12,17])expect(lampNightFactor(hour)).toBe(0)
    expect(lampNightFactor(6)).toBeCloseTo(.5);expect(lampNightFactor(18)).toBeCloseTo(.5)
    let previous=0
    for(let i=0;i<=100;i++){const value=lampNightFactor(17+i*.02);expect(value).toBeGreaterThanOrEqual(previous);previous=value}
    for(const hour of [5,7,17,19])expect(Math.abs(lampNightFactor(hour+.0001)-lampNightFactor(hour-.0001))).toBeLessThan(.00001)
  })
  it('assembles five distinct stages with isolated daylight and live light only after completion',async()=>{
    const model=await load(),m=createBuildingMotion(model)!,parts=nodes(model,'buildStart'),counts=[]
    const light=model.getObjectByName('StreetLampLight') as PointLight
    for(const progress of [0,.3,.52,.78,1]){
      m.setSettings({...defaultBuildingSettings,progress,hour:22});advance(m,3,false)
      counts.push(parts.filter((p)=>p.visible).length)
      expect(m.state.lighting!.power).toBe(progress===1?1:0)
      expect(light.intensity).toBe(progress===1?35:0)
      expect(model.getObjectByName('BuildingRoot')!.scale.toArray()).toEqual([1,1,1])
    }
    expect(new Set(counts).size).toBe(5);expect(buildingStage(.78,'street-lamp')).toBe('灯室与电气')
    const upgrade=parts.filter((p)=>p.userData.buildingTier===2);expect(upgrade.length).toBeGreaterThan(0)
    expect(upgrade.every((p)=>!p.visible)).toBe(true)
    m.setSettings({...defaultBuildingSettings,tier:2});m.update(0,false);expect(upgrade.every((p)=>p.visible)).toBe(true)
    m.setSettings({...defaultBuildingSettings,progress:0,hour:22});advance(m,3,false);expect(light.intensity).toBe(0)
  })
  it('keeps the physical bulb, power source and attachment point within the authored frame',async()=>{
    const model=await load(),m=createBuildingMotion(model)!;m.update(0,false);model.updateMatrixWorld(true)
    const root=model.getObjectByName('BuildingRoot')!,emitter=nodes(model,'lampEmitter')[0],light=model.getObjectByName('StreetLampLight')!
    const bulb=new Box3().setFromObject(emitter,true)
    expect(bulb.containsPoint(light.getWorldPosition(new Vector3()))).toBe(true)
    expect(light.getWorldPosition(new Vector3()).y).toBeCloseTo(3.31)
    const bounds=new Box3(new Vector3().fromArray(root.userData.animationBoundsMin),new Vector3().fromArray(root.userData.animationBoundsMax))
    model.traverse((o)=>{if(o instanceof Mesh)expect(bounds.containsBox(new Box3().setFromObject(o,true)),o.name).toBe(true)})
    expect(model.getObjectByName('PavementAnchor')!.position.toArray()).toEqual([0,0,0])
    expect(model.getObjectByName('PavementAnchor')!.userData.clearRadius).toBe(.72)
  })
  it('isolates materials, turns off with power and leaves unrelated buildings without lights',async()=>{
    const first=await load(),second=first.clone(true),a=createBuildingMotion(first)!,b=createBuildingMotion(second)!
    a.setSettings({...defaultBuildingSettings,hour:22});a.update(0,false)
    b.setSettings({...defaultBuildingSettings,hour:12});b.update(0,false)
    const firstM=materials(nodes(first,'lampEmitter')[0]),secondM=materials(nodes(second,'lampEmitter')[0])
    expect(firstM[0]).not.toBe(secondM[0]);expect(firstM[0].emissiveIntensity).toBe(3.5);expect(secondM[0].emissiveIntensity).toBe(0)
    a.setSettings({...defaultBuildingSettings,hour:22,working:false});a.update(0,false)
    expect((first.getObjectByName('StreetLampLight') as PointLight).intensity).toBe(0)
    expect(firstM[0].emissiveIntensity).toBe(0)
    const fence=await load('fence'),old=createBuildingMotion(fence)!
    expect(old.update(1,true).lighting).toBeUndefined();expect(fence.getObjectByName('StreetLampLight')).toBeUndefined()
  })
  it('exposes the service hatch in front of the tapered plinth, not buried inside it',async()=>{
    const model=await load();createBuildingMotion(model)!.update(0,false);model.updateMatrixWorld(true)
    const targets:Mesh[]=[];model.traverse((o)=>{if(o instanceof Mesh)targets.push(o)})
    const hatch=model.getObjectByName('ServiceHatch')!
    for(const height of [.37,.46,.55]){
      const hit=new Raycaster(new Vector3(0,height,1),new Vector3(0,0,-1),0,1).intersectObjects(targets,false)[0]
      expect(hit).toBeDefined()
      let belongs=false;for(let p:Object3D|null=hit.object;p;p=p.parent)if(p===hatch)belongs=true
      expect(belongs,`Hidden hatch at ${height}`).toBe(true)
    }
  })
  it('supports midnight wrap, explicit time changes, pause and zero-speed freezes',async()=>{
    const model=await load(),m=createBuildingMotion(model)!
    m.setSettings({...defaultBuildingSettings,hour:23.9,dayCycle:true,speed:1});advance(m,1)
    expect(m.state.lighting!.hour).toBeCloseTo(.3,5)
    const paused={...m.state.lighting};advance(m,1,false);expect(m.state.lighting).toEqual(paused)
    m.setSettings({...defaultBuildingSettings,hour:23.9,dayCycle:true,speed:0});advance(m,1);expect(m.state.lighting).toEqual(paused)
    m.setSettings({...defaultBuildingSettings,hour:6,dayCycle:false});m.update(0,false)
    expect(m.state.lighting).toEqual({hour:6,night:.5,power:.5})
  })
  it('pauses construction and resumes without turning on unfinished equipment',async()=>{
    const model=await load(),m=createBuildingMotion(model)!
    m.setSettings({...defaultBuildingSettings,progress:0});advance(m,3,false)
    m.setSettings({...defaultBuildingSettings,progress:0,automatic:true,hour:22});advance(m,2)
    const state=structuredClone(m.state);advance(m,1,false);expect(m.state).toEqual({...state,operating:false})
    expect(m.state.lighting!.power).toBe(0)
    advance(m,34);expect(m.state.progress).toBe(1);expect(m.state.lighting!.power).toBe(1)
  })
})
