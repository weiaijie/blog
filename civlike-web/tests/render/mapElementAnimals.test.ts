import { readFileSync } from 'node:fs'
import { Box3, Group, Mesh, MeshStandardMaterial, Object3D, Vector3 } from 'three'
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
  for (const id of ['sheep-v5','cow','horse','chicken','goat','pig','duck','deer','fox','wolf']) {
    const bird = id==='chicken' || id==='duck'
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
      if (bird) {
        model.updateMatrixWorld(true)
        for (const root of model.children.filter((node) => node.visible)) {
          for (const egg of tagged(root,'egg').filter((node) => node.visible)) expect(new Box3().setFromObject(egg,true).min.y).toBeGreaterThan(-.0001)
        }
      }
      expect(motion.update(3,false).breedingProgress).toBe(started.breedingProgress)
      expect(motion.update(8,true).offspring).toBe(bird ? 3 : 1)
      const newbornAge=motion.state.offspringAge
      expect(motion.update(4,true).offspringAge).toBeGreaterThan(newbornAge)
      const pausedAge=motion.state.offspringAge
      expect(motion.update(4,false).offspringAge).toBe(pausedAge)
      expect(motion.update(800,true).offspring).toBe(bird ? 3 : 1)
      expect(motion.state.offspringAge).toBe(1)
      expect(model.children.filter((node) => node.userData.faunaSpecies)).toHaveLength(bird ? 5 : 3)
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
  for (const id of ['fox','wolf']) {
    it(`${id} grows its coat separately, keeps ear hinges attached and authors paw digits`, async () => {
      const model=await load(id),motion=createAnimalMotion(model)!
      const root=model.children.find((node)=>node.userData.faunaSpecies)!
      const ears: Object3D[]=[],coats: MeshStandardMaterial[]=[],cream: MeshStandardMaterial[]=[]
      root.traverse((node)=>{
        if(node.userData.canidEarSide)ears.push(node)
        if(node instanceof Mesh)for(const material of Array.isArray(node.material)?node.material:[node.material]) {
          if(material instanceof MeshStandardMaterial && material.name==='coat')coats.push(material)
          if(material instanceof MeshStandardMaterial && material.name==='fur_cream')cream.push(material)
        }
      })
      expect(ears).toHaveLength(2)
      expect(tagged(root,'foot').map((node)=>node.userData.pawDigits)).toEqual([4,4,4,4])
      const adultColor=coats[0].color.clone(),creamColor=cream[0].color.clone()
      const origins=ears.map((node)=>node.position.clone())
      const setAge=(age:number)=>{
        motion.setSettings({...defaultAnimalSettings,age,behavior:'graze'})
        for(let frame=0;frame<180;frame++)motion.update(1/60,true)
      }
      setAge(0)
      expect(coats[0].color.equals(adultColor)).toBe(false)
      const youngColor=coats[0].color.clone()
      expect(tagged(root,'head')[0].scale.x/tagged(root,'body')[0].scale.x).toBeGreaterThan(1.3)
      setAge(.5)
      expect(coats[0].color.equals(youngColor)).toBe(false)
      expect(coats[0].color.equals(adultColor)).toBe(false)
      setAge(1)
      expect(coats[0].color.equals(adultColor)).toBe(true)
      expect(cream.every((material)=>material.color.equals(creamColor))).toBe(true)
      expect(ears.every((node,i)=>node.position.equals(origins[i]))).toBe(true)
      for(const ear of ears) {
        expect(ear.parent!.userData.followHead).toBe(true)
        expect(ear.parent!.quaternion.angleTo(tagged(root,'head')[0].quaternion)).toBeLessThan(.0001)
        expect(new Box3().setFromObject(ear,true).min.y).toBeGreaterThan(0)
      }
      expect(new Box3().setFromObject(tagged(root,'head')[0],true).min.y).toBeGreaterThan(0)
      const rotation=ears[0].quaternion.clone()
      motion.update(.2,true)
      expect(ears[0].quaternion.equals(rotation)).toBe(false)
      const paused=ears[0].quaternion.clone()
      motion.update(1,false)
      expect(ears[0].quaternion.equals(paused)).toBe(true)
      motion.setSettings({...defaultAnimalSettings,age:0,automatic:true})
      motion.update(0,false)
      for(let frame=0;frame<60*36;frame++)motion.update(1/60,true)
      expect(motion.state.age).toBeGreaterThan(.99)
    })
  }
  it('distinguishes fox and wolf silhouettes, tail markings and gait metadata', async () => {
    const fox=await load('fox'),wolf=await load('wolf')
    const f=fox.children.find((node)=>node.userData.faunaSpecies)!,w=wolf.children.find((node)=>node.userData.faunaSpecies)!
    const bodySize=(node:Object3D)=>new Box3().setFromObject(tagged(node,'body')[0],true).getSize(new Vector3())
    expect(bodySize(w).x/bodySize(f).x).toBeGreaterThan(1.4)
    expect(w.userData.gaitStride).toBeGreaterThan(f.userData.gaitStride)
    expect(w.userData.gaitFrequency).toBeLessThan(f.userData.gaitFrequency)
    for(const [root,marking] of [[f,'fur_cream'],[w,'coat_back']] as const) {
      const tail=tagged(root,'tail')[0]
      const names=new Set<string>()
      tail.traverse((node)=>{if(node instanceof Mesh)for(const material of Array.isArray(node.material)?node.material:[node.material])names.add(material.name)})
      expect(names.has(marking)).toBe(true)
      expect(new Box3().setFromObject(tail,true).min.y).toBeGreaterThan(0)
    }
  })
  it('fades fawn markings independently and keeps the adult partner without antlers', async () => {
    const model=await load('deer'), motion=createAnimalMotion(model)!
    const roots=model.children.filter((node) => node.userData.faunaSpecies)
    const spots=tagged(roots[0],'juvenile-detail')[0]
    const materials: import('three').Material[]=[]
    spots.traverse((node) => { if (node instanceof Mesh) materials.push(...(Array.isArray(node.material) ? node.material : [node.material])) })
    const setAge=(age: number) => {
      motion.setSettings({ ...defaultAnimalSettings,age })
      for (let i=0;i<150;i++) motion.update(1/60,false)
    }
    setAge(0)
    expect(spots.visible).toBe(true)
    expect(materials.every((material) => material.opacity===1)).toBe(true)
    setAge(.5)
    expect(materials.every((material) => material.opacity>.4 && material.opacity<.6)).toBe(true)
    setAge(1)
    expect(spots.visible).toBe(false)
    motion.setSettings({ ...defaultAnimalSettings,family:true })
    motion.update(0,false)
    expect(tagged(roots[0],'adult-detail').some((part) => part.visible && part.userData.sexTrait==='male')).toBe(true)
    expect(tagged(roots[1],'adult-detail').some((part) => part.visible && part.userData.sexTrait==='male')).toBe(false)
    roots[0].traverse((node) => {
      if (node instanceof Mesh) for (const material of Array.isArray(node.material) ? node.material : [node.material]) {
        if (material.name.startsWith('wool_light')) expect(material.opacity).toBe(1)
      }
    })
  })
})
