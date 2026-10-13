import {
  AnimationMixer, Box3, Color, DirectionalLight, Group, HemisphereLight, Mesh,
  MeshStandardMaterial, OrthographicCamera, Scene, SRGBColorSpace, Vector3, WebGLRenderer,
} from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { createFieldMotion, defaultFieldSettings, type FieldSettings } from './mapElementGrowth'
import { createBotanicalMotion } from './mapElementLifecycle'
import { createAnimalMotion, defaultAnimalSettings, type AnimalSettings, type AnimalState } from './mapElementAnimals'
import { createBuildingMotion, defaultBuildingSettings, type BuildingSettings, type BuildingState } from './mapElementBuildings'
import { createTerrainMotion, defaultTerrainSettings, type TerrainSettings, type TerrainState } from './mapElementTerrain'
import { createHumanMotion, defaultHumanSettings, type HumanSettings, type HumanState } from './mapElementPeople'
import { createRouteMotion, defaultRouteSettings, type RouteSettings, type RouteState } from './mapElementRoutes'
import { createTransportMotion, defaultTransportSettings, type TransportSettings, type TransportState } from './mapElementTransport'
import { createMountedMotion, defaultMountedSettings, type MountedSettings, type MountedState } from './mapElementMounted'
import { createVesselMotion, defaultVesselSettings, type VesselSettings, type VesselState } from './mapElementVessels'
import { createSkeletalMotion, defaultSkeletalSettings, type SkeletalSettings, type SkeletalState } from './mapElementSkeletal'

export type ElementView = 'perspective' | 'front' | 'side' | 'back' | 'top'
export type ElementScene = {
  setView: (view: ElementView) => void
  setPlaying: (value: boolean) => void
  setWireframe: (value: boolean) => void
  setCutaway: (value: boolean) => void
  setFieldSettings: (value: FieldSettings) => void
  setAnimalSettings: (value: AnimalSettings) => void
  setBuildingSettings: (value: BuildingSettings) => void
  setTerrainSettings: (value: TerrainSettings) => void
  setHumanSettings: (value: HumanSettings) => void
  setRouteSettings: (value: RouteSettings) => void
  setTransportSettings: (value: TransportSettings) => void
  setMountedSettings: (value: MountedSettings) => void
  setVesselSettings: (value: VesselSettings) => void
  setSkeletalSettings: (value: SkeletalSettings) => void
  destroy: () => void
}

function disposeModel(group: Group) {
  group.traverse((object) => {
    if (object instanceof Mesh) {
      object.geometry.dispose()
      const materials = Array.isArray(object.material) ? object.material : [object.material]
      for (const material of materials) material.dispose()
    }
  })
}

export function mountMapElement(
  host: HTMLDivElement,
  url: string,
  onLoad: (animations: number) => void,
  onError: (message: string) => void,
  onGrowth?: (value: number) => void,
  onAnimal?: (value: AnimalState) => void,
  onBuilding?: (value: BuildingState) => void,
  onTerrain?: (value: TerrainState) => void,
  onHuman?: (value: HumanState) => void,
  onRoute?: (value: RouteState) => void,
  onTransport?: (value: TransportState) => void,
  onMounted?: (value: MountedState) => void,
  onVessel?: (value: VesselState) => void,
  onSkeletal?: (value: SkeletalState) => void,
): ElementScene {
  const renderer = new WebGLRenderer({ antialias: true, preserveDrawingBuffer: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.outputColorSpace = SRGBColorSpace
  renderer.domElement.setAttribute('aria-label', '三维模型')
  host.appendChild(renderer.domElement)
  const scene = new Scene()
  scene.background = new Color('#edf1f2')
  const ambient=new HemisphereLight(0xffffff, 0x939aa0, 2.2)
  scene.add(ambient)
  const dayBackground=new Color('#edf1f2'),nightBackground=new Color('#262d31')
  const key = new DirectionalLight(0xffffff, 2.5)
  key.position.set(-3, 6, 5)
  scene.add(key)
  const fill = new DirectionalLight(0xdae9ff, 1.1)
  fill.position.set(4, 2, -3)
  scene.add(fill)
  const camera = new OrthographicCamera(-3, 3, 3, -3, .01, 100)
  const controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.enablePan = false
  controls.minZoom = .35
  controls.maxZoom = 5
  let model: Group | undefined
  let mixer: AnimationMixer | undefined
  let field: ReturnType<typeof createFieldMotion> | undefined
  let botanical: ReturnType<typeof createBotanicalMotion> | undefined
  let animal: ReturnType<typeof createAnimalMotion>
  let building: ReturnType<typeof createBuildingMotion>
  let terrain: ReturnType<typeof createTerrainMotion>
  let human: ReturnType<typeof createHumanMotion>
  let humanSettings={...defaultHumanSettings}
  let skeletal: ReturnType<typeof createSkeletalMotion>
  let skeletalSettings={...defaultSkeletalSettings}
  let route:ReturnType<typeof createRouteMotion>
  let transport:ReturnType<typeof createTransportMotion>
  let transportSettings={...defaultTransportSettings}
  let mounted:ReturnType<typeof createMountedMotion>
  let mountedSettings={...defaultMountedSettings}
  let vessel:ReturnType<typeof createVesselMotion>
  let vesselSettings={...defaultVesselSettings}
  let routeSettings={...defaultRouteSettings}
  const routeNeighbors:{model:Group;motion:NonNullable<ReturnType<typeof createRouteMotion>>;edge:number}[]=[]
  let terrainSettings=defaultTerrainSettings('grassland')
  let buildingSettings = { ...defaultBuildingSettings }
  let animalSettings = { ...defaultAnimalSettings }
  let fieldSettings = { ...defaultFieldSettings }
  let lastGrowthReport = 0
  let destroyed = false
  let playing = !window.matchMedia('(prefers-reduced-motion: reduce)').matches
  let wireframe = false
  let cutaway = false
  let view: ElementView = 'perspective'
  let size = 4
  let singleSize = 4
  let frameRatio = .68
  let frame = 0
  let previousTime = 0
  const center = new Vector3()
  const skeletalBounds=new Map<string,Box3>()
  function fitSkeletal(clip: string) {
    const bounds=skeletalBounds.get(clip)
    if(!bounds)return
    bounds.getCenter(center)
    const extent=bounds.getSize(new Vector3())
    size=Math.max(extent.x,extent.y,extent.z,.1)
    singleSize=size
    frameRatio=Math.max(.68,extent.length()*.55/size)
    setView(view)
  }

  function resize() {
    const width = Math.max(1, host.clientWidth)
    const height = Math.max(1, host.clientHeight)
    renderer.setSize(width, height, false)
    const aspect = width / height
    // Cover the full bounding sphere so rotating wide, tall assets cannot clip their corners.
    const halfHeight = size * Math.max(frameRatio, aspect < 1.2 ? .76 : .68) / Math.min(aspect, 1)
    camera.left = -halfHeight * aspect
    camera.right = halfHeight * aspect
    camera.top = halfHeight
    camera.bottom = -halfHeight
    camera.updateProjectionMatrix()
  }

  function setView(next: ElementView) {
    view = next
    controls.reset()
    camera.zoom = 1
    camera.up.set(0, 1, 0)
    const direction = next === 'front' ? new Vector3(0, 0, 1) : next==='back' ? new Vector3(0,0,-1)
      : next === 'side' ? new Vector3(1, 0, 0)
        : next === 'top' ? new Vector3(0, 1, 0) : new Vector3(1.3, .9, 1.6).normalize()
    if (next === 'top') camera.up.set(0, 0, -1)
    camera.position.copy(center).addScaledVector(direction, size * 2.5)
    camera.far = size * 8 + 10
    camera.lookAt(center)
    controls.target.copy(center)
    controls.enableRotate = next === 'perspective'
    controls.update()
    resize()
  }

  function setWireframe(value: boolean) {
    wireframe = value
    model?.traverse((object) => {
      if (object instanceof Mesh) {
        for (const material of Array.isArray(object.material) ? object.material : [object.material]) {
          if (material instanceof MeshStandardMaterial) material.wireframe = value
        }
      }
    })
  }

  function setCutaway(value: boolean) {
    cutaway=value
    model?.traverse((object) => { if (object.userData.inspectionCover) object.visible=!value })
    host.dataset.cutaway=String(value)
  }

  void new GLTFLoader().loadAsync(url).then((gltf) => {
    if (destroyed) { disposeModel(gltf.scene); return }
    model = gltf.scene
    scene.add(model)
    const bounds = new Box3().setFromObject(model)
    model.traverse((node) => {
      if(node.userData.licensedAsset && typeof node.userData.clipBounds==='string') {
        const clips=JSON.parse(node.userData.clipBounds) as Record<string,{min:number[];max:number[]}>
        for(const [name,box]of Object.entries(clips))skeletalBounds.set(name,new Box3(new Vector3().fromArray(box.min).applyMatrix4(node.matrixWorld),new Vector3().fromArray(box.max).applyMatrix4(node.matrixWorld)))
        return
      }
      if (Array.isArray(node.userData.animationBoundsMin) && Array.isArray(node.userData.animationBoundsMax)) {
        bounds.expandByPoint(new Vector3().fromArray(node.userData.animationBoundsMin).applyMatrix4(node.matrixWorld))
        bounds.expandByPoint(new Vector3().fromArray(node.userData.animationBoundsMax).applyMatrix4(node.matrixWorld))
      }
    })
    if(skeletalBounds.has('Idle'))bounds.copy(skeletalBounds.get('Idle')!)
    bounds.getCenter(center)
    const extent = bounds.getSize(new Vector3())
    size = Math.max(extent.x, extent.y, extent.z, .1)
    frameRatio = Math.max(.68, extent.length() * .55 / size)
    singleSize = size
    building = createBuildingMotion(model)
    building?.setSettings(buildingSettings)
    building?.update(0,false)
    terrain=createTerrainMotion(model)
    terrain?.setSettings(terrainSettings)
    terrain?.update(0,false)
    animal = createAnimalMotion(model)
    animal?.setSpread(singleSize*.8)
    animal?.setSettings(animalSettings)
    if (animalSettings.family) size=singleSize*2.25
    field = createFieldMotion(model)
    field.setSettings(fieldSettings)
    botanical = createBotanicalMotion(model)
    botanical.setSettings(fieldSettings)
    host.dataset.plants = String(field.cropCount)
    field.update(0, false)
    botanical.update(0, false)
    animal?.update(0,false)
    human=createHumanMotion(model,gltf.animations)
    human?.setSettings(humanSettings)
    human?.update(0,false)
    skeletal=createSkeletalMotion(model,gltf.animations)
    skeletal?.setSettings(skeletalSettings)
    skeletal?.update(0,false)
    route=createRouteMotion(model)
    transport=createTransportMotion(model)
    transport?.setSettings(transportSettings)
    transport?.update(0,false)
    mounted=createMountedMotion(model)
    mounted?.setSettings(mountedSettings)
    mounted?.update(0,false)
    vessel=createVesselMotion(model)
    vessel?.setSettings(vesselSettings)
    vessel?.update(0,false)
    if(route){
      const ports:{edge:number;offset:Vector3}[]=[]
      model.traverse((o)=>{if(typeof o.userData.routePort==='number')ports.push({edge:o.userData.routePort,offset:new Vector3().fromArray(o.userData.neighborOffsetGltf)})})
      for(const {edge,offset}of ports){
        const neighbor=model.clone(true),motion=createRouteMotion(neighbor)!
        neighbor.position.copy(offset);neighbor.rotation.y=(edge+3)*Math.PI/3;neighbor.visible=false
        scene.add(neighbor);routeNeighbors.push({model:neighbor,motion,edge})
      }
    }
    route?.setSettings(routeSettings)
    route?.update(0,false)
    if(route && routeSettings.connected)size=singleSize*2.6
    if (gltf.animations.length && !human && !skeletal) {
      mixer = new AnimationMixer(model)
      for (const clip of gltf.animations) mixer.clipAction(clip).play()
    }
    setWireframe(wireframe)
    setCutaway(cutaway)
    setView(view)
    if(skeletal)fitSkeletal(skeletal.update(0,false).clip)
    host.dataset.loaded = 'true'
    host.dataset.animations = String(gltf.animations.length)
    onLoad(gltf.animations.length + (field.count || botanical.count || animal || building || terrain || route || transport || mounted || vessel ? 1 : 0))
  }).catch((error: unknown) => {
    if (!destroyed) onError(error instanceof Error ? error.message : '模型加载失败')
  })

  const observer = new ResizeObserver(resize)
  observer.observe(host)
  setView(view)
  function animate(time: number) {
    const delta = previousTime ? Math.min((time - previousTime) / 1000, .05) : 0
    previousTime = time
    if (playing) mixer?.update(delta)
    if(vessel){
      const state=vessel.update(delta,playing)
      host.dataset.vessel=JSON.stringify(state)
      if(time-lastGrowthReport>120){onVessel?.({...state});lastGrowthReport=time}
    }
    if(mounted){
      const state=mounted.update(delta,playing)
      host.dataset.mounted=JSON.stringify(state)
      if(time-lastGrowthReport>120){onMounted?.({...state});lastGrowthReport=time}
    }
    if(transport){
      const state=transport.update(delta,playing)
      host.dataset.transport=JSON.stringify(state)
      if(time-lastGrowthReport>120){onTransport?.({...state});lastGrowthReport=time}
    }
    if(route){
      const state=route.update(delta,playing)
      const ports=routeSettings.shape==='straight' ? [0,3] : routeSettings.shape==='bend' ? [0,2] : route.kind==='rail-track' ? [0,2,3] : [0,2,4]
      for(const neighbor of routeNeighbors){
        neighbor.model.visible=routeSettings.connected&&ports.includes(neighbor.edge)
        if(neighbor.model.visible){neighbor.motion.setSettings({...routeSettings,shape:'straight',progress:state.progress,automatic:false,connected:false});neighbor.motion.update(delta,playing)}
      }
      host.dataset.route=JSON.stringify(state)
      if(time-lastGrowthReport>120){onRoute?.({...state});lastGrowthReport=time}
    }
    if(human){
      const state=human.update(delta,playing)
      host.dataset.human=JSON.stringify(state)
      if(time-lastGrowthReport>120){onHuman?.(state);lastGrowthReport=time}
    }
    if(skeletal){
      const state=skeletal.update(delta,playing)
      host.dataset.skeletal=JSON.stringify(state)
      if(time-lastGrowthReport>120){onSkeletal?.(state);lastGrowthReport=time}
    }
    if(terrain) {
      const state=terrain.update(delta,playing)
      host.dataset.terrain=JSON.stringify(state)
      if(time-lastGrowthReport>120){onTerrain?.(state);lastGrowthReport=time}
    }
    if (building) {
      const state=building.update(delta,playing)
      if(state.lighting){
        const night=state.lighting.night
        ;(scene.background as Color).copy(dayBackground).lerp(nightBackground,night)
        ambient.intensity=2.2-1.92*night;key.intensity=2.5-2.25*night;fill.intensity=1.1-.92*night
      }
      host.dataset.building=JSON.stringify(state)
      if (time-lastGrowthReport>120) { onBuilding?.({ ...state }); lastGrowthReport=time }
    }
    if (animal) {
      const state = animal.update(delta,playing)
      host.dataset.animals=JSON.stringify(state)
      if (time-lastGrowthReport>120) { onAnimal?.({ ...state }); lastGrowthReport=time }
    }
    if (field?.count || botanical?.count) {
      const fieldProgress = field?.update(delta, playing) ?? fieldSettings.growth
      const progress = botanical?.count ? botanical.update(delta, playing) : fieldProgress
      host.dataset.growth = progress.toFixed(4)
      if (botanical?.count) host.dataset.organs = JSON.stringify(botanical.visible)
      if (time - lastGrowthReport > 120) { onGrowth?.(progress); lastGrowthReport = time }
    }
    controls.update()
    renderer.render(scene, camera)
    host.dataset.drawCalls = String(renderer.info.render.calls)
    frame = requestAnimationFrame(animate)
  }
  frame = requestAnimationFrame(animate)
  return {
    setView, setPlaying(value) { playing = value }, setWireframe, setCutaway,
    setFieldSettings(value) { fieldSettings = value; field?.setSettings(value); botanical?.setSettings(value) },
    setBuildingSettings(value) { buildingSettings=value; building?.setSettings(value) },
    setTerrainSettings(value) { terrainSettings=value;terrain?.setSettings(value) },
    setHumanSettings(value) { humanSettings=value;human?.setSettings(value) },
    setSkeletalSettings(value) { const changed=value.clip!==skeletalSettings.clip;skeletalSettings=value;skeletal?.setSettings(value);if(changed&&skeletal)fitSkeletal(skeletal.update(0,false).clip) },
    setTransportSettings(value){transportSettings=value;transport?.setSettings(value)},
    setMountedSettings(value){mountedSettings=value;mounted?.setSettings(value)},
    setVesselSettings(value){vesselSettings=value;vessel?.setSettings(value)},
    setRouteSettings(value) {
      const changed=routeSettings.connected!==value.connected
      routeSettings=value;route?.setSettings(value)
      if(changed){size=singleSize*(value.connected?2.6:1);setView(view)}
    },
    setAnimalSettings(value) {
      const changed = animalSettings.family!==value.family
      animalSettings=value
      animal?.setSettings(value)
      if (changed) { size=singleSize*(value.family ? 2.25 : 1); setView(view) }
    },
    destroy() {
      destroyed = true
      cancelAnimationFrame(frame)
      observer.disconnect()
      controls.dispose()
      mixer?.stopAllAction()
      human?.destroy()
      skeletal?.destroy()
      for(const neighbor of routeNeighbors)scene.remove(neighbor.model)
      if (model) { mixer?.uncacheRoot(model); disposeModel(model) }
      renderer.dispose()
      renderer.forceContextLoss()
      renderer.domElement.remove()
      delete host.dataset.loaded
      delete host.dataset.animations
      delete host.dataset.plants
      delete host.dataset.growth
      delete host.dataset.drawCalls
      delete host.dataset.organs
      delete host.dataset.animals
      delete host.dataset.building
      delete host.dataset.cutaway
      delete host.dataset.terrain
      delete host.dataset.human
      delete host.dataset.skeletal
      delete host.dataset.route
      delete host.dataset.transport
      delete host.dataset.mounted
      delete host.dataset.vessel
    },
  }
}
