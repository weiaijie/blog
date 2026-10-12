import {
  AnimationMixer, Box3, Color, DirectionalLight, Group, HemisphereLight, Mesh,
  MeshStandardMaterial, OrthographicCamera, Scene, SRGBColorSpace, Vector3, WebGLRenderer,
} from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

export type ElementView = 'perspective' | 'front' | 'side' | 'top'
export type ElementScene = {
  setView: (view: ElementView) => void
  setPlaying: (value: boolean) => void
  setWireframe: (value: boolean) => void
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
  let destroyed = false
  let playing = !window.matchMedia('(prefers-reduced-motion: reduce)').matches
  let wireframe = false
  let view: ElementView = 'perspective'
  let size = 4
  let frame = 0
  let previousTime = 0
  const center = new Vector3()

  function resize() {
    const width = Math.max(1, host.clientWidth)
    const height = Math.max(1, host.clientHeight)
    renderer.setSize(width, height, false)
    const aspect = width / height
    const halfHeight = size * .68 / Math.min(aspect, 1)
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
    bounds.getCenter(center)
    const extent = bounds.getSize(new Vector3())
    size = Math.max(extent.x, extent.y, extent.z, .1)
    if (gltf.animations.length) {
      mixer = new AnimationMixer(model)
      for (const clip of gltf.animations) mixer.clipAction(clip).play()
    }
    setWireframe(wireframe)
    setView(view)
    host.dataset.loaded = 'true'
    host.dataset.animations = String(gltf.animations.length)
    onLoad(gltf.animations.length)
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
    controls.update()
    renderer.render(scene, camera)
    frame = requestAnimationFrame(animate)
  }
  frame = requestAnimationFrame(animate)
  return {
    setView, setPlaying(value) { playing = value }, setWireframe,
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
    },
  }
}
