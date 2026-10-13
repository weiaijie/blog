import { describe, expect, it } from 'vitest'
import { BoxGeometry, Group, Mesh, MeshStandardMaterial } from 'three'
import { createFieldMotion, cropGrowth, defaultFieldSettings } from '../../src/render/visuals/mapElementGrowth'
import { initialMapElement, mapElementLibrary } from '../../src/render/assets/mapElementCatalog'

describe('living field growth', () => {
  it('keeps leaves before grain and reaches full maturity', () => {
    expect(cropGrowth(0, .08, false).visible).toBe(false)
    expect(cropGrowth(.4, 0, false).head).toBe(0)
    expect(cropGrowth(.4, 0, true).head).toBeGreaterThan(0)
    for (const offset of [-.08, 0, .08]) {
      expect(cropGrowth(1, offset, false)).toEqual({ visible: true, height: 1, width: 1, head: 1, ripe: 1 })
      let previous = 0
      for (let i = 0; i <= 100; i++) {
        const height = cropGrowth(i / 100, offset, false).height
        expect(height).toBeGreaterThanOrEqual(previous)
        previous = height
      }
    }
  })
  it('anchors roots, pauses wind, and grows heads separately', () => {
    const model = new Group(), root = new Group(), head = new Group()
    root.position.set(.5, .13, -.7)
    root.userData.crop = 'wheat'
    head.userData.cropPart = 'head'
    head.position.y = .7
    model.add(root); root.add(head)
    const field = createFieldMotion(model)
    field.setSettings({ ...defaultFieldSettings, growth: .2 })
    for (let i = 0; i < 120; i++) field.update(1 / 60, true)
    expect(root.position.toArray()).toEqual([.5, .13, -.7])
    expect(head.visible).toBe(false)
    const rotation = root.quaternion.clone()
    field.update(.25, false)
    expect(root.quaternion.equals(rotation)).toBe(true)
    field.setSettings({ ...defaultFieldSettings, growth: 1, wind: 0 })
    for (let i = 0; i < 120; i++) field.update(1 / 60, true)
    expect(head.visible).toBe(true)
    expect(head.scale.x).toBeCloseTo(1, 3)
    expect(root.position.y).toBe(.13)
  })
  it('resolves old links and defaults only unspecified revisions to latest', () => {
    expect(mapElementLibrary).toHaveLength(89)
    expect(initialMapElement('?element=wheat-field').id).toBe('wheat-field-v3')
    expect(initialMapElement('?element=wheat-field&revision=2').id).toBe('wheat-field-v2')
    expect(initialMapElement('?element=vegetable-field&revision=1').id).toBe('vegetable-field')
    expect(initialMapElement('?element=wheat-field-v3').revision).toBe(3)
    for(const family of ['pine-tree','reeds']) {
      expect(initialMapElement(`?element=${family}`).id).toBe(`${family}-v4`)
      expect(initialMapElement(`?element=${family}`).lifecycle).toBe(true)
      expect(initialMapElement(`?element=${family}&revision=1`).id).toBe(family)
      expect(initialMapElement(`?element=${family}&revision=1`).lifecycle).toBe(false)
    }
  })
  it('pauses automatic growth and stops at maturity without looping backwards', () => {
    const model = new Group(), plant = new Group()
    plant.userData.crop = 'wheat'
    model.add(plant)
    const field = createFieldMotion(model)
    field.setSettings({ ...defaultFieldSettings, automatic: true })
    const first = field.update(1, true)
    expect(field.update(1, false)).toBe(first)
    let current = first
    for (let i = 0; i < 60; i++) {
      const next = field.update(1, true)
      expect(next).toBeGreaterThanOrEqual(current)
      expect(next).toBeLessThanOrEqual(1)
      current = next
    }
    expect(current).toBe(1)
  })
  it('does not recolor previous static model revisions', () => {
    const model = new Group()
    const material = new MeshStandardMaterial({ name: 'straw', color: '#d3b45a' })
    const geometry = new BoxGeometry()
    model.add(new Mesh(geometry, material))
    const original = material.color.clone()
    createFieldMotion(model).update(0, false)
    expect(material.color.equals(original)).toBe(true)
    geometry.dispose(); material.dispose()
  })
})
