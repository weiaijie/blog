import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import manifest from '../../src/render/assets/elements/manifest.json'

describe('C-style Blender element kit', () => {
  it('has twelve distinct assets', () => {
    expect(manifest.assets).toHaveLength(12)
    expect(new Set(manifest.assets.map((a) => a.id)).size).toBe(12)
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
      expect(asset.triangles).toBeLessThan(15000)
      expect(bytes.length).toBeLessThan(1_500_000)
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
