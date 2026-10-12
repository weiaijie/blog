import type { GameState, TurnPhase } from '../state/gameState'

export const endTurnPhaseOrder: TurnPhase[] = [
  'PLAYER_END',
  'AI_PLAN',
  'AI_ACTION',
  'TURN_RESOLVE',
  'WORLD_RESOLVE',
  'AUTOSAVE',
  'NEXT_TURN',
  'PLAYER_ACTION',
]

export function advanceEndTurnPhases(state: GameState): GameState {
  return {
    ...state,
    turnPhase: 'PLAYER_ACTION',
    turnTrace: [...state.turnTrace, ...endTurnPhaseOrder],
  }
}
