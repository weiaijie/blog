import { Color, Euler, Group, Mesh, MeshStandardMaterial, Object3D, Quaternion, Vector3 } from 'three'
import { defaultFieldSettings, type FieldSettings } from './mapElementGrowth'

type Organ = {
  object: Object3D; scale: Vector3; rotation: Quaternion; role: string
  start: number; full: number; end: number; gone: number; bend: number; phase: number; position: Vector3; fallHeight: number
  openAngle: number; openAxis: Vector3; openStart: number; openFull: number
  droopAngle: number; droopStart: number
}

function smooth(value: number) { const t = Math.max(0, Math.min(1, value)); return t*t*(3-2*t) }

export function organEnvelope(progress: number, start: number, full: number, end: number, gone: number) {
  return smooth((progress-start)/Math.max(.001, full-start)) * (1-smooth((progress-end)/Math.max(.001, gone-end)))
}

export function botanicalStage(progress: number, family: string) {
  if (progress < .12) return '萌芽'
  if (progress < .36) return '展叶'
  if (progress < .55) return family==='corn-field' ? '抽雄吐丝' : family==='rice-paddy' ? '抽穗开花' : '开花'
  if (family==='cotton-field' && progress>=.76) return progress<.89 ? '棉铃开裂' : '吐絮留种'
  if ((family==='rice-paddy' || family==='corn-field') && progress<.76) return '灌浆'
  if (progress < .76) return ['sunflower-field','birch-tree','willow-tree'].includes(family) ? '结籽' : '结果'
  if (progress < .89) return '成熟'
  if (family === 'palm-tree') return '常绿结实'
  return ['apple-tree','berry-shrub','vineyard','oak-tree','birch-tree','willow-tree'].includes(family) ? '落叶休眠' : '衰老留种'
}

export function createBotanicalMotion(model: Group) {
  const organs: Organ[] = []
  const fruits = new Map<MeshStandardMaterial, Color>()
  const foliage = new Map<MeshStandardMaterial, Color>()
  model.traverse((object) => {
    const data = object.userData
    if (typeof data.lifeRole === 'string') {
      organs.push({ object, scale: object.scale.clone(), rotation: object.quaternion.clone(), role: data.lifeRole,
        start: Number(data.lifeStart), full: Number(data.lifeFull), end: Number(data.lifeEnd), gone: Number(data.lifeGone),
        bend: Number(data.lifeBend), phase: Number(data.lifePhase), position: object.position.clone(), fallHeight: Number(data.lifeFallHeight ?? 0),
        openAngle:Number(data.lifeOpenAngle ?? 0),openAxis:new Vector3().fromArray(data.lifeOpenAxis ?? [1,0,0]).normalize(),
        openStart:Number(data.lifeOpenStart ?? .7),openFull:Number(data.lifeOpenFull ?? .92),
        droopAngle:Number(data.lifeDroopAngle ?? (data.lifeRole==='seed' ? .30 : data.lifeRole==='foliage' ? .25 : 0)),
        droopStart:Number(data.lifeDroopStart ?? (data.lifeRole==='seed' ? .8 : .86)) })
    }
    if (object instanceof Mesh) {
      for (const material of Array.isArray(object.material) ? object.material : [object.material]) {
        if (!(material instanceof MeshStandardMaterial)) continue
        if (/^fruit_/.test(material.name)) fruits.set(material, material.color.clone())
        if (/^leaf(_|$)/.test(material.name)) foliage.set(material, material.color.clone())
      }
    }
  })
  let settings = { ...defaultFieldSettings }
  let progress = settings.growth
  let elapsed = 0
  const angle = new Euler(), motion = new Quaternion(), opening = new Quaternion(), scale = new Vector3()
  const unripe = new Color('#629644'), autumn = new Color('#b79049')
  const visible: Record<string, number> = {}
  return {
    count: organs.length,
    visible,
    setSettings(next: FieldSettings) { settings = { ...next, growth: Math.max(0, Math.min(1, next.growth)), wind: Math.max(0, Math.min(1, next.wind)) } },
    update(delta: number, playing: boolean) {
      if (!organs.length) return progress
      if (playing) {
        elapsed += delta
        if (settings.automatic) settings.growth = Math.min(1, settings.growth + delta/40)
      }
      if (playing || !settings.automatic) {
        const difference = settings.growth-progress
        progress = Math.abs(difference)<.0001 ? settings.growth : progress+difference*(1-Math.exp(-delta*7))
      }
      for (const role of Object.keys(visible)) delete visible[role]
      for (const organ of organs) {
        const { object, role } = organ
        const variation = Math.sin(organ.phase*13+settings.seed*17)*.022*4*progress*(1-progress)
        const p = progress+variation
        const amount = organEnvelope(p, organ.start, organ.full, organ.end, organ.gone)
        object.visible = amount>.006
        if (object.visible) visible[role] = (visible[role]??0)+1
        // Organs emerge at their attachment points. The entire plant is never scaled.
        object.scale.copy(organ.scale).multiply(role==='structure'
          ? scale.set(.45+.55*amount, Math.max(.001,amount), .45+.55*amount)
          : scale.setScalar(Math.max(.001,amount)))
        const wind = (Math.sin(elapsed*1.6+organ.phase)+.23*Math.sin(elapsed*3.8+organ.phase*2))*settings.wind*organ.bend
        const unfold = role==='foliage' ? (1-smooth((p-organ.start)/.18))*.95 : 0
        const droop = smooth((p-organ.droopStart)/Math.max(.001,1-organ.droopStart))*organ.droopAngle
        angle.set(wind+unfold+droop, 0, wind*.4)
        motion.setFromEuler(angle)
        const open = smooth((p-organ.openStart)/Math.max(.001,organ.openFull-organ.openStart))*organ.openAngle
        object.quaternion.copy(organ.rotation).multiply(opening.setFromAxisAngle(organ.openAxis,open)).multiply(motion)
        if (role === 'litter') {
          const fall = smooth((p-.88)/.12)
          object.position.copy(organ.position)
          object.position.y += organ.fallHeight*(1-fall)
          object.position.x += Math.sin(fall*Math.PI*3+organ.phase)*.12*(1-fall)
        }
      }
      for (const [material, ripe] of fruits) material.color.copy(unripe).lerp(ripe,smooth((progress-.62)/.20))
      for (const [material, green] of foliage) material.color.copy(green).lerp(autumn,smooth((progress-.84)/.16)*.78)
      return progress
    },
  }
}
