import { Application, Container, Graphics, Sprite, Texture } from 'pixi.js'
import { getTerrainConfig } from '../../game/config/terrain'
import { createFixedMap, type GameMap } from '../../game/state/map'
import {
  installCivPerfApi,
  type CivPerfApi,
  type PerfExplorationSnapshot,
  type PerfScenarioId,
} from '../../perf/civPerfApi'
import { PerformanceSampler } from '../../perf/sampler'
import { CameraController } from '../camera/cameraController'
import { calculateChunkStats } from '../chunks/chunkManager'
import { TilePool } from '../chunks/tilePool'
import { calculateActiveTileRect } from '../chunks/viewportManager'
import {
  getHexMapWorldSize,
  getHexPolygonPoints,
  tileToWorld,
  worldToTile,
} from '../coordinates/hexCoordinates'
import {
  getCityVisualStyle,
  getTerrainVisualStyle,
  getUnitVisualKind,
  getUnitVisualStyle,
  mapVisualTheme,
  type MapVisualOwner,
  type TerrainVisualStyle,
} from '../visuals/mapVisualTheme'

const HEX_RADIUS = 24
const TILE_SIZE = HEX_RADIUS * Math.sqrt(3)
const TERRAIN_TEXTURE_SCALE = 1
const TERRAIN_BLEND_RADIUS = HEX_RADIUS * 1.72
const GRID_LINE_WIDTH = 0.75
const FOG_TEXTURE_SCALE = 0.0625
const FOG_DRAG_RESTORE_MS = 120
const CAMERA_PADDING = 24
const CHUNK_SIZE = 8
const DEFAULT_SEED = 1001

export type PixiStageStats = {
  width: number
  height: number
  tileCount: number
  activeTileCount: number
  activeChunkCount: number
  allocatedTileGraphics: number
  cameraX: number
  cameraY: number
  zoom: number
  p95FrameMs: number
  selectedTileId: string | null
  fogVisibleTileCount: number
  fogExploredTileCount: number
}

export type PixiStageHandle = {
  stats: PixiStageStats
  selectTile: (tileId: string) => void
  setExploration: (exploration: PixiExplorationSnapshot | null) => void
  setVisualEntities: (entities: PixiVisualEntities) => void
  destroy: () => void
}

export type PixiExplorationSnapshot = PerfExplorationSnapshot

export type PixiVisualUnit = {
  id: string
  owner: MapVisualOwner
  tileId: string
  typeId: string
}

export type PixiVisualCity = {
  id: string
  owner: MapVisualOwner
  tileId: string
}

export type PixiVisualBuildHint = {
  kind: 'citySite' | 'objective'
  tileId: string
}

export type PixiVisualEntities = {
  buildHints: PixiVisualBuildHint[]
  cities: PixiVisualCity[]
  units: PixiVisualUnit[]
}

export type MountPixiStageOptions = {
  initialExploration?: PixiExplorationSnapshot | null
  initialVisualEntities?: PixiVisualEntities
  onTileSelect?: (tileId: string) => void
  onStats?: (stats: PixiStageStats) => void
}

const emptyVisualEntities: PixiVisualEntities = {
  buildHints: [],
  cities: [],
  units: [],
}

export async function mountPixiStage(
  host: HTMLElement,
  options: MountPixiStageOptions = {},
): Promise<PixiStageHandle> {
  const app = new Application()

  await app.init({
    resizeTo: host,
    backgroundColor: mapVisualTheme.background,
    antialias: false,
  })

  host.appendChild(app.canvas)

  const mapLayer = new Container()
  const terrainBaseCanvas = document.createElement('canvas')
  const terrainBaseContext = terrainBaseCanvas.getContext('2d')
  const terrainBaseTexture = Texture.from(terrainBaseCanvas)
  const terrainBaseSprite = new Sprite(terrainBaseTexture)
  const entityLayer = new Graphics()
  const buildHintLayer = new Graphics()
  const selection = new Graphics()
  const tilePool = new TilePool()
  const sampler = new PerformanceSampler()
  let gameMap = createFixedMap(16, 16, DEFAULT_SEED)
  let currentExploration = options.initialExploration ?? null
  let visualEntities = options.initialVisualEntities ?? emptyVisualEntities
  let selectedTileId: string | null = null
  let latestTrace = sampler.stop()
  let queuedStats: PixiStageStats | null = null
  let statsFrame = 0
  let isPerfTraceActive = false
  let fogRestoreTimer = 0
  let isFogPanSuppressed = false
  const initialWorldSize = getHexMapWorldSize(gameMap.width, gameMap.height, { hexRadius: HEX_RADIUS })
  const camera = new CameraController({
    viewportWidth: app.renderer.width,
    viewportHeight: app.renderer.height,
    mapWidth: gameMap.width,
    mapHeight: gameMap.height,
    tileSize: TILE_SIZE,
    worldHeight: initialWorldSize.height,
    worldWidth: initialWorldSize.width,
    padding: CAMERA_PADDING,
  })
  const fogCanvas = document.createElement('canvas')
  const fogContext = fogCanvas.getContext('2d')
  const fogTexture = Texture.from(fogCanvas)
  const fogSprite = new Sprite(fogTexture)

  mapLayer.addChild(terrainBaseSprite)
  mapLayer.addChild(entityLayer)
  mapLayer.addChild(buildHintLayer)
  mapLayer.addChild(fogSprite)
  mapLayer.addChild(selection)
  app.stage.addChild(mapLayer)

  function renderMap(map: GameMap): void {
    const terrainByTileId = new Map(
      map.tiles.map((tile) => {
        const terrain = getTerrainConfig(tile.terrainId)

        return [tile.id, getTerrainVisualStyle(tile.terrainId, terrain.color)] as const
      }),
    )

    renderContinuousTerrainBase(map, terrainByTileId)
    tilePool.setAllocatedTileGraphics(map.tiles.length)
    renderVisualEntities()
    renderFog()
    renderSelection()
  }

  function renderContinuousTerrainBase(
    map: GameMap,
    terrainByTileId: Map<string, TerrainVisualStyle>,
  ): void {
    if (!terrainBaseContext) {
      return
    }

    const worldSize = getHexMapWorldSize(map.width, map.height, { hexRadius: HEX_RADIUS })

    prepareMapTexture(
      terrainBaseCanvas,
      terrainBaseContext,
      terrainBaseTexture,
      terrainBaseSprite,
      worldSize,
    )

    terrainBaseContext.fillStyle = getAverageTerrainColor(map, terrainByTileId)
    terrainBaseContext.fillRect(0, 0, worldSize.width, worldSize.height)

    for (const tile of map.tiles) {
      const terrain = getTerrainConfig(tile.terrainId)
      const visual = terrainByTileId.get(tile.id) ?? getTerrainVisualStyle(tile.terrainId, terrain.color)
      const center = tileToWorld(tile, { hexRadius: HEX_RADIUS })

      drawTerrainBlend(terrainBaseContext, center, visual)
    }

    renderTerrainGridOverlay(terrainBaseContext, map, terrainByTileId)
    terrainBaseTexture.source.update()
  }

  function renderTerrainGridOverlay(
    context: CanvasRenderingContext2D,
    map: GameMap,
    terrainByTileId: Map<string, TerrainVisualStyle>,
  ): void {
    context.lineJoin = 'round'
    context.lineCap = 'round'
    context.lineWidth = GRID_LINE_WIDTH

    for (const tile of map.tiles) {
      const terrain = getTerrainConfig(tile.terrainId)
      const visual = terrainByTileId.get(tile.id) ?? getTerrainVisualStyle(tile.terrainId, terrain.color)
      const center = tileToWorld(tile, { hexRadius: HEX_RADIUS })
      const points = getHexPolygonPoints(center, HEX_RADIUS - 0.7)

      context.strokeStyle = colorToRgba(visual.stroke, Math.min(0.16, visual.strokeAlpha * 0.24))
      context.beginPath()
      points.forEach((point, index) => {
        if (index === 0) {
          context.moveTo(point.x, point.y)
        } else {
          context.lineTo(point.x, point.y)
        }
      })
      context.closePath()
      context.stroke()
    }
  }

  function prepareMapTexture(
    canvas: HTMLCanvasElement,
    context: CanvasRenderingContext2D,
    texture: Texture,
    sprite: Sprite,
    worldSize: { width: number; height: number },
  ): void {
    const textureWidth = Math.ceil(worldSize.width * TERRAIN_TEXTURE_SCALE)
    const textureHeight = Math.ceil(worldSize.height * TERRAIN_TEXTURE_SCALE)

    texture.source.scaleMode = 'linear'

    if (canvas.width !== textureWidth || canvas.height !== textureHeight) {
      canvas.width = textureWidth
      canvas.height = textureHeight
      texture.source.resize(textureWidth, textureHeight)
    }

    context.setTransform(TERRAIN_TEXTURE_SCALE, 0, 0, TERRAIN_TEXTURE_SCALE, 0, 0)
    context.imageSmoothingEnabled = true
    sprite.setSize(worldSize.width, worldSize.height)
  }

  function renderVisualEntities(): void {
    entityLayer.clear()
    buildHintLayer.clear()

    for (const city of visualEntities.cities) {
      drawCityMarker(entityLayer, city)
    }

    for (const unit of visualEntities.units) {
      drawUnitMarker(entityLayer, unit)
    }

    for (const hint of visualEntities.buildHints) {
      drawBuildHint(buildHintLayer, hint)
    }
  }

  function getActiveTileRect() {
    const cameraState = camera.getState()

    return calculateActiveTileRect({
      camera: cameraState,
      viewportWidth: app.renderer.width,
      viewportHeight: app.renderer.height,
      mapWidth: gameMap.width,
      mapHeight: gameMap.height,
      hexRadius: HEX_RADIUS,
    })
  }

  function renderFog(): void {
    if (!fogContext) {
      return
    }

    const worldSize = getHexMapWorldSize(gameMap.width, gameMap.height, { hexRadius: HEX_RADIUS })
    const width = worldSize.width
    const height = worldSize.height
    const textureWidth = Math.ceil(width * FOG_TEXTURE_SCALE)
    const textureHeight = Math.ceil(height * FOG_TEXTURE_SCALE)
    fogTexture.source.scaleMode = gameMap.width >= 32 ? 'nearest' : 'linear'

    if (fogCanvas.width !== textureWidth || fogCanvas.height !== textureHeight) {
      fogCanvas.width = textureWidth
      fogCanvas.height = textureHeight
      fogContext.imageSmoothingEnabled = false
      fogTexture.source.resize(textureWidth, textureHeight)
    }

    fogSprite.setSize(width, height)

    fogContext.clearRect(0, 0, textureWidth, textureHeight)

    if (!currentExploration) {
      updateFogVisibility()
      fogTexture.source.update()
      return
    }

    updateFogVisibility()
    fogContext.fillStyle = mapVisualTheme.fog.unknownFill
    fogContext.fillRect(0, 0, textureWidth, textureHeight)

    fogContext.fillStyle = mapVisualTheme.fog.exploredFill

    for (const tileId of currentExploration.exploredTileIds) {
      const tile = parseTileId(tileId)

      if (tile && tile.x < gameMap.width && tile.y < gameMap.height) {
        clearFogTile(fogContext, tile.x, tile.y)
        fillFogTile(fogContext, tile.x, tile.y)
      }
    }

    for (const tileId of currentExploration.visibleTileIds) {
      const tile = parseTileId(tileId)

      if (tile && tile.x < gameMap.width && tile.y < gameMap.height) {
        clearFogTile(fogContext, tile.x, tile.y)
      }
    }

    fogTexture.source.update()
  }

  function updateFogVisibility(): void {
    fogSprite.visible = currentExploration !== null && !isFogPanSuppressed
  }

  function restoreFogAfterCameraMove(): void {
    if (fogRestoreTimer !== 0) {
      window.clearTimeout(fogRestoreTimer)
      fogRestoreTimer = 0
    }

    isFogPanSuppressed = false
    updateFogVisibility()
  }

  function pauseFogDuringCameraMove(): void {
    if (!currentExploration) {
      return
    }

    // Only suppress the render sprite during camera motion; exploration state stays authoritative.
    isFogPanSuppressed = true
    updateFogVisibility()

    if (fogRestoreTimer !== 0) {
      window.clearTimeout(fogRestoreTimer)
    }

    fogRestoreTimer = window.setTimeout(() => {
      restoreFogAfterCameraMove()
    }, FOG_DRAG_RESTORE_MS)
  }

  function renderSelection(): void {
    selection.clear()

    if (!selectedTileId) {
      return
    }

    const tile = gameMap.tiles.find((item) => item.id === selectedTileId)

    if (!tile) {
      return
    }

    const world = tileToWorld(tile, { hexRadius: HEX_RADIUS })
    const points = getHexPolygonPoints(world, HEX_RADIUS - 3)

    selection
      .poly(points.flatMap((point) => [point.x, point.y]))
      .stroke({ color: mapVisualTheme.selection.stroke, width: mapVisualTheme.selection.width })
  }

  function applyCamera(): void {
    const state = camera.getState()

    mapLayer.x = state.x
    mapLayer.y = state.y
    mapLayer.scale.set(state.zoom)
  }

  function calculateStats(): PixiStageStats {
    const cameraState = camera.getState()
    const activeRect = getActiveTileRect()
    const chunkStats = calculateChunkStats(activeRect, CHUNK_SIZE)

    return {
      width: app.renderer.width,
      height: app.renderer.height,
      tileCount: gameMap.tiles.length,
      activeTileCount: activeRect.count,
      activeChunkCount: chunkStats.activeChunkCount,
      allocatedTileGraphics: tilePool.getStats().allocatedTileGraphics,
      cameraX: Math.round(cameraState.x),
      cameraY: Math.round(cameraState.y),
      zoom: Number(cameraState.zoom.toFixed(2)),
      p95FrameMs: Number(latestTrace.p95FrameMs.toFixed(2)),
      selectedTileId,
      fogVisibleTileCount: currentExploration?.visibleTileIds.length ?? 0,
      fogExploredTileCount: currentExploration?.exploredTileIds.length ?? 0,
    }
  }

  function publishStats(): PixiStageStats {
    const stats = calculateStats()

    if (isPerfTraceActive) {
      return stats
    }

    queuedStats = stats

    if (statsFrame === 0) {
      statsFrame = requestAnimationFrame(() => {
        statsFrame = 0

        if (queuedStats) {
          options.onStats?.(queuedStats)
          queuedStats = null
        }
      })
    }

    return stats
  }

  function resetMap(scenarioId: PerfScenarioId): void {
    const mapSizeByScenario: Record<PerfScenarioId, number> = {
      'default-16': 16,
      'perf-stress-20': 20,
      'perf-stress-32': 32,
      'perf-stress-64': 64,
    }

    const mapSize = mapSizeByScenario[scenarioId]
    const worldSize = getHexMapWorldSize(mapSize, mapSize, { hexRadius: HEX_RADIUS })

    gameMap = createFixedMap(mapSize, mapSize, DEFAULT_SEED)
    currentExploration = null
    visualEntities = emptyVisualEntities
    restoreFogAfterCameraMove()

    camera.setBounds({
      viewportWidth: app.renderer.width,
      viewportHeight: app.renderer.height,
      mapWidth: gameMap.width,
      mapHeight: gameMap.height,
      tileSize: TILE_SIZE,
      worldHeight: worldSize.height,
      worldWidth: worldSize.width,
      padding: CAMERA_PADDING,
    })
    selectedTileId = null
    renderMap(gameMap)
    applyCamera()
    publishStats()
  }

  function setExploration(exploration: PixiExplorationSnapshot | null): void {
    currentExploration = exploration
    renderFog()
    publishStats()
  }

  function setVisualEntities(entities: PixiVisualEntities): void {
    visualEntities = entities
    renderVisualEntities()
    publishStats()
  }

  function selectTile(tileId: string): void {
    if (!gameMap.tiles.some((tile) => tile.id === tileId)) {
      return
    }

    selectedTileId = tileId
    renderSelection()
    publishStats()
  }

  renderMap(gameMap)
  applyCamera()

  let isDragging = false
  let lastPointer = { x: 0, y: 0 }

  function onPointerDown(event: PointerEvent): void {
    isDragging = true
    lastPointer = { x: event.clientX, y: event.clientY }
  }

  function onPointerMove(event: PointerEvent): void {
    if (!isDragging) {
      return
    }

    camera.panBy(event.clientX - lastPointer.x, event.clientY - lastPointer.y)
    lastPointer = { x: event.clientX, y: event.clientY }
    pauseFogDuringCameraMove()
    applyCamera()
    publishStats()
  }

  function onPointerUp(): void {
    isDragging = false
    restoreFogAfterCameraMove()
  }

  function onWheel(event: WheelEvent): void {
    event.preventDefault()
    const rect = app.canvas.getBoundingClientRect()

    camera.zoomBy(event.deltaY < 0 ? 0.08 : -0.08, {
      x: event.clientX - rect.left,
      y: event.clientY - rect.top,
    })
    applyCamera()
    publishStats()
  }

  function onClick(event: MouseEvent): void {
    const rect = app.canvas.getBoundingClientRect()
    const world = camera.screenToWorld({
      x: event.clientX - rect.left,
      y: event.clientY - rect.top,
    })
    const tile = worldToTile(world, { hexRadius: HEX_RADIUS })

    if (tile.x >= 0 && tile.x < gameMap.width && tile.y >= 0 && tile.y < gameMap.height) {
      selectedTileId = `tile:${tile.x}:${tile.y}`
      renderSelection()
      publishStats()
      options.onTileSelect?.(selectedTileId)
    }
  }

  app.canvas.addEventListener('pointerdown', onPointerDown)
  app.canvas.addEventListener('pointermove', onPointerMove)
  app.canvas.addEventListener('pointerup', onPointerUp)
  app.canvas.addEventListener('pointerleave', onPointerUp)
  app.canvas.addEventListener('pointercancel', onPointerUp)
  app.canvas.addEventListener('wheel', onWheel, { passive: false })
  app.canvas.addEventListener('click', onClick)

  app.ticker.add(() => {
    sampler.sample(performance.now())
  })

  const civPerfApi: CivPerfApi = {
    loadScenario: resetMap,
    setExploration,
    startTrace: (label: string) => {
      isPerfTraceActive = true
      sampler.start(label)
    },
    stopTrace: () => {
      latestTrace = sampler.stop()
      isPerfTraceActive = false
      publishStats()
      return latestTrace
    },
    dragCamera: (deltaX: number, deltaY: number, steps = 1) => {
      for (let index = 0; index < steps; index += 1) {
        camera.panBy(deltaX / steps, deltaY / steps)
      }

      pauseFogDuringCameraMove()
      applyCamera()
      publishStats()
    },
    zoomCamera: (delta: number, steps = 1) => {
      const anchor = {
        x: app.renderer.width / 2,
        y: app.renderer.height / 2,
      }

      for (let index = 0; index < steps; index += 1) {
        camera.zoomBy(delta / steps, anchor)
      }

      applyCamera()
      publishStats()
    },
    getStats: publishStats,
  }

  installCivPerfApi(civPerfApi)

  const initialStats = publishStats()

  return {
    stats: initialStats,
    selectTile,
    setExploration,
    setVisualEntities,
    destroy: () => {
      app.canvas.removeEventListener('pointerdown', onPointerDown)
      app.canvas.removeEventListener('pointermove', onPointerMove)
      app.canvas.removeEventListener('pointerup', onPointerUp)
      app.canvas.removeEventListener('pointerleave', onPointerUp)
      app.canvas.removeEventListener('pointercancel', onPointerUp)
      app.canvas.removeEventListener('wheel', onWheel)
      app.canvas.removeEventListener('click', onClick)
      cancelAnimationFrame(statsFrame)
      if (fogRestoreTimer !== 0) {
        window.clearTimeout(fogRestoreTimer)
      }
      if (window.__civPerf === civPerfApi) {
        delete window.__civPerf
        delete document.documentElement.dataset.civPerf
      }
      app.canvas.remove()
      app.destroy(true, { children: true })
    },
  }
}

function drawCityMarker(graphics: Graphics, city: PixiVisualCity): void {
  const tile = parseTileId(city.tileId)

  if (!tile) {
    return
  }

  const center = tileToWorld(tile, { hexRadius: HEX_RADIUS })
  const style = getCityVisualStyle(city.owner)
  const baseY = center.y + 4

  graphics
    .poly([
      center.x - 9,
      baseY,
      center.x,
      baseY - 9,
      center.x + 9,
      baseY,
      center.x + 9,
      baseY + 9,
      center.x - 9,
      baseY + 9,
    ])
    .fill(style.fill)
    .stroke({ color: style.stroke, width: 1.5 })
    .poly([
      center.x - 11,
      baseY,
      center.x,
      baseY - 11,
      center.x + 11,
      baseY,
    ])
    .fill(style.roof)
    .stroke({ color: style.stroke, width: 1.5 })
}

function drawUnitMarker(graphics: Graphics, unit: PixiVisualUnit): void {
  const tile = parseTileId(unit.tileId)

  if (!tile) {
    return
  }

  const center = tileToWorld(tile, { hexRadius: HEX_RADIUS })
  const style = getUnitVisualStyle(unit.owner)
  const kind = getUnitVisualKind(unit.typeId)
  const x = center.x
  const y = center.y - 5

  graphics.circle(x, y, 9).fill(style.fill).stroke({ color: style.stroke, width: 2 })

  if (kind === 'scout') {
    graphics
      .circle(x, y, 4)
      .stroke({ color: style.detail, width: 1.5 })
      .circle(x, y, 1.4)
      .fill(style.detail)
    return
  }

  if (kind === 'warrior') {
    graphics
      .poly([x - 5, y - 4, x + 5, y - 4, x + 4, y + 3, x, y + 7, x - 4, y + 3])
      .fill(style.detail)
    return
  }

  if (kind === 'settler') {
    graphics
      .moveTo(x - 3, y + 5)
      .lineTo(x - 3, y - 6)
      .stroke({ color: style.detail, width: 1.5 })
      .poly([x - 2, y - 6, x + 6, y - 3, x - 2, y])
      .fill(style.detail)
    return
  }

  graphics
    .moveTo(x - 4, y - 4)
    .lineTo(x + 4, y + 4)
    .moveTo(x + 4, y - 4)
    .lineTo(x - 4, y + 4)
    .stroke({ color: style.detail, width: 1.5 })
}

function drawBuildHint(graphics: Graphics, hint: PixiVisualBuildHint): void {
  const tile = parseTileId(hint.tileId)

  if (!tile) {
    return
  }

  const center = tileToWorld(tile, { hexRadius: HEX_RADIUS })
  const points = getHexPolygonPoints(center, HEX_RADIUS - 6)
  const style = hint.kind === 'objective'
    ? mapVisualTheme.objectiveHint
    : mapVisualTheme.buildHint

  graphics
    .poly(points.flatMap((point) => [point.x, point.y]))
    .fill({ alpha: style.fillAlpha, color: style.fill })
    .stroke({
      alpha: style.strokeAlpha,
      color: style.stroke,
      width: 2,
    })

  if (hint.kind === 'citySite') {
    graphics
      .moveTo(center.x - 4, center.y + 7)
      .lineTo(center.x - 4, center.y - 7)
      .stroke({ color: mapVisualTheme.buildHint.stroke, width: 1.5 })
      .poly([center.x - 3, center.y - 7, center.x + 7, center.y - 3, center.x - 3, center.y + 1])
      .fill(mapVisualTheme.buildHint.stroke)
  }

  if (hint.kind === 'objective') {
    graphics
      .circle(center.x, center.y, 6)
      .stroke({ color: mapVisualTheme.objectiveHint.stroke, width: 2 })
      .moveTo(center.x - 10, center.y)
      .lineTo(center.x + 10, center.y)
      .moveTo(center.x, center.y - 10)
      .lineTo(center.x, center.y + 10)
      .stroke({ color: mapVisualTheme.objectiveHint.stroke, width: 1.5 })
  }
}

function getAverageTerrainColor(
  map: GameMap,
  terrainByTileId: Map<string, TerrainVisualStyle>,
): string {
  if (map.tiles.length === 0) {
    return colorToHex(mapVisualTheme.background)
  }

  const total = map.tiles.reduce(
    (sum, tile) => {
      const terrain = getTerrainConfig(tile.terrainId)
      const visual = terrainByTileId.get(tile.id) ?? getTerrainVisualStyle(tile.terrainId, terrain.color)
      const color = splitColor(visual.fill)

      return {
        b: sum.b + color.b,
        g: sum.g + color.g,
        r: sum.r + color.r,
      }
    },
    { b: 0, g: 0, r: 0 },
  )

  return colorToHex(joinColor({
    b: Math.round(total.b / map.tiles.length),
    g: Math.round(total.g / map.tiles.length),
    r: Math.round(total.r / map.tiles.length),
  }))
}

function drawTerrainBlend(
  context: CanvasRenderingContext2D,
  center: { x: number; y: number },
  visual: TerrainVisualStyle,
): void {
  const radius = TERRAIN_BLEND_RADIUS + visual.elevation * 2
  const gradient = context.createRadialGradient(
    center.x,
    center.y,
    HEX_RADIUS * 0.08,
    center.x,
    center.y,
    radius,
  )

  gradient.addColorStop(0, colorToRgba(visual.fill, 0.82))
  gradient.addColorStop(0.48, colorToRgba(visual.fill, 0.56))
  gradient.addColorStop(0.86, colorToRgba(visual.transition, 0.16))
  gradient.addColorStop(1, colorToRgba(visual.transition, 0))

  context.fillStyle = gradient
  context.beginPath()
  context.arc(center.x, center.y, radius, 0, Math.PI * 2)
  context.fill()
}

function colorToHex(color: number): string {
  return `#${color.toString(16).padStart(6, '0')}`
}

function colorToRgba(color: number, alpha: number): string {
  const channels = splitColor(color)

  return `rgba(${channels.r}, ${channels.g}, ${channels.b}, ${alpha})`
}

function splitColor(color: number): { b: number; g: number; r: number } {
  return {
    b: color & 0xff,
    g: (color >> 8) & 0xff,
    r: (color >> 16) & 0xff,
  }
}

function joinColor(color: { b: number; g: number; r: number }): number {
  return (color.r << 16) | (color.g << 8) | color.b
}

function fillFogTile(context: CanvasRenderingContext2D, x: number, y: number): void {
  drawFogHex(context, x, y, 'fill')
}

function clearFogTile(context: CanvasRenderingContext2D, x: number, y: number): void {
  drawFogHex(context, x, y, 'clear')
}

function drawFogHex(context: CanvasRenderingContext2D, x: number, y: number, mode: 'clear' | 'fill'): void {
  const center = tileToWorld({ x, y }, { hexRadius: HEX_RADIUS })
  const points = getHexPolygonPoints(center, HEX_RADIUS)

  context.beginPath()
  points.forEach((point, index) => {
    const scaledX = point.x * FOG_TEXTURE_SCALE
    const scaledY = point.y * FOG_TEXTURE_SCALE

    if (index === 0) {
      context.moveTo(scaledX, scaledY)
    } else {
      context.lineTo(scaledX, scaledY)
    }
  })
  context.closePath()

  if (mode === 'clear') {
    context.save()
    context.clip()
    context.clearRect(
      (center.x - TILE_SIZE / 2) * FOG_TEXTURE_SCALE,
      (center.y - HEX_RADIUS) * FOG_TEXTURE_SCALE,
      TILE_SIZE * FOG_TEXTURE_SCALE,
      HEX_RADIUS * 2 * FOG_TEXTURE_SCALE,
    )
    context.restore()
  } else {
    context.fill()
  }
}

function parseTileId(tileId: string): { x: number; y: number } | null {
  const [, xValue, yValue] = tileId.split(':')
  const x = Number(xValue)
  const y = Number(yValue)

  if (!Number.isInteger(x) || !Number.isInteger(y) || x < 0 || y < 0) {
    return null
  }

  return { x, y }
}
