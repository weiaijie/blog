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
  root.traverse((o) => { if(o.userData.lifeRole && o.name.startsWith(prefix))result.push(o) })
  return result
}
function settle(motion:ReturnType<typeof createBotanicalMotion>,growth:number) {
  motion.setSettings({...defaultFieldSettings,growth,wind:0})
  for(let i=0;i<160;i++)motion.update(1/60,false)
}

describe('bamboo, meadow and tuber anatomy',() => {
  for(const id of ['bamboo','wildflowers','potato-field']) {
    it(`${id} changes organs, rewinds exactly and freezes while paused`,async () => {
      const model=await load(id),motion=createBotanicalMotion(model)
      settle(motion,.05);expect(motion.visible.shoot).toBeGreaterThan(0)
      expect(motion.visible.blossom??0).toBe(0)
      settle(motion,.49);expect(motion.visible[id==='bamboo'?'foliage':'blossom']).toBeGreaterThan(0)
      settle(motion,.82);expect(motion.visible[id==='bamboo'?'foliage':id==='wildflowers'?'seed':'tuber']).toBeGreaterThan(0)
      model.updateMatrixWorld(true)
      const organs=nodes(model,''),full=organs.map((o)=>o.matrixWorld.toArray())
      settle(motion,.05);settle(motion,.82);model.updateMatrixWorld(true)
      expect(organs.map((o)=>o.matrixWorld.toArray())).toEqual(full)
      expect(model.scale.toArray()).toEqual([1,1,1])
      motion.setSettings({...defaultFieldSettings,growth:.82,wind:.8,automatic:true})
      motion.update(0,false);const still=organs.map((o)=>[...o.position.toArray(),...o.quaternion.toArray()])
      motion.update(2,false);expect(organs.map((o)=>[...o.position.toArray(),...o.quaternion.toArray()])).toEqual(still)
      for(let i=0;i<100;i++)motion.update(.5,true)
      expect(motion.update(.5,true)).toBe(1)
    })
  }
  it('grows bamboo internodes lengthwise with fixed culm diameter and evergreen leaves',async () => {
    const model=await load('bamboo'),motion=createBotanicalMotion(model),culms=nodes(model,'BambooInternode')
    expect(culms).toHaveLength(40)
    expect(nodes(model,'BambooLeaves')).toHaveLength(50)
    expect(nodes(model,'BambooTip')).toHaveLength(10)
    expect(culms.filter((o)=>o.parent?.name.startsWith('BambooInternode'))).toHaveLength(35)
    settle(motion,.20);const early=culms.map((o)=>o.scale.y)
    for(const c of culms) {expect(c.scale.x).toBeCloseTo(1);expect(c.scale.z).toBeCloseTo(1)}
    const colors:string[]=[]
    model.traverse((o)=>{if(o instanceof Mesh)for(const m of Array.isArray(o.material)?o.material:[o.material])if(m instanceof MeshStandardMaterial && m.name.startsWith('bamboo_leaf'))colors.push(m.color.getHexString())})
    settle(motion,1)
    expect(culms.filter((o,i)=>o.scale.y>early[i]+.1).length).toBeGreaterThan(30)
    const mature:string[]=[]
    model.traverse((o)=>{if(o instanceof Mesh)for(const m of Array.isArray(o.material)?o.material:[o.material])if(m instanceof MeshStandardMaterial && m.name.startsWith('bamboo_leaf'))mature.push(m.color.getHexString())})
    expect(mature).toEqual(colors)
    expect(motion.visible.litter).toBeGreaterThan(0)
    for(const role of ['blossom','fruit','seed'])expect(motion.visible[role]??0).toBe(0)
    expect(motion.visible.husk??0).toBe(0)
  })
  it('opens separate meadow rays around discs then retains achenes without fruit berries',async () => {
    const model=await load('wildflowers'),motion=createBotanicalMotion(model),rays=nodes(model,'MeadowRay')
    expect(rays).toHaveLength(192)
    expect(nodes(model,'MeadowSeedHead')).toHaveLength(12)
    for(const ray of rays)expect(ray.parent!.name.startsWith('FlowerReceptacle')).toBe(true)
    settle(motion,.35);const buds=rays.map((o)=>o.quaternion.clone())
    settle(motion,.51)
    expect(rays.filter((o,i)=>o.quaternion.angleTo(buds[i])>.6).length).toBeGreaterThan(170)
    settle(motion,.85)
    expect(motion.visible.blossom??0).toBe(0)
    expect(motion.visible.seed).toBe(12)
    expect(motion.visible.fruit??0).toBe(0)
  })
  it('keeps growing tubers on underground stolons, distinct from aerial flowers',async () => {
    const model=await load('potato-field'),motion=createBotanicalMotion(model),tubers=nodes(model,'PotatoTuber')
    expect(tubers).toHaveLength(20)
    expect(nodes(model,'PotatoCompoundLeaf')).toHaveLength(48)
    const flowers=nodes(model,'PotatoFlower')
    expect(flowers).toHaveLength(12)
    for(const flower of flowers)expect(flower.parent!.name.startsWith('PotatoPedicel')).toBe(true)
    for(const tuber of tubers)expect(tuber.parent!.name.startsWith('PotatoStolon')).toBe(true)
    settle(motion,.49);model.updateMatrixWorld(true)
    const early=tubers.map((o)=>new Box3().setFromObject(o).getSize(new Vector3()).length())
    settle(motion,.9);model.updateMatrixWorld(true)
    tubers.forEach((o,i)=>{
      const box=new Box3().setFromObject(o)
      expect(box.max.y).toBeLessThan(.03)
      expect(box.min.y).toBeGreaterThan(-.55)
      expect(Math.max(Math.abs(box.min.x),Math.abs(box.max.x),Math.abs(box.min.z),Math.abs(box.max.z))).toBeLessThan(1.75)
      expect(box.getSize(new Vector3()).length()).toBeGreaterThan(early[i]*2)
    })
    const skins:MeshStandardMaterial[]=[]
    model.traverse((o)=>{if(o instanceof Mesh)for(const m of Array.isArray(o.material)?o.material:[o.material])if(m instanceof MeshStandardMaterial && m.name==='potato_skin')skins.push(m)})
    const color=skins[0].color.getHexString();settle(motion,.40)
    for(const skin of skins)expect(skin.color.getHexString()).toBe(color)
    settle(motion,1)
    expect(motion.visible.tuber).toBe(20)
    expect(motion.visible.fruit??0).toBe(0)
    expect(motion.visible.blossom??0).toBe(0)
  })
  it('exports a separate near soil cover without hiding plants or tubers',async () => {
    const model=await load('potato-field'),covers:Object3D[]=[]
    model.traverse((o)=>{if(o.userData.inspectionCover)covers.push(o)})
    expect(covers).toHaveLength(1)
    const cover=covers[0],box=new Box3().setFromObject(cover)
    expect(box.min.z).toBeCloseTo(0,4)
    expect(box.max.z).toBeCloseTo(1.75,4)
    cover.traverse((o)=>expect(o.userData.lifeRole).toBeUndefined())
    expect(model.getObjectByName('BackSoil')).toBeDefined()
  })
  it('labels vegetative bamboo growth and underground tuber stages explicitly',() => {
    expect(botanicalStage(.49,'bamboo')).toBe('展枝')
    expect(botanicalStage(.97,'bamboo')).toBe('换叶')
    expect(botanicalStage(.65,'potato-field')).toBe('块茎膨大')
    expect(botanicalStage(.65,'wildflowers')).toBe('结籽')
  })
})
