import {
  ACESFilmicToneMapping,
  AmbientLight,
  Box3,
  BoxGeometry,
  CanvasTexture,
  Color,
  ConeGeometry,
  CylinderGeometry,
  DirectionalLight,
  Group,
  Material,
  Mesh,
  MeshStandardMaterial,
  Object3D,
  PerspectiveCamera,
  PCFSoftShadowMap,
  PlaneGeometry,
  RingGeometry,
  Scene,
  SphereGeometry,
  SRGBColorSpace,
  Texture,
  Vector3,
  WebGLRenderer,
} from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { runtimeModelAssetUrls, type RuntimeModelAssetId } from '../assets/modelAssetUrls'
import type {
  BuildableModuleId,
  TerrainModuleId,
  UnitModuleId,
} from './tileModuleCatalog'

export type ModuleSceneKind = 'terrain' | 'terrain-set' | 'transition' | 'unit' | 'buildable'

export type ModuleSceneSpec = {
  buildableId?: BuildableModuleId
  leftTerrainId?: TerrainModuleId
  rightTerrainId?: TerrainModuleId
  terrainId?: TerrainModuleId
  unitId?: UnitModuleId
  kind: ModuleSceneKind
  variantSeed?: number
}

export type ModuleSceneHandle = {
  destroy: () => void
}

const TERRAIN_COLORS: Record<TerrainModuleId, { base: number; side: number; top: number }> = {
  forest: { base: 0x244b34, side: 0x173424, top: 0x3f7449 },
  grassland: { base: 0x6f9b55, side: 0x557a46, top: 0x9bc474 },
  hill: { base: 0x6d5339, side: 0x4c3725, top: 0xb08a5c },
  water: { base: 0x31739d, side: 0x23516f, top: 0x67add0 },
}

const gltfLoader = new GLTFLoader()

export function mountThreeModuleScene(
  host: HTMLElement,
  spec: ModuleSceneSpec,
): ModuleSceneHandle {
  const isGrassland = spec.kind === 'terrain' && (spec.terrainId ?? 'grassland') === 'grassland'
  const scene = new Scene()
  scene.background = new Color(0x172129)

  const renderer = new WebGLRenderer({ antialias: true, alpha: false })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.outputColorSpace = SRGBColorSpace
  if (isGrassland) {
    renderer.toneMapping = ACESFilmicToneMapping
    renderer.toneMappingExposure = 1.15
    renderer.shadowMap.enabled = true
    renderer.shadowMap.type = PCFSoftShadowMap
  }
  host.appendChild(renderer.domElement)

  const camera = new PerspectiveCamera(spec.kind === 'terrain-set' ? 31 : 34, 1, 0.1, 100)
  camera.position.set(spec.kind === 'terrain-set' ? 5.2 : 2.6, spec.kind === 'terrain-set' ? 4.3 : 2.3, spec.kind === 'terrain-set' ? 5.6 : 3.25)
  camera.lookAt(0, 0, 0)
  const controls = isGrassland ? new OrbitControls(camera, renderer.domElement) : undefined
  if (controls) {
    controls.enableDamping = true
    controls.enablePan = false
    controls.minDistance = 3
    controls.maxDistance = 8
    controls.maxPolarAngle = Math.PI * 0.49
  }

  scene.add(new AmbientLight(0xffffff, isGrassland ? 0.95 : 1.8))
  const keyLight = new DirectionalLight(0xfff5df, isGrassland ? 3 : 2.8)
  keyLight.position.set(3, 5, 4)
  if (isGrassland) {
    keyLight.castShadow = true
    keyLight.shadow.mapSize.set(2048, 2048)
    keyLight.shadow.camera.left = keyLight.shadow.camera.bottom = -2.5
    keyLight.shadow.camera.right = keyLight.shadow.camera.top = 2.5
    keyLight.shadow.camera.near = 0.1
    keyLight.shadow.camera.far = 15
    keyLight.shadow.bias = -0.0001
    keyLight.shadow.normalBias = 0.005
  }
  scene.add(keyLight)
  const fillLight = new DirectionalLight(0x9fc8ff, isGrassland ? 0.5 : 0.9)
  fillLight.position.set(-4, 2, -3)
  scene.add(fillLight)

  const root = new Group()
  scene.add(root)
  let destroyed = false

  if (spec.kind === 'terrain-set') {
    root.add(createTerrainSetModel())
  } else if (spec.kind === 'transition') {
    const leftTerrain = spec.leftTerrainId ?? 'water'
    const rightTerrain = spec.rightTerrainId ?? 'grassland'

    root.add(createTransitionModel(leftTerrain, rightTerrain))
    if ((leftTerrain === 'water' && rightTerrain === 'grassland') || (leftTerrain === 'grassland' && rightTerrain === 'water')) {
      void addRuntimeAssetModel(root, 'transition-shoreline', 1.3, () => destroyed)
    }
  } else if (spec.kind === 'unit') {
    root.add(createTerrainTile('grassland', { x: 0, z: 0 }, 0.5))
    root.add(createUnitModel(spec.unitId ?? 'scout'))
  } else if (spec.kind === 'buildable') {
    root.add(createTerrainTile('grassland', { x: 0, z: 0 }, 0.5))
    root.add(createBuildableModel(spec.buildableId ?? 'city-site'))
  } else {
    const terrainId = spec.terrainId ?? 'grassland'

    if (terrainId !== 'grassland') {
      root.add(createTerrainTile(terrainId, { x: 0, z: 0 }, 1))
    }

    if (terrainId === 'grassland') {
      void addRuntimeAssetModel(root, 'terrain-grassland', 2.8, () => destroyed, spec.variantSeed)
    }

    if (terrainId === 'water') {
      void addRuntimeAssetModel(root, 'terrain-water', 1.35, () => destroyed, spec.variantSeed)
    }

    if (terrainId === 'hill') {
      void addRuntimeAssetModel(root, 'terrain-hill', 1.35, () => destroyed, spec.variantSeed)
    }
  }

  let animationFrame = 0

  function resize(): void {
    const rect = host.getBoundingClientRect()
    const width = Math.max(1, Math.floor(rect.width))
    const height = Math.max(1, Math.floor(rect.height))

    renderer.setSize(width, height, false)
    camera.aspect = width / height
    if (spec.kind === 'terrain' && (spec.terrainId ?? 'grassland') === 'grassland') {
      camera.zoom = Math.min(1, camera.aspect / 1.25)
    }
    camera.updateProjectionMatrix()
  }

  function animate(time: number): void {
    if (!isGrassland) {
      root.rotation.y = spec.kind === 'terrain-set' ? -0.18 + Math.sin(time * 0.00018) * 0.04 : time * 0.00022
    }
    controls?.update()

    root.traverse((child) => {
      if (child.userData.animate === 'bob') {
        child.position.y = child.userData.baseY + Math.sin(time * 0.003) * 0.035
      }

      if (child.userData.animate === 'water') {
        child.rotation.z = Math.sin(time * 0.0016) * 0.035
      }
    })

    renderer.render(scene, camera)
    animationFrame = requestAnimationFrame(animate)
  }

  resize()
  window.addEventListener('resize', resize)
  animationFrame = requestAnimationFrame(animate)

  return {
    destroy: () => {
      destroyed = true
      window.removeEventListener('resize', resize)
      cancelAnimationFrame(animationFrame)
      controls?.dispose()
      renderer.forceContextLoss()
      renderer.dispose()
      disposeObjectTree(scene)
      renderer.domElement.remove()
    },
  }
}

async function addRuntimeAssetModel(
  root: Group,
  assetId: RuntimeModelAssetId,
  targetSize: number,
  isDestroyed: () => boolean,
  variantSeed = 0,
): Promise<void> {
  const model = await loadRuntimeAssetModel(assetId, targetSize, variantSeed)

  if (isDestroyed()) {
    disposeObjectTree(model)
    return
  }

  root.add(model)
}

async function loadRuntimeAssetModel(assetId: RuntimeModelAssetId, targetSize: number, variantSeed: number): Promise<Group> {
  const gltf = await gltfLoader.loadAsync(runtimeModelAssetUrls[assetId])
  const model = gltf.scene

  model.name = `${assetId}-runtime-preview`
  fitModelToPreview(model, targetSize)
  applyRuntimeVariant(model, assetId, variantSeed)
  setRuntimePreviewMetadata(model)

  const wrapper = new Group()

  wrapper.name = `${assetId}-runtime-wrapper`
  wrapper.add(model)
  return wrapper
}

function applyRuntimeVariant(model: Object3D, assetId: RuntimeModelAssetId, variantSeed: number): void {
  if (assetId !== 'terrain-grassland' || variantSeed <= 0) {
    return
  }

  const fertility = seededUnit(variantSeed, 'fertility')
  const hueShift = (fertility - 0.5) * 0.05 + (seededUnit(variantSeed, 'grassland-hue') - 0.5) * 0.018
  const saturationShift = (fertility - 0.5) * 0.28 + (seededUnit(variantSeed, 'grassland-saturation') - 0.5) * 0.07
  const lightnessShift = (fertility - 0.5) * 0.16 + (seededUnit(variantSeed, 'grassland-lightness') - 0.5) * 0.05

  model.rotation.y += (seededUnit(variantSeed, 'grassland-base-rotation') - 0.5) * 0.22

  model.traverse((child) => {
    if (!(child instanceof Mesh)) {
      return
    }

    const name = child.name.toLowerCase()
    const localSeed = name
    const isGrassMaterial =
      name.includes('grass') ||
      name.includes('turf') ||
      name.includes('top_surface') ||
      name.includes('blade')
    child.material = cloneVariantMaterials(child.material, hueShift, saturationShift, lightnessShift, fertility, isGrassMaterial)

    if (name.includes('short_grass_blade')) {
      child.visible = seededUnit(variantSeed, `${localSeed}:visible`) > 0.28 - fertility * 0.20
      child.scale.y *= 0.68 + fertility * 0.24 + seededUnit(variantSeed, `${localSeed}:height`) * 0.48
      child.rotation.y += (seededUnit(variantSeed, `${localSeed}:rotation`) - 0.5) * 0.38
      return
    }

    if (name.includes('grass_clump')) {
      const scale = 0.78 + fertility * 0.22 + seededUnit(variantSeed, `${localSeed}:clump-scale`) * 0.32
      child.scale.multiplyScalar(scale)
      child.visible = seededUnit(variantSeed, `${localSeed}:clump-visible`) > 0.18 - fertility * 0.14
      return
    }

    if (name.includes('wildflower')) {
      child.visible = seededUnit(variantSeed, `${localSeed}:flower-visible`) > 0.24
      child.scale.multiplyScalar(0.82 + seededUnit(variantSeed, `${localSeed}:flower-scale`) * 0.42)
      return
    }

    if (name.includes('stone') || name.includes('sphere')) {
      child.scale.multiplyScalar(0.88 + seededUnit(variantSeed, `${localSeed}:stone-scale`) * 0.28)
      child.rotation.y += seededUnit(variantSeed, `${localSeed}:stone-rotation`) * Math.PI
    }
  })
}

function cloneVariantMaterials(
  source: Mesh['material'],
  hueShift: number,
  saturationShift: number,
  lightnessShift: number,
  fertility: number,
  isGrassMaterial: boolean,
): Mesh['material'] {
  if (Array.isArray(source)) {
    return source.map((materialItem) =>
      cloneVariantMaterial(materialItem, hueShift, saturationShift, lightnessShift, fertility, isGrassMaterial),
    )
  }

  return cloneVariantMaterial(source, hueShift, saturationShift, lightnessShift, fertility, isGrassMaterial)
}

function cloneVariantMaterial(
  source: Material,
  hueShift: number,
  saturationShift: number,
  lightnessShift: number,
  fertility: number,
  isGrassMaterial: boolean,
): Material {
  const cloned = source.clone()

  if (cloned instanceof MeshStandardMaterial) {
    const isMeadow = source.name === 'meadow_surface' || source.name === 'meadow_leaf'
    if (isMeadow || (isGrassMaterial && cloned.map)) {
      cloned.color.setRGB(1.08 - fertility * 0.24, 0.88 + fertility * 0.20, 0.72 + fertility * 0.12)
    } else if (isGrassMaterial) {
      cloned.color.setHSL(
        0.19 + fertility * 0.06 + hueShift * 0.5,
        0.30 + fertility * 0.16 + saturationShift * 0.45,
        0.25 + fertility * 0.12 + lightnessShift * 0.45,
      )
    } else {
      cloned.color.offsetHSL(hueShift * 0.25, saturationShift * 0.18, lightnessShift * 0.18)
    }

    cloned.roughness = Math.min(1, cloned.roughness + 0.02)
  }

  return cloned
}

function seededUnit(seed: number, salt: string): number {
  let value = Math.imul(seed || 1, 1664525) + 1013904223

  for (let index = 0; index < salt.length; index += 1) {
    value = Math.imul(value ^ salt.charCodeAt(index), 2246822519)
    value ^= value >>> 13
  }

  return (value >>> 0) / 4_294_967_295
}

function fitModelToPreview(model: Object3D, targetSize: number): void {
  const box = new Box3().setFromObject(model)
  const size = new Vector3()
  const center = new Vector3()

  box.getSize(size)
  box.getCenter(center)

  const maxDimension = Math.max(size.x, size.y, size.z, 0.001)
  const scale = targetSize / maxDimension

  model.scale.multiplyScalar(scale)
  model.position.sub(center.multiplyScalar(scale))
  model.position.y += 0.02
}

function setRuntimePreviewMetadata(model: Object3D): void {
  model.traverse((child) => {
    child.userData.runtimeAsset = true
    if (child instanceof Mesh) {
      child.castShadow = true
      child.receiveShadow = true
    }
  })
}

function disposeObjectTree(object: Object3D): void {
  const textures = new Set<Texture>()
  object.traverse((child) => {
    if (child instanceof Mesh) {
      child.geometry.dispose()
      const materials = Array.isArray(child.material) ? child.material : [child.material]

      for (const childMaterial of materials) {
        for (const value of Object.values(childMaterial)) {
          if (value instanceof Texture) textures.add(value)
        }
        childMaterial.dispose()
      }
    }
  })
  for (const texture of textures) texture.dispose()
}

function createTerrainSetModel(): Group {
  const group = new Group()
  const tiles: Array<{ id: TerrainModuleId; q: number; r: number; scale: number }> = [
    { id: 'grassland', q: 0, r: 0, scale: 0.78 },
    { id: 'forest', q: -1, r: 0, scale: 0.78 },
    { id: 'forest', q: -1, r: 1, scale: 0.78 },
    { id: 'hill', q: 1, r: -1, scale: 0.78 },
    { id: 'hill', q: 1, r: 0, scale: 0.78 },
    { id: 'water', q: 0, r: 1, scale: 0.78 },
    { id: 'water', q: -0.5, r: 1.65, scale: 0.64 },
    { id: 'grassland', q: 0, r: -1, scale: 0.78 },
  ]

  for (const tile of tiles) {
    const position = axialToWorld(tile.q, tile.r)

    group.add(createTerrainTile(tile.id, position, tile.scale))
  }

  group.add(createSoftTransitionBand('water', 'grassland', axialToWorld(-0.12, 0.84), 1.04, -0.1))
  group.add(createSoftTransitionBand('forest', 'grassland', axialToWorld(-0.58, 0.18), 0.86, -0.72))
  group.add(createSoftTransitionBand('hill', 'grassland', axialToWorld(0.63, -0.34), 0.96, 0.82))
  group.add(createSoftTransitionBand('hill', 'forest', axialToWorld(0.18, -0.04), 0.72, 0.28))

  const trail = new Mesh(
    new PlaneGeometry(2.1, 0.11),
    material(0xe6d7a4, 0.86, 0.25, 0.74),
  )

  trail.position.set(-0.58, 0.18, -0.12)
  trail.rotation.set(-Math.PI / 2, 0, 0.52)
  group.add(trail)

  return group
}

function axialToWorld(q: number, r: number): { x: number; z: number } {
  return {
    x: (q + r / 2) * 1.65,
    z: r * 1.42,
  }
}

function createSoftTransitionBand(
  left: TerrainModuleId,
  right: TerrainModuleId,
  position: { x: number; z: number },
  length: number,
  rotation: number,
): Mesh {
  const isShore = left === 'water' || right === 'water'
  const isHill = left === 'hill' || right === 'hill'
  const band = new Mesh(
    new BoxGeometry(length, isHill ? 0.1 : 0.055, isShore ? 0.24 : 0.18),
    material(isShore ? 0xd8d3ad : isHill ? 0x9d8359 : 0x698b55, 0.82, 0.28, isShore ? 0.82 : 0.72),
  )

  band.position.set(position.x, isHill ? 0.18 : 0.09, position.z)
  band.rotation.y = rotation
  return band
}

function createTransitionModel(left: TerrainModuleId, right: TerrainModuleId): Group {
  const group = new Group()

  group.add(createTerrainTile(left, { x: -0.92, z: 0 }, 0.46))
  group.add(createTerrainTile(right, { x: 0.92, z: 0 }, 0.46))

  group.add(createSoftTransitionBand(left, right, { x: 0, z: 0 }, 1.8, Math.PI / 2))

  return group
}

function createTerrainTile(id: TerrainModuleId, position: { x: number; z: number }, scale: number): Group {
  const colors = TERRAIN_COLORS[id]
  const group = new Group()
  const height = id === 'water' ? 0.2 : id === 'hill' ? 0.58 : id === 'forest' ? 0.4 : 0.3
  const base = new Mesh(
    new CylinderGeometry(1.15 * scale, 1.05 * scale, height, 6),
    [
      material(colors.side, 0.74, 0.42),
      material(colors.side, 0.74, 0.42),
      material(colors.top, 0.82, 0.48),
    ],
  )
  base.position.set(0, height / 2 - 0.2, 0)
  base.rotation.y = Math.PI / 6
  group.add(base)

  if (id !== 'water') {
    group.add(createGroundSurface(id, scale))
  }

  if (id === 'hill') {
    group.add(createHillRidges(scale))
  }

  if (id === 'forest') {
    group.add(createTreeCluster(scale))
  }

  if (id === 'water') {
    group.add(createWaterBasin(scale))
  }

  if (id === 'grassland') {
    group.add(createGrassDetail(scale))
  }

  group.position.set(position.x, 0, position.z)
  return group
}

function createGroundSurface(id: Exclude<TerrainModuleId, 'water'>, scale: number): Group {
  const group = new Group()
  const patches =
    id === 'grassland'
      ? [
          { color: 0xb8d879, x: -0.3, z: 0.15, sx: 0.55, sz: 0.24, y: 0.02 },
          { color: 0x7fa85c, x: 0.36, z: -0.2, sx: 0.36, sz: 0.18, y: 0.025 },
        ]
      : id === 'forest'
        ? [
            { color: 0x2d5a3b, x: -0.34, z: 0.18, sx: 0.48, sz: 0.18, y: 0.04 },
            { color: 0x557a46, x: 0.32, z: -0.18, sx: 0.34, sz: 0.14, y: 0.045 },
          ]
        : [
            { color: 0xd0ab72, x: -0.28, z: 0.13, sx: 0.48, sz: 0.14, y: 0.06 },
            { color: 0x76563a, x: 0.3, z: -0.12, sx: 0.42, sz: 0.12, y: 0.065 },
          ]

  for (const patch of patches) {
    const mesh = new Mesh(
      new BoxGeometry(patch.sx * scale, 0.018 * scale, patch.sz * scale),
      material(patch.color, 0.86, 0.24, 0.74),
    )

    mesh.position.set(patch.x * scale, patch.y * scale, patch.z * scale)
    mesh.rotation.y = patch.x > 0 ? -0.45 : 0.38
    group.add(mesh)
  }

  return group
}

function createWaterBasin(scale: number): Group {
  const group = new Group()
  const shoal = new Mesh(
    new CylinderGeometry(1.0 * scale, 1.02 * scale, 0.035 * scale, 6),
    material(0xd5d0a8, 0.88, 0.2, 0.82),
  )

  shoal.position.y = -0.02 * scale
  shoal.rotation.y = Math.PI / 6
  group.add(shoal)

  const water = new Mesh(
    new CylinderGeometry(0.82 * scale, 0.9 * scale, 0.035 * scale, 36),
    material(0x5fb4d3, 0.46, 0.16, 0.82),
  )

  water.position.y = 0.02 * scale
  water.userData.animate = 'water'
  group.add(water)

  for (const [index, wave] of [
    { x: -0.2, z: -0.18, width: 0.5, rotation: 0.18 },
    { x: 0.18, z: 0.04, width: 0.62, rotation: -0.12 },
    { x: -0.05, z: 0.26, width: 0.42, rotation: 0.28 },
  ].entries()) {
    const strip = new Mesh(
      new BoxGeometry(wave.width * scale, 0.012 * scale, 0.035 * scale),
      material(0xd6f2ee, 0.36, 0.08, 0.72),
    )

    strip.position.set(wave.x * scale, (0.05 + index * 0.006) * scale, wave.z * scale)
    strip.rotation.y = wave.rotation
    strip.userData.animate = 'water'
    group.add(strip)
  }

  for (const reed of [
    { x: -0.7, z: 0.28, h: 0.16 },
    { x: 0.66, z: -0.18, h: 0.13 },
  ]) {
    const stem = new Mesh(
      new CylinderGeometry(0.012 * scale, 0.014 * scale, reed.h * scale, 6),
      material(0x789454, 0.9, 0.18),
    )

    stem.position.set(reed.x * scale, (0.06 + reed.h / 2) * scale, reed.z * scale)
    stem.rotation.z = reed.x > 0 ? -0.22 : 0.22
    group.add(stem)
  }

  return group
}

function createGrassDetail(scale: number): Group {
  const group = new Group()

  for (const tuft of [
    { x: -0.44, z: -0.18, rotation: 0.24 },
    { x: 0.12, z: 0.32, rotation: -0.18 },
    { x: 0.46, z: -0.02, rotation: 0.5 },
  ]) {
    const blade = new Mesh(
      new BoxGeometry(0.18 * scale, 0.05 * scale, 0.035 * scale),
      material(0xd3e68f, 0.88, 0.18),
    )

    blade.position.set(tuft.x * scale, 0.05 * scale, tuft.z * scale)
    blade.rotation.y = tuft.rotation
    group.add(blade)
  }

  return group
}

function createHillRidges(scale: number): Group {
  const group = new Group()
  const ridgeMaterial = material(0xe0c28a, 0.86, 0.38)

  for (const ridgeSpec of [
    { x: -0.24, z: 0.02, radius: 0.34, height: 0.52 },
    { x: 0.16, z: -0.08, radius: 0.42, height: 0.66 },
    { x: 0.34, z: 0.2, radius: 0.26, height: 0.42 },
  ]) {
    const ridge = new Mesh(new ConeGeometry(ridgeSpec.radius * scale, ridgeSpec.height * scale, 5), ridgeMaterial)

    ridge.position.set(ridgeSpec.x * scale, (0.23 + ridgeSpec.height / 2) * scale, ridgeSpec.z * scale)
    ridge.rotation.y = ridgeSpec.x > 0 ? Math.PI / 5 : -Math.PI / 7
    group.add(ridge)
  }

  const shadowSlope = new Mesh(
    new BoxGeometry(0.92 * scale, 0.045 * scale, 0.16 * scale),
    material(0x5f442e, 0.88, 0.25, 0.76),
  )

  shadowSlope.position.set(0.02 * scale, 0.16 * scale, 0.34 * scale)
  shadowSlope.rotation.y = -0.32
  group.add(shadowSlope)

  return group
}

function createTreeCluster(scale: number): Group {
  const group = new Group()

  for (const [index, point] of [
    { x: -0.38, z: 0.1, h: 0.42, radius: 0.18 },
    { x: -0.08, z: -0.22, h: 0.5, radius: 0.22 },
    { x: 0.24, z: 0.16, h: 0.46, radius: 0.2 },
    { x: 0.42, z: -0.12, h: 0.34, radius: 0.16 },
  ].entries()) {
    const trunk = new Mesh(new CylinderGeometry(0.035 * scale, 0.05 * scale, 0.24 * scale, 8), material(0x5f4428, 0.78, 0.32))
    const crown = new Mesh(new ConeGeometry(point.radius * scale, point.h * scale, 9), material(index % 2 === 0 ? 0x6e9857 : 0x4d7f45, 0.82, 0.36))
    const lowerCrown = new Mesh(new ConeGeometry(point.radius * 1.12 * scale, point.h * 0.45 * scale, 9), material(0x365f3f, 0.84, 0.28))

    trunk.position.set(point.x * scale, 0.18 * scale, point.z * scale)
    lowerCrown.position.set(point.x * scale, 0.37 * scale, point.z * scale)
    crown.position.set(point.x * scale, 0.53 * scale + index * 0.01, point.z * scale)
    group.add(trunk, lowerCrown, crown)
  }

  return group
}

function createUnitModel(id: UnitModuleId): Group {
  const group = new Group()
  const bodyColor = id === 'warrior' ? 0xb74c38 : id === 'settler' ? 0xd6bd74 : 0xf1d36e
  const body = new Mesh(new SphereGeometry(0.16, 18, 12), material(bodyColor, 0.82, 0.42))

  body.position.y = 0.46
  group.add(body)

  if (id === 'warrior') {
    const shield = new Mesh(new BoxGeometry(0.08, 0.28, 0.22), material(0x6e241f, 0.8, 0.34))

    shield.position.set(-0.18, 0.44, 0)
    group.add(shield)
  }

  if (id === 'settler') {
    const pole = new Mesh(new CylinderGeometry(0.015, 0.015, 0.55, 8), material(0x5c4a1a, 0.78, 0.35))
    const flag = new Mesh(new PlaneGeometry(0.22, 0.14), material(0xffd36c, 0.7, 0.4))

    pole.position.set(0.18, 0.66, 0)
    flag.position.set(0.3, 0.82, 0)
    group.add(pole, flag)
  }

  if (id === 'scout') {
    const lens = new Mesh(new RingGeometry(0.08, 0.11, 20), material(0x2d3b30, 0.72, 0.28))

    lens.position.set(0, 0.48, 0.15)
    group.add(lens)
  }

  group.userData.animate = 'bob'
  group.userData.baseY = 0
  return group
}

function createBuildableModel(id: BuildableModuleId): Group {
  const group = new Group()

  if (id === 'city-site') {
    const ring = new Mesh(new RingGeometry(0.32, 0.38, 32), material(0xffd36c, 0.58, 0.32, 0.72))

    ring.rotation.x = -Math.PI / 2
    ring.position.y = 0.05
    group.add(ring)
    return group
  }

  if (id === 'outpost') {
    const tower = new Mesh(new BoxGeometry(0.22, 0.5, 0.22), material(0xd6bd74, 0.76, 0.36))

    tower.position.y = 0.38
    group.add(tower)
    return group
  }

  const base = new Mesh(new BoxGeometry(0.42, 0.26, 0.34), material(0xf3e5b0, 0.82, 0.42))
  const roof = new Mesh(new ConeGeometry(0.34, 0.28, 4), material(0x8b6a32, 0.8, 0.36))

  base.position.y = 0.32
  roof.position.y = 0.6
  roof.rotation.y = Math.PI / 4
  group.add(base, roof)
  return group
}

function material(color: number, roughness: number, metalness: number, opacity = 1): MeshStandardMaterial {
  return new MeshStandardMaterial({
    color,
    metalness,
    opacity,
    roughness,
    transparent: opacity < 1,
  })
}

export function createGridPreviewTexture(): CanvasTexture {
  const canvas = document.createElement('canvas')

  canvas.width = 128
  canvas.height = 128
  const context = canvas.getContext('2d')

  if (context) {
    context.fillStyle = '#172129'
    context.fillRect(0, 0, 128, 128)
    context.strokeStyle = 'rgba(255,255,255,0.08)'

    for (let index = 0; index <= 128; index += 16) {
      context.beginPath()
      context.moveTo(index, 0)
      context.lineTo(index, 128)
      context.moveTo(0, index)
      context.lineTo(128, index)
      context.stroke()
    }
  }

  return new CanvasTexture(canvas)
}
