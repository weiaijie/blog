import type { CameraState } from '../camera/cameraController'
import { getHexMapWorldSize, tileToWorld } from '../coordinates/hexCoordinates'

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
  hexRadius: number
}

export function calculateActiveTileRect(input: ViewportInput): ActiveTileRect {
  const hexRadius = input.hexRadius
  const worldSize = getHexMapWorldSize(input.mapWidth, input.mapHeight, { hexRadius })
  const worldLeft = Math.max(0, -input.camera.x / input.camera.zoom)
  const worldTop = Math.max(0, -input.camera.y / input.camera.zoom)
  const worldRight = Math.min(worldSize.width, (input.viewportWidth - input.camera.x) / input.camera.zoom)
  const worldBottom = Math.min(worldSize.height, (input.viewportHeight - input.camera.y) / input.camera.zoom)
  let minX = input.mapWidth
  let minY = input.mapHeight
  let maxX = 0
  let maxY = 0
  let count = 0

  for (let y = 0; y < input.mapHeight; y += 1) {
    for (let x = 0; x < input.mapWidth; x += 1) {
      const center = tileToWorld({ x, y }, { hexRadius })

      if (
        center.x + hexRadius < worldLeft ||
        center.x - hexRadius > worldRight ||
        center.y + hexRadius < worldTop ||
        center.y - hexRadius > worldBottom
      ) {
        continue
      }

      minX = Math.min(minX, x)
      minY = Math.min(minY, y)
      maxX = Math.max(maxX, x + 1)
      maxY = Math.max(maxY, y + 1)
      count += 1
    }
  }

  if (count === 0) {
    return { minX: 0, minY: 0, maxX: 0, maxY: 0, count: 0 }
  }

  return { minX, minY, maxX, maxY, count }
}
