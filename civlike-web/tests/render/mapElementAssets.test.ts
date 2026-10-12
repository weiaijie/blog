import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import manifest from '../../src/render/assets/elements/manifest.json'

describe('C-style Blender element kit', () => {
  it('has twelve asset families and five refined comparison models', () => {
    expect(manifest.assets).toHaveLength(17)
    expect(new Set(manifest.assets.map((a) => a.id)).size).toBe(17)
    expect(new Set(manifest.assets.map((a) => a.id.replace(/-v\d+$/, ''))).size).toBe(12)
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
      expect(asset.triangles).toBeLessThan(living ? 25000 : 15000)
      expect(bytes.length).toBeLessThan(living ? 2_500_000 : 1_500_000)
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
