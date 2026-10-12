import { readFileSync } from 'node:fs'
import { Box3, Mesh, Object3D, Raycaster, Vector3 } from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { describe, expect, it } from 'vitest'
import { createBuildingMotion, defaultBuildingSettings } from '../../src/render/visuals/mapElementBuildings'

async function load(id: string) {
  const bytes=readFileSync(new URL(`../../src/render/assets/elements/${id}.glb`,import.meta.url))
  return (await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'')).scene
}
function matching(root: Object3D, test: (node: Object3D) => boolean) {
  const found: Object3D[]=[]; root.traverse((node) => { if (test(node)) found.push(node) }); return found
}
function surfaces(root: Object3D) { return matching(root,(node) => node instanceof Mesh) as Mesh[] }

describe('fortification passage, interfaces and cloth', () => {
  for (const id of ['watchtower','castle-keep','castle-gate','castle-wall'] as const) {
    it(`${id} assembles distinct components and animates cloth with a fixed pole edge`, async () => {
      const model=await load(id),motion=createBuildingMotion(model)!
      const banners=matching(model,(node) => node.userData.buildingMotion==='banner').flatMap(surfaces)
      expect(banners.length).toBeGreaterThan(0)
      motion.update(0,true)
      model.updateMatrixWorld(true)
      const mastBase = { watchtower:5.3,'castle-keep':4.4,'castle-gate':5.33,'castle-wall':3.18 }[id]!
      for (const mast of matching(model,(node) => node.name.startsWith('FlagMast'))) {
        expect(new Box3().setFromObject(mast,true).min.y).toBeCloseTo(mastBase,4)
      }
      const before=banners.map((node) => Array.from(node.geometry.attributes.position.array))
      motion.update(.4,true)
      let moved=0
      banners.forEach((mesh,index) => {
        const attr=mesh.geometry.attributes.position,min=mesh.geometry.boundingBox!.min.x
        for (let i=0;i<attr.count;i++) {
          expect(attr.getX(i)).toBe(before[index][i*3])
          expect(attr.getY(i)).toBe(before[index][i*3+1])
          if (Math.abs(attr.getX(i)-min)<.00001) expect(attr.getZ(i)).toBe(before[index][i*3+2])
          else if (attr.getZ(i)!==before[index][i*3+2]) moved++
        }
      })
      expect(moved).toBeGreaterThan(10)
      const stopped=banners.map((node) => Array.from(node.geometry.attributes.position.array))
      motion.update(3,false)
      expect(banners.map((node) => Array.from(node.geometry.attributes.position.array))).toEqual(stopped)
      motion.setSettings({ ...defaultBuildingSettings,working:false })
      motion.update(2,true)
      expect(banners.map((node) => Array.from(node.geometry.attributes.position.array))).toEqual(stopped)
      const nodes=matching(model,(node) => typeof node.userData.buildStart==='number')
      motion.setSettings({ ...defaultBuildingSettings,progress:0 })
      for(let i=0;i<150;i++) motion.update(1/60,false)
      expect(nodes.filter((node) => node.visible)).toHaveLength(1)
      motion.setSettings({ ...defaultBuildingSettings,progress:1,tier:2 })
      for(let i=0;i<150;i++) motion.update(1/60,false)
      expect(nodes.filter((node) => node.userData.buildingTier===2).every((node) => node.visible)).toBe(true)
      expect(model.children.find((node) => node.userData.buildingType)!.scale.toArray()).toEqual([1,1,1])
    })
  }
  it('matches opposing wall sockets and preserves an unobstructed wall walk at the ends', async () => {
    const wall=await load('castle-wall'), gate=await load('castle-gate')
    createBuildingMotion(wall)!.update(0,false);createBuildingMotion(gate)!.update(0,false)
    const right=matching(wall,(node) => node.name==='WallRight')[0]
    const left=matching(gate,(node) => node.name==='WallLeft')[0]
    expect(right.userData.connectionProfile).toBe(left.userData.connectionProfile)
    expect(right.userData.walkwayHeight).toBe(3.2)
    expect(right.userData.wallThickness).toBe(left.userData.wallThickness)
    expect(new Vector3().fromArray(right.userData.connectionNormal).dot(new Vector3().fromArray(left.userData.connectionNormal))).toBe(-1)
    const shift=left.position.clone().sub(right.position)
    wall.position.copy(shift);wall.updateMatrixWorld(true);gate.updateMatrixWorld(true)
    expect(right.getWorldPosition(new Vector3()).distanceTo(left.getWorldPosition(new Vector3()))).toBeLessThan(.0001)
    const cast=new Raycaster(new Vector3(0,3.36,0),new Vector3(1,0,0))
    wall.position.set(0,0,0);wall.updateMatrixWorld(true)
    const wallMesh=matching(wall,(node) => node.userData.buildStart!==undefined && node.visible).flatMap(surfaces)
    expect(cast.intersectObjects(wallMesh).filter((hit) => hit.distance<2)).toHaveLength(0)
  })
  it('opens the bridge before the portcullis, preserves chain anchors and clears the passage', async () => {
    const model=await load('castle-gate'),motion=createBuildingMotion(model)!
    const bridge=matching(model,(node) => node.userData.buildingMotion==='bridge')[0]
    const gate=matching(model,(node) => node.userData.buildingMotion==='lift')[0]
    const chains=matching(model,(node) => node.userData.buildingMotion==='chain').flatMap(surfaces)
    const root=model.children.find((node) => node.userData.buildingType)!
    motion.update(0,true);model.updateMatrixWorld(true)
    const baseGate=gate.position.y
    const poleTops=chains.map((mesh) => new Box3().setFromObject(mesh,true).max.y)
    motion.setSettings({ ...defaultBuildingSettings,gateOpen:true })
    motion.update(.1,true)
    expect(bridge.quaternion.x).not.toBe(0)
    expect(gate.position.y).toBeCloseTo(baseGate,5)
    const paused=motion.state.access
    motion.update(2,false)
    expect(motion.state.access).toBe(paused)
    for(let i=0;i<400;i++) motion.update(1/60,true)
    expect(motion.state.access).toBe(1)
    model.updateMatrixWorld(true)
    expect(gate.position.y-baseGate).toBeCloseTo(2.32,4)
    const bridgeBounds=new Box3().setFromObject(bridge,true)
    expect(bridgeBounds.max.z).toBeCloseTo(3.74,2)
    chains.forEach((mesh,index) => {
      const bounds=new Box3().setFromObject(mesh,true)
      expect(bounds.max.y).toBeCloseTo(poleTops[index],5)
      expect(bounds.min.y).toBeCloseTo(.26,4)
      expect(bounds.max.z).toBeGreaterThan(3.72)
    })
    const ray=new Raycaster(new Vector3(0,1.3,4),new Vector3(0,0,-1))
    expect(ray.intersectObjects(surfaces(model).filter((mesh) => mesh.visible))).toHaveLength(0)
    const bounds=new Box3(new Vector3().fromArray(root.userData.animationBoundsMin),new Vector3().fromArray(root.userData.animationBoundsMax))
    expect(bounds.containsBox(bridgeBounds)).toBe(true)
    motion.setSettings({ ...defaultBuildingSettings,gateOpen:false })
    for(let i=0;i<400;i++) motion.update(1/60,true)
    expect(motion.state.access).toBe(0)
    expect(gate.position.y).toBeCloseTo(baseGate,5)
  })
})
