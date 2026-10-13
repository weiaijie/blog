import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import manifest from '../../src/render/assets/elements/manifest.json'
import { mapElementRoadmap } from '../../src/render/assets/mapElementRoadmap'

describe('C-style Blender element kit', () => {
  it('counts modeled families separately from roadmap entries and revisions', () => {
    expect(manifest.assets).toHaveLength(96)
    expect(new Set(manifest.assets.map((a) => a.id)).size).toBe(96)
    expect(new Set(manifest.assets.map((a) => a.id.replace(/-v\d+$/, ''))).size).toBe(87)
    expect(mapElementRoadmap).toHaveLength(108)
    expect(new Set(mapElementRoadmap.map((a) => a.id)).size).toBe(108)
    for (const asset of manifest.assets) expect(mapElementRoadmap.some((a) => a.id === asset.id.replace(/-v\d+$/, ''))).toBe(true)
    for (const id of ['plowed-field', 'wheat-field']) {
      const before = readFileSync(new URL(`../../src/render/assets/elements/${id}.glb`, import.meta.url))
      const after = readFileSync(new URL(`../../src/render/assets/elements/${id}-v2.glb`, import.meta.url))
      expect(after.equals(before)).toBe(false)
    }
  })
  for (const asset of manifest.assets) {
    it(`${asset.id} exports geometry, source and promised animation`, () => {
      const bytes = readFileSync(new URL(`../../src/render/assets/elements/${asset.id}.glb`, import.meta.url))
      expect(bytes.toString('ascii', 0, 4)).toBe('glTF')
      expect(bytes.readUInt32LE(4)).toBe(2)
      expect(bytes.readUInt32LE(8)).toBe(bytes.length)
      expect(bytes.length).toBe(asset.glbBytes)
      const json = JSON.parse(bytes.toString('utf8', 20, 20 + bytes.readUInt32LE(12)))
      expect(json.meshes.length).toBeGreaterThan(0)
      expect(asset.triangles).toBeGreaterThan(100)
      const living = asset.id.endsWith('-v3')
      const botanical = json.nodes.some((node: { extras?: { lifeRole?: string } }) => node.extras?.lifeRole)
      const animal = json.nodes.some((node: { extras?: { faunaSpecies?: string } }) => node.extras?.faunaSpecies)
      const building = json.nodes.some((node: { extras?: { buildingType?: string } }) => node.extras?.buildingType)
      const route = json.nodes.some((node: { extras?: { routeKind?: string } }) => node.extras?.routeKind)
      if (animal) {
        const roles = new Set(json.nodes.map((node: { extras?: { animalRole?: string } }) => node.extras?.animalRole))
        for (const role of ['body','head','upper-leg','lower-leg','foot']) expect(roles.has(role)).toBe(true)
        for (const node of json.nodes.filter((node: { extras?: { animalRole?: string } }) => node.extras?.animalRole)) {
          expect(node.extras.youngPosition).toHaveLength(3)
          expect(node.extras.youngScale.every((value: number) => value>0 && value<=1)).toBe(true)
        }
      }
      expect(asset.triangles).toBeLessThan(living || botanical || building || route ? 25000 : 15000)
      expect(bytes.length).toBeLessThan(living || botanical || building || route ? 2_500_000 : 1_500_000)
      if (botanical) {
        const roles = new Set(json.nodes.map((node: { extras?: { lifeRole?: string } }) => node.extras?.lifeRole))
        const expected=asset.id==='pine-tree-v4' ? ['shoot','structure','foliage','pollen','cone','scale','seed'] : asset.id==='bamboo' ? ['shoot','structure','foliage','husk','litter'] : asset.id==='potato-field' ? ['shoot','structure','foliage','blossom','stolon','tuber'] : asset.id==='fern' ? ['shoot','structure','foliage','spore'] : asset.id==='mushrooms' ? ['shoot','structure','cap','spore'] : asset.id==='cactus' ? ['shoot','structure','armor','blossom','fruit'] : ['shoot','structure','foliage','blossom',['sunflower-field','rice-paddy','birch-tree','willow-tree','wildflowers','reeds-v4'].includes(asset.id) ? 'seed' : 'fruit']
        for (const role of expected) expect(roles.has(role)).toBe(true)
        if (['fern','mushrooms','bamboo'].includes(asset.id)) expect(roles.has('blossom') || roles.has('fruit') || roles.has('seed')).toBe(false)
        for (const node of json.nodes.filter((node: { extras?: { lifeRole?: string } }) => node.extras?.lifeRole)) {
          expect(node.extras.lifeStart).toBeLessThan(node.extras.lifeFull)
          expect(node.extras.lifeEnd).toBeLessThan(node.extras.lifeGone)
        }
      }
      if (living) {
        expect(json.nodes.some((node: { extras?: { crop?: string } }) => node.extras?.crop === 'edge-grass')).toBe(true)
        expect(json.meshes.some((mesh: { primitives: { attributes: { COLOR_0?: number } }[] }) => mesh.primitives.some((primitive) => primitive.attributes.COLOR_0 !== undefined))).toBe(true)
        if (!asset.id.startsWith('plowed')) expect(json.nodes.some((node: { extras?: { cropPart?: string } }) => node.extras?.cropPart === 'head')).toBe(true)
      }
      for (const mesh of json.meshes) {
        for (const primitive of mesh.primitives) {
          const position = json.accessors[primitive.attributes.POSITION]
          expect(position.count).toBeGreaterThan(0)
          expect(position.min.every(Number.isFinite)).toBe(true)
          expect(position.max.every(Number.isFinite)).toBe(true)
        }
      }
      if (asset.animatedPivots.length) {
        expect(json.animations.length).toBeGreaterThan(0)
        expect(json.animations[0].channels.length).toBeGreaterThan(0)
      }
      const source = readFileSync(new URL(`../../src/render/assets/source/elements/${asset.id}.blend`, import.meta.url))
      expect(source.length).toBeGreaterThan(1000)
    })
  }
})
