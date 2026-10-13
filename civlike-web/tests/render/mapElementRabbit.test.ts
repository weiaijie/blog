import { readFileSync } from 'node:fs'
import { Box3, Mesh, MeshStandardMaterial, Object3D, Vector3 } from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { describe, expect, it } from 'vitest'
import { createAnimalMotion, defaultAnimalSettings, sampleRabbitHop } from '../../src/render/visuals/mapElementAnimals'

async function load() {
  const bytes=readFileSync(new URL('../../src/render/assets/elements/rabbit.glb',import.meta.url))
  return (await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'')).scene
}
function tagged(root:Object3D,key:string,value?:unknown) {
  const nodes:Object3D[]=[]
  root.traverse((node)=>{if(value===undefined ? node.userData[key] : node.userData[key]===value)nodes.push(node)})
  return nodes
}
function snapshot(root:Object3D) {
  const result:unknown[]=[]
  root.traverse((node)=>result.push([node.visible,...node.position.toArray(),...node.quaternion.toArray(),...node.scale.toArray()]))
  return result
}

describe('cottontail anatomy, hop and life stages',()=>{
  it('exports grounded folded legs, large hind feet and two real ear hinges',async()=>{
    const model=await load(),root=tagged(model,'faunaSpecies')[0]
    const feet=tagged(root,'animalRole','foot'),ears=tagged(root,'rabbitEarSide')
    expect(ears).toHaveLength(2)
    expect(feet).toHaveLength(4)
    expect(new Box3().setFromObject(model,true).min.y).toBeGreaterThanOrEqual(-.00001)
    const size=(node:Object3D)=>new Box3().setFromObject(node,true).getSize(new Vector3())
    expect(size(feet[2]).z/size(feet[0]).z).toBeGreaterThan(2)
    expect(size(ears[0]).y/size(ears[0]).x).toBeGreaterThan(2.4)
    const legs=tagged(root,'animalRole','upper-leg')
    expect(legs.map((leg)=>leg.userData.kneeBend)).toEqual([-1,-1,1,1])
    expect(legs[2].userData.restDrop).toBeLessThan(legs[2].userData.segmentLength*1.6)
    const positions=feet.map((node)=>node.position.clone())
    const rotations=legs.map((node)=>node.quaternion.clone().normalize())
    createAnimalMotion(model)!.update(0,false)
    expect(feet.every((node,index)=>node.position.distanceTo(positions[index])<.00001)).toBe(true)
    for(const [index,node] of legs.entries())expect(node.quaternion.clone().normalize().angleTo(rotations[index])).toBeLessThan(.00001)
  })

  it('samples a continuous cycle with forefeet landing before hind feet',()=>{
    expect(sampleRabbitHop(0)).toEqual(sampleRabbitHop(1))
    expect(sampleRabbitHop(.16).body).toBeLessThan(0)
    const flight=sampleRabbitHop(.44),landing=sampleRabbitHop(.70)
    expect(flight.body).toBeGreaterThan(.1)
    expect(flight.frontLift).toBeGreaterThan(.14)
    expect(flight.hindLift).toBeGreaterThan(.15)
    expect(landing.frontLift).toBeCloseTo(0,6)
    expect(landing.hindLift).toBeGreaterThan(.05)
    for(const phase of [0,.16,.28,.44,.60,.70,.80,1]) {
      const left=sampleRabbitHop(phase-1e-6),right=sampleRabbitHop(phase+1e-6)
      for(const key of Object.keys(left) as (keyof typeof left)[])expect(Math.abs(left[key]-right[key])).toBeLessThan(.00001)
    }
  })

  it('preserves limb lengths and ground contacts throughout juvenile and adult hops',async()=>{
    const model=await load(),motion=createAnimalMotion(model)!,root=tagged(model,'faunaSpecies')[0]
    const feet=tagged(root,'animalRole','foot'),uppers=tagged(root,'animalRole','upper-leg'),lowers=tagged(root,'animalRole','lower-leg')
    let airborne=0,landing=0,grounded=0
    for(const age of [0,.5,1]) {
      motion.setSettings({...defaultAnimalSettings,age,behavior:'walk'})
      for(let frame=0;frame<360;frame++) {
        motion.update(1/120,true)
        model.updateMatrixWorld(true)
        const heights=feet.map((foot,index)=>{
          const bounds=new Box3().setFromObject(foot,true),lower=lowers[index],upper=uppers[index]
          expect(bounds.min.y).toBeGreaterThan(-.00001)
          expect(bounds.min.y).toBeLessThanOrEqual(.161)
          const endpoint=new Vector3(0,-Number(lower.userData.segmentLength),0).multiply(lower.scale).applyQuaternion(lower.quaternion).add(lower.position)
          expect(endpoint.distanceTo(foot.position)).toBeLessThan(.00001)
          expect(upper.position.distanceTo(lower.position)).toBeCloseTo(upper.userData.segmentLength*upper.scale.y,5)
          expect(lower.position.distanceTo(foot.position)).toBeCloseTo(lower.userData.segmentLength*lower.scale.y,5)
          return bounds.min.y
        })
        if(heights.every((height)=>height>.01))airborne++
        if(heights.every((height)=>height<.00001))grounded++
        if(heights[0]<.00001 && heights[2]>.02)landing++
        const bounds=new Box3().setFromObject(root,true)
        expect(bounds.min.y).toBeGreaterThan(-.00001)
        expect(bounds.max.y).toBeLessThan(.78)
        expect(bounds.min.z).toBeGreaterThan(-.40)
        expect(bounds.max.z).toBeLessThan(.42)
        expect(root.scale.toArray()).toEqual([1,1,1])
      }
    }
    expect(airborne).toBeGreaterThan(120)
    expect(grounded).toBeGreaterThan(60)
    expect(landing).toBeGreaterThan(15)
    const paused=snapshot(root)
    motion.update(2,false)
    expect(snapshot(root)).toEqual(paused)
    motion.update(0,true)
    expect(snapshot(root)).toEqual(paused)
  })

  it('grows ears and body proportions separately, preserving pale markings',async()=>{
    const model=await load(),motion=createAnimalMotion(model)!,root=tagged(model,'faunaSpecies')[0]
    const ears=tagged(root,'rabbitEarSide'),head=tagged(root,'animalRole','head')[0],body=tagged(root,'animalRole','body')[0]
    const materials=new Map<string,MeshStandardMaterial>()
    root.traverse((node)=>{if(node instanceof Mesh)for(const material of Array.isArray(node.material)?node.material:[node.material])if(material instanceof MeshStandardMaterial)materials.set(material.name,material)})
    const adult=materials.get('coat')!.color.clone(),cream=materials.get('rabbit_cream')!.color.clone()
    const origins=ears.map((node)=>node.position.clone())
    const setAge=(age:number)=>{
      motion.setSettings({...defaultAnimalSettings,age})
      for(let frame=0;frame<180;frame++)motion.update(1/60,false)
    }
    setAge(0)
    expect(head.scale.x/body.scale.x).toBeGreaterThan(1.3)
    expect(ears[0].scale.y).toBeCloseTo(.6,3)
    expect(materials.get('coat')!.color.equals(adult)).toBe(false)
    const young=materials.get('coat')!.color.clone()
    setAge(.5)
    expect(ears[0].scale.y).toBeCloseTo(.8,3)
    expect(materials.get('coat')!.color.equals(young)).toBe(false)
    setAge(1)
    expect(ears[0].scale.y).toBeCloseTo(1,3)
    expect(materials.get('coat')!.color.equals(adult)).toBe(true)
    expect(materials.get('rabbit_cream')!.color.equals(cream)).toBe(true)
    expect(ears.every((node,index)=>node.position.equals(origins[index]))).toBe(true)
    expect(ears.every((node)=>node.parent!.userData.followHead)).toBe(true)
  })

  it('chews from the jaw hinge and twitches the nose while keeping the head above ground',async()=>{
    const model=await load(),motion=createAnimalMotion(model)!,root=tagged(model,'faunaSpecies')[0]
    const jaw=tagged(root,'rabbitJaw')[0],nose=tagged(root,'rabbitNose')[0],head=tagged(root,'animalRole','head')[0]
    motion.setSettings({...defaultAnimalSettings,behavior:'graze'})
    for(let i=0;i<150;i++)motion.update(1/60,true)
    const j=jaw.quaternion.clone(),n=nose.position.clone()
    motion.update(.13,true)
    expect(jaw.quaternion.equals(j)).toBe(false)
    expect(nose.position.equals(n)).toBe(false)
    expect(new Box3().setFromObject(head,true).min.y).toBeGreaterThan(.02)
    const paused=snapshot(root)
    motion.update(1,false)
    expect(snapshot(root)).toEqual(paused)
    motion.setSettings({...defaultAnimalSettings,behavior:'idle'})
    for(let i=0;i<180;i++)motion.update(1/60,true)
    expect(jaw.rotation.x).toBeCloseTo(0,5)
  })

  it('bounds the family, separates child materials and pauses then completes growth',async()=>{
    const model=await load(),motion=createAnimalMotion(model)!
    motion.setSpread(.8)
    motion.setSettings({...defaultAnimalSettings,family:true})
    const waiting={...motion.update(4,true)}
    expect(waiting.offspring).toBe(0)
    expect({...motion.update(4,false)}).toEqual(waiting)
    motion.update(5,true)
    expect(motion.state.offspring).toBe(1)
    const roots=tagged(model,'faunaSpecies')
    expect(roots).toHaveLength(3)
    expect(roots.every((node)=>node.visible)).toBe(true)
    const childHead=tagged(roots[2],'animalRole','head')[0],adultHead=tagged(roots[0],'animalRole','head')[0]
    expect(childHead.scale.x).toBeLessThan(adultHead.scale.x)
    const coat=(root:Object3D)=>{
      let material:MeshStandardMaterial|undefined
      root.traverse((node)=>{if(node instanceof Mesh)for(const item of Array.isArray(node.material)?node.material:[node.material])if(item.name==='coat')material=item})
      return material!
    }
    expect(coat(roots[0])).not.toBe(coat(roots[2]))
    expect(coat(roots[0]).color.equals(coat(roots[2]).color)).toBe(false)
    const state={...motion.state},pose=snapshot(model)
    motion.update(2,false)
    expect({...motion.state}).toEqual(state)
    expect(snapshot(model)).toEqual(pose)
    motion.update(50,true)
    expect(motion.state.offspringAge).toBe(1)
    expect(motion.state.offspring).toBe(1)
    motion.setSettings({...defaultAnimalSettings,family:false})
    motion.update(0,false)
    expect(roots.filter((node)=>node.visible)).toHaveLength(1)
    motion.setSettings({...defaultAnimalSettings,age:0,automatic:true})
    for(let frame=0;frame<60*36;frame++)motion.update(1/60,true)
    expect(motion.state.age).toBeGreaterThan(.99)
  })
})
