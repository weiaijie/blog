import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import {
  WATER_LEVEL, WORLD_LAYOUT_SCALE, clipWaterTriangle, createTerrainField, createTerrainSurface, createWorldTiles, edgePoints,
  getWorldEdges, randomTilePoint, seededRandom, smoothstep,
  type GroundSample, type WorldTile,
} from './terrainWorld'
import { createBoulderGeometry, createBroadleafGeometry, createFernGeometry, createFlowerGeometry, createGrassGeometry, createPineGeometry, createReedGeometry, createShrubGeometry } from './terrainWorldModels'
import { createTerrainWaterMaterial } from './terrainWorldWater'

export type TerrainWorldSettings = { animated: boolean; wind: number; flow: number; grid: boolean; pan: boolean }
export type TerrainWorldStats = { tiles: number; trees: number; grass: number; triangles: number }
export type TerrainWorldSelection = { id: string; label: string; fertility: number; elevation: number }
export type TerrainWorldHandle = {
  destroy: () => void
  update: (settings: TerrainWorldSettings) => void
  view: (mode: 'isometric' | 'top') => void
  zoom: (factor: number) => void
  focus: () => void
}

const PALETTE = {
  grass: new THREE.Color('#83a532'), forest: new THREE.Color('#536f2c'), dry: new THREE.Color('#e6b940'),
  sand: new THREE.Color('#efda9c'), rock: new THREE.Color('#737c89'), peak: new THREE.Color('#c3c6c4'),
}

function groundColor(sample: GroundSample): THREE.Color {
  const color = PALETTE.grass.clone().lerp(PALETTE.forest, sample.forest * 0.6).lerp(PALETTE.dry, sample.dry)
  color.multiplyScalar(1 + sample.patch * 0.08)
  color.lerp(PALETTE.sand, 1 - smoothstep(0.12, 0.5, sample.shore))
  color.lerp(PALETTE.rock, sample.rock)
  return color.lerp(PALETTE.peak, smoothstep(1.5, 3.6, sample.height) * sample.rock * 0.75)
}

function bufferGeometry(positions: number[], colors?: number[]): THREE.BufferGeometry {
  const geometry = new THREE.BufferGeometry()
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3))
  if (colors) geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3))
  geometry.computeVertexNormals()
  return geometry
}

const windFunction = `
  uniform float meadowTime;
  uniform float meadowWind;
  vec3 bendInWind(vec3 p) {
    vec3 root = vec3(0.0);
    #ifdef USE_INSTANCING
      root = instanceMatrix[3].xyz;
    #endif
    float phase = root.x * 0.85 + root.z * 0.55;
    float bend = sin(meadowTime * 1.65 + phase) * 0.65 + sin(meadowTime * 2.8 + phase * 1.9) * 0.25;
    float weight = max(0.0, p.y);
    p.x += bend * meadowWind * weight * (0.45 + weight) * 0.032;
    p.z += cos(meadowTime * 1.4 + phase) * meadowWind * weight * 0.016;
    return p;
  }
`

export function mountTerrainWorldScene(
  host: HTMLElement,
  seed: number,
  initialSettings: TerrainWorldSettings,
  onStats: (stats: TerrainWorldStats) => void,
  onSelect: (selection: TerrainWorldSelection) => void,
): TerrainWorldHandle {
  const field = createTerrainField(seed)
  const tiles = createWorldTiles()
  const surface = createTerrainSurface(field, tiles)
  const edges = getWorldEdges(tiles)
  let settings = { ...initialSettings }
  const uniforms = { meadowTime: { value: 0 }, meadowWind: { value: settings.wind } }
  const flow = { value: 0 }
  const scene = new THREE.Scene()
  scene.background = new THREE.Color('#dfe5e7')
  const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.75))
  renderer.outputColorSpace = THREE.SRGBColorSpace
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  renderer.toneMappingExposure = 1.05
  renderer.shadowMap.enabled = true
  renderer.shadowMap.type = THREE.PCFShadowMap
  renderer.domElement.setAttribute('aria-label', 'C 风格连续三维地形')
  renderer.domElement.setAttribute('role', 'img')
  renderer.domElement.style.touchAction = 'none'
  host.appendChild(renderer.domElement)

  const camera = new THREE.OrthographicCamera(-22, 22, 18, -18, 0.1, 200)
  const controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.09
  controls.enablePan = true
  controls.screenSpacePanning = false
  controls.mouseButtons.LEFT = settings.pan ? THREE.MOUSE.PAN : THREE.MOUSE.ROTATE
  controls.touches.ONE = settings.pan ? THREE.TOUCH.PAN : THREE.TOUCH.ROTATE
  controls.minZoom = 0.55
  controls.maxZoom = 8
  controls.minPolarAngle = 0.03
  controls.maxPolarAngle = Math.PI * 0.46
  controls.target.set(0, 0.7, 0)
  function setView(mode: 'isometric' | 'top') {
    controls.target.set(0, 0.7, 0)
    camera.position.set(...(mode === 'top' ? [0, 60, 0.01] : [9, 31, 48]) as [number, number, number])
    camera.zoom = mode === 'top' ? 0.85 : 1
    camera.lookAt(controls.target)
    camera.updateProjectionMatrix()
    controls.update()
  }
  setView('isometric')

  scene.add(new THREE.HemisphereLight(0xe5f2ff, 0x827f4e, 1.05))
  const sun = new THREE.DirectionalLight(0xfff2d5, 3.0)
  sun.position.set(-18, 32, 15)
  sun.castShadow = true
  sun.shadow.mapSize.set(4096, 4096)
  Object.assign(sun.shadow.camera, { left: -24, right: 24, top: 24, bottom: -24, near: 0.5, far: 110 })
  sun.shadow.bias = -0.0002
  sun.shadow.normalBias = 0.016
  scene.add(sun)
  const fill = new THREE.DirectionalLight(0xc7e8ff, 0.3)
  fill.position.set(4, 6, -7)
  scene.add(fill)

  const landPositions: number[] = [], landColors: number[] = [], cover: number[] = []
  const waterPositions: number[] = [], depths: number[] = [], flows: number[] = []
  for (const points of surface.triangles) {
    const center = field.sample(points.reduce((sum, p) => sum + p.x, 0) / 3, points.reduce((sum, p) => sum + p.z, 0) / 3)
    const color = groundColor(center)
    const facet = Math.sin(center.x * 112.1 + center.z * 173.7) * 0.018 + 1
    color.multiplyScalar(facet)
    for (const p of points) { landPositions.push(p.x, p.height, p.z); landColors.push(color.r, color.g, color.b); cover.push(p.rock, p.dry, p.shore) }
    const water = clipWaterTriangle(points)
    for (let index = 1; index < water.length - 1; index++) {
      for (const p of [water[0], water[index], water[index + 1]]) {
        const depth = WATER_LEVEL - p.height
        const flowAt = field.waterCoordinates(p.x, p.z)
        waterPositions.push(p.x, WATER_LEVEL + 0.006, p.z)
        flows.push(flowAt.across, flowAt.along, flowAt.river)
        depths.push(depth)
      }
    }
  }
  const groundMaterial = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 1, flatShading: true })
  groundMaterial.onBeforeCompile = (shader) => {
    shader.vertexShader = 'attribute vec3 terrainCover; varying vec3 vCover; varying vec3 terrainPosition; varying float terrainUp;\n' + shader.vertexShader.replace('#include <begin_vertex>', '#include <begin_vertex>\nterrainPosition = position; terrainUp = normal.y; vCover=terrainCover;')
    shader.fragmentShader = `varying vec3 vCover; varying vec3 terrainPosition; varying float terrainUp;
      float terrainHash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
      float terrainNoise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.0-2.0*f);return mix(mix(terrainHash(i),terrainHash(i+vec2(1,0)),f.x),mix(terrainHash(i+vec2(0,1)),terrainHash(i+vec2(1,1)),f.x),f.y);}
    ` + shader.fragmentShader.replace('#include <color_fragment>', `#include <color_fragment>
      vec2 cell = terrainPosition.xz * 33.0;
      vec2 f = fract(cell); float h = terrainHash(floor(cell));
      float fleck = step(0.68,h)*step(f.y,f.x*0.48)*step(f.x,0.7);
      float meadow = smoothstep(0.65,0.98,terrainUp) * (1.0-vCover.x) * smoothstep(0.18,0.65,vCover.z);
      float coverNoise=terrainNoise(terrainPosition.xz*2.1)*0.6+terrainNoise(terrainPosition.xz*5.8)*0.4;
      float soil=smoothstep(0.61,0.79,coverNoise)*(0.12+vCover.y*0.28);
      diffuseColor.rgb=mix(diffuseColor.rgb,vec3(0.30,0.22,0.075),soil*meadow);
      diffuseColor.rgb *= 1.0 + ((coverNoise-0.5)*0.22+fleck*0.26-0.04)*meadow;
      float grain=terrainNoise(terrainPosition.xz*37.0);
      diffuseColor.rgb *= 1.0+(grain-0.5)*0.09*(1.0-vCover.x);
      float strata=sin(terrainPosition.y*22.0+terrainPosition.x*1.5+terrainNoise(terrainPosition.xz*3.0)*3.0);
      float fissure=smoothstep(0.7,0.95,strata)*vCover.x*(1.0-smoothstep(0.8,0.98,terrainUp));
      diffuseColor.rgb *= 1.0-fissure*0.14+(grain-0.5)*0.07*vCover.x;
    `)
  }
  const groundGeometry = bufferGeometry(landPositions, landColors)
  groundGeometry.setAttribute('terrainCover', new THREE.Float32BufferAttribute(cover, 3))
  const ground = new THREE.Mesh(groundGeometry, groundMaterial)
  ground.receiveShadow = true
  ground.castShadow = true
  scene.add(ground)

  const sidePositions: number[] = [], sideColors: number[] = [], gridPositions: number[] = []
  for (const edge of edges) {
    const points = edgePoints(edge.a, edge.b)
    for (let i = 0; i < points.length - 1; i++) {
      const a = field.sample(points[i].x, points[i].z), b = field.sample(points[i + 1].x, points[i + 1].z)
      gridPositions.push(a.x, Math.max(a.height, WATER_LEVEL) + 0.017, a.z, b.x, Math.max(b.height, WATER_LEVEL) + 0.017, b.z)
      if (edge.tiles.length !== 1) continue
      const topA = Math.max(a.height, WATER_LEVEL), topB = Math.max(b.height, WATER_LEVEL)
      const mid = -0.12 + Math.sin(a.x * 3 + a.z * 4) * 0.065
      const levels = [[topA, topB], [mid, mid], [-0.53, -0.53]]
      for (let band = 0; band < 2; band++) {
        const shade = new THREE.Color(band === 0 ? '#9c825c' : '#786b60')
        const triangles = [
          [[a.x, levels[band][0], a.z], [b.x, levels[band][1], b.z], [a.x, levels[band+1][0], a.z]],
          [[b.x, levels[band][1], b.z], [b.x, levels[band+1][1], b.z], [a.x, levels[band+1][0], a.z]],
        ]
        triangles.forEach((triangle, j) => {
          const c = shade.clone().multiplyScalar(0.88 + Math.sin(a.x * 52 + a.z * 81 + j * 18) * 0.17)
          triangle.forEach((v) => { sidePositions.push(...v); sideColors.push(c.r, c.g, c.b) })
        })
      }
    }
  }
  const sides = new THREE.Mesh(bufferGeometry(sidePositions, sideColors), new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 1, flatShading: true, side: THREE.DoubleSide }))
  sides.castShadow = true
  sides.receiveShadow = true
  scene.add(sides)
  const grid = new THREE.LineSegments(bufferGeometry(gridPositions), new THREE.LineBasicMaterial({ color: 0xfff5d0, transparent: true, opacity: 0.16, depthWrite: false }))
  grid.visible = settings.grid
  scene.add(grid)

  const waterGeometry = bufferGeometry(waterPositions)
  waterGeometry.setAttribute('waterDepth', new THREE.Float32BufferAttribute(depths, 1))
  waterGeometry.setAttribute('waterFlow', new THREE.Float32BufferAttribute(flows, 3))
  const waterMaterial = createTerrainWaterMaterial(flow)
  scene.add(new THREE.Mesh(waterGeometry, waterMaterial))

  function windMaterial(color: number) {
    const mat = new THREE.MeshStandardMaterial({ color, vertexColors: true, flatShading: true, roughness: 0.95, side: THREE.DoubleSide })
    mat.onBeforeCompile = (shader) => {
      Object.assign(shader.uniforms, uniforms)
      shader.vertexShader = windFunction + shader.vertexShader.replace('#include <begin_vertex>', 'vec3 transformed = bendInWind(position);')
    }
    mat.customProgramCacheKey = () => 'terrain-world-wind-v1'
    return mat
  }
  const windDepth = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking, side: THREE.DoubleSide })
  windDepth.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, uniforms)
    shader.vertexShader = windFunction + shader.vertexShader.replace('#include <begin_vertex>', 'vec3 transformed = bendInWind(position);')
  }
  const leafMaterial = windMaterial(0xffffff)
  const grassMaterial = windMaterial(0xffffff)
  const stemMaterial = new THREE.MeshStandardMaterial({ color: 0x725840, flatShading: true, roughness: 1 })
  const rockMaterial = new THREE.MeshStandardMaterial({ color: 0xffffff, vertexColors: true, roughness: 1, flatShading: true })
  const trunkGeometry = new THREE.CylinderGeometry(0.052, 0.085, 1.15, 6).translate(0, 0.575, 0)
  type Instance = { sample: GroundSample; scale: number; rotation: number; color: THREE.Color; aspect?: number }
  const trees: Instance[] = [], pines: Instance[] = [], shrubs: Instance[] = [], grass: Instance[] = [], stones: Instance[] = [], flowers: Instance[] = [], reeds: Instance[] = [], ferns: Instance[] = []
  const random = seededRandom(seed ^ 0x41c6ce57)
  const leafColors = ['#285443', '#396445', '#597e32', '#719334', '#8ca337'].map((c) => new THREE.Color(c))
  const flowerColors = ['#fff8e4', '#f6d155', '#dfb7e5', '#efac73'].map((c) => new THREE.Color(c))
  const occupied: Instance[] = []
  for (const tile of tiles) {
    for (let i = 0; i < 440; i++) {
      const point = randomTilePoint(tile, random), sample = surface.sample(point.x, point.z)
      if (sample && sample.rock > 0.3 && sample.shore > 0.6 && i < 10) {
        stones.push({ sample, scale: 0.08 + random() * 0.24, rotation: random() * Math.PI * 2,
          aspect: 0.5 + random() * 0.4, color: PALETTE.rock.clone().lerp(PALETTE.peak, random() * 0.3) })
      }
      if (!sample || sample.height < WATER_LEVEL + 0.01 || sample.shore < 0.14 || sample.rock > 0.7) continue
      const roll = random()
      const instance: Instance = { sample, scale: 0.65 + random() * 0.6, rotation: random() * Math.PI * 2, color: groundColor(sample), aspect: 0.85 + random() * 0.35 }
      const riverWood = (1 - smoothstep(0.45, 1.0, sample.shore)) * 0.07
      const grouping = smoothstep(-0.25, 0.5, sample.patch)
      if (sample.shore < 0.48) {
        if (i < 120 && roll < 0.55) reeds.push({ ...instance, color: new THREE.Color('#7e9744'), scale: 0.65 + random() * 0.65 })
        continue
      }
      if (i < 70 && sample.rock < 0.18 && roll < sample.forest * 0.92 + riverWood + grouping * 0.009) {
        instance.scale *= 0.28 + sample.forest * 0.43 + riverWood * 0.7
        if (occupied.some((tree) => Math.hypot(tree.sample.x - sample.x, tree.sample.z - sample.z) < (tree.scale + instance.scale) * 0.43)) continue
        const pine = random() < 0.23 + sample.forest * 0.45
        if (pine) instance.scale *= 0.82
        instance.color = leafColors[Math.floor(random() * leafColors.length)].clone()
        if (pine) instance.color.multiplyScalar(0.8)
        ;(pine ? pines : trees).push(instance)
        occupied.push(instance)
      } else if (i < 100 && sample.rock < 0.25 && roll < grouping * 0.045 + riverWood * 0.8 + sample.forest * 0.07) {
        instance.scale *= 0.4 + random() * 0.48
        instance.color = leafColors[Math.floor(random() * leafColors.length)].clone()
        shrubs.push(instance)
      } else if (i > 125 && sample.rock < 0.25 && roll < grouping * 0.5) {
        instance.scale *= 0.45 + random() * 0.55
        instance.color.lerp(new THREE.Color('#b7b947'), random() * 0.4)
        grass.push(instance)
        if (sample.forest > 0.3 && i % 5 === 0) ferns.push({ ...instance, color: new THREE.Color('#638844'), scale: 0.65 + random() * 0.55 })
        if (sample.dry < 0.6 && grouping > 0.7 && i % 3 === 0) {
          flowers.push({ ...instance, scale: 0.7 + random() * 0.5, color: flowerColors[Math.floor(random() * flowerColors.length)] })
        }
      }
      if (i < 12 && sample.patch > 0.12 && (sample.rock > 0.12 || sample.shore < 1.1 || roll < 0.12)) {
        stones.push({ ...instance, scale: 0.07 + random() * 0.25, color: PALETTE.rock.clone().lerp(PALETTE.sand, random() * 0.32) })
      }
    }
  }
  // Art-directed rock groups reinforce bank bends and the foot of each ridge.
  const rockGroups = [[-3.6, 1.1, 0.8], [-4.8, 1.5, 0.65], [-2.8, 2.4, 1.0], [-1.0, 2.5, 0.65],
    [0.2, 0.8, 0.6], [0.9, -1, 0.6], [-1.4, -0.5, 0.65], [-3, -2, 0.7], [2.6, -0.6, 0.85],
    [4.1, -0.1, 1.0], [4.9, -2.5, 0.8], [4.8, 1.8, 0.75], [3.5, 3.1, 0.55], [-4.4, -3.1, 0.8]]
  for (const [baseX, baseZ, size] of rockGroups) {
    const x = baseX * WORLD_LAYOUT_SCALE, z = baseZ * WORLD_LAYOUT_SCALE
    for (let i = 0; i < 13; i++) {
      const angle = random() * Math.PI * 2, radius = i === 0 ? 0 : 0.18 + random() * 0.65
      const sample = surface.sample(x + Math.cos(angle) * radius, z + Math.sin(angle) * radius)
      if (!sample || sample.height < -0.08 || sample.height > 1.8) continue
      stones.push({ sample, scale: size * (i < 2 ? 0.6 + random() * 0.38 : 0.12 + random() * 0.25),
        aspect: 0.7 + random() * 0.8, rotation: random() * Math.PI * 2,
        color: PALETTE.rock.clone().lerp(PALETTE.peak, random() * 0.65) })
    }
  }
  for (const [x, z, scale] of [[-4.3, 2.1, 0.95], [-3.6, 3.3, 1.05], [-2.7, 3.55, 0.75]]) {
    const sample = surface.sample(x * WORLD_LAYOUT_SCALE, z * WORLD_LAYOUT_SCALE)
    if (sample && sample.height < WATER_LEVEL) stones.push({ sample, scale, rotation: random() * 6.28, aspect: 1.55, color: PALETTE.rock.clone() })
  }
  const transform = new THREE.Object3D()
  function instances(geometry: THREE.BufferGeometry, material: THREE.Material, list: Instance[], wind = false) {
    const mesh = new THREE.InstancedMesh(geometry, material, list.length)
    list.forEach((item, index) => {
      transform.position.set(item.sample.x, item.sample.height - 0.012, item.sample.z)
      transform.rotation.set(0, item.rotation, 0)
      transform.scale.setScalar(item.scale)
      transform.scale.y *= item.aspect ?? 1
      transform.updateMatrix()
      mesh.setMatrixAt(index, transform.matrix)
      if (material !== stemMaterial) mesh.setColorAt(index, item.color)
    })
    mesh.castShadow = material !== grassMaterial
    mesh.receiveShadow = true
    if (wind) mesh.customDepthMaterial = windDepth
    mesh.computeBoundingSphere()
    if (mesh.boundingSphere) mesh.boundingSphere.radius += 0.5
    scene.add(mesh)
    return mesh
  }
  for (let variant = 0; variant < 4; variant++) {
    const select = (list: Instance[]) => list.filter((_, i) => i % 4 === variant)
    instances(createBroadleafGeometry(variant), leafMaterial, select(trees), true)
    instances(createPineGeometry(variant), leafMaterial, select(pines), true)
    instances(createShrubGeometry(variant), leafMaterial, select(shrubs), true)
    instances(createBoulderGeometry(variant), rockMaterial, select(stones))
  }
  instances(trunkGeometry, stemMaterial, [...trees, ...pines])
  instances(createGrassGeometry(), grassMaterial, grass, true)
  instances(createFlowerGeometry(), grassMaterial, flowers, true)
  instances(createReedGeometry(), grassMaterial, reeds, true)
  instances(createFernGeometry(), grassMaterial, ferns, true)

  const floor = new THREE.Mesh(new THREE.PlaneGeometry(200, 200), new THREE.ShadowMaterial({ color: 0x42535c, opacity: 0.22 }))
  floor.rotation.x = -Math.PI / 2
  floor.position.y = -0.55
  floor.receiveShadow = true
  scene.add(floor)

  const selection = new THREE.LineLoop(new THREE.BufferGeometry(), new THREE.LineBasicMaterial({ color: 0xffffff, depthTest: false }))
  selection.renderOrder = 2
  scene.add(selection)
  const raycaster = new THREE.Raycaster()
  let selectedTile: WorldTile | null = null
  let pointerDown = { x: 0, y: 0 }
  function selectTile(tile: WorldTile, sample: GroundSample) {
    selectedTile = tile
    const points: THREE.Vector3[] = []
    tile.corners.forEach((a, i) => edgePoints(a, tile.corners[(i + 1) % 6]).slice(0, -1).forEach((p) => {
      points.push(new THREE.Vector3(p.x, Math.max(field.sample(p.x, p.z).height, WATER_LEVEL) + 0.025, p.z))
    }))
    selection.geometry.dispose()
    selection.geometry = new THREE.BufferGeometry().setFromPoints(points)
    const label = sample.height < WATER_LEVEL ? '水域' : sample.shore < 0.4 ? '河岸' : sample.rock > 0.4 ? '山地' : sample.height > 0.65 ? '丘陵' : sample.forest > 0.5 ? '森林' : sample.dry > 0.55 ? '干草平原' : '草原'
    onSelect({ id: tile.id, label, elevation: Number(sample.height.toFixed(2)), fertility: Math.round(90 - sample.dry * 55 - sample.rock * 40) })
  }
  const down = (event: PointerEvent) => { pointerDown = { x: event.clientX, y: event.clientY } }
  const up = (event: PointerEvent) => {
    if (event.button !== 0) return
    if (Math.hypot(event.clientX - pointerDown.x, event.clientY - pointerDown.y) > 5) return
    const rect = renderer.domElement.getBoundingClientRect()
    raycaster.setFromCamera(new THREE.Vector2((event.clientX - rect.left) / rect.width * 2 - 1, -(event.clientY - rect.top) / rect.height * 2 + 1), camera)
    const hit = raycaster.intersectObject(ground)[0]
    if (!hit) return
    const tile = tiles.reduce((best, item) => Math.hypot(item.center.x - hit.point.x, item.center.z - hit.point.z) < Math.hypot(best.center.x - hit.point.x, best.center.z - hit.point.z) ? item : best)
    selectTile(tile, field.sample(hit.point.x, hit.point.z))
  }
  renderer.domElement.addEventListener('pointerdown', down)
  renderer.domElement.addEventListener('pointerup', up)
  function resize() {
    const width = Math.max(1, host.clientWidth), height = Math.max(1, host.clientHeight)
    renderer.setSize(width, height, false)
    const vertical = Math.max(27.5, 39.5 / (width / height))
    camera.left = -vertical * width / height / 2
    camera.right = -camera.left
    camera.top = vertical / 2
    camera.bottom = -camera.top
    camera.updateProjectionMatrix()
  }
  const observer = new ResizeObserver(resize)
  observer.observe(host)
  resize()
  let frame = 0, previousTime = performance.now(), lastReport = 0
  const animate = (now: number) => {
    const delta = Math.min((now - previousTime) / 1000, 0.05)
    previousTime = now
    if (settings.animated && !document.hidden) {
      uniforms.meadowTime.value += delta
      flow.value += delta * settings.flow
    }
    controls.update()
    renderer.render(scene, camera)
    if (now - lastReport > 250) {
      host.dataset.simulationTime = uniforms.meadowTime.value.toFixed(3)
      host.dataset.flowTime = flow.value.toFixed(3)
      host.dataset.drawCalls = String(renderer.info.render.calls)
      host.dataset.triangles = String(renderer.info.render.triangles)
      lastReport = now
    }
    frame = requestAnimationFrame(animate)
  }
  frame = requestAnimationFrame(animate)
  onStats({ tiles: tiles.length, trees: trees.length + pines.length, grass: grass.length, triangles: landPositions.length / 9 })
  return {
    update: (next) => {
      settings = { ...next }; grid.visible = next.grid; uniforms.meadowWind.value = next.wind
      controls.mouseButtons.LEFT = next.pan ? THREE.MOUSE.PAN : THREE.MOUSE.ROTATE
      controls.touches.ONE = next.pan ? THREE.TOUCH.PAN : THREE.TOUCH.ROTATE
    },
    view: setView,
    zoom: (factor) => { camera.zoom = Math.min(8, Math.max(0.55, camera.zoom * factor)); camera.updateProjectionMatrix() },
    focus: () => {
      const center = selectedTile?.center ?? { x: field.riverX(2) - 1.8, z: 2 }
      const y = Math.max(WATER_LEVEL, surface.sample(center.x, center.z)?.height ?? 0.3)
      controls.target.set(center.x, y, center.z)
      camera.position.set(center.x + 9, y + 31, center.z + 48)
      camera.zoom = 3.8
      camera.updateProjectionMatrix()
      controls.update()
    },
    destroy: () => {
      cancelAnimationFrame(frame)
      observer.disconnect()
      controls.dispose()
      renderer.domElement.removeEventListener('pointerdown', down)
      renderer.domElement.removeEventListener('pointerup', up)
      const geometries = new Set<THREE.BufferGeometry>(), materials = new Set<THREE.Material>()
      scene.traverse((child) => {
        if (child instanceof THREE.Mesh || child instanceof THREE.Line) {
          geometries.add(child.geometry)
          for (const mat of Array.isArray(child.material) ? child.material : [child.material]) materials.add(mat)
        }
        if (child instanceof THREE.InstancedMesh) child.dispose()
      })
      geometries.forEach((g) => g.dispose())
      materials.forEach((m) => m.dispose())
      windDepth.dispose()
      sun.shadow.dispose()
      renderer.dispose()
      renderer.forceContextLoss()
      renderer.domElement.remove()
    },
  }
}
