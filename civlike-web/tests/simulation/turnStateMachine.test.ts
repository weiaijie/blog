import { describe, expect, it } from 'vitest'
import { applyRuleCommand } from '../../src/game/simulation/applyRuleCommand'
import { endTurnPhaseOrder } from '../../src/game/simulation/turnStateMachine'
import { createInitialGameState } from '../../src/game/state/gameState'
import { hashGameState } from '../../src/game/state/hashGameState'

describe('TurnStateMachine', () => {
  it('records the authoritative end-turn phase order', () => {
    const state = applyRuleCommand(createInitialGameState(1001), {
      playerId: 'player:human',
      type: 'END_TURN',
    })

    expect(state.turnTrace).toEqual(endTurnPhaseOrder)
    expect(state.turnPhase).toBe('PLAYER_ACTION')
    expect(state.turn).toBe(2)
  })

  it('keeps the phase trace deterministic across replay', () => {
    const first = applyRuleCommand(createInitialGameState(1001), {
      playerId: 'player:human',
      type: 'END_TURN',
    })
    const second = applyRuleCommand(createInitialGameState(1001), {
      playerId: 'player:human',
      type: 'END_TURN',
    })

    expect(hashGameState(first)).toBe(hashGameState(second))
  })
})
