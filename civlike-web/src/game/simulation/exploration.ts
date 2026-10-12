import type { GameState, UnitState } from '../state/gameState'
import type { GameMap, MapTile } from '../state/map'
import { getHexDistance } from './hexGrid'

export type PlayerExploration = {
  exploredTileIds: string[]
  visibleTileIds: string[]
}

const scoutSightRange = 1

export function createInitialExploration(state: GameState): Record<string, PlayerExploration> {
  return Object.fromEntries(
    state.players.map((player) => {
      const visibleTileIds = getVisibleTileIdsForUnits(
        state.map,
        state.units.filter((unit) => unit.ownerId === player.id),
      )

      return [
        player.id,
        {
          exploredTileIds: visibleTileIds,
          visibleTileIds,
        },
      ]
    }),
  )
}

export function refreshExploration(state: GameState): GameState {
  return {
    ...state,
    explorationByPlayerId: Object.fromEntries(
      state.players.map((player) => {
        const current = state.explorationByPlayerId[player.id] ?? {
          exploredTileIds: [],
          visibleTileIds: [],
        }
        const visibleTileIds = getVisibleTileIdsForUnits(
          state.map,
          state.units.filter((unit) => unit.ownerId === player.id),
        )

        return [
          player.id,
          {
            exploredTileIds: sortTileIds([...new Set([...current.exploredTileIds, ...visibleTileIds])]),
            visibleTileIds,
          },
        ]
      }),
    ),
  }
}

function getVisibleTileIdsForUnits(map: GameMap, units: UnitState[]): string[] {
  const tileIds = units.flatMap((unit) => {
    const center = map.tiles.find((tile) => tile.id === unit.tileId)

    if (!center) {
      return []
    }

    return getVisibleTiles(map.tiles, center).map((tile) => tile.id)
  })

  return sortTileIds([...new Set(tileIds)])
}

function getVisibleTiles(tiles: MapTile[], center: MapTile): MapTile[] {
  return tiles.filter((tile) => getHexDistance(tile, center) <= scoutSightRange)
}

function sortTileIds(tileIds: string[]): string[] {
  return [...tileIds].sort((first, second) => {
    const [firstX, firstY] = parseTileId(first)
    const [secondX, secondY] = parseTileId(second)

    return firstY - secondY || firstX - secondX
  })
}

function parseTileId(tileId: string): [number, number] {
  const [, x = '0', y = '0'] = tileId.split(':')

  return [Number(x), Number(y)]
}
