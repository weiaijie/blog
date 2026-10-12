import { Group, Object3D } from 'three'
import { describe, expect, it } from 'vitest'
import { createBotanicalMotion, organEnvelope, botanicalStage } from '../../src/render/visuals/mapElementLifecycle'
import { defaultFieldSettings } from '../../src/render/visuals/mapElementGrowth'
import { initialMapElement } from '../../src/render/assets/mapElementCatalog'

describe('organ-level botanical life cycle', () => {
  it('opens flowers, removes petals and then fills separate fruit geometry', () => {
    expect(organEnvelope(.25,.38,.48,.56,.66)).toBe(0)
    expect(organEnvelope(.5,.38,.48,.56,.66)).toBe(1)
    expect(organEnvelope(.8,.38,.48,.56,.66)).toBe(0)
    expect(organEnvelope(.5,.53,.76,1.2,1.3)).toBe(0)
    expect(organEnvelope(.8,.53,.76,1.2,1.3)).toBe(1)
    expect(botanicalStage(.97,'sunflower-field')).toBe('衰老留种')
    expect(botanicalStage(.97,'apple-tree')).toBe('落叶休眠')
  })
  it('keeps attachment points and root scale, rewinds organs and freezes automatic playback', () => {
    const model = new Group()
    const flower = new Object3D(), fruit = new Object3D()
    for (const [object,role,start,full,end,gone] of [
      [flower,'blossom',.38,.48,.56,.66], [fruit,'fruit',.53,.76,1.2,1.3],
    ] as const) {
      object.position.set(.5,1,.1)
      object.userData = { lifeRole:role, lifeStart:start, lifeFull:full, lifeEnd:end, lifeGone:gone, lifeBend:.05, lifePhase:1 }
      model.add(object)
    }
    const motion = createBotanicalMotion(model)
    const settle = (growth: number) => {
      motion.setSettings({ ...defaultFieldSettings, growth })
      for (let i=0;i<120;i++) motion.update(1/60,false)
    }
    settle(.49)
    expect(flower.visible).toBe(true)
    expect(fruit.visible).toBe(false)
    settle(.82)
    expect(flower.visible).toBe(false)
    expect(fruit.visible).toBe(true)
    expect(fruit.position.toArray()).toEqual([.5,1,.1])
    expect(model.scale.toArray()).toEqual([1,1,1])
    settle(.05)
    expect(fruit.visible).toBe(false)
    expect(flower.visible).toBe(false)
    motion.setSettings({ ...defaultFieldSettings, growth:.05, automatic:true })
    const frozen = motion.update(0,false)
    expect(motion.update(1,false)).toBe(frozen)
    expect(motion.update(1,true)).toBeGreaterThan(frozen)
  })
  it('does not infer lifecycle capabilities from a new family version number', () => {
    expect(initialMapElement('?element=apple-tree').lifecycle).toBe(true)
    expect(initialMapElement('?element=berry-shrub&revision=1').lifecycle).toBe(false)
    expect(initialMapElement('?element=berry-shrub&revision=4').lifecycle).toBe(true)
  })
  it('drops leaves onto their authored ground height and can rewind without drift', () => {
    const model = new Group(), leaf = new Object3D()
    leaf.position.set(.4,.08,.3)
    leaf.userData = { lifeRole:'litter',lifeStart:.87,lifeFull:.91,lifeEnd:1.2,lifeGone:1.3,lifeBend:0,lifePhase:1,lifeFallHeight:1.5 }
    model.add(leaf)
    const motion = createBotanicalMotion(model)
    motion.setSettings({ ...defaultFieldSettings,growth:1,wind:0 })
    for (let i=0;i<150;i++) motion.update(1/60,false)
    expect(leaf.position.toArray()).toEqual([.4,.08,.3])
    motion.setSettings({ ...defaultFieldSettings,growth:.91,wind:0 })
    for (let i=0;i<150;i++) motion.update(1/60,false)
    expect(leaf.position.y).toBeGreaterThan(.8)
    motion.setSettings({ ...defaultFieldSettings,growth:.4,wind:0 })
    for (let i=0;i<150;i++) motion.update(1/60,false)
    expect(leaf.visible).toBe(false)
    expect(model.position.toArray()).toEqual([0,0,0])
  })
})
