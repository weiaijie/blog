export type TilePoint = {
  x: number
  y: number
}

export type WorldPoint = {
  x: number
  y: number
}

export type SquareCoordinateOptions = {
  tileSize: number
}

export function tileToWorld(tile: TilePoint, options: SquareCoordinateOptions): WorldPoint {
  return {
    x: tile.x * options.tileSize,
    y: tile.y * options.tileSize,
  }
}

export function worldToTile(world: WorldPoint, options: SquareCoordinateOptions): TilePoint {
  return {
    x: Math.floor(world.x / options.tileSize),
    y: Math.floor(world.y / options.tileSize),
  }
}
