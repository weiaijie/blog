import { Color, Euler, Group, Material, Mesh, MeshStandardMaterial, Object3D, Quaternion, Vector3 } from 'three'

export type AnimalBehavior = 'idle' | 'walk' | 'graze'
export type AnimalSettings = { age: number; automatic: boolean; behavior: AnimalBehavior; family: boolean }
export type AnimalState = { age: number; offspring: number; offspringAge: number; breedingProgress: number; breedingState: 'single' | 'waiting' | 'nursing' }
export const defaultAnimalSettings: AnimalSettings = { age: 1, automatic: false, behavior: 'idle', family: false }

function smooth(value: number) { const t = Math.max(0,Math.min(1,value)); return t*t*(3-2*t) }

// Two-link sagittal IK keeps the hoof on the authored ground during stance.
export function solveAnimalLeg(upper: number, lower: number, forward: number, drop: number) {
  const distance = Math.max(.001,Math.min(upper+lower-.00001,Math.hypot(forward,drop)))
  const cosine = Math.max(-1,Math.min(1,(upper*upper+distance*distance-lower*lower)/(2*upper*distance)))
  const angle = Math.atan2(forward,drop)-Math.acos(cosine)
  const kneeY = -upper*Math.cos(angle), kneeZ = upper*Math.sin(angle)
  return { kneeY, kneeZ, upperAngle: -angle, lowerAngle: -Math.atan2(forward-kneeZ,drop+kneeY) }
}

type Part = {
  object: Object3D; role: string; position: Vector3; scale: Vector3; rotation: Quaternion
  youngPosition: Vector3; youngScale: Vector3; maturity: number; followHead: boolean
}
type Leg = { upper: Part; lower: Part; foot: Part; upperLength: number; lowerLength: number; footHeight: number; index: number }

function rig(root: Object3D) {
  const parts: Part[] = []
  const coats = new Map<MeshStandardMaterial,Color>()
  root.traverse((object) => {
    if (typeof object.userData.animalRole === 'string') {
      parts.push({ object,role:object.userData.animalRole,position:object.position.clone(),scale:object.scale.clone(),rotation:object.quaternion.clone(),
        youngPosition:new Vector3().fromArray(object.userData.youngPosition),youngScale:new Vector3().fromArray(object.userData.youngScale),
        maturity:Number(object.userData.maturity??0),followHead:Boolean(object.userData.followHead) })
    }
    if (object instanceof Mesh) {
      for (const material of Array.isArray(object.material) ? object.material : [object.material]) {
        if (material instanceof MeshStandardMaterial && /^coat/.test(material.name)) coats.set(material,material.color.clone())
      }
    }
  })
  const legs: Leg[] = parts.filter((p) => p.role==='upper-leg').map((upper) => {
    const index = Number(upper.object.userData.legIndex)
    const lower = parts.find((p) => p.role==='lower-leg' && p.object.userData.legIndex===index)!
    const foot = parts.find((p) => p.role==='foot' && p.object.userData.legIndex===index)!
    return { upper,lower,foot,index,upperLength:Number(upper.object.userData.segmentLength),lowerLength:Number(lower.object.userData.segmentLength),footHeight:Number(upper.object.userData.footHeight) }
  })
  return { root,parts,legs,coats }
}

export function createAnimalMotion(model: Group) {
  let original: Object3D | undefined
  model.traverse((object) => { if (object.userData.faunaSpecies) original=object })
  if (!original) return undefined
  const species = String(original.userData.faunaSpecies)
  const bird = species==='chicken' || species==='duck'
  const animals = [rig(original)]
  const template = original.clone(true)
  // A bounded family shares geometry, but each animal owns its changing coat materials.
  for (let i=0;i<(bird ? 4 : 2);i++) {
    const clone = template.clone(true)
    const copies = new Map<Material,Material>()
    clone.traverse((object) => {
      if (!(object instanceof Mesh)) return
      const copy = (material: Material) => {
        if (!copies.has(material)) copies.set(material,material.clone())
        return copies.get(material)!
      }
      object.material = Array.isArray(object.material) ? object.material.map(copy) : copy(object.material)
    })
    original.parent!.add(clone)
    clone.visible=false
    animals.push(rig(clone))
  }
  let settings = { ...defaultAnimalSettings }
  let age = 1, elapsed = 0, breeding = 0, nursery = 0
  const blend = { walk:0,graze:0 }
  const state: AnimalState = { age,offspring:0,offspringAge:0,breedingProgress:0,breedingState:'single' }
  const motion = new Quaternion(), angles = new Euler(), scale = new Vector3()
  const unitScale = new Vector3(1,1,1)
  const chick = new Color('#e6ce78')
  let spread = 1

  function pose(animal: ReturnType<typeof rig>, progress: number, index: number, incubating: boolean) {
    const growth = smooth(progress)
    const headAngle = blend.graze*((bird ? .72 : .68)+Math.sin(elapsed*2.6+index)*.07)+(1-blend.graze)*Math.sin(elapsed*1.2+index)*.025
    const firstLeg = animal.legs[0]
    const legFactor = firstLeg.upper.youngScale.y+(1-firstLeg.upper.youngScale.y)*growth
    const legReach = (firstLeg.upperLength+firstLeg.lowerLength)*legFactor
    const maxStride = (bird ? .075 : .19)*legFactor*blend.walk
    const crouch = legReach-Math.sqrt(Math.max(.001,legReach*legReach-maxStride*maxStride))+.001*blend.walk
    for (const part of animal.parts) {
      const { object,role } = part
      object.position.copy(part.youngPosition).lerp(part.position,growth)
      if (role==='egg') object.position.copy(part.position)
      if (!['foot','egg','lower-leg','upper-leg'].includes(role)) object.position.y-=crouch
      object.scale.copy(part.scale).multiply(scale.copy(part.youngScale).lerp(unitScale,growth))
      object.quaternion.copy(part.rotation)
      const maturity = part.maturity ? smooth((progress-part.maturity)/.40) : 1
      object.visible = incubating ? role==='egg' : role!=='egg' && maturity>.01
      if (index===1 && object.userData.sexTrait==='female') object.visible=false
      if (index===1 && object.userData.sexTrait==='male') object.visible=false
      if (part.maturity) object.scale.multiplyScalar(Math.max(.001,maturity))
      if (role==='juvenile-detail') {
        object.visible=!incubating && progress<.7
        object.traverse((node) => {
          if (node instanceof Mesh) for (const material of Array.isArray(node.material) ? node.material : [node.material]) {
            material.transparent=true
            material.depthWrite=false
            material.opacity=1-smooth((progress-.30)/.40)
          }
        })
      }
      if (index===1 && role==='body') object.scale.x*=1.06
      if (bird && index!==1 && object.name.startsWith('Comb')) object.scale.multiplyScalar(.55)
      let x = part.followHead || role==='head' ? headAngle : 0, y = 0, z = 0
      if (role==='ear') z = Math.sin(elapsed*2.1+index)*.06*Number(object.userData.side??1)
      if (role==='tail') y = Math.sin(elapsed*2.5+index)*.14
      if (role==='wing') z = Math.sin(elapsed*1.6+index)*.045*Number(object.userData.side??1)
      if (role==='body' || role==='juvenile-detail') x = Math.sin(elapsed*1.4+index)*.006
      if (role==='egg') z = Math.sin(elapsed*8+index)*.045*state.breedingProgress
      angles.set(x,y,z); motion.setFromEuler(angles)
      object.quaternion.multiply(motion)
    }
    for (const leg of animal.legs) {
      const { upper,lower,foot } = leg
      const factor = upper.youngScale.y+(1-upper.youngScale.y)*growth
      const a = leg.upperLength*factor, b = leg.lowerLength*factor, height = leg.footHeight*factor
      const phase = (elapsed*(bird ? 1.9 : 1.15)+leg.index*.5+Math.floor(leg.index/2)*.5+index*.13)%1
      const stride = (bird ? .075 : .19)*factor
      const forward = blend.walk*(phase<.62 ? stride*(1-2*phase/.62) : stride*(-1+2*(phase-.62)/.38))
      const lift = phase<.62 ? 0 : blend.walk*Math.sin((phase-.62)/.38*Math.PI)*(bird ? .048 : .09)*factor
      const solution = solveAnimalLeg(a,b,forward,a+b-crouch-lift)
      const hip = upper.object.position
      hip.y=a+b+height-crouch
      angles.set(solution.upperAngle,0,0); motion.setFromEuler(angles)
      upper.object.quaternion.copy(upper.rotation).multiply(motion)
      lower.object.position.set(hip.x,hip.y+solution.kneeY,hip.z+solution.kneeZ)
      angles.set(solution.lowerAngle,0,0); motion.setFromEuler(angles)
      lower.object.quaternion.copy(lower.rotation).multiply(motion)
      foot.object.position.set(hip.x,height+lift,hip.z+forward)
    }
    if (bird) for (const [material,adult] of animal.coats) material.color.copy(chick).lerp(adult,smooth((progress-.2)/.55))
  }

  return {
    species,
    state,
    setSpread(value: number) { spread=value },
    setSettings(next: AnimalSettings) {
      const wasFamily = settings.family
      settings = { ...next,age:Math.max(0,Math.min(1,next.age)) }
      if (!settings.family || !wasFamily) { breeding=0; nursery=0 }
    },
    update(delta: number, playing: boolean) {
      if (playing) {
        elapsed+=delta
        for (const behavior of ['walk','graze'] as const) blend[behavior]+=((settings.behavior===behavior ? 1 : 0)-blend[behavior])*(1-Math.exp(-delta*8))
        if (settings.automatic) settings.age=Math.min(1,settings.age+delta/35)
      }
      if (playing || !settings.automatic) {
        const difference = settings.age-age
        age = Math.abs(difference)<.0001 ? settings.age : age+difference*(1-Math.exp(-delta*7))
      }
      const family = settings.family && age>=.72
      if (family && playing) {
        if (breeding>=8) nursery=Math.min(45,nursery+delta)
        breeding=Math.min(8,breeding+delta)
      }
      if (!family) { breeding=0; nursery=0 }
      state.age=age
      state.breedingProgress=breeding/8
      state.breedingState=!family ? 'single' : breeding<8 ? 'waiting' : 'nursing'
      state.offspring=family && breeding>=8 ? animals.length-2 : 0
      state.offspringAge=state.offspring ? Math.min(1,.04+nursery/45) : 0
      animals.forEach((animal,index) => {
        const child = index>1
        const incubating = child && family && breeding<8
        animal.root.visible=index===0 || family && (index===1 || breeding>=8 || bird)
        animal.root.position.set(!family ? 0 : index<2 ? (index===0 ? -.46 : .46)*spread : (index-2-(animals.length-3)/2)*spread*.80,0,!family ? 0 : child ? spread*.80 : -spread*.55)
        pose(animal,child ? Math.max(.04,state.offspringAge) : age,index,incubating)
      })
      return state
    },
  }
}
