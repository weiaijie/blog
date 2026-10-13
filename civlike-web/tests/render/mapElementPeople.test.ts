import { readFileSync } from 'node:fs'
import { AnimationMixer, Bone, Box3, Group, Mesh, Quaternion, SkinnedMesh, Vector3 } from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { describe, expect, it } from 'vitest'
import { createHumanMotion, defaultHumanSettings, humanModes } from '../../src/render/visuals/mapElementPeople'

const ids=['farmer','fisher','woodcutter','merchant','builder','town-resident','engineer']
async function load(id:string){const b=readFileSync(new URL(`../../src/render/assets/elements/${id}.glb`,import.meta.url));return new GLTFLoader().parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'')}
function pose(model:Group){const result:number[]=[];model.updateMatrixWorld(true);model.traverse((o)=>{if(o instanceof Bone)result.push(...o.matrixWorld.elements)});return result}
function vertices(model:Group,material:string,bone?:string){
  const points:Vector3[]=[]
  model.updateMatrixWorld(true)
  model.traverse((o)=>{
    if(!(o instanceof Mesh) || Array.isArray(o.material) || o.material.name!==material)return
    if(o instanceof SkinnedMesh)o.skeleton.update()
    for(let i=0;i<o.geometry.getAttribute('position').count;i++){
      if(bone && (!(o instanceof SkinnedMesh) || o.skeleton.bones[o.geometry.getAttribute('skinIndex').getX(i)].name!==bone))continue
      points.push(o.getVertexPosition(i,new Vector3()).applyMatrix4(o.matrixWorld))
    }
  })
  expect(points.length).toBeGreaterThan(0)
  return points
}
describe('portable worker rigs',()=>{
  for(const id of ids){
    it(`${id} exports only its own three skeletal actions and remains on the ground through every action`,async()=>{
      const {scene,animations}=await load(id)
      expect(animations.map((a)=>a.name).sort()).toEqual(['Idle','Walk','Work'])
      const meshes:SkinnedMesh[]=[];scene.traverse((o)=>{if(o instanceof SkinnedMesh)meshes.push(o)})
      expect(meshes.length).toBeGreaterThan(0)
      const bones=meshes[0].skeleton.bones.map((b)=>b.name)
      for(const name of ['Spine','Head','ThighR','ShinR','FootR','HandL','HandR'])expect(bones).toContain(name)
      const bounds=scene.getObjectByName('WorkerRig')!.userData
      const minimum=new Vector3().fromArray(bounds.animationBoundsMin),maximum=new Vector3().fromArray(bounds.animationBoundsMax)
      for(const clip of animations){
        const mixer=new AnimationMixer(scene);mixer.clipAction(clip).play()
        expect(clip.duration).toBeCloseTo(3,4)
        for(let step=0;step<=24;step++){
          mixer.setTime(step/24*clip.duration);scene.updateMatrixWorld(true)
          if(clip.name==='Work' && ['farmer','woodcutter'].includes(id)){
            const right=scene.getObjectByName('HandR')!,left=scene.getObjectByName('HandL')!
            const grip=new Vector3(0,id==='farmer' ? -.18 : -.17,0).applyQuaternion(right.getWorldQuaternion(new Quaternion())).add(right.getWorldPosition(new Vector3()))
            expect(left.getWorldPosition(new Vector3()).distanceTo(grip)).toBeLessThan(.035)
          }
          let low=Infinity
          for(const mesh of meshes){mesh.skeleton.update();const p=mesh.geometry.getAttribute('position')
            for(let i=0;i<p.count;i++){
              const v=mesh.getVertexPosition(i,new Vector3()).applyMatrix4(mesh.matrixWorld)
              expect(v.toArray().every(Number.isFinite)).toBe(true)
              low=Math.min(low,v.y)
              expect(v.x).toBeGreaterThanOrEqual(minimum.x-.01);expect(v.x).toBeLessThanOrEqual(maximum.x+.01)
              expect(v.y).toBeLessThanOrEqual(maximum.y+.01);expect(v.z).toBeGreaterThanOrEqual(minimum.z-.01);expect(v.z).toBeLessThanOrEqual(maximum.z+.01)
            }
          }
          expect(low).toBeGreaterThan(-.015)
          expect(low).toBeLessThan(.025)
        }
        mixer.stopAllAction();mixer.uncacheRoot(scene)
      }
    })
    it(`${id} switches with blending, pauses and has a real zero-speed state`,async()=>{
      const {scene,animations}=await load(id),motion=createHumanMotion(scene,animations)!
      const poses=[]
      for(const [mode] of humanModes){
        motion.setSettings({mode,speed:1});motion.update(.8,true);poses.push(pose(scene))
        const state=motion.update(.2,true),frozen=pose(scene)
        expect(motion.update(5,false)).toEqual(state);expect(pose(scene)).toEqual(frozen)
        motion.setSettings({mode,speed:0});motion.update(5,true);expect(pose(scene)).toEqual(frozen)
        motion.setSettings({mode,speed:1});motion.update(.2,true);expect(pose(scene)).not.toEqual(frozen)
        scene.traverse((o)=>{if(o.userData.humanWorkProp)expect(o.visible).toBe(mode==='Work')})
      }
      expect(new Set(poses.map((p)=>JSON.stringify(p))).size).toBe(3)
      motion.setSettings(defaultHumanSettings);motion.update(.5,true)
      const before=pose(scene);motion.setSettings({mode:'Walk',speed:1});motion.update(0,true)
      expect(Math.max(...pose(scene).map((v,i)=>Math.abs(v-before[i])))).toBeLessThan(1e-5)
      motion.update(.35,true);expect(pose(scene)).not.toEqual(before)
      expect(scene.scale.toArray()).toEqual([1,1,1]);motion.destroy()
    })
  }
  it('builder strikes the brick top with the actual mallet mesh without passing through it',async()=>{
    const {scene,animations}=await load('builder'),mixer=new AnimationMixer(scene)
    mixer.clipAction(animations.find((c)=>c.name==='Work')!).play()
    const top=new Box3().setFromPoints(vertices(scene,'tile')).max.y
    const contact=scene.getObjectByName('ToolContact')!
    for(let frame=0;frame<72;frame++){
      mixer.setTime(frame/24);scene.updateMatrixWorld(true)
      expect(new Box3().setFromPoints(vertices(scene,'builder_mallet')).min.y).toBeGreaterThanOrEqual(top-.003)
    }
    mixer.setTime(1.5);scene.updateMatrixWorld(true)
    expect(contact.getWorldPosition(new Vector3()).distanceTo(new Vector3(0,top,.52))).toBeLessThan(.002)
    expect(new Box3().setFromPoints(vertices(scene,'builder_mallet')).min.y).toBeCloseTo(top,3)
    mixer.stopAllAction();mixer.uncacheRoot(scene)
  })
  it('engineer keeps the open spanner on the fixed nut and rotates the exported nut mesh with it',async()=>{
    const {scene,animations}=await load('engineer'),mixer=new AnimationMixer(scene)
    mixer.clipAction(animations.find((c)=>c.name==='Work')!).play();mixer.setTime(0);scene.updateMatrixWorld(true)
    const nut=scene.getObjectByName('ValveNut')!,contact=scene.getObjectByName('ToolContact')!
    const center=nut.getWorldPosition(new Vector3()),initial=vertices(scene,'engineer_bolt')
    const hand=scene.getObjectByName('HandR')!,restHand=hand.getWorldQuaternion(new Quaternion())
    for(let frame=0;frame<72;frame++){
      mixer.setTime(frame/24);scene.updateMatrixWorld(true)
      expect(contact.getWorldPosition(new Vector3()).distanceTo(center)).toBeLessThan(.002)
      expect(nut.getWorldPosition(new Vector3()).distanceTo(center)).toBeLessThan(1e-5)
      const rotation=nut.getWorldQuaternion(new Quaternion()),actual=vertices(scene,'engineer_bolt')
      actual.forEach((v,i)=>expect(v.distanceTo(initial[i].clone().sub(center).applyQuaternion(rotation).add(center))).toBeLessThan(1e-5))
      const handTurn=hand.getWorldQuaternion(new Quaternion()).multiply(restHand.clone().invert())
      expect(handTurn.angleTo(rotation)).toBeLessThan(.002)
    }
    mixer.setTime(.75);scene.updateMatrixWorld(true)
    expect(vertices(scene,'engineer_bolt').some((v,i)=>v.distanceTo(initial[i])>.01)).toBe(true)
    expect(vertices(scene,'engineer_spanner').length).toBeGreaterThan(50)
    mixer.stopAllAction();mixer.uncacheRoot(scene)
  })
  it('resident holds the basket clear of the legs and raises a separate open hand to greet',async()=>{
    const {scene,animations}=await load('town-resident'),mixer=new AnimationMixer(scene)
    for(const clip of animations){
      mixer.stopAllAction();mixer.clipAction(clip).play()
      for(let frame=0;frame<72;frame+=3){
        mixer.setTime(frame/24);scene.updateMatrixWorld(true)
        const basket=new Box3().setFromPoints(vertices(scene,'wood_light','HandL'))
        expect(basket.max.x).toBeLessThan(-.28);expect(basket.min.y).toBeGreaterThan(.4)
        if(clip.name==='Work'){
          expect(scene.getObjectByName('HandR')!.getWorldPosition(new Vector3()).y).toBeGreaterThan(1.58)
          const openHand=new Box3().setFromPoints(vertices(scene,'human_skin_light','HandR'))
          expect(openHand.max.y).toBeGreaterThan(1.69)
        }
      }
    }
    mixer.stopAllAction();mixer.uncacheRoot(scene)
  })
  it('does not add worker controls to unrelated assets',()=>expect(createHumanMotion(new Group(),[])).toBeUndefined())
  it('fails visibly when an authored worker clip is missing',async()=>{
    const {scene,animations}=await load('farmer');expect(()=>createHumanMotion(scene,animations.filter((a)=>a.name!=='Walk'))).toThrow('missing Walk')
  })
})
