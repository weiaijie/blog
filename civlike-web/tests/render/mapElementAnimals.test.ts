import { readFileSync } from 'node:fs'
import { Box3, Group, Object3D, Vector3 } from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { describe, expect, it } from 'vitest'
import { createAnimalMotion, defaultAnimalSettings, solveAnimalLeg } from '../../src/render/visuals/mapElementAnimals'
import { initialMapElement } from '../../src/render/assets/mapElementCatalog'

async function load(id: string) {
  const bytes = readFileSync(new URL(`../../src/render/assets/elements/${id}.glb`,import.meta.url))
  const gltf = await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'')
  return gltf.scene
}
function tagged(root: Object3D, role: string) {
  const result: Object3D[]=[]
  root.traverse((node) => { if (node.userData.animalRole===role) result.push(node) })
  return result
}

describe('animal growth, articulation and bounded offspring', () => {
  it('solves foot targets without stretching limb segments', () => {
    for (const [forward,drop] of [[0,.9],[.1,.85],[-.12,.91],[.08,.76]]) {
      const solution=solveAnimalLeg(.5,.45,forward,drop)
      expect(solution.kneeY-.45*Math.cos(solution.lowerAngle)).toBeCloseTo(-drop,5)
      expect(solution.kneeZ-.45*Math.sin(solution.lowerAngle)).toBeCloseTo(forward,5)
      expect(Math.hypot(solution.kneeY,solution.kneeZ)).toBeCloseTo(.5,6)
    }
  })
  for (const id of ['sheep-v5','cow','horse','chicken']) {
    it(`${id} preserves grounded feet, changes proportions and hides adult details when young`, async () => {
      const model = await load(id), motion = createAnimalMotion(model)!
      const root = model.children.find((node) => node.userData.faunaSpecies)!
      const head = tagged(root,'head')[0], body = tagged(root,'body')[0]
      motion.setSettings({ ...defaultAnimalSettings,age:0 })
      for (let i=0;i<150;i++) motion.update(1/60,false)
      expect(head.scale.x/body.scale.x).toBeGreaterThan(1.10)
      expect(root.scale.toArray()).toEqual([1,1,1])
      expect(tagged(root,'adult-detail').every((node) => !node.visible)).toBe(true)
      for (const age of [0,.45,1]) {
        motion.setSettings({ ...defaultAnimalSettings,age,behavior:'walk' })
        for (let i=0;i<180;i++) {
          motion.update(1/60,true)
          model.updateMatrixWorld(true)
          for (const foot of tagged(root,'foot')) {
            const bounds = new Box3().setFromObject(foot,true)
            expect(bounds.min.y).toBeGreaterThan(-.0001)
            expect(bounds.min.y).toBeLessThan(.16)
            const lower = tagged(root,'lower-leg').find((node) => node.userData.legIndex===foot.userData.legIndex)!
            const endpoint = new Vector3(0,-Number(lower.userData.segmentLength),0).multiply(lower.scale).applyQuaternion(lower.quaternion).add(lower.position)
            expect(endpoint.distanceTo(foot.position)).toBeLessThan(.0001)
          }
        }
      }
      const rotations = tagged(root,'upper-leg').map((node) => node.quaternion.toArray())
      motion.update(1,false)
      expect(tagged(root,'upper-leg').map((node) => node.quaternion.toArray())).toEqual(rotations)
      const bounds=new Box3().setFromObject(root)
      expect(bounds.getSize(new Vector3()).toArray().every(Number.isFinite)).toBe(true)
    })
    it(`${id} caps offspring, pauses the preview clock and clears the family on reset`, async () => {
      const model=await load(id), motion=createAnimalMotion(model)!
      motion.setSettings({ ...defaultAnimalSettings,family:true })
      const started = { ...motion.update(2,true) }
      expect(started.offspring).toBe(0)
      if (id==='chicken') {
        model.updateMatrixWorld(true)
        for (const root of model.children.filter((node) => node.visible)) {
          for (const egg of tagged(root,'egg').filter((node) => node.visible)) expect(new Box3().setFromObject(egg,true).min.y).toBeGreaterThan(-.0001)
        }
      }
      expect(motion.update(3,false).breedingProgress).toBe(started.breedingProgress)
      expect(motion.update(8,true).offspring).toBe(id==='chicken' ? 3 : 1)
      const newbornAge=motion.state.offspringAge
      expect(motion.update(4,true).offspringAge).toBeGreaterThan(newbornAge)
      const pausedAge=motion.state.offspringAge
      expect(motion.update(4,false).offspringAge).toBe(pausedAge)
      expect(motion.update(800,true).offspring).toBe(id==='chicken' ? 3 : 1)
      expect(motion.state.offspringAge).toBe(1)
      expect(model.children.filter((node) => node.userData.faunaSpecies)).toHaveLength(id==='chicken' ? 5 : 3)
      motion.setSettings({ ...defaultAnimalSettings,family:false })
      expect(motion.update(0,false).offspring).toBe(0)
      expect(model.children.filter((node) => node.userData.faunaSpecies && node.visible)).toHaveLength(1)
      motion.setSettings({ ...defaultAnimalSettings,age:0,family:true })
      for (let i=0;i<150;i++) motion.update(1/60,true)
      expect(motion.state.breedingState).toBe('single')
    })
  }
  it('keeps old sheep links static and does not add animals to other assets', () => {
    expect(initialMapElement('?element=sheep').id).toBe('sheep-v5')
    expect(initialMapElement('?element=sheep&revision=1').animal).toBe(false)
    expect(createAnimalMotion(new Group())).toBeUndefined()
  })
})
