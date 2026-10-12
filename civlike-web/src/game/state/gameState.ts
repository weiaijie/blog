import type { CommandLog } from '../commands/ruleCommand'
import { getUnitConfig, type UnitId } from '../config/unit'
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
  hp: number
  id: string
  maxHp: number
  ownerId: string
  tileId: string
  typeId: UnitId
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
  scenarioId: ScenarioId
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

export type ScenarioId = 'combat:adjacent-enemy' | 'default'

export type TurnPhase =
  | 'AI_ACTION'
  | 'AI_PLAN'
  | 'AUTOSAVE'
  | 'NEXT_TURN'
  | 'PLAYER_ACTION'
  | 'PLAYER_END'
  | 'TURN_RESOLVE'
  | 'WORLD_RESOLVE'

export function createInitialGameState(
  seed: number,
  options: {
    scenarioId?: ScenarioId
  } = {},
): GameState {
  const scenarioId = options.scenarioId ?? 'default'
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
    scenarioId,
    schemaVersion: 1,
    seed,
    turn: 1,
    turnPhase: 'PLAYER_ACTION',
    turnTrace: [],
    units: createInitialUnits({ aiPlayerId: aiPlayer.id, humanPlayerId: humanPlayer.id, scenarioId }),
    explorationByPlayerId: {},
  }

  return {
    ...state,
    explorationByPlayerId: createInitialExploration(state),
  }
}

function createInitialUnits(params: {
  aiPlayerId: string
  humanPlayerId: string
  scenarioId: ScenarioId
}): UnitState[] {
  if (params.scenarioId === 'combat:adjacent-enemy') {
    return [
      createUnitState({
        id: 'unit:warrior:scenario:1',
        ownerId: params.humanPlayerId,
        tileId: 'tile:8:9',
        typeId: 'unit:warrior',
      }),
      createUnitState({
        id: 'unit:enemy:scout:1',
        ownerId: params.aiPlayerId,
        tileId: 'tile:8:10',
        typeId: 'unit:scout',
      }),
    ]
  }

  return [
    createUnitState({
      id: 'unit:scout:1',
      ownerId: params.humanPlayerId,
      tileId: 'tile:8:9',
      typeId: 'unit:scout',
    }),
  ]
}

export function createUnitState(params: {
  id: string
  ownerId: string
  tileId: string
  typeId: UnitId
}): UnitState {
  const unitConfig = getUnitConfig(params.typeId)

  if (!unitConfig) {
    throw new Error(`Unknown unit type: ${params.typeId}`)
  }

  return {
    hp: unitConfig.maxHp,
    id: params.id,
    maxHp: unitConfig.maxHp,
    ownerId: params.ownerId,
    tileId: params.tileId,
    typeId: params.typeId,
  }
}
