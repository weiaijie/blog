import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import {
  WATER_LEVEL, clipWaterTriangle, createTerrainField, createTerrainSurface, createWorldTiles, edgePoints,
  getWorldEdges, randomTilePoint, seededRandom, smoothstep,
  type GroundSample, type WorldTile,
} from './terrainWorld'
import { createBareTreeGeometry, createBoulderGeometry, createBroadleafGeometry, createCactusGeometry, createFernGeometry, createFlowerGeometry, createGrassGeometry, createLeafLitterGeometry, createLilyGeometry, createPineGeometry, createReedGeometry, createShrubGeometry } from './terrainWorldModels'
import { createTerrainWaterMaterial, sampleWaterHeight, waterEnvironment, type WaterEnvironment } from './terrainWorldWater'
import { snowCover, terrainBiome, terrainGroundColor, TERRAIN_BIOMES, type TerrainBiome, type TerrainSeason } from './terrainWorldClimate'
import { civilizationOccupies, createCivilizationPlan } from './terrainWorldCivilization'
import { createWorldScenery } from './terrainWorldScenery'
import { advanceWorldDay, seasonalBlend, worldCalendar, type WorldCalendar } from './terrainWorldTime'
import { createWorldLife, type LifeKind } from './terrainWorldLife'
import { createWorldAquatic } from './terrainWorldAquatic'

export type TerrainWorldSettings = { animated: boolean; wind: number; flow: number; waves: number; grid: boolean; pan: boolean; day: number; dayRevision: number; autoSeason: boolean; timeSpeed: number }
export type TerrainWorldStats = { tiles: number; trees: number; grass: number; triangles: number; biomes: { id: TerrainBiome; count: number }[]; places: { id: string; label: string }[]; buildings: number; farms: number; bridges: number; people: number; animals: number; fish: number; layout: string }
export type TerrainWorldSelection = { id: string; label: string; fertility: number; elevation: number }
export type TerrainWorldHandle = {
  destroy: () => void
  update: (settings: TerrainWorldSettings) => void
  view: (mode: 'isometric' | 'top') => void
  zoom: (factor: number) => void
  focus: () => void
  focusBiome: (biome: TerrainBiome) => void
  focusPlace: (id: string) => void
  focusLife: (kind: LifeKind | 'fish') => void
}

const PALETTE = {
  sand: new THREE.Color('#efda9c'), rock: new THREE.Color('#737c89'), peak: new THREE.Color('#c3c6c4'),
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
  onCalendar: (calendar: WorldCalendar) => void,
): TerrainWorldHandle {
  const field = createTerrainField(seed)
  const tiles = createWorldTiles()
  const surface = createTerrainSurface(field, tiles)
  const civilization = createCivilizationPlan(field, surface.sample)
  const edges = getWorldEdges(tiles)
  const boundary=edges.filter((edge)=>edge.tiles.length===1)
  const waterEdgeFade=(x:number,z:number)=> {
    let distance=Infinity
    for(const {a,b} of boundary) {
      const dx=b.x-a.x,dz=b.z-a.z,t=Math.max(0,Math.min(1,((x-a.x)*dx+(z-a.z)*dz)/(dx*dx+dz*dz)))
      distance=Math.min(distance,Math.hypot(x-a.x-dx*t,z-a.z-dz*t))
    }
    return smoothstep(0,0.4,distance)
  }
  let settings = { ...initialSettings }
  let day=settings.day, lastSeasonDay=day
  let season = seasonalBlend(day)
  const groundColor = (sample: GroundSample) => terrainGroundColor(sample, season)
  const uniforms = { meadowTime: { value: 0 }, meadowWind: { value: settings.wind } }
  const flow = { value: 0 }
  const waterHeight=(x:number,z:number)=> {
    const sample=surface.sample(x,z)
    return sample?sampleWaterHeight(x,z,flow.value,waterEnvironment(field,sample,waterEdgeFade(x,z)),settings.waves,season.ice):WATER_LEVEL+0.006
  }
  const waterAt=(x:number,z:number)=>({height:waterHeight(x,z),dx:(waterHeight(x+0.04,z)-waterHeight(x-0.04,z))/0.08,dz:(waterHeight(x,z+0.04)-waterHeight(x,z-0.04))/0.08})
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
  controls.maxZoom = 16
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
  const waterPositions: number[] = [], depths: number[] = [], flows: number[] = [], waterClimates: number[] = [], stillWater: number[] = [], waterEdges: number[] = []
  const landFaces: { sample: GroundSample; facet: number }[] = []
  const snowAmounts: number[] = []
  for (const points of surface.triangles) {
    const center = field.sample(points.reduce((sum, p) => sum + p.x, 0) / 3, points.reduce((sum, p) => sum + p.z, 0) / 3)
    const color = groundColor(center)
    const facet = Math.sin(center.x * 112.1 + center.z * 173.7) * 0.018 + 1
    color.multiplyScalar(facet)
    landFaces.push({ sample: center, facet })
    snowAmounts.push(...points.map((p) => snowCover(p, season)))
    for (const p of points) { landPositions.push(p.x, p.height, p.z); landColors.push(color.r, color.g, color.b); cover.push(p.rock, p.dry, p.shore) }
    const water = clipWaterTriangle(points)
    for (let index = 1; index < water.length - 1; index++) {
      const [a,b,c]=[water[0],water[index],water[index+1]]
      const midpoint=(p:typeof a,q:typeof a)=>({x:(p.x+q.x)/2,z:(p.z+q.z)/2,height:(p.height+q.height)/2})
      const ab=midpoint(a,b),bc=midpoint(b,c),ca=midpoint(c,a)
      // Subdivide only water; preserve the clipped shoreline and interpolated bed depth.
      for (const p of [a,ab,ca, ab,b,bc, ca,bc,c, ab,bc,ca]) {
        const depth = WATER_LEVEL - p.height
        const flowAt = field.waterCoordinates(p.x, p.z)
        waterPositions.push(p.x, WATER_LEVEL + 0.006, p.z)
        flows.push(flowAt.across, flowAt.along, flowAt.river)
        depths.push(depth)
        const climate = field.sample(p.x, p.z)
        waterClimates.push(Math.max(0,0.65+climate.cold*0.35-climate.desert*0.6-climate.badlands*0.25))
        stillWater.push(climate.wetland)
        waterEdges.push(waterEdgeFade(p.x,p.z))
      }
    }
  }
  const groundMaterial = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 1, flatShading: true })
  groundMaterial.onBeforeCompile = (shader) => {
    shader.vertexShader = 'attribute float snowCover; varying float vSnow; attribute vec3 terrainCover; varying vec3 vCover; varying vec3 terrainPosition; varying float terrainUp;\n' + shader.vertexShader.replace('#include <begin_vertex>', '#include <begin_vertex>\nterrainPosition = position; terrainUp = normal.y; vCover=terrainCover; vSnow=snowCover;')
    shader.fragmentShader = `varying float vSnow; varying vec3 vCover; varying vec3 terrainPosition; varying float terrainUp;
      float terrainHash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
      float terrainNoise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.0-2.0*f);return mix(mix(terrainHash(i),terrainHash(i+vec2(1,0)),f.x),mix(terrainHash(i+vec2(0,1)),terrainHash(i+vec2(1,1)),f.x),f.y);}
    ` + shader.fragmentShader.replace('#include <color_fragment>', `#include <color_fragment>
      vec2 cell = terrainPosition.xz * 33.0;
      vec2 f = fract(cell); float h = terrainHash(floor(cell));
      float fleck = step(0.68,h)*step(f.y,f.x*0.48)*step(f.x,0.7);
      float meadow = smoothstep(0.65,0.98,terrainUp) * (1.0-vCover.x) * smoothstep(0.18,0.65,vCover.z)*(1.0-vSnow);
      float coverNoise=terrainNoise(terrainPosition.xz*2.1)*0.6+terrainNoise(terrainPosition.xz*5.8)*0.4;
      float soil=smoothstep(0.61,0.79,coverNoise)*(0.12+vCover.y*0.28);
      diffuseColor.rgb=mix(diffuseColor.rgb,vec3(0.30,0.22,0.075),soil*meadow);
      diffuseColor.rgb *= 1.0 + ((coverNoise-0.5)*0.22+fleck*0.26-0.04)*meadow;
      float grain=terrainNoise(terrainPosition.xz*37.0);
      diffuseColor.rgb *= 1.0+(grain-0.5)*0.09*(1.0-vCover.x);
      float strata=sin(terrainPosition.y*22.0+terrainPosition.x*1.5+terrainNoise(terrainPosition.xz*3.0)*3.0);
      float fissure=smoothstep(0.7,0.95,strata)*vCover.x*(1.0-smoothstep(0.8,0.98,terrainUp));
      diffuseColor.rgb *= 1.0-fissure*0.14*(1.0-vSnow)+(grain-0.5)*0.07*vCover.x;
    `)
  }
  const groundGeometry = bufferGeometry(landPositions, landColors)
  groundGeometry.setAttribute('terrainCover', new THREE.Float32BufferAttribute(cover, 3))
  groundGeometry.setAttribute('snowCover', new THREE.Float32BufferAttribute(snowAmounts, 1))
  const ground = new THREE.Mesh(groundGeometry, groundMaterial)
  ground.receiveShadow = true
  ground.castShadow = true
  scene.add(ground)

  const sidePositions: number[] = [], sideColors: number[] = [], gridPositions: number[] = []
  const waterGridPoints: {index:number;x:number;z:number;env:WaterEnvironment}[]=[]
  for (const edge of edges) {
    const points = edgePoints(edge.a, edge.b)
    for (let i = 0; i < points.length - 1; i++) {
      const a = field.sample(points[i].x, points[i].z), b = field.sample(points[i + 1].x, points[i + 1].z)
      for(const [offset,p] of [a,b].entries()) if(p.height<WATER_LEVEL) {
        waterGridPoints.push({index:gridPositions.length/3+offset,x:p.x,z:p.z,env:waterEnvironment(field,p,waterEdgeFade(p.x,p.z))})
      }
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
  waterGeometry.setAttribute('waterClimate', new THREE.Float32BufferAttribute(waterClimates, 1))
  waterGeometry.setAttribute('waterStill', new THREE.Float32BufferAttribute(stillWater, 1))
  waterGeometry.setAttribute('waterEdge', new THREE.Float32BufferAttribute(waterEdges, 1))
  waterGeometry.computeBoundingSphere()
  if(waterGeometry.boundingSphere) waterGeometry.boundingSphere.radius+=0.18
  const waterMaterial = createTerrainWaterMaterial(flow)
  waterMaterial.uniforms.waveStrength.value=settings.waves
  scene.add(new THREE.Mesh(waterGeometry, waterMaterial))
  const scenery = createWorldScenery(civilization, surface.sample)
  scene.add(scenery.group)
  const life=createWorldLife(seed,civilization,surface.sample)
  scene.add(life.group)
  const aquatic=createWorldAquatic(seed,tiles,surface.sample,waterHeight)
  scene.add(aquatic.group)

  function windMaterial(color: number) {
    const mat = new THREE.MeshStandardMaterial({ color, vertexColors: true, flatShading: true, roughness: 0.95, side: THREE.DoubleSide })
    mat.onBeforeCompile = (shader) => {
      Object.assign(shader.uniforms, uniforms)
      shader.vertexShader = 'attribute float instanceSnow; varying float plantSnow; varying float plantUp;\n' + windFunction + shader.vertexShader.replace('#include <begin_vertex>', 'vec3 transformed = bendInWind(position); plantSnow=instanceSnow; plantUp=normal.y;')
      shader.fragmentShader = 'varying float plantSnow; varying float plantUp;\n' + shader.fragmentShader.replace('#include <color_fragment>', '#include <color_fragment>\ndiffuseColor.rgb=mix(diffuseColor.rgb,vec3(0.82,0.9,0.91),plantSnow*smoothstep(0.0,0.65,plantUp));')
    }
    mat.customProgramCacheKey = () => 'terrain-world-wind-snow-v2'
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
  const trees: Instance[] = [], pines: Instance[] = [], shrubs: Instance[] = [], grass: Instance[] = [], stones: Instance[] = [], flowers: Instance[] = [], reeds: Instance[] = [], ferns: Instance[] = [], cacti: Instance[] = [], lilies: Instance[] = [], litter: Instance[] = []
  const random = seededRandom(seed ^ 0x41c6ce57)
  const leafColors = ['#285443', '#396445', '#597e32', '#719334', '#8ca337'].map((c) => new THREE.Color(c))
  const flowerColors = ['#fff8e4', '#f6d155', '#dfb7e5', '#efac73'].map((c) => new THREE.Color(c))
  const occupied: Instance[] = []
  for (const tile of tiles) {
    for (let i = 0; i < 440; i++) {
      const point = randomTilePoint(tile, random), sample = surface.sample(point.x, point.z)
      if (civilizationOccupies(civilization, point)) continue
      if (sample && sample.wetland > 0.4 && sample.height < WATER_LEVEL && i < 28) {
        lilies.push({ sample: { ...sample, height: WATER_LEVEL+0.028 }, scale: 0.4+random()*0.5, rotation: random()*6.28, color: new THREE.Color('#547d46') })
      }
      if (sample && sample.rock > 0.3 && sample.shore > 0.6 && i < 10) {
        stones.push({ sample, scale: 0.08 + random() * 0.24, rotation: random() * Math.PI * 2,
          aspect: 0.5 + random() * 0.4, color: PALETTE.rock.clone().lerp(PALETTE.peak, random() * 0.3) })
      }
      if (!sample || sample.height < WATER_LEVEL + 0.01 || sample.shore < 0.14 || sample.rock > 0.7) continue
      const roll = random()
      const instance: Instance = { sample, scale: 0.65 + random() * 0.6, rotation: random() * Math.PI * 2, color: groundColor(sample), aspect: 0.85 + random() * 0.35 }
      const riverWood = (1 - smoothstep(0.45, 1.0, sample.shore)) * 0.07
      const grouping = smoothstep(-0.25, 0.5, sample.patch)
      if (sample.desert > 0.55 || sample.badlands > 0.58) {
        if (i < 7 && sample.desert > 0.7 && roll < 0.3) cacti.push({ ...instance, scale: 0.6+random()*0.8, color: new THREE.Color('#5c876d') })
        if (i < 16 && roll < 0.4) stones.push({ ...instance, scale: sample.badlands * (0.3+random()*0.7)+0.1, color: new THREE.Color('#b27855') })
        if (i > 250 && roll < 0.04) grass.push({ ...instance, scale: instance.scale*0.6, color: new THREE.Color('#b8a96a') })
        continue
      }
      if (sample.shore < 0.48 || sample.wetland > 0.45) {
        if (i < 120 && roll < 0.55) reeds.push({ ...instance, color: new THREE.Color('#7e9744'), scale: 0.65 + random() * 0.65 })
        continue
      }
      const woodland = Math.max(sample.forest, sample.pine * 0.95) * (1-smoothstep(0.68,0.86,sample.cold))
      if (i < 70 && sample.rock < 0.18 && roll < woodland * 0.92 + riverWood + grouping * 0.009) {
        instance.scale *= 0.18 + woodland * (0.13+grouping*0.18) + riverWood * 0.4
        if (occupied.some((tree) => Math.hypot(tree.sample.x - sample.x, tree.sample.z - sample.z) < (tree.scale + instance.scale) * 0.62)) continue
        const pine = random() < 0.12 + sample.pine * 0.85
        if (pine) instance.scale *= 0.82
        instance.color = leafColors[Math.floor(random() * leafColors.length)].clone()
        if (pine) instance.color.multiplyScalar(0.8)
        ;(pine ? pines : trees).push(instance)
        occupied.push(instance)
      } else if (i < 100 && sample.rock < 0.25 && roll < grouping * 0.045 + riverWood * 0.8 + sample.forest * 0.07) {
        instance.scale *= 0.4 + random() * 0.48
        instance.color = leafColors[Math.floor(random() * leafColors.length)].clone()
        shrubs.push(instance)
      } else if (i > 125 && sample.rock < 0.25 && roll < grouping * (0.5-sample.cold*0.3)) {
        instance.scale *= 0.25 + random() * 0.3
        instance.color.lerp(new THREE.Color('#b7b947'), random() * 0.4)
        grass.push(instance)
        if (sample.forest > 0.3 && i % 5 === 0) ferns.push({ ...instance, color: new THREE.Color('#638844'), scale: 0.65 + random() * 0.55 })
        if (sample.dry < 0.6 && sample.cold < 0.55 && grouping > 0.7 && (i % 3 === 0 || sample.meadow > 0.6)) {
          flowers.push({ ...instance, scale: 0.3 + random() * 0.25, color: flowerColors[Math.floor(random() * flowerColors.length)] })
        }
        if (sample.forest > 0.25 && i % 3 === 0) litter.push({ ...instance, color: new THREE.Color('#c18c43') })
      }
      if (i < 12 && sample.patch > 0.12 && (sample.rock > 0.12 || sample.shore < 1.1 || roll < 0.12)) {
        stones.push({ ...instance, scale: 0.07 + random() * 0.25, color: PALETTE.rock.clone().lerp(PALETTE.sand, random() * 0.32) })
      }
    }
  }
  // Cluster rocks at this seed's banks and ridges, not fixed world coordinates.
  const rockGroups=tiles.filter((tile)=> {
    const s=field.sample(tile.center.x,tile.center.z)
    return (s.shore<1.5 || s.rock>0.15) && random()<0.32
  }).slice(0,22)
  for (const tile of rockGroups) {
    const {x,z}=tile.center,size=0.4+random()*0.55
    for (let i = 0; i < 13; i++) {
      const angle = random() * Math.PI * 2, radius = i === 0 ? 0 : 0.18 + random() * 0.65
      const sample = surface.sample(x + Math.cos(angle) * radius, z + Math.sin(angle) * radius)
      if (sample && civilizationOccupies(civilization, sample)) continue
      if (!sample || sample.height < -0.08 || sample.height > 1.8) continue
      stones.push({ sample, scale: size * (i < 2 ? 0.6 + random() * 0.38 : 0.12 + random() * 0.25),
        aspect: 0.7 + random() * 0.8, rotation: random() * Math.PI * 2,
        color: PALETTE.rock.clone().lerp(PALETTE.peak, random() * 0.65) })
    }
  }
  const transform = new THREE.Object3D()
  type PropKind = 'broadleaf' | 'pine' | 'branch' | 'shrub' | 'grass' | 'flower' | 'reed' | 'fern' | 'rock' | 'cactus' | 'lily' | 'litter'
  const seasonalUpdates: ((value: TerrainSeason) => void)[] = []
  function instances(geometry: THREE.BufferGeometry, material: THREE.Material, list: Instance[], wind = false, kind: PropKind = 'rock') {
    const mesh = new THREE.InstancedMesh(geometry, material, list.length)
    const snowAttribute = new THREE.InstancedBufferAttribute(new Float32Array(list.length), 1)
    geometry.setAttribute('instanceSnow', snowAttribute)
    const updateSeason = (value: TerrainSeason) => {
      list.forEach((item, index) => {
        const s=item.sample, snow=snowCover(s,value), choice=(Math.sin(index*127.1+13.7)*43758.5453)%1
        let size=1, color=item.color.clone()
        if (kind==='broadleaf' || kind==='shrub') {
          color=new THREE.Color(value.leaves[index%value.leaves.length])
          size=kind==='broadleaf'?Math.cbrt(value.foliage):0.35+value.foliage*0.65
        }
        if (kind==='grass' || kind==='fern' || kind==='reed') {
          color=terrainGroundColor(s,value).lerp(new THREE.Color('#b9ac72'),value.dry*0.4)
          size=1-snow*(kind==='reed'?0.15:0.75)
        }
        if (kind==='flower') size=Math.abs(choice)<value.bloom?1:0
        if (kind==='lily') size=1-value.ice
        if (kind==='litter') size=value.litter*(1-snow)
        if (kind==='rock') color.lerp(new THREE.Color('#edf3f1'),snow*0.75)
        transform.position.set(s.x, s.height - 0.012, s.z)
        transform.rotation.set(0, item.rotation, 0)
        transform.scale.setScalar(item.scale*Math.max(0.00001,size))
        transform.scale.y *= item.aspect ?? 1
        transform.updateMatrix()
        mesh.setMatrixAt(index, transform.matrix)
        if (material !== stemMaterial) mesh.setColorAt(index, color)
        snowAttribute.setX(index,snow)
      })
      mesh.instanceMatrix.needsUpdate=true
      if(mesh.instanceColor) mesh.instanceColor.needsUpdate=true
      snowAttribute.needsUpdate=true
      mesh.computeBoundingSphere()
      if(mesh.boundingSphere) mesh.boundingSphere.radius+=0.5
    }
    seasonalUpdates.push(updateSeason)
    updateSeason(season)
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
    instances(createBroadleafGeometry(variant), leafMaterial, select(trees), true, 'broadleaf')
    instances(createPineGeometry(variant), leafMaterial, select(pines), true, 'pine')
    instances(createShrubGeometry(variant), leafMaterial, select(shrubs), true, 'shrub')
    instances(createBoulderGeometry(variant), rockMaterial, select(stones))
  }
  instances(trunkGeometry, stemMaterial, pines, false, 'branch')
  instances(createBareTreeGeometry().scale(0.78,0.65,0.78), stemMaterial, trees, false, 'branch')
  instances(createGrassGeometry(), grassMaterial, grass, true, 'grass')
  instances(createFlowerGeometry(), grassMaterial, flowers, true, 'flower')
  instances(createReedGeometry(), grassMaterial, reeds, true, 'reed')
  instances(createFernGeometry(), grassMaterial, ferns, true, 'fern')
  instances(createCactusGeometry(), rockMaterial, cacti, false, 'cactus')
  instances(createLilyGeometry(), grassMaterial, lilies, true, 'lily')
  instances(createLeafLitterGeometry(), grassMaterial, litter, false, 'litter')

  function applySeason(next: TerrainSeason) {
    season=next
    const colorAttribute=groundGeometry.getAttribute('color'), snowAttribute=groundGeometry.getAttribute('snowCover')
    landFaces.forEach(({sample,facet},index)=> {
      const color=groundColor(sample).multiplyScalar(facet)
      for(let j=0;j<3;j++) {
        colorAttribute.setXYZ(index*3+j,color.r,color.g,color.b)
        snowAttribute.setX(index*3+j,snowCover(surface.triangles[index][j],season))
      }
    })
    colorAttribute.needsUpdate=true; snowAttribute.needsUpdate=true
    seasonalUpdates.forEach((update)=>update(season))
    scenery.updateSeason(season)
    waterMaterial.uniforms.iceAmount.value=season.ice
    renderer.toneMappingExposure=1.05-season.snow*0.13
    host.dataset.season=season.id
  }
  applySeason(season)

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
    const label = TERRAIN_BIOMES.find((biome)=>biome.id===terrainBiome(sample))!.label
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
  let frame = 0, previousTime = performance.now(), lastReport = 0, sceneryTime = 0, aquaticTime=0, lastSeasonUpdate=0
  const animate = (now: number) => {
    const delta = Math.min((now - previousTime) / 1000, 0.05)
    previousTime = now
    if (settings.animated && !document.hidden) {
      uniforms.meadowTime.value += delta
      flow.value += delta * settings.flow
      sceneryTime += delta * settings.wind
      aquaticTime += delta*(1-season.ice*0.7)
      day=advanceWorldDay(day,delta,settings.timeSpeed,settings.autoSeason)
      if(Math.abs(day-lastSeasonDay)>1.5 && now-lastSeasonUpdate>800) {
        applySeason(seasonalBlend(day));lastSeasonDay=day;lastSeasonUpdate=now
      }
    }
    controls.update()
    if(grid.visible) {
      const positions=grid.geometry.getAttribute('position')
      for(const p of waterGridPoints) positions.setY(p.index,sampleWaterHeight(p.x,p.z,flow.value,p.env,settings.waves,season.ice)+0.012)
      positions.needsUpdate=true
    }
    scenery.animate(sceneryTime,flow.value,waterAt)
    life.animate(uniforms.meadowTime.value)
    aquatic.animate(aquaticTime)
    renderer.render(scene, camera)
    if (now - lastReport > 250) {
      host.dataset.simulationTime = uniforms.meadowTime.value.toFixed(3)
      host.dataset.flowTime = flow.value.toFixed(3)
      host.dataset.drawCalls = String(renderer.info.render.calls)
      host.dataset.triangles = String(renderer.info.render.triangles)
      host.dataset.buildings = String(civilization.buildings.length)
      host.dataset.windmills = String(scenery.rotors)
      host.dataset.worldDay=day.toFixed(3)
      const fish=aquatic.position(aquaticTime)
      host.dataset.fishCount=String(aquatic.fish.length)
      host.dataset.fishPosition=fish?`${fish.x.toFixed(3)},${fish.height.toFixed(3)},${fish.z.toFixed(3)}`:''
      const waterProbe=aquatic.fish[0]?.school.center??{x:field.riverX(0),z:0}
      host.dataset.waterHeight=waterHeight(waterProbe.x,waterProbe.z).toFixed(4)
      host.dataset.waveStrength=String(settings.waves)
      const resident=life.position('traveler',uniforms.meadowTime.value)
      const animal=life.position('deer',uniforms.meadowTime.value)
      host.dataset.residentPosition=resident?`${resident.x.toFixed(3)},${resident.z.toFixed(3)}`:''
      host.dataset.animalPosition=animal?`${animal.x.toFixed(3)},${animal.z.toFixed(3)}`:''
      onCalendar(worldCalendar(day))
      lastReport = now
    }
    frame = requestAnimationFrame(animate)
  }
  frame = requestAnimationFrame(animate)
  const biomeTiles = new Map<TerrainBiome, WorldTile[]>()
  for(const tile of tiles) {
    const biome=terrainBiome(field.sample(tile.center.x,tile.center.z))
    const list=biomeTiles.get(biome)??[]; list.push(tile); biomeTiles.set(biome,list)
  }
  onStats({ tiles: tiles.length, trees: trees.length + pines.length, grass: grass.length, triangles: landPositions.length / 9,
    biomes:TERRAIN_BIOMES.map(({id})=>({id,count:biomeTiles.get(id)?.length??0})),
    places:civilization.places.map(({id,label,tileId})=>({id,label:`${label} · ${tileId}`})),buildings:civilization.buildings.length,farms:civilization.farms.length,bridges:civilization.roads.filter((r)=>r.bridge).length,
    people:life.actors.filter((a)=>a.kind==='traveler'||a.kind==='cart').length,animals:life.actors.filter((a)=>a.kind!=='traveler'&&a.kind!=='cart').length,fish:aquatic.fish.length,layout:field.layout })
  function focusTile() {
    const center = selectedTile?.center ?? { x: field.riverX(2) - 1.8, z: 2 }
    const y = Math.max(WATER_LEVEL, surface.sample(center.x, center.z)?.height ?? 0.3)
    controls.target.set(center.x, y, center.z)
    camera.position.set(center.x + 9, y + 31, center.z + 48)
    camera.zoom = 3.8
    camera.updateProjectionMatrix()
    controls.update()
  }
  return {
    update: (next) => {
      if (next.day!==settings.day || next.dayRevision!==settings.dayRevision) { day=next.day;lastSeasonDay=day;applySeason(seasonalBlend(day));onCalendar(worldCalendar(day)) }
      settings = { ...next }; grid.visible = next.grid; uniforms.meadowWind.value = next.wind
      waterMaterial.uniforms.waveStrength.value=next.waves
      controls.mouseButtons.LEFT = next.pan ? THREE.MOUSE.PAN : THREE.MOUSE.ROTATE
      controls.touches.ONE = next.pan ? THREE.TOUCH.PAN : THREE.TOUCH.ROTATE
    },
    view: setView,
    zoom: (factor) => { camera.zoom = Math.min(16, Math.max(0.55, camera.zoom * factor)); camera.updateProjectionMatrix() },
    focus: focusTile,
    focusBiome: (biome) => {
      const list=biomeTiles.get(biome)
      if(!list?.length) return
      const tile=list[Math.floor(list.length/2)]
      selectTile(tile,field.sample(tile.center.x,tile.center.z))
      focusTile()
    },
    focusPlace: (id) => {
      const place=civilization.places.find((p)=>p.id===id)
      if(!place) return
      const {x,z,height}=place.center
      controls.target.set(x,height,z)
      camera.position.set(x+9,height+31,z+48)
      selectTile(tiles.find((tile)=>tile.id===place.tileId)!,place.center)
      camera.zoom=10
      camera.updateProjectionMatrix();controls.update()
    },
    focusLife: (kind) => {
      const center=aquatic.fish[0]?.school.center
      const p=kind==='fish'?(center?{...center,height:WATER_LEVEL}:null):life.position(kind,uniforms.meadowTime.value)
      if(!p) return
      controls.target.set(p.x,p.height,p.z);camera.position.set(p.x+9,p.height+31,p.z+48)
      camera.zoom=kind==='fish'?10:12;camera.updateProjectionMatrix();controls.update()
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
