import { readFileSync } from 'node:fs'
import { Group, Object3D, Raycaster, Vector3 } from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { describe, expect, it } from 'vitest'
import { createBuildingMotion, defaultBuildingSettings, buildingStage } from '../../src/render/visuals/mapElementBuildings'
import { initialMapElement } from '../../src/render/assets/mapElementCatalog'

async function load(id: string) {
  const bytes=readFileSync(new URL(`../../src/render/assets/elements/${id}.glb`,import.meta.url))
  return (await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'')).scene
}
function parts(model: Group) {
  const result: Object3D[]=[]
  model.traverse((node) => { if (typeof node.userData.buildStart==='number') result.push(node) })
  return result
}

describe('building assembly, upgrades and independent working pivots', () => {
  for (const id of ['cottage','barn','windmill','watermill']) {
    it(`${id} assembles actual parts and preserves the footprint and connection nodes`, async () => {
      const model=await load(id), motion=createBuildingMotion(model)!, nodes=parts(model)
      const root=model.children.find((node) => node.userData.buildingType)!
      const sockets: Object3D[]=[]
      model.traverse((node) => { if (node.userData.connectionKind) sockets.push(node) })
      expect(sockets.some((node) => node.userData.connectionKind==='road')).toBe(true)
      if (id==='watermill') expect(sockets.filter((node) => node.userData.connectionKind==='water')).toHaveLength(2)
      expect(nodes.length).toBeGreaterThan(14)
      for (const node of nodes) {
        expect(node.userData.buildStart).toBeLessThan(node.userData.buildFull)
        expect(node.userData.buildFull).toBeLessThanOrEqual(1)
      }
      const anchors=sockets.map((node) => node.position.toArray())
      model.updateMatrixWorld(true)
      const walls=nodes.filter((node) => /^(TowerCourse|WallCourse)/.test(node.name))
      const doorwayRay=new Raycaster(new Vector3(0,1.05,5),new Vector3(0,0,-1))
      const hit=doorwayRay.intersectObjects(walls,true)[0]
      expect(hit,`${id} has a rear wall`).toBeDefined()
      expect(hit.distance,`${id} front doorway is not filled by a wall`).toBeGreaterThan(5)
      if (id==='watermill') {
        const inlet=sockets.find((node) => node.name==='ChannelInlet')!,outlet=sockets.find((node) => node.name==='ChannelOutlet')!
        const flow=nodes.find((node) => node.userData.buildingMotion==='flow')!
        expect(new Vector3().fromArray(flow.userData.motionAxis).dot(outlet.position.clone().sub(inlet.position))).toBeGreaterThan(0)
      }
      let lastCount=0
      for (const progress of [0,.20,.40,.60,.80,1]) {
        motion.setSettings({ ...defaultBuildingSettings,progress,working:false })
        for (let i=0;i<150;i++) motion.update(1/60,false)
        const permanent=nodes.filter((node) => node.visible && !node.userData.buildingTemporary)
        expect(permanent.length).toBeGreaterThanOrEqual(lastCount)
        lastCount=permanent.length
        expect(root.scale.toArray()).toEqual([1,1,1])
        expect(sockets.map((node) => node.position.toArray())).toEqual(anchors)
        expect(nodes.filter((node) => node.userData.buildingTier===2).every((node) => !node.visible)).toBe(true)
        if (progress===0) expect(permanent.length).toBe(1)
        if (progress===1) expect(nodes.filter((node) => node.userData.buildingTemporary).every((node) => !node.visible)).toBe(true)
      }
      motion.setSettings({ ...defaultBuildingSettings,tier:2 })
      motion.update(0,false)
      expect(nodes.filter((node) => node.userData.buildingTier===2).every((node) => node.visible)).toBe(true)
      expect(initialMapElement(`?element=${id}`).building).toBe(true)
    })
    it(`${id} stops mechanisms during construction, respects pause and finishes automatic construction`, async () => {
      const model=await load(id),motion=createBuildingMotion(model)!,nodes=parts(model)
      const moving=nodes.filter((node) => node.userData.buildingMotion)
      const pose=() => moving.map((node) => [...node.position.toArray(),...node.quaternion.toArray()])
      motion.update(0,true)
      const initial=pose()
      motion.update(1,true)
      expect(pose()).not.toEqual(initial)
      const advanced=pose()
      motion.update(2,false)
      expect(pose()).toEqual(advanced)
      motion.setSettings({ ...defaultBuildingSettings,working:false })
      motion.update(2,true)
      expect(pose()).toEqual(advanced)
      motion.setSettings({ ...defaultBuildingSettings,speed:0 })
      motion.update(2,true)
      expect(pose()).toEqual(advanced)
      motion.setSettings({ ...defaultBuildingSettings,progress:0,working:true })
      for (let i=0;i<200;i++) motion.update(1/60,false)
      const rotations=moving.map((node) => node.quaternion.toArray())
      motion.update(2,true)
      expect(moving.map((node) => node.quaternion.toArray())).toEqual(rotations)
      motion.setSettings({ ...defaultBuildingSettings,progress:0,automatic:true })
      const before=motion.update(0,false).progress
      motion.update(3,false)
      expect(motion.state.progress).toBe(before)
      for (let i=0;i<2100;i++) motion.update(1/60,true)
      expect(motion.state.progress).toBe(1)
      expect(motion.state.operating).toBe(true)
    })
  }
  it('does not attach building logic to other assets', () => {
    expect(createBuildingMotion(new Group())).toBeUndefined()
    expect(initialMapElement('?element=deer').building).toBe(false)
    expect(buildingStage(0)).toBe('地基')
    expect(buildingStage(1)).toBe('竣工')
  })
})
