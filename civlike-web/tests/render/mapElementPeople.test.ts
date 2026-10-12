import { readFileSync } from 'node:fs'
import { AnimationMixer, Bone, Group, Quaternion, SkinnedMesh, Vector3 } from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { describe, expect, it } from 'vitest'
import { createHumanMotion, defaultHumanSettings, humanModes } from '../../src/render/visuals/mapElementPeople'

const ids=['farmer','fisher','woodcutter','merchant']
async function load(id:string){const b=readFileSync(new URL(`../../src/render/assets/elements/${id}.glb`,import.meta.url));return new GLTFLoader().parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'')}
function pose(model:Group){const result:number[]=[];model.updateMatrixWorld(true);model.traverse((o)=>{if(o instanceof Bone)result.push(...o.matrixWorld.elements)});return result}
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
  it('does not add worker controls to unrelated assets',()=>expect(createHumanMotion(new Group(),[])).toBeUndefined())
  it('fails visibly when an authored worker clip is missing',async()=>{
    const {scene,animations}=await load('farmer');expect(()=>createHumanMotion(scene,animations.filter((a)=>a.name!=='Walk'))).toThrow('missing Walk')
  })
})
