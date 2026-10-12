import { Color, Euler, Group, Mesh, MeshStandardMaterial, Object3D, Quaternion, Vector3 } from 'three'
import { defaultFieldSettings, type FieldSettings } from './mapElementGrowth'

type Organ = {
  object: Object3D; scale: Vector3; rotation: Quaternion; role: string
  start: number; full: number; end: number; gone: number; bend: number; phase: number; position: Vector3; fallHeight: number
  openAngle: number; openAxis: Vector3; openStart: number; openFull: number
  droopAngle: number; droopStart: number; unfurlAngle: number; unfoldAngle: number; bob: number; radialGrowth: number
}

function smooth(value: number) { const t = Math.max(0, Math.min(1, value)); return t*t*(3-2*t) }

export function organEnvelope(progress: number, start: number, full: number, end: number, gone: number) {
  return smooth((progress-start)/Math.max(.001, full-start)) * (1-smooth((progress-end)/Math.max(.001, gone-end)))
}

export function botanicalStage(progress: number, family: string) {
  if (family==='pine-tree' || family==='reeds') {
    const stages=family==='pine-tree' ? ['幼苗','抽梢','花粉球花','球果发育','球果成熟','鳞片张开'] : ['出芽','展叶拔高','抽穗开花','结籽','绒穗成熟','枯黄留穗']
    return stages[progress<.12 ? 0 : progress<.36 ? 1 : progress<.55 ? 2 : progress<.76 ? 3 : progress<.89 ? 4 : 5]
  }
  if (family==='bamboo' || family==='potato-field') {
    const stages=family==='bamboo' ? ['出笋','拔节','展枝','展叶','成竹','换叶'] : ['出苗','茎叶生长','开花结薯','块茎膨大','薯块成熟','茎叶枯退']
    return stages[progress<.12 ? 0 : progress<.36 ? 1 : progress<.55 ? 2 : progress<.76 ? 3 : progress<.89 ? 4 : 5]
  }
  if (family==='fern' || family==='mushrooms') {
    const stages=family==='fern' ? ['卷芽','舒卷','羽叶展开','孢子囊形成','孢子成熟','老叶衰退'] : ['原基','菌柄伸长','菌盖展开','菌褶成熟','产孢','衰败']
    return stages[progress<.12 ? 0 : progress<.36 ? 1 : progress<.55 ? 2 : progress<.76 ? 3 : progress<.89 ? 4 : 5]
  }
  if (family==='cactus' && progress>=.12 && progress<.36) return '茎节伸长'
  if (progress < .12) return '萌芽'
  if (progress < .36) return '展叶'
  if (progress < .55) return family==='corn-field' ? '抽雄吐丝' : family==='rice-paddy' ? '抽穗开花' : '开花'
  if (family==='cotton-field' && progress>=.76) return progress<.89 ? '棉铃开裂' : '吐絮留种'
  if ((family==='rice-paddy' || family==='corn-field') && progress<.76) return '灌浆'
  if (progress < .76) return ['sunflower-field','birch-tree','willow-tree','wildflowers'].includes(family) ? '结籽' : '结果'
  if (progress < .89) return '成熟'
  if (family === 'palm-tree') return '常绿结实'
  if (family === 'cactus') return '留果休眠'
  return ['apple-tree','berry-shrub','vineyard','oak-tree','birch-tree','willow-tree'].includes(family) ? '落叶休眠' : '衰老留种'
}

export function createBotanicalMotion(model: Group) {
  const organs: Organ[] = []
  const fruits = new Map<MeshStandardMaterial, Color>()
  const foliage = new Map<MeshStandardMaterial, Color>()
  const caps: { mesh: Mesh; index: number }[] = []
  model.traverse((object) => {
    const data = object.userData
    if (typeof data.lifeRole === 'string') {
      organs.push({ object, scale: object.scale.clone(), rotation: object.quaternion.clone(), role: data.lifeRole,
        start: Number(data.lifeStart), full: Number(data.lifeFull), end: Number(data.lifeEnd), gone: Number(data.lifeGone),
        bend: Number(data.lifeBend), phase: Number(data.lifePhase), position: object.position.clone(), fallHeight: Number(data.lifeFallHeight ?? 0),
        openAngle:Number(data.lifeOpenAngle ?? 0),openAxis:new Vector3().fromArray(data.lifeOpenAxis ?? [1,0,0]).normalize(),
        openStart:Number(data.lifeOpenStart ?? .7),openFull:Number(data.lifeOpenFull ?? .92),
        unfurlAngle:Number(data.lifeUnfurlAngle ?? 0),unfoldAngle:Number(data.lifeUnfoldAngle ?? .95),bob:Number(data.lifeBob ?? 0),
        radialGrowth:Number(data.lifeRadialGrowth ?? .45),
        droopAngle:Number(data.lifeDroopAngle ?? (data.lifeRole==='seed' ? .30 : data.lifeRole==='foliage' ? .25 : 0)),
        droopStart:Number(data.lifeDroopStart ?? (data.lifeRole==='seed' ? .8 : .86)) })
    }
    if (object instanceof Mesh) {
      const capIndex=object.morphTargetDictionary?.ClosedCap
      if (capIndex!==undefined && object.morphTargetInfluences) caps.push({ mesh:object,index:capIndex })
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
          ? scale.set(organ.radialGrowth+(1-organ.radialGrowth)*amount, Math.max(.001,amount), organ.radialGrowth+(1-organ.radialGrowth)*amount)
          : scale.setScalar(Math.max(.001,amount)))
        const wind = (Math.sin(elapsed*1.6+organ.phase)+.23*Math.sin(elapsed*3.8+organ.phase*2))*settings.wind*organ.bend
        const unfold = role==='foliage' ? (1-smooth((p-organ.start)/.18))*organ.unfoldAngle : 0
        const droop = smooth((p-organ.droopStart)/Math.max(.001,1-organ.droopStart))*organ.droopAngle
        angle.set(wind+unfold+droop, 0, wind*.4)
        motion.setFromEuler(angle)
        const openness = smooth((p-organ.openStart)/Math.max(.001,organ.openFull-organ.openStart))
        const open = openness*organ.openAngle+(1-openness)*organ.unfurlAngle
        object.quaternion.copy(organ.rotation).multiply(opening.setFromAxisAngle(organ.openAxis,open)).multiply(motion)
        if (role === 'litter') {
          const fall = smooth((p-.88)/.12)
          object.position.copy(organ.position)
          object.position.y += organ.fallHeight*(1-fall)
          object.position.x += Math.sin(fall*Math.PI*3+organ.phase)*.12*(1-fall)
        } else if (organ.bob) {
          object.position.copy(organ.position)
          object.position.y+=Math.sin(elapsed*1.3+organ.phase)*organ.bob*settings.wind
        }
      }
      for (const { mesh,index } of caps) mesh.morphTargetInfluences![index]=1-smooth((progress-.24)/.38)
      for (const [material, ripe] of fruits) material.color.copy(unripe).lerp(ripe,smooth((progress-.62)/.20))
      for (const [material, green] of foliage) material.color.copy(green).lerp(autumn,smooth((progress-.84)/.16)*.78)
      return progress
    },
  }
}
