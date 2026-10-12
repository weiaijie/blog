import { readFileSync } from 'node:fs'
import { Mesh, MeshStandardMaterial, Object3D, Vector3 } from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { describe, expect, it } from 'vitest'
import { botanicalStage, createBotanicalMotion } from '../../src/render/visuals/mapElementLifecycle'
import { defaultFieldSettings } from '../../src/render/visuals/mapElementGrowth'

async function load(id: string) {
  const bytes=readFileSync(new URL(`../../src/render/assets/elements/${id}.glb`,import.meta.url))
  return (await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'')).scene
}
function nodes(root: Object3D, prefix: string) {
  const found:Object3D[]=[]
  root.traverse((node) => { if(node.userData.lifeRole && node.name.startsWith(prefix)) found.push(node) })
  return found
}
function materials(root:Object3D) {
  const result=new Map<string,MeshStandardMaterial>()
  root.traverse((node) => { if(node instanceof Mesh) for(const m of Array.isArray(node.material)?node.material:[node.material]) if(m instanceof MeshStandardMaterial) result.set(m.name,m) })
  return result
}
function settle(motion:ReturnType<typeof createBotanicalMotion>,growth:number) {
  motion.setSettings({ ...defaultFieldSettings,growth,wind:0 })
  for(let i=0;i<160;i++) motion.update(1/60,false)
}

describe('tree structure and seasonal organs', () => {
  for(const [id,twigName,leafName,fruitName,count] of [
    ['oak-tree','OakTwig','OakLeaves','Acorns',36],
    ['birch-tree','BirchTwig','BirchLeaves','BirchSeeds',30],
    ['willow-tree','WillowPendant','WillowLeaves','WillowSeeds',24],
    ['palm-tree','PalmFrond','PalmLeaflets','Coconuts',11],
  ] as const) {
    it(`${id} grows distinct rooted branches, leaves and reproductive organs without root scaling`,async () => {
      const model=await load(id),motion=createBotanicalMotion(model)
      const twigs=nodes(model,twigName),leaves=nodes(model,leafName),fruit=nodes(model,fruitName)
      expect(twigs).toHaveLength(count)
      expect(leaves).toHaveLength(count)
      for(const leaf of leaves) expect(leaf.parent!.name.startsWith(twigName)).toBe(true)
      for(const part of fruit) expect(part.parent!.userData.lifeRole).toBe('structure')
      settle(motion,.49)
      expect(motion.visible.blossom).toBeGreaterThan(0)
      expect(fruit.every((node) => !node.visible)).toBe(true)
      settle(motion,.82)
      expect(fruit.every((node) => node.visible)).toBe(true)
      expect(motion.visible.blossom??0).toBe(0)
      expect(model.scale.toArray()).toEqual([1,1,1])
      model.updateMatrixWorld(true)
      const authored=twigs.map((node) => node.matrixWorld.toArray())
      settle(motion,.05)
      expect(motion.visible.shoot).toBeGreaterThan(0)
      expect(fruit.every((node) => !node.visible)).toBe(true)
      settle(motion,.82);model.updateMatrixWorld(true)
      expect(twigs.map((node) => node.matrixWorld.toArray())).toEqual(authored)
      const frozen=leaves.map((node) => node.quaternion.toArray())
      motion.setSettings({ ...defaultFieldSettings,growth:.82,wind:1 })
      motion.update(1,false)
      const paused=leaves.map((node) => node.quaternion.toArray())
      motion.update(1,false)
      expect(leaves.map((node) => node.quaternion.toArray())).toEqual(paused)
      motion.update(.5,true)
      expect(leaves.map((node) => node.quaternion.toArray())).not.toEqual(frozen)
    })
  }
  it('retains green palm fronds but senesces deciduous leaves without tinting bark',async () => {
    for(const id of ['oak-tree','birch-tree','willow-tree','palm-tree']) {
      const model=await load(id),motion=createBotanicalMotion(model),mats=materials(model)
      const leaf=mats.get(id==='palm-tree'?'palm_leaf':'leaf')!
      const bark=mats.get(id==='birch-tree'?'birch_bark':'bark')!
      expect(leaf).toBeDefined();expect(bark).toBeDefined()
      const green=leaf.color.toArray(),barkColor=bark.color.toArray()
      settle(motion,.82)
      const crownScale=nodes(model,id==='palm-tree'?'PalmLeaflets':id==='oak-tree'?'OakLeaves':id==='birch-tree'?'BirchLeaves':'WillowLeaves').reduce((sum,n) => sum+n.scale.length(),0)
      settle(motion,1)
      expect(bark.color.toArray()).toEqual(barkColor)
      const endScale=nodes(model,id==='palm-tree'?'PalmLeaflets':id==='oak-tree'?'OakLeaves':id==='birch-tree'?'BirchLeaves':'WillowLeaves').reduce((sum,n) => sum+n.scale.length(),0)
      if(id==='palm-tree') {
        expect(leaf.color.toArray()).toEqual(green)
        expect(endScale).toBeCloseTo(crownScale,5)
      } else {
        expect(leaf.color.toArray()).not.toEqual(green)
        expect(endScale).toBeLessThan(crownScale*.4)
      }
    }
  })
  it('orients woody growth axes along individual branches instead of flattening a shared vertical canopy',async () => {
    const model=await load('oak-tree'),motion=createBotanicalMotion(model)
    settle(motion,.82);model.updateMatrixWorld(true)
    for(const node of nodes(model,'OakLimb')) {
      const up=new Vector3(0,1,0).transformDirection(node.matrixWorld)
      expect(Math.abs(up.x)+Math.abs(up.z)).toBeGreaterThan(.4)
      expect(up.y).toBeGreaterThan(0)
    }
    const willow=await load('willow-tree'),willowMotion=createBotanicalMotion(willow)
    settle(willowMotion,.82);willow.updateMatrixWorld(true)
    for(const node of nodes(willow,'WillowPendant')) expect(new Vector3(0,1,0).transformDirection(node.matrixWorld).y).toBeLessThan(-.6)
  })
  it('labels seed-bearing trees and evergreen palms independently',() => {
    expect(botanicalStage(.65,'birch-tree')).toBe('结籽')
    expect(botanicalStage(.65,'willow-tree')).toBe('结籽')
    expect(botanicalStage(.97,'oak-tree')).toBe('落叶休眠')
    expect(botanicalStage(.97,'palm-tree')).toBe('常绿结实')
  })
})
