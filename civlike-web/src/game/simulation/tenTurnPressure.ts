import type { RuleCommand } from '../commands/ruleCommand'
import { createInitialGameState, type GameState } from '../state/gameState'
import { hashGameState } from '../state/hashGameState'
import { replayCommandLog } from './replayCommands'
import { applyRuleCommand } from './applyRuleCommand'

export type TurnPressureSummary = {
  capitalProductionId: string | null
  capitalProgress: number
  commandCount: number
  completedTechs: string[]
  foodStockpile: number
  hash: string
  replayHash: string
  scienceProgress: number
  turn: number
  unitCount: number
}

export function runTenTurnPressure(seed: number): TurnPressureSummary {
  return runFixedTurnPressure(seed, 10)
}

export function runThirtyTurnPressure(seed: number): TurnPressureSummary {
  return runFixedTurnPressure(seed, 30)
}

export function runFixedTurnPressure(seed: number, turnCount: number): TurnPressureSummary {
  const state = runFixedTurnPressureState(seed, turnCount)
  const replayed = replayCommandLog(seed, state.commandLog)
  const capital = state.cities.find((city) => city.id === 'city:capital')
  const human = state.players.find((player) => player.id === 'player:human')

  return {
    capitalProductionId: capital?.productionId ?? null,
    capitalProgress: capital?.productionProgress ?? 0,
    commandCount: state.commandLog.length,
    completedTechs: state.completedTechByPlayerId['player:human'],
    foodStockpile: human?.foodStockpile ?? 0,
    hash: hashGameState(state),
    replayHash: hashGameState(replayed),
    scienceProgress: human?.scienceProgress ?? 0,
    turn: state.turn,
    unitCount: state.units.length,
  }
}

export function runTenTurnPressureState(seed: number): GameState {
  return runFixedTurnPressureState(seed, 10)
}

export function runFixedTurnPressureState(seed: number, turnCount: number): GameState {
  return createTurnPressureCommands(turnCount).reduce(
    (state, command) => applyRuleCommand(state, command),
    createInitialGameState(seed),
  )
}

function createTurnPressureCommands(turnCount: number): RuleCommand[] {
  return [
    {
      playerId: 'player:human',
      techId: 'tech:mining',
      type: 'CHOOSE_TECH',
    },
    {
      cityId: 'city:capital',
      playerId: 'player:human',
      productionId: 'unit:scout',
      type: 'SET_PRODUCTION',
    },
    ...Array.from({ length: turnCount }, () => ({
      playerId: 'player:human',
      type: 'END_TURN' as const,
    })),
  ]
}
