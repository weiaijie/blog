export type TilePoint = {
  x: number
  y: number
}

export type WorldPoint = {
  x: number
  y: number
}

export type HexCoordinateOptions = {
  hexRadius: number
}

export function getHexMetrics(hexRadius: number): {
  height: number
  horizontalSpacing: number
  verticalSpacing: number
  width: number
} {
  return {
    height: hexRadius * 2,
    horizontalSpacing: Math.sqrt(3) * hexRadius,
    verticalSpacing: hexRadius * 1.5,
    width: Math.sqrt(3) * hexRadius,
  }
}

export function getHexMapWorldSize(
  width: number,
  height: number,
  options: HexCoordinateOptions,
): { width: number; height: number } {
  const metrics = getHexMetrics(options.hexRadius)

  return {
    height: metrics.height + Math.max(0, height - 1) * metrics.verticalSpacing,
    width: metrics.width * width + metrics.width / 2,
  }
}

export function tileToWorld(tile: TilePoint, options: HexCoordinateOptions): WorldPoint {
  const metrics = getHexMetrics(options.hexRadius)

  return {
    x: metrics.width / 2 + tile.x * metrics.horizontalSpacing + (tile.y % 2) * (metrics.width / 2),
    y: options.hexRadius + tile.y * metrics.verticalSpacing,
  }
}

export function worldToTile(world: WorldPoint, options: HexCoordinateOptions): TilePoint {
  const metrics = getHexMetrics(options.hexRadius)
  const approximateY = Math.round((world.y - options.hexRadius) / metrics.verticalSpacing)
  let bestTile: TilePoint | null = null
  let bestDistance = Number.POSITIVE_INFINITY

  for (let y = approximateY - 2; y <= approximateY + 2; y += 1) {
    const rowOffset = (y % 2) * (metrics.width / 2)
    const approximateX = Math.round((world.x - metrics.width / 2 - rowOffset) / metrics.horizontalSpacing)

    for (let x = approximateX - 2; x <= approximateX + 2; x += 1) {
      const center = tileToWorld({ x, y }, options)
      const distance = Math.hypot(world.x - center.x, world.y - center.y)

      if (isPointInHex(world, center, options.hexRadius)) {
        return { x, y }
      }

      if (distance < bestDistance) {
        bestDistance = distance
        bestTile = { x, y }
      }
    }
  }

  return bestTile ?? { x: 0, y: 0 }
}

export function getHexPolygonPoints(center: WorldPoint, hexRadius: number): WorldPoint[] {
  return Array.from({ length: 6 }, (_, index) => {
    const angle = (-90 + index * 60) * (Math.PI / 180)

    return {
      x: center.x + Math.cos(angle) * hexRadius,
      y: center.y + Math.sin(angle) * hexRadius,
    }
  })
}

function isPointInHex(point: WorldPoint, center: WorldPoint, hexRadius: number): boolean {
  const points = getHexPolygonPoints(center, hexRadius)
  let inside = false

  for (let index = 0, previous = points.length - 1; index < points.length; previous = index, index += 1) {
    const currentPoint = points[index]
    const previousPoint = points[previous]
    const intersects =
      currentPoint.y > point.y !== previousPoint.y > point.y &&
      point.x <
        ((previousPoint.x - currentPoint.x) * (point.y - currentPoint.y)) /
          (previousPoint.y - currentPoint.y) +
          currentPoint.x

    if (intersects) {
      inside = !inside
    }
  }

  return inside
}
