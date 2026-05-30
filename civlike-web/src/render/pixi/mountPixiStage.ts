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
import { tileToWorld, worldToTile } from '../coordinates/squareCoordinates'

const TILE_SIZE = 40
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
  setExploration: (exploration: PixiExplorationSnapshot | null) => void
  destroy: () => void
}

export type PixiExplorationSnapshot = PerfExplorationSnapshot

export type MountPixiStageOptions = {
  initialExploration?: PixiExplorationSnapshot | null
  onTileSelect?: (tileId: string) => void
  onStats?: (stats: PixiStageStats) => void
}

export async function mountPixiStage(
  host: HTMLElement,
  options: MountPixiStageOptions = {},
): Promise<PixiStageHandle> {
  const app = new Application()

  await app.init({
    resizeTo: host,
    backgroundColor: 0x182027,
    antialias: false,
  })

  host.appendChild(app.canvas)

  const mapLayer = new Container()
  const grid = new Graphics()
  const selection = new Graphics()
  const tilePool = new TilePool()
  const sampler = new PerformanceSampler()
  let gameMap = createFixedMap(16, 16, DEFAULT_SEED)
  let currentExploration = options.initialExploration ?? null
  let selectedTileId: string | null = null
  let latestTrace = sampler.stop()
  let queuedStats: PixiStageStats | null = null
  let statsFrame = 0
  let fogRestoreTimer = 0
  let isFogPanSuppressed = false
  const camera = new CameraController({
    viewportWidth: app.renderer.width,
    viewportHeight: app.renderer.height,
    mapWidth: gameMap.width,
    mapHeight: gameMap.height,
    tileSize: TILE_SIZE,
    padding: CAMERA_PADDING,
  })
  const fogCanvas = document.createElement('canvas')
  const fogContext = fogCanvas.getContext('2d')
  const fogTexture = Texture.from(fogCanvas)
  const fogSprite = new Sprite(fogTexture)

  mapLayer.addChild(grid)
  mapLayer.addChild(fogSprite)
  mapLayer.addChild(selection)
  app.stage.addChild(mapLayer)

  function renderMap(map: GameMap): void {
    grid.clear()

    for (const tile of map.tiles) {
      const terrain = getTerrainConfig(tile.terrainId)
      const world = tileToWorld(tile, { tileSize: TILE_SIZE })

      grid.rect(world.x, world.y, TILE_SIZE - 1, TILE_SIZE - 1).fill(terrain.color)
    }

    tilePool.setAllocatedTileGraphics(map.tiles.length)
    renderFog()
    renderSelection()
  }

  function getActiveTileRect() {
    const cameraState = camera.getState()

    return calculateActiveTileRect({
      camera: cameraState,
      viewportWidth: app.renderer.width,
      viewportHeight: app.renderer.height,
      mapWidth: gameMap.width,
      mapHeight: gameMap.height,
      tileSize: TILE_SIZE,
    })
  }

  function renderFog(): void {
    if (!fogContext) {
      return
    }

    const width = gameMap.width * TILE_SIZE
    const height = gameMap.height * TILE_SIZE
    const textureWidth = Math.ceil(width * FOG_TEXTURE_SCALE)
    const textureHeight = Math.ceil(height * FOG_TEXTURE_SCALE)
    fogTexture.source.scaleMode = gameMap.width >= 32 ? 'nearest' : 'linear'

    if (fogCanvas.width !== textureWidth || fogCanvas.height !== textureHeight) {
      fogCanvas.width = textureWidth
      fogCanvas.height = textureHeight
      fogContext.imageSmoothingEnabled = false
      fogTexture.source.resize(textureWidth, textureHeight)
      fogSprite.width = width
      fogSprite.height = height
    }

    fogContext.clearRect(0, 0, textureWidth, textureHeight)

    if (!currentExploration) {
      updateFogVisibility()
      fogTexture.source.update()
      return
    }

    updateFogVisibility()
    fogContext.fillStyle = 'rgba(6, 16, 20, 0.72)'
    fogContext.fillRect(0, 0, textureWidth, textureHeight)

    fogContext.globalCompositeOperation = 'copy'
    fogContext.fillStyle = 'rgba(6, 16, 20, 0.32)'

    for (const tileId of currentExploration.exploredTileIds) {
      const tile = parseTileId(tileId)

      if (tile && tile.x < gameMap.width && tile.y < gameMap.height) {
        fillFogTile(fogContext, tile.x, tile.y)
      }
    }

    fogContext.globalCompositeOperation = 'source-over'

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

    const world = tileToWorld(tile, { tileSize: TILE_SIZE })

    selection
      .rect(world.x + 2, world.y + 2, TILE_SIZE - 5, TILE_SIZE - 5)
      .stroke({ color: 0xfff0a3, width: 3 })
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

    gameMap = createFixedMap(mapSize, mapSize, DEFAULT_SEED)
    currentExploration = null
    restoreFogAfterCameraMove()

    camera.setBounds({
      viewportWidth: app.renderer.width,
      viewportHeight: app.renderer.height,
      mapWidth: gameMap.width,
      mapHeight: gameMap.height,
      tileSize: TILE_SIZE,
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
    const tile = worldToTile(world, { tileSize: TILE_SIZE })

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
      sampler.start(label)
    },
    stopTrace: () => {
      latestTrace = sampler.stop()
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
    setExploration,
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
      app.destroy(true, { children: true })
    },
  }
}

function fillFogTile(context: CanvasRenderingContext2D, x: number, y: number): void {
  const left = Math.floor(x * TILE_SIZE * FOG_TEXTURE_SCALE)
  const top = Math.floor(y * TILE_SIZE * FOG_TEXTURE_SCALE)
  const size = Math.max(1, Math.ceil((TILE_SIZE - 1) * FOG_TEXTURE_SCALE))

  context.fillRect(left, top, size, size)
}

function clearFogTile(context: CanvasRenderingContext2D, x: number, y: number): void {
  const left = Math.floor(x * TILE_SIZE * FOG_TEXTURE_SCALE)
  const top = Math.floor(y * TILE_SIZE * FOG_TEXTURE_SCALE)
  const size = Math.max(1, Math.ceil((TILE_SIZE - 1) * FOG_TEXTURE_SCALE))

  context.clearRect(left, top, size, size)
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
