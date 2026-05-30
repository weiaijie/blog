import type { WorldPoint } from '../coordinates/hexCoordinates'

export type CameraState = {
  x: number
  y: number
  zoom: number
}

export type CameraBounds = {
  viewportHeight: number
  viewportWidth: number
  worldHeight?: number
  worldWidth?: number
  mapWidth: number
  mapHeight: number
  tileSize: number
  padding: number
}

const MIN_ZOOM = 0.65
const MAX_ZOOM = 2

export class CameraController {
  private state: CameraState
  private bounds: CameraBounds

  constructor(bounds: CameraBounds) {
    this.bounds = bounds
    this.state = {
      x: bounds.padding,
      y: bounds.padding,
      zoom: 1,
    }
  }

  getState(): CameraState {
    return { ...this.state }
  }

  setBounds(bounds: CameraBounds): CameraState {
    this.bounds = bounds
    return this.clamp()
  }

  panBy(deltaX: number, deltaY: number): CameraState {
    this.state.x += deltaX
    this.state.y += deltaY
    return this.clamp()
  }

  zoomBy(delta: number, anchor: WorldPoint): CameraState {
    const previousZoom = this.state.zoom
    const nextZoom = clampNumber(previousZoom + delta, MIN_ZOOM, MAX_ZOOM)
    const worldX = (anchor.x - this.state.x) / previousZoom
    const worldY = (anchor.y - this.state.y) / previousZoom

    this.state.zoom = nextZoom
    this.state.x = anchor.x - worldX * nextZoom
    this.state.y = anchor.y - worldY * nextZoom

    return this.clamp()
  }

  screenToWorld(point: WorldPoint): WorldPoint {
    return {
      x: (point.x - this.state.x) / this.state.zoom,
      y: (point.y - this.state.y) / this.state.zoom,
    }
  }

  private clamp(): CameraState {
    const worldWidth =
      (this.bounds.worldWidth ?? this.bounds.mapWidth * this.bounds.tileSize) * this.state.zoom
    const worldHeight =
      (this.bounds.worldHeight ?? this.bounds.mapHeight * this.bounds.tileSize) * this.state.zoom
    const minX = Math.min(this.bounds.padding, this.bounds.viewportWidth - worldWidth - this.bounds.padding)
    const minY = Math.min(this.bounds.padding, this.bounds.viewportHeight - worldHeight - this.bounds.padding)

    this.state.x = clampNumber(this.state.x, minX, this.bounds.padding)
    this.state.y = clampNumber(this.state.y, minY, this.bounds.padding)

    return this.getState()
  }
}

function clampNumber(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value))
}
