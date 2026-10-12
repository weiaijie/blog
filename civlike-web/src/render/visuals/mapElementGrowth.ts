import { Color, Euler, Group, Mesh, MeshStandardMaterial, Object3D, Quaternion, Vector3 } from 'three'

export type FieldSettings = { growth: number; wind: number; automatic: boolean; seed: number }
export const defaultFieldSettings: FieldSettings = { growth: .78, wind: .4, automatic: false, seed: 1 }

function clamp(value: number) { return Math.max(0, Math.min(1, value)) }
function smooth(value: number) { const t = clamp(value); return t * t * (3 - 2 * t) }

export function cropGrowth(progress: number, offset: number, cabbage: boolean) {
  const p = clamp(progress + offset * 4 * progress * (1 - progress))
  const body = smooth(p)
  return {
    visible: p > .015,
    height: .07 + .93 * body,
    width: .16 + .84 * Math.sqrt(body),
    head: smooth((p - (cabbage ? .28 : .52)) / (cabbage ? .57 : .38)),
    ripe: smooth((p - .62) / .36),
  }
}

function noise(index: number, seed: number) {
  const value = Math.sin(index * 127.1 + seed * 311.7) * 43758.5453
  return value - Math.floor(value)
}

type Plant = { object: Object3D; scale: Vector3; rotation: Quaternion; kind: string; vigor: number; heads: { object: Object3D; scale: Vector3 }[] }

export function createFieldMotion(model: Group) {
  const plants: Plant[] = []
  const materials = new Map<MeshStandardMaterial, Color>()
  model.traverse((object) => {
    if (typeof object.userData.crop === 'string') {
      const heads: Plant['heads'] = []
      object.traverse((part) => {
        if (part.userData.cropPart === 'head') heads.push({ object: part, scale: part.scale.clone() })
      })
      plants.push({ object, scale: object.scale.clone(), rotation: object.quaternion.clone(),
        kind: object.userData.crop, vigor: Number(object.userData.vigor ?? 1), heads })
    }
    if (object instanceof Mesh) {
      for (const material of Array.isArray(object.material) ? object.material : [object.material]) {
        if (material instanceof MeshStandardMaterial && /^(straw|ripe_grain)/.test(material.name)) materials.set(material, material.color.clone())
      }
    }
  })
  let settings = { ...defaultFieldSettings }
  let progress = settings.growth
  let elapsed = 0
  const motion = new Quaternion()
  const angle = new Euler()
  const scale = new Vector3()
  const young = new Color('#629149')
  return {
    count: plants.length,
    cropCount: plants.filter((plant) => plant.kind !== 'edge-grass').length,
    setSettings(next: FieldSettings) { settings = { ...next, growth: clamp(next.growth), wind: clamp(next.wind) } },
    update(delta: number, playing: boolean) {
      if (!plants.length) return progress
      if (playing) {
        elapsed += delta
        if (settings.automatic) settings.growth = Math.min(1, settings.growth + delta / 28)
      }
      const difference = settings.growth - progress
      if (playing || !settings.automatic) {
        progress = Math.abs(difference) < .0001 ? settings.growth : progress + difference * (1 - Math.exp(-delta * 7))
      }
      plants.forEach((plant, index) => {
        const edge = plant.kind === 'edge-grass'
        const random = noise(index, settings.seed)
        const state = cropGrowth(progress, (random - .5) * .16, plant.kind === 'cabbage')
        const vigor = edge ? 1 : plant.vigor * (.93 + random * .14)
        plant.object.visible = edge || state.visible
        plant.object.scale.copy(plant.scale).multiply(scale.set(
          edge ? 1 : state.width * vigor, edge ? 1 : state.height * vigor, edge ? 1 : state.width * vigor,
        ))
        const wave = Math.sin(elapsed * 1.5 + plant.object.position.x * 2.4 + plant.object.position.z * 1.2)
          + .28 * Math.sin(elapsed * 3.1 + index * 1.73)
        const strength = settings.wind * (edge ? .16 : plant.kind === 'cabbage' ? .025 : .065)
        angle.set(wave * strength, 0, Math.sin(elapsed * 1.1 + index) * strength * .45)
        motion.setFromEuler(angle)
        plant.object.quaternion.copy(plant.rotation).multiply(motion)
        for (const head of plant.heads) {
          head.object.visible = state.head > .015
          head.object.scale.copy(head.scale).multiplyScalar(Math.max(.001, state.head))
        }
      })
      const ripe = cropGrowth(progress, 0, false).ripe
      for (const [material, mature] of materials) material.color.copy(young).lerp(mature, ripe)
      return progress
    },
  }
}
