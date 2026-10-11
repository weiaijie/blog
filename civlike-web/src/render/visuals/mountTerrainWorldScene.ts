import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js'
import {
  WATER_LEVEL, clipWaterTriangle, createTerrainField, createWorldTiles, edgePoints,
  getWorldEdges, randomTilePoint, seededRandom, smoothstep, tileTriangles,
  type GroundSample, type WorldTile,
} from './terrainWorld'

export type TerrainWorldSettings = { animated: boolean; wind: number; flow: number; grid: boolean }
export type TerrainWorldStats = { tiles: number; trees: number; grass: number; triangles: number }
export type TerrainWorldSelection = { id: string; label: string; fertility: number; elevation: number }
export type TerrainWorldHandle = {
  destroy: () => void
  update: (settings: TerrainWorldSettings) => void
  view: (mode: 'isometric' | 'top') => void
  zoom: (factor: number) => void
}

const PALETTE = {
  grass: new THREE.Color('#91ac47'), forest: new THREE.Color('#62883d'), dry: new THREE.Color('#d4b75b'),
  sand: new THREE.Color('#dcc891'), rock: new THREE.Color('#8c9696'), peak: new THREE.Color('#b6bdb7'),
  water: new THREE.Color('#2082a0'), shallow: new THREE.Color('#58c1bc'),
}

function groundColor(sample: GroundSample): THREE.Color {
  const color = PALETTE.grass.clone().lerp(PALETTE.forest, sample.forest * 0.7).lerp(PALETTE.dry, sample.dry)
  color.lerp(PALETTE.sand, 1 - smoothstep(0.08, 0.48, sample.shore))
  color.lerp(PALETTE.rock, sample.rock)
  return color.lerp(PALETTE.peak, smoothstep(2.05, 2.9, sample.height))
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
    p.x += bend * meadowWind * weight * (0.45 + weight) * 0.075;
    p.z += cos(meadowTime * 1.4 + phase) * meadowWind * weight * 0.026;
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
  const edges = getWorldEdges(tiles)
  let settings = { ...initialSettings }
  const uniforms = { meadowTime: { value: 0 }, meadowWind: { value: settings.wind } }
  const flow = { value: 0 }
  const scene = new THREE.Scene()
  scene.background = new THREE.Color('#e8eef1')
  const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.75))
  renderer.outputColorSpace = THREE.SRGBColorSpace
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  renderer.toneMappingExposure = 0.95
  renderer.shadowMap.enabled = true
  renderer.shadowMap.type = THREE.PCFShadowMap
  renderer.domElement.setAttribute('aria-label', 'C 风格连续三维地形')
  renderer.domElement.setAttribute('role', 'img')
  renderer.domElement.style.touchAction = 'none'
  host.appendChild(renderer.domElement)

  const camera = new THREE.OrthographicCamera(-8, 8, 6, -6, 0.1, 100)
  const controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.09
  controls.enablePan = false
  controls.minZoom = 0.7
  controls.maxZoom = 3
  controls.minPolarAngle = 0.03
  controls.maxPolarAngle = Math.PI * 0.46
  controls.target.set(0, 0.5, 0)
  function setView(mode: 'isometric' | 'top') {
    camera.position.set(...(mode === 'top' ? [0, 22, 0.01] : [9, 12, 15]) as [number, number, number])
    camera.zoom = mode === 'top' ? 0.78 : 1
    camera.lookAt(controls.target)
    camera.updateProjectionMatrix()
    controls.update()
  }
  setView('isometric')

  scene.add(new THREE.HemisphereLight(0xe9f5ff, 0xaaa281, 1.3))
  const sun = new THREE.DirectionalLight(0xfff5df, 2.4)
  sun.position.set(-6, 12, 7)
  sun.castShadow = true
  sun.shadow.mapSize.set(2048, 2048)
  Object.assign(sun.shadow.camera, { left: -10, right: 10, top: 10, bottom: -10, near: 0.5, far: 35 })
  sun.shadow.bias = -0.0002
  sun.shadow.normalBias = 0.025
  scene.add(sun)
  const fill = new THREE.DirectionalLight(0xc7e8ff, 0.55)
  fill.position.set(4, 6, -7)
  scene.add(fill)

  const landPositions: number[] = [], landColors: number[] = []
  const waterPositions: number[] = [], waterColors: number[] = [], depths: number[] = []
  for (const tile of tiles) {
    for (const triangle of tileTriangles(tile)) {
      const points = triangle.map((p) => field.sample(p.x, p.z))
      const center = field.sample(points.reduce((sum, p) => sum + p.x, 0) / 3, points.reduce((sum, p) => sum + p.z, 0) / 3)
      const color = groundColor(center)
      const facet = Math.sin(center.x * 112.1 + center.z * 173.7) * 0.035 + 1
      color.multiplyScalar(facet)
      for (const p of points) { landPositions.push(p.x, p.height, p.z); landColors.push(color.r, color.g, color.b) }
      const water = clipWaterTriangle(points)
      for (let index = 1; index < water.length - 1; index++) {
        for (const p of [water[0], water[index], water[index + 1]]) {
          const depth = WATER_LEVEL - p.height
          const c = PALETTE.shallow.clone().lerp(PALETTE.water, smoothstep(0, 0.45, depth))
          waterPositions.push(p.x, WATER_LEVEL + 0.006, p.z)
          waterColors.push(c.r, c.g, c.b)
          depths.push(depth)
        }
      }
    }
  }
  const ground = new THREE.Mesh(bufferGeometry(landPositions, landColors), new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 1, flatShading: true }))
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
      const shade = new THREE.Color('#958770')
      const topA = Math.max(a.height, WATER_LEVEL), topB = Math.max(b.height, WATER_LEVEL)
      const vertices = [[a.x, topA, a.z], [b.x, topB, b.z], [a.x, -0.6, a.z],
        [b.x, topB, b.z], [b.x, -0.6, b.z], [a.x, -0.6, a.z]]
      vertices.forEach((v) => { sidePositions.push(...v); sideColors.push(shade.r, shade.g, shade.b) })
    }
  }
  const sides = new THREE.Mesh(bufferGeometry(sidePositions, sideColors), new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 1, flatShading: true, side: THREE.DoubleSide }))
  sides.castShadow = true
  sides.receiveShadow = true
  scene.add(sides)
  const grid = new THREE.LineSegments(bufferGeometry(gridPositions), new THREE.LineBasicMaterial({ color: 0xf6f4d9, transparent: true, opacity: 0.23, depthWrite: false }))
  grid.visible = settings.grid
  scene.add(grid)

  const waterGeometry = bufferGeometry(waterPositions, waterColors)
  waterGeometry.setAttribute('waterDepth', new THREE.Float32BufferAttribute(depths, 1))
  const waterMaterial = new THREE.ShaderMaterial({
    uniforms: { flowTime: flow }, vertexColors: true,
    vertexShader: `attribute float waterDepth; varying float vDepth; varying vec3 vTint; varying vec2 vWorld;
      void main(){vDepth=waterDepth;vTint=color;vWorld=position.xz;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}`,
    fragmentShader: `uniform float flowTime; varying float vDepth; varying vec3 vTint; varying vec2 vWorld;
      void main(){
        float ripple=sin(vWorld.y*18.0-flowTime*3.5+sin(vWorld.x*5.0)*1.4);
        float streak=smoothstep(0.975,1.0,ripple)*smoothstep(0.2,0.7,sin(vWorld.x*8.0+vWorld.y*1.5));
        float foam=(1.0-smoothstep(0.0,0.06,vDepth))*(0.45+0.25*sin(vWorld.y*12.0-flowTime*2.0));
        vec3 c=mix(vTint,vec3(0.76,0.95,0.88),streak*0.3+foam*0.65);
        c+=sin(vWorld.x*4.0+vWorld.y*3.0-flowTime)*0.018;
        gl_FragColor=vec4(c,1.0);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`,
  })
  scene.add(new THREE.Mesh(waterGeometry, waterMaterial))

  function windMaterial(color: number) {
    const mat = new THREE.MeshStandardMaterial({ color, flatShading: true, roughness: 0.95, side: THREE.DoubleSide })
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
  const rockMaterial = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 1, flatShading: true })
  const canopyParts = [
    new THREE.IcosahedronGeometry(0.52, 0).scale(1, 0.95, 0.95).translate(-0.23, 0.97, 0),
    new THREE.IcosahedronGeometry(0.51, 0).scale(0.85, 1.1, 0.92).translate(0.25, 1.19, 0.07),
    new THREE.IcosahedronGeometry(0.49, 0).scale(0.95, 1.1, 0.92).translate(0, 1.55, -0.02),
  ]
  const canopyGeometry = mergeGeometries(canopyParts)
  canopyParts.forEach((g) => g.dispose())
  const pineParts = [
    new THREE.ConeGeometry(0.6, 1.1, 7).toNonIndexed().translate(0, 1.05, 0),
    new THREE.ConeGeometry(0.45, 0.95, 7).toNonIndexed().translate(0, 1.58, 0),
    new THREE.ConeGeometry(0.29, 0.78, 7).toNonIndexed().translate(0, 2.05, 0),
  ]
  const pineGeometry = mergeGeometries(pineParts)
  pineParts.forEach((g) => g.dispose())
  const trunkGeometry = new THREE.CylinderGeometry(0.052, 0.085, 1.15, 6).translate(0, 0.575, 0)
  const bladePositions: number[] = []
  for (let i = 0; i < 5; i++) {
    const angle = i * Math.PI * 0.76, dx = Math.cos(angle), dz = Math.sin(angle)
    const h = 0.10 + (i % 3) * 0.035, w = 0.019
    bladePositions.push(-dz*w,0,dx*w, dz*w,0,-dx*w, dx*0.05,h,dz*0.05,
      dz*w,0,-dx*w, dx*0.08,h*0.64,dz*0.08, dx*0.05,h,dz*0.05)
  }
  const bladeGeometry = bufferGeometry(bladePositions)
  const stoneGeometry = new THREE.IcosahedronGeometry(0.22, 0).scale(1, 0.68, 0.82)
  const flowerGeometry = new THREE.IcosahedronGeometry(0.025, 0).translate(0, 0.085, 0)
  type Instance = { sample: GroundSample; scale: number; rotation: number; color: THREE.Color }
  const trees: Instance[] = [], pines: Instance[] = [], grass: Instance[] = [], stones: Instance[] = [], flowers: Instance[] = []
  const random = seededRandom(seed ^ 0x41c6ce57)
  for (const tile of tiles) {
    for (let i = 0; i < 105; i++) {
      const point = randomTilePoint(tile, random), sample = field.sample(point.x, point.z)
      const roll = random()
      if (sample.height < 0.18 || sample.shore < 0.28 || sample.rock > 0.4) continue
      const instance = { sample, scale: 0.7 + random() * 0.65, rotation: random() * Math.PI * 2, color: groundColor(sample) }
      if (i < 29 && sample.rock < 0.3 && roll < sample.forest * 0.8 + 0.025) {
        if ([...trees, ...pines].some((tree) => Math.hypot(tree.sample.x - sample.x, tree.sample.z - sample.z) < 0.36)) continue
        instance.scale *= 0.4 + sample.forest * 0.22
        instance.color = new THREE.Color('#2e6940').lerp(new THREE.Color('#73983e'), random())
        ;(random() < 0.43 ? pines : trees).push(instance)
      } else if (i < 6 && roll < 0.45 + sample.rock * 0.3) {
        instance.scale *= sample.rock > 0.5 ? 2 : 0.8
        instance.color = PALETTE.rock.clone().lerp(PALETTE.peak, random() * 0.6)
        stones.push(instance)
      } else if (sample.rock < 0.45 && roll < 0.34) {
        instance.color.lerp(new THREE.Color('#d6c765'), random() * 0.3)
        grass.push(instance)
        if (i % 7 === 0 && sample.dry < 0.65) flowers.push({ ...instance, color: new THREE.Color(random() > 0.5 ? '#faf0bd' : '#b2a0d6') })
      }
    }
  }
  const transform = new THREE.Object3D()
  function instances(geometry: THREE.BufferGeometry, material: THREE.Material, list: Instance[], wind = false) {
    const mesh = new THREE.InstancedMesh(geometry, material, list.length)
    list.forEach((item, index) => {
      transform.position.set(item.sample.x, item.sample.height - 0.012, item.sample.z)
      transform.rotation.set(0, item.rotation, 0)
      transform.scale.setScalar(item.scale)
      transform.updateMatrix()
      mesh.setMatrixAt(index, transform.matrix)
      if (material !== stemMaterial) mesh.setColorAt(index, item.color)
    })
    mesh.castShadow = true
    mesh.receiveShadow = true
    if (wind) mesh.customDepthMaterial = windDepth
    mesh.computeBoundingSphere()
    if (mesh.boundingSphere) mesh.boundingSphere.radius += 0.5
    scene.add(mesh)
    return mesh
  }
  instances(canopyGeometry, leafMaterial, trees, true)
  instances(pineGeometry, leafMaterial, pines, true)
  instances(trunkGeometry, stemMaterial, [...trees, ...pines])
  instances(bladeGeometry, grassMaterial, grass, true)
  instances(stoneGeometry, rockMaterial, stones)
  instances(flowerGeometry, grassMaterial, flowers, true)

  const floor = new THREE.Mesh(new THREE.PlaneGeometry(200, 200), new THREE.ShadowMaterial({ color: 0x496069, opacity: 0.15 }))
  floor.rotation.x = -Math.PI / 2
  floor.position.y = -0.62
  floor.receiveShadow = true
  scene.add(floor)

  const selection = new THREE.LineLoop(new THREE.BufferGeometry(), new THREE.LineBasicMaterial({ color: 0xffffff, depthTest: false }))
  selection.renderOrder = 2
  scene.add(selection)
  const raycaster = new THREE.Raycaster()
  let pointerDown = { x: 0, y: 0 }
  function selectTile(tile: WorldTile, sample: GroundSample) {
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
    const vertical = Math.max(11.1, 16.2 / (width / height))
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
      host.dataset.drawCalls = String(renderer.info.render.calls)
      host.dataset.triangles = String(renderer.info.render.triangles)
      lastReport = now
    }
    frame = requestAnimationFrame(animate)
  }
  frame = requestAnimationFrame(animate)
  onStats({ tiles: tiles.length, trees: trees.length + pines.length, grass: grass.length, triangles: landPositions.length / 9 })
  return {
    update: (next) => { settings = { ...next }; grid.visible = next.grid; uniforms.meadowWind.value = next.wind },
    view: setView,
    zoom: (factor) => { camera.zoom = Math.min(3, Math.max(0.7, camera.zoom * factor)); camera.updateProjectionMatrix() },
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
