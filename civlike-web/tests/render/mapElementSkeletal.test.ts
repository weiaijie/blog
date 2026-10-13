import { readFileSync } from 'node:fs'
import { Bone, Box3, Group, Mesh, SkinnedMesh, Vector3 } from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { describe, expect, it } from 'vitest'
import { createSkeletalMotion } from '../../src/render/visuals/mapElementSkeletal'
import { initialMapElement } from '../../src/render/assets/mapElementCatalog'

async function load(id:string) {const b=readFileSync(new URL(`../../src/render/assets/elements/${id}.glb`,import.meta.url));return new GLTFLoader().parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'')}
function pose(model:Group){const values:number[]=[];model.updateMatrixWorld(true);model.traverse((o)=>{if(o instanceof Bone)values.push(...o.matrixWorld.elements)});return values}
describe('CC0 character samples',()=>{
  for(const [family,count]of [['farmer',24],['horse',13]] as const) {
    it(`${family} preserves the source clips, skinning and license`,async()=>{
      const id=`${family}-v3`,{scene,animations}=await load(id)
      const original=JSON.parse(readFileSync(new URL(`../../src/render/assets/source/vendor/quaternius/${family==='farmer' ? 'Farmer' : 'Horse'}.gltf`,import.meta.url),'utf8'))
      expect(animations).toHaveLength(count)
      expect(animations.map((clip)=>clip.name).sort()).toEqual(original.animations.map((clip:{name:string})=>clip.name).sort())
      const root=scene.getObjectByName('LicensedAssetRoot')!
      expect(root.userData.assetLicense).toBe('CC0-1.0');expect(root.userData.assetAuthor).toBe('Quaternius')
      const skins:SkinnedMesh[]=[];scene.traverse((o)=>{if(o instanceof SkinnedMesh)skins.push(o)})
      expect(skins.length).toBeGreaterThan(0)
      expect(skins[0].skeleton.bones.length).toBeGreaterThan(15)
      const license=readFileSync(new URL(`../../src/render/assets/source/vendor/quaternius/${family==='farmer' ? 'characters' : 'animals'}-License.txt`,import.meta.url),'utf8')
      expect(license).toContain('CC0 1.0 Universal')
      const catalog=initialMapElement(`?element=${family}`)
      expect(catalog.id).toBe(id);expect(catalog.skeletal).toBe(true)
      expect(catalog.human).toBe(false);expect(catalog.animal).toBe(false)
    })
    it(`${family} plays one clip, blends changes and freezes on pause or zero speed`,async()=>{
      const {scene,animations}=await load(`${family}-v3`),motion=createSkeletalMotion(scene,animations)!
      expect(motion.update(0,false).clip).toBe('Idle')
      motion.setSettings({clip:'Walk',speed:1});motion.update(.4,true)
      const before=pose(scene);motion.update(.15,true);expect(pose(scene)).not.toEqual(before)
      const stopped=pose(scene),state=motion.update(0,false);expect(motion.update(5,false)).toEqual(state);expect(pose(scene)).toEqual(stopped)
      motion.setSettings({clip:'Walk',speed:0});motion.update(5,true);expect(pose(scene)).toEqual(stopped)
      motion.setSettings({clip:family==='horse' ? 'Eating' : 'Wave',speed:1});motion.update(0,true)
      expect(Math.max(...pose(scene).map((v,i)=>Math.abs(v-stopped[i])))).toBeLessThan(1e-5)
      motion.update(.5,true);expect(pose(scene)).not.toEqual(stopped)
      expect(()=>motion.setSettings({clip:'not-a-clip',speed:1})).toThrow('Missing animation')
      motion.destroy()
    })
    it(`${family} has finite animated geometry inside the authored per-clip bounds`,async()=>{
      const {scene,animations}=await load(`${family}-v3`),motion=createSkeletalMotion(scene,animations)!
      const clips=JSON.parse(scene.getObjectByName('LicensedAssetRoot')!.userData.clipBounds) as Record<string,{min:number[];max:number[]}>
      for(const clip of animations) {
        motion.setSettings({clip:clip.name,speed:1});motion.update(.3,true)
        const bounds=new Box3(new Vector3().fromArray(clips[clip.name].min),new Vector3().fromArray(clips[clip.name].max)).expandByScalar(.1)
        for(let frame=0;frame<10;frame++) {
          motion.update(clip.duration/10,true);scene.updateMatrixWorld(true)
          scene.traverse((o)=>{if(!(o instanceof Mesh))return;if(o instanceof SkinnedMesh)o.skeleton.update()
            const p=o.geometry.getAttribute('position')
            for(let i=0;i<p.count;i++) {const v=o.getVertexPosition(i,new Vector3()).applyMatrix4(o.matrixWorld);expect(v.toArray().every(Number.isFinite)).toBe(true);expect(bounds.containsPoint(v),`${clip.name}/${o.name}/${frame}`).toBe(true)}
          })
        }
      }
      motion.destroy()
    })
  }
  it('leaves ordinary models to their existing animation controllers',()=>expect(createSkeletalMotion(new Group(),[])).toBeUndefined())
})
