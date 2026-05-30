import type { CommandLog } from '../commands/ruleCommand'
import { createInitialExploration, type PlayerExploration } from '../simulation/exploration'
import { createFixedMap, type GameMap } from './map'

export type PlayerState = {
  foodStockpile: number
  id: string
  name: string
  isHuman: boolean
  scienceProgress: number
}

export type UnitState = {
  id: string
  ownerId: string
  tileId: string
}

export type CityState = {
  id: string
  ownerId: string
  tileId: string
  productionId: string | null
  productionProgress: number
}

export type GameState = {
  schemaVersion: 1
  seed: number
  turn: number
  turnPhase: TurnPhase
  turnTrace: TurnPhase[]
  activePlayerId: string
  players: PlayerState[]
  map: GameMap
  cities: CityState[]
  units: UnitState[]
  completedTechByPlayerId: Record<string, string[]>
  currentTechByPlayerId: Record<string, string | null>
  commandLog: CommandLog
  explorationByPlayerId: Record<string, PlayerExploration>
}

export type TurnPhase =
  | 'AI_ACTION'
  | 'AI_PLAN'
  | 'AUTOSAVE'
  | 'NEXT_TURN'
  | 'PLAYER_ACTION'
  | 'PLAYER_END'
  | 'TURN_RESOLVE'
  | 'WORLD_RESOLVE'

export function createInitialGameState(seed: number): GameState {
  const humanPlayer: PlayerState = {
    foodStockpile: 0,
    id: 'player:human',
    isHuman: true,
    name: 'Human',
    scienceProgress: 0,
  }
  const aiPlayer: PlayerState = {
    foodStockpile: 0,
    id: 'player:ai:1',
    isHuman: false,
    name: 'AI 1',
    scienceProgress: 0,
  }

  const state: GameState = {
    activePlayerId: humanPlayer.id,
    cities: [
      {
        id: 'city:capital',
        ownerId: humanPlayer.id,
        productionId: null,
        productionProgress: 0,
        tileId: 'tile:8:8',
      },
    ],
    commandLog: [],
    completedTechByPlayerId: {
      [aiPlayer.id]: [],
      [humanPlayer.id]: [],
    },
    currentTechByPlayerId: {
      [aiPlayer.id]: null,
      [humanPlayer.id]: null,
    },
    map: createFixedMap(16, 16, seed),
    players: [humanPlayer, aiPlayer],
    schemaVersion: 1,
    seed,
    turn: 1,
    turnPhase: 'PLAYER_ACTION',
    turnTrace: [],
    units: [
      {
        id: 'unit:scout:1',
        ownerId: humanPlayer.id,
        tileId: 'tile:8:9',
      },
    ],
    explorationByPlayerId: {},
  }

  return {
    ...state,
    explorationByPlayerId: createInitialExploration(state),
  }
}
