import { getTerrainConfig } from '../config/terrain'
import { getUnitConfig } from '../config/unit'
import type { CityState, GameState } from '../state/gameState'
import type { MapTile } from '../state/map'
import { areHexNeighbors } from './hexGrid'

export type CityYield = {
  food: number
  production: number
  science: number
}

const cityCenterYield: CityYield = {
  food: 1,
  production: 1,
  science: 1,
}

export function getCityYield(state: GameState, city: CityState): CityYield {
  const tile = state.map.tiles.find((item) => item.id === city.tileId)

  if (!tile) {
    return cityCenterYield
  }

  const terrain = getTerrainConfig(tile.terrainId)

  return {
    food: cityCenterYield.food + terrain.food,
    production: cityCenterYield.production + terrain.production,
    science: cityCenterYield.science + terrain.science,
  }
}

export function advanceCityProduction(state: GameState): GameState {
  let nextState = state

  for (const city of state.cities) {
    nextState = advanceOneCityProduction(nextState, city.id)
  }

  return nextState
}

export function collectCityYields(state: GameState): GameState {
  return {
    ...state,
    players: state.players.map((player) => {
      const playerCities = state.cities.filter((city) => city.ownerId === player.id)
      const totalYield = playerCities.reduce(
        (sum, city) => {
          const cityYield = getCityYield(state, city)

          return {
            food: sum.food + cityYield.food,
            production: sum.production + cityYield.production,
            science: sum.science + cityYield.science,
          }
        },
        { food: 0, production: 0, science: 0 },
      )

      return {
        ...player,
        foodStockpile: player.foodStockpile + totalYield.food,
        scienceProgress: player.scienceProgress + totalYield.science,
      }
    }),
  }
}

function advanceOneCityProduction(state: GameState, cityId: string): GameState {
  const city = state.cities.find((item) => item.id === cityId)

  if (!city?.productionId) {
    return state
  }

  const unitConfig = getUnitConfig(city.productionId)
  const cityYield = getCityYield(state, city)
  const nextProgress = city.productionProgress + cityYield.production

  if (!unitConfig || nextProgress < unitConfig.productionCost) {
    return {
      ...state,
      cities: state.cities.map((item) =>
        item.id === city.id ? { ...item, productionProgress: nextProgress } : item,
      ),
    }
  }

  const spawnTileId = findUnitSpawnTileId(state, city)
  const nextUnitIndex = state.units.length + 1

  return {
    ...state,
    cities: state.cities.map((item) =>
      item.id === city.id
        ? {
            ...item,
            productionProgress: nextProgress - unitConfig.productionCost,
          }
        : item,
    ),
    units: [
      ...state.units,
      {
        id: `${city.productionId}:${nextUnitIndex}`,
        ownerId: city.ownerId,
        tileId: spawnTileId,
      },
    ],
  }
}

function findUnitSpawnTileId(state: GameState, city: CityState): string {
  const cityTile = state.map.tiles.find((tile) => tile.id === city.tileId)

  if (!cityTile) {
    return city.tileId
  }

  const candidateTiles = [
    cityTile,
    ...getAdjacentTiles(state.map.tiles, cityTile),
  ]

  return (
    candidateTiles.find(
      (tile) =>
        tile.terrainId !== 'water' &&
        !state.units.some((unit) => unit.ownerId === city.ownerId && unit.tileId === tile.id),
    )?.id ?? city.tileId
  )
}

function getAdjacentTiles(tiles: MapTile[], center: MapTile): MapTile[] {
  return tiles.filter((tile) => areHexNeighbors(tile, center))
}
