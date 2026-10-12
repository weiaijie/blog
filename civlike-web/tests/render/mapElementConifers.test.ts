import { readFileSync } from 'node:fs'
import { Box3, Mesh, MeshStandardMaterial, Object3D, Vector3 } from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { describe, expect, it } from 'vitest'
import { botanicalStage, createBotanicalMotion } from '../../src/render/visuals/mapElementLifecycle'
import { defaultFieldSettings } from '../../src/render/visuals/mapElementGrowth'

async function load(id:string) {
  const b=readFileSync(new URL(`../../src/render/assets/elements/${id}.glb`,import.meta.url))
  return (await new GLTFLoader().parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'')).scene
}
function nodes(root:Object3D,prefix:string) {
  const result:Object3D[]=[]
  root.traverse((o)=>{if(o.userData.lifeRole && o.name.startsWith(prefix))result.push(o)})
  return result
}
function settle(motion:ReturnType<typeof createBotanicalMotion>,growth:number) {
  motion.setSettings({...defaultFieldSettings,growth,wind:0})
  for(let i=0;i<160;i++)motion.update(1/60,false)
}
function colors(root:Object3D,prefix:string) {
  const result:string[]=[]
  root.traverse((o)=>{if(o instanceof Mesh)for(const m of Array.isArray(o.material)?o.material:[o.material])if(m instanceof MeshStandardMaterial && m.name.startsWith(prefix))result.push(m.color.getHexString())})
  return result
}

describe('pine cone and reed panicle anatomy',()=>{
  for(const id of ['pine-tree-v4','reeds-v4']) {
    it(`${id} grows distinct organs, rewinds and pauses`,async()=>{
      const model=await load(id),motion=createBotanicalMotion(model)
      settle(motion,.05);expect(motion.visible.shoot).toBeGreaterThan(0)
      settle(motion,.49);expect(motion.visible[id==='pine-tree-v4'?'pollen':'blossom']).toBeGreaterThan(0)
      settle(motion,.82);expect(motion.visible[id==='pine-tree-v4'?'cone':'seed']).toBeGreaterThan(0)
      const all=nodes(model,'');model.updateMatrixWorld(true)
      const full=all.map((o)=>o.matrixWorld.toArray())
      settle(motion,.05);settle(motion,.82);model.updateMatrixWorld(true)
      expect(all.map((o)=>o.matrixWorld.toArray())).toEqual(full)
      expect(model.scale.toArray()).toEqual([1,1,1])
      motion.setSettings({...defaultFieldSettings,growth:.82,wind:.8,automatic:true})
      motion.update(0,false);const still=all.map((o)=>o.quaternion.toArray())
      motion.update(2,false);expect(all.map((o)=>o.quaternion.toArray())).toEqual(still)
      for(let i=0;i<100;i++)motion.update(.5,true)
      expect(motion.update(.5,true)).toBe(1)
    })
  }
  it('attaches fascicles to twigs, cones to stalks and opens woody scales',async()=>{
    const model=await load('pine-tree-v4'),motion=createBotanicalMotion(model)
    expect(nodes(model,'PineLimb')).toHaveLength(20)
    expect(nodes(model,'PineTwig')).toHaveLength(60)
    const leaves=nodes(model,'PineNeedles'),cones=nodes(model,'PineSeedCone'),scales=nodes(model,'ConeScale')
    expect(leaves).toHaveLength(60);expect(cones).toHaveLength(4);expect(scales).toHaveLength(72)
    for(const o of leaves)expect(o.parent!.name.startsWith('PineTwig')).toBe(true)
    for(const o of cones)expect(o.parent!.name.startsWith('PineConeStalk')).toBe(true)
    for(const o of scales)expect(o.parent!.name.startsWith('PineSeedCone')).toBe(true)
    settle(motion,.25)
    expect(motion.visible.foliage).toBe(61)
    for(const leaf of leaves)expect(leaf.scale.x).toBeGreaterThan(.4)
    expect(nodes(model,'PineTrunk')[0].scale.y).toBeLessThan(.7)
    settle(motion,.76);const closed=scales.map((o)=>o.quaternion.clone()),green=colors(model,'needle')
    model.updateMatrixWorld(true)
    const closedSize=new Box3().setFromObject(cones[0]).getSize(new Vector3())
    expect(green.length).toBeGreaterThan(60)
    settle(motion,1)
    model.updateMatrixWorld(true)
    const openSize=new Box3().setFromObject(cones[0]).getSize(new Vector3())
    expect(openSize.x).toBeGreaterThan(closedSize.x*1.15)
    expect(openSize.z).toBeGreaterThan(closedSize.z*1.15)
    for(let i=0;i<scales.length;i++)expect(scales[i].quaternion.angleTo(closed[i])).toBeCloseTo(.67,3)
    expect(colors(model,'needle')).toEqual(green)
    expect(motion.visible.seed).toBe(4)
    expect(motion.visible.cone).toBe(4)
    for(const role of ['blossom','fruit','pollen'])expect(motion.visible[role]??0).toBe(0)
  })
  it('attaches reed leaves and branched flower/seed plumes to culms',async()=>{
    const model=await load('reeds-v4'),motion=createBotanicalMotion(model)
    expect(nodes(model,'ReedCulm')).toHaveLength(9)
    expect(nodes(model,'ReedLeaf')).toHaveLength(45)
    expect(nodes(model,'ReedPanicle')).toHaveLength(9)
    for(const prefix of ['ReedFlowering','ReedSeedPlume']) {
      const parts=nodes(model,prefix);expect(parts).toHaveLength(9)
      for(const o of parts)expect(o.parent!.name.startsWith('ReedPanicle')).toBe(true)
    }
    settle(motion,.49);const green=colors(model,'leaf')
    expect(motion.visible.blossom).toBe(9);expect(motion.visible.seed??0).toBe(0)
    settle(motion,1)
    expect(motion.visible.seed).toBe(9);expect(motion.visible.blossom??0).toBe(0)
    expect(motion.visible.fruit??0).toBe(0)
    expect(colors(model,'leaf')).not.toEqual(green)
  })
  it('names nonfruit pine stages and retained reed plumes',()=>{
    expect(botanicalStage(.49,'pine-tree')).toBe('花粉球花')
    expect(botanicalStage(.65,'pine-tree')).toBe('球果发育')
    expect(botanicalStage(.97,'pine-tree')).toBe('鳞片张开')
    expect(botanicalStage(.97,'reeds')).toBe('枯黄留穗')
  })
})
