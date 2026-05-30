import type { CameraState } from '../camera/cameraController'

export type ActiveTileRect = {
  minX: number
  minY: number
  maxX: number
  maxY: number
  count: number
}

export type ViewportInput = {
  camera: CameraState
  viewportWidth: number
  viewportHeight: number
  mapWidth: number
  mapHeight: number
  tileSize: number
}

export function calculateActiveTileRect(input: ViewportInput): ActiveTileRect {
  const worldLeft = Math.max(0, -input.camera.x / input.camera.zoom)
  const worldTop = Math.max(0, -input.camera.y / input.camera.zoom)
  const worldRight = Math.min(
    input.mapWidth * input.tileSize,
    (input.viewportWidth - input.camera.x) / input.camera.zoom,
  )
  const worldBottom = Math.min(
    input.mapHeight * input.tileSize,
    (input.viewportHeight - input.camera.y) / input.camera.zoom,
  )
  const minX = clampTile(Math.floor(worldLeft / input.tileSize), input.mapWidth)
  const minY = clampTile(Math.floor(worldTop / input.tileSize), input.mapHeight)
  const maxX = clampTile(Math.ceil(worldRight / input.tileSize), input.mapWidth)
  const maxY = clampTile(Math.ceil(worldBottom / input.tileSize), input.mapHeight)
  const count = Math.max(0, maxX - minX) * Math.max(0, maxY - minY)

  return { minX, minY, maxX, maxY, count }
}

function clampTile(value: number, max: number): number {
  return Math.min(max, Math.max(0, value))
}
