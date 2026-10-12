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

export type ElementView = 'perspective' | 'front' | 'side' | 'top'
export type ElementScene = {
  setView: (view: ElementView) => void
  setPlaying: (value: boolean) => void
  setWireframe: (value: boolean) => void
  setFieldSettings: (value: FieldSettings) => void
  setAnimalSettings: (value: AnimalSettings) => void
  setBuildingSettings: (value: BuildingSettings) => void
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
): ElementScene {
  const renderer = new WebGLRenderer({ antialias: true, preserveDrawingBuffer: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.outputColorSpace = SRGBColorSpace
  renderer.domElement.setAttribute('aria-label', '三维模型')
  host.appendChild(renderer.domElement)
  const scene = new Scene()
  scene.background = new Color('#edf1f2')
  scene.add(new HemisphereLight(0xffffff, 0x939aa0, 2.2))
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
  let buildingSettings = { ...defaultBuildingSettings }
  let animalSettings = { ...defaultAnimalSettings }
  let fieldSettings = { ...defaultFieldSettings }
  let lastGrowthReport = 0
  let destroyed = false
  let playing = !window.matchMedia('(prefers-reduced-motion: reduce)').matches
  let wireframe = false
  let view: ElementView = 'perspective'
  let size = 4
  let singleSize = 4
  let frameRatio = .68
  let frame = 0
  let previousTime = 0
  const center = new Vector3()

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
    const direction = next === 'front' ? new Vector3(0, 0, 1)
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

  void new GLTFLoader().loadAsync(url).then((gltf) => {
    if (destroyed) { disposeModel(gltf.scene); return }
    model = gltf.scene
    scene.add(model)
    const bounds = new Box3().setFromObject(model)
    model.traverse((node) => {
      if (Array.isArray(node.userData.animationBoundsMin) && Array.isArray(node.userData.animationBoundsMax)) {
        bounds.expandByPoint(new Vector3().fromArray(node.userData.animationBoundsMin).applyMatrix4(node.matrixWorld))
        bounds.expandByPoint(new Vector3().fromArray(node.userData.animationBoundsMax).applyMatrix4(node.matrixWorld))
      }
    })
    bounds.getCenter(center)
    const extent = bounds.getSize(new Vector3())
    size = Math.max(extent.x, extent.y, extent.z, .1)
    frameRatio = Math.max(.68, extent.length() * .55 / size)
    singleSize = size
    building = createBuildingMotion(model)
    building?.setSettings(buildingSettings)
    building?.update(0,false)
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
    if (gltf.animations.length) {
      mixer = new AnimationMixer(model)
      for (const clip of gltf.animations) mixer.clipAction(clip).play()
    }
    setWireframe(wireframe)
    setView(view)
    host.dataset.loaded = 'true'
    host.dataset.animations = String(gltf.animations.length)
    onLoad(gltf.animations.length + (field.count || botanical.count || animal || building ? 1 : 0))
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
    if (building) {
      const state=building.update(delta,playing)
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
    setView, setPlaying(value) { playing = value }, setWireframe,
    setFieldSettings(value) { fieldSettings = value; field?.setSettings(value); botanical?.setSettings(value) },
    setBuildingSettings(value) { buildingSettings=value; building?.setSettings(value) },
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
    },
  }
}
