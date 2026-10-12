import { readFileSync } from 'node:fs'
import { Mesh, Object3D, Vector3 } from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { describe, expect, it } from 'vitest'
import { botanicalStage, createBotanicalMotion } from '../../src/render/visuals/mapElementLifecycle'
import { defaultFieldSettings } from '../../src/render/visuals/mapElementGrowth'

async function load(id:string) {
  const b=readFileSync(new URL(`../../src/render/assets/elements/${id}.glb`,import.meta.url))
  return (await new GLTFLoader().parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'')).scene
}
function nodes(root:Object3D,prefix:string) {
  const found:Object3D[]=[]
  root.traverse((o) => { if(o.userData.lifeRole && o.name.startsWith(prefix)) found.push(o) })
  return found
}
function settle(motion:ReturnType<typeof createBotanicalMotion>,growth:number) {
  motion.setSettings({...defaultFieldSettings,growth,wind:0})
  for(let i=0;i<160;i++) motion.update(1/60,false)
}
describe('understory and aquatic specimens',() => {
  for(const id of ['cactus','fern','mushrooms','lily-pad']) {
    it(`${id} has reversible, independent phases and keeps its root stable`,async () => {
      const model=await load(id),motion=createBotanicalMotion(model)
      settle(motion,.05)
      expect(motion.visible.shoot).toBeGreaterThan(0)
      expect(motion.visible.blossom??0).toBe(0)
      settle(motion,.49)
      expect(motion.visible[id==='fern' ? 'foliage' : id==='mushrooms' ? 'cap' : 'blossom']).toBeGreaterThan(0)
      settle(motion,.82)
      expect(motion.visible[['fern','mushrooms'].includes(id)?'spore':'fruit']).toBeGreaterThan(0)
      expect(motion.visible.blossom??0).toBe(0)
      model.updateMatrixWorld(true)
      const parts=nodes(model,''),final=parts.map((o) => o.matrixWorld.toArray())
      settle(motion,.05);settle(motion,.82);model.updateMatrixWorld(true)
      expect(parts.map((o) => o.matrixWorld.toArray())).toEqual(final)
      expect(model.scale.toArray()).toEqual([1,1,1])
      motion.setSettings({...defaultFieldSettings,growth:.82,wind:.7,automatic:true})
      motion.update(0,false)
      const frozen=parts.map((o) => [...o.position.toArray(),...o.quaternion.toArray()])
      motion.update(2,false)
      expect(parts.map((o) => [...o.position.toArray(),...o.quaternion.toArray()])).toEqual(frozen)
    })
  }
  it('uncoils successive fern rachis joints and carries sori with the pinnae',async () => {
    const model=await load('fern'),motion=createBotanicalMotion(model),joints=nodes(model,'FernRachis')
    expect(joints).toHaveLength(90)
    expect(nodes(model,'FernSori')).toHaveLength(90)
    for(const sorus of nodes(model,'FernSori')) expect(sorus.parent!.name.startsWith('FernPinnae')).toBe(true)
    settle(motion,.2);const curled=joints.map((o) => o.quaternion.clone())
    settle(motion,.65)
    expect(joints.filter((o,i) => o.quaternion.angleTo(curled[i])>.1).length).toBeGreaterThan(60)
    const up=new Vector3(0,1,0)
    for(const joint of joints) {
      const axis=new Vector3().fromArray(joint.userData.lifeOpenAxis)
      expect(Math.abs(axis.dot(up))).toBeLessThan(.001)
    }
    expect(motion.visible.blossom??0).toBe(0)
    expect(motion.visible.seed??0).toBe(0)
    for(const growth of [.15,.25,.35]) {
      settle(motion,growth);model.updateMatrixWorld(true)
      let minimum=Infinity
      model.traverse((o) => {
        if(!(o instanceof Mesh)) return
        let ancestor:Object3D|null=o
        while(ancestor) {if(!ancestor.visible)return;ancestor=ancestor.parent}
        const p=new Vector3()
        for(let i=0;i<o.geometry.attributes.position.count;i++) minimum=Math.min(minimum,p.fromBufferAttribute(o.geometry.attributes.position,i).applyMatrix4(o.matrixWorld).y)
      })
      expect(minimum).toBeGreaterThan(-.001)
    }
  })
  it('exports actual cap morph targets and opens caps without scaling the entire fungus',async () => {
    const model=await load('mushrooms'),motion=createBotanicalMotion(model),caps:Mesh[]=[]
    model.traverse((o) => {if(o instanceof Mesh && o.morphTargetDictionary?.ClosedCap!==undefined)caps.push(o)})
    expect(caps.length).toBeGreaterThanOrEqual(7)
    settle(motion,.24)
    for(const cap of caps) {
      expect(cap.morphTargetInfluences![cap.morphTargetDictionary!.ClosedCap]).toBe(1)
      expect(cap.geometry.morphAttributes.position.length).toBeGreaterThan(0)
      const base=cap.geometry.attributes.position,morph=cap.geometry.morphAttributes.position[0]
      expect(Array.from(morph.array).some((value,i) => cap.geometry.morphTargetsRelative ? Math.abs(value)>.01 : Math.abs(value-base.array[i])>.01)).toBe(true)
    }
    settle(motion,.82)
    for(const cap of caps) expect(cap.morphTargetInfluences![cap.morphTargetDictionary!.ClosedCap]).toBe(0)
    settle(motion,.24)
    for(const cap of caps) expect(cap.morphTargetInfluences![cap.morphTargetDictionary!.ClosedCap]).toBe(1)
    expect(nodes(model,'MushroomStipe')).toHaveLength(7)
    expect(motion.visible.blossom??0).toBe(0)
    expect(motion.visible.foliage??0).toBe(0)
  })
  it('keeps lily pads above water, unfolds separate petals and freezes water-driven bobbing',async () => {
    const model=await load('lily-pad'),motion=createBotanicalMotion(model),pads=nodes(model,'LilyPad')
    expect(pads).toHaveLength(6)
    expect(nodes(model,'LilyOuterPetal')).toHaveLength(24)
    expect(nodes(model,'LilyInnerPetal')).toHaveLength(18)
    settle(motion,.49)
    motion.setSettings({...defaultFieldSettings,growth:.49,wind:1})
    const before=pads.map((o) => o.position.y)
    motion.update(.5,true)
    expect(pads.map((o) => o.position.y)).not.toEqual(before)
    for(const p of pads) expect(p.position.y).toBeGreaterThan(.15)
    motion.setSettings({...defaultFieldSettings,growth:.49,wind:0})
    motion.update(.5,true);const calm=pads.map((o) => o.position.toArray())
    motion.update(.5,true);expect(pads.map((o) => o.position.toArray())).toEqual(calm)
  })
  it('uses spores for fern/fungus labels and stem growth for cactus',() => {
    expect(botanicalStage(.47,'fern')).toBe('羽叶展开')
    expect(botanicalStage(.81,'fern')).toBe('孢子成熟')
    expect(botanicalStage(.47,'mushrooms')).toBe('菌盖展开')
    expect(botanicalStage(.81,'mushrooms')).toBe('产孢')
    expect(botanicalStage(.25,'cactus')).toBe('茎节伸长')
  })
})
