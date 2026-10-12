import { readFileSync } from 'node:fs'
import { Group, Mesh, MeshStandardMaterial, Object3D, Quaternion } from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { describe, expect, it } from 'vitest'
import { createBotanicalMotion, botanicalStage } from '../../src/render/visuals/mapElementLifecycle'
import { defaultFieldSettings } from '../../src/render/visuals/mapElementGrowth'

async function load(id: string) {
  const bytes=readFileSync(new URL(`../../src/render/assets/elements/${id}.glb`,import.meta.url))
  return (await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'')).scene
}
function nodes(root: Object3D, prefix: string) {
  const result:Object3D[]=[]
  root.traverse((node) => { if(node.userData.lifeRole && node.name.startsWith(prefix)) result.push(node) })
  return result
}
function organs(root: Group) {
  const result:Object3D[]=[]
  root.traverse((node) => { if(node.userData.lifeRole) result.push(node) })
  return result
}
describe('distinct crop geometry and lifecycle', () => {
  for (const [id,structure,reproductive] of [
    ['corn-field','JointedCornStalk','CornEar'],['rice-paddy','RiceTiller','RicePanicle'],
    ['vineyard','TrainingCane','GrapeCluster'],['cotton-field','CottonBranch','OpenCotton'],
  ]) {
    it(`${id} has rooted organs, separate flowers and harvest parts with reversible maturity`, async () => {
      const model=await load(id),motion=createBotanicalMotion(model)
      const all=organs(model),fruit=nodes(model,reproductive)
      expect(nodes(model,structure).length).toBeGreaterThan(0)
      expect(fruit.length).toBeGreaterThan(0)
      for(const node of fruit) expect(node.parent!.userData.lifeRole).toBe('structure')
      const settle=(growth:number) => {
        motion.setSettings({ ...defaultFieldSettings,growth,wind:0 })
        for(let i=0;i<160;i++) motion.update(1/60,false)
        model.updateMatrixWorld(true)
      }
      settle(.49)
      expect(motion.visible.blossom).toBeGreaterThan(0)
      expect(fruit.every((node) => !node.visible)).toBe(true)
      settle(.96)
      expect(motion.visible.blossom ?? 0).toBe(0)
      expect(fruit.every((node) => node.visible)).toBe(true)
      expect(model.scale.toArray()).toEqual([1,1,1])
      const mature=all.map((node) => node.matrixWorld.toArray())
      settle(.05)
      expect(motion.visible.shoot).toBeGreaterThan(0)
      expect(fruit.every((node) => !node.visible)).toBe(true)
      settle(.96)
      expect(all.map((node) => node.matrixWorld.toArray())).toEqual(mature)
      motion.setSettings({ ...defaultFieldSettings,growth:.96,wind:1,automatic:true })
      const frozen=motion.update(0,false)
      expect(motion.update(2,false)).toBe(frozen)
      expect(motion.update(.5,true)).toBeGreaterThan(frozen)
      expect(motion.update(60,true)).toBe(1)
      expect(motion.update(60,true)).toBe(1)
    })
  }
  it('splits cotton boll valves at their anchors and reveals fiber only after the closed boll', async () => {
    const model=await load('cotton-field'),motion=createBotanicalMotion(model)
    const valves=nodes(model,'BollValve'),lint=nodes(model,'OpenCotton'),bolls=nodes(model,'ClosedBoll')
    expect(valves.length).toBe(72)
    const anchors=valves.map((node) => node.position.toArray())
    const rotations=valves.map((node) => node.quaternion.clone())
    const settle=(growth:number) => { motion.setSettings({ ...defaultFieldSettings,growth,wind:0 });for(let i=0;i<160;i++)motion.update(1/60,false) }
    settle(.7)
    expect(bolls.every((node) => node.visible)).toBe(true)
    expect(lint.every((node) => !node.visible)).toBe(true)
    settle(1)
    expect(bolls.every((node) => !node.visible)).toBe(true)
    expect(lint.every((node) => node.visible)).toBe(true)
    valves.forEach((node,i) => {
      expect(node.position.toArray()).toEqual(anchors[i])
      expect(rotations[i].angleTo(node.quaternion)).toBeCloseTo(1.35,4)
    })
    settle(.65)
    valves.forEach((node,i) => expect(node.quaternion.angleTo(rotations[i])).toBeCloseTo(0,4))
    expect(lint.every((node) => !node.visible)).toBe(true)
  })
  it('ripens grapes from green to purple without recoloring the trellis', async () => {
    const model=await load('vineyard'),motion=createBotanicalMotion(model)
    const materials=new Map<string,MeshStandardMaterial>()
    model.traverse((node) => { if(node instanceof Mesh) for(const m of Array.isArray(node.material)?node.material:[node.material]) if(m instanceof MeshStandardMaterial) materials.set(m.name,m) })
    const wood=materials.get('wood_dark')!,berry=materials.get('fruit_grape')!
    const woodColor=wood.color.clone(),ripe=berry.color.clone()
    motion.setSettings({ ...defaultFieldSettings,growth:.58,wind:0 })
    for(let i=0;i<160;i++)motion.update(1/60,false)
    expect(berry.color.g).toBeGreaterThan(berry.color.r)
    motion.setSettings({ ...defaultFieldSettings,growth:.85,wind:0 })
    for(let i=0;i<160;i++)motion.update(1/60,false)
    expect(berry.color.toArray()).toEqual(ripe.toArray())
    expect(wood.color.toArray()).toEqual(woodColor.toArray())
  })
  it('keeps flowers and grains on a shared panicle and retains the dry corn tassel', async () => {
    const rice=await load('rice-paddy'),motion=createBotanicalMotion(rice)
    const grain=nodes(rice,'RicePanicle'),heads=nodes(rice,'RiceRachis')
    expect(heads.length).toBe(27)
    for(const node of [...grain,...nodes(rice,'RiceFlowering')]) expect(node.parent!.name.startsWith('RiceRachis')).toBe(true)
    motion.setSettings({ ...defaultFieldSettings,growth:1,wind:0 })
    for(let i=0;i<160;i++) motion.update(1/60,false)
    for(const node of heads) expect(node.quaternion.angleTo(new Quaternion())).toBeCloseTo(.3,4)
    for(const node of grain) expect(node.quaternion.angleTo(new Quaternion())).toBeCloseTo(0,4)
    const corn=await load('corn-field'),cornMotion=createBotanicalMotion(corn)
    cornMotion.setSettings({ ...defaultFieldSettings,growth:1,wind:0 })
    for(let i=0;i<160;i++) cornMotion.update(1/60,false)
    expect(nodes(corn,'CornTasselRachis')).toHaveLength(6)
    expect(nodes(corn,'CornTasselRachis').every((node) => node.visible)).toBe(true)
    expect(nodes(corn,'MaleTassel').every((node) => !node.visible)).toBe(true)
    const vine=await load('vineyard')
    expect(nodes(vine,'BunchFramework')).toHaveLength(8)
    for(const node of nodes(vine,'GrapeCluster')) expect(node.parent!.name.startsWith('BunchFramework')).toBe(true)
  })
  it('uses crop-specific stage labels and neutral opening defaults for old organs', () => {
    expect(botanicalStage(.47,'corn-field')).toBe('抽雄吐丝')
    expect(botanicalStage(.47,'rice-paddy')).toBe('抽穗开花')
    expect(botanicalStage(.65,'rice-paddy')).toBe('灌浆')
    expect(botanicalStage(.81,'cotton-field')).toBe('棉铃开裂')
    expect(botanicalStage(.97,'cotton-field')).toBe('吐絮留种')
    const model=new Group(),node=new Object3D()
    node.userData={ lifeRole:'husk',lifeStart:0,lifeFull:.2,lifeEnd:1.2,lifeGone:1.3,lifeBend:0,lifePhase:0 }
    model.add(node)
    const motion=createBotanicalMotion(model)
    motion.update(1,false)
    expect(node.quaternion.angleTo(new Quaternion())).toBe(0)
  })
})
