export type HexPoint = {
  x: number
  y: number
}

export function areHexNeighbors(first: HexPoint, second: HexPoint): boolean {
  return getHexDistance(first, second) === 1
}

export function getHexDistance(first: HexPoint, second: HexPoint): number {
  const firstCube = oddRowOffsetToCube(first)
  const secondCube = oddRowOffsetToCube(second)

  return Math.max(
    Math.abs(firstCube.x - secondCube.x),
    Math.abs(firstCube.y - secondCube.y),
    Math.abs(firstCube.z - secondCube.z),
  )
}

function oddRowOffsetToCube(point: HexPoint): { x: number; y: number; z: number } {
  const x = point.x - (point.y - (point.y & 1)) / 2
  const z = point.y
  const y = -x - z

  return { x, y, z }
}
