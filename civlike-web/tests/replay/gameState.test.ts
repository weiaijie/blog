import { describe, expect, it } from 'vitest'
import { applyRuleCommand } from '../../src/game/simulation/applyRuleCommand'
import { createInitialGameState } from '../../src/game/state/gameState'
import { hashGameState } from '../../src/game/state/hashGameState'

describe('GameState replay baseline', () => {
  it('creates deterministic initial state from the same seed', () => {
    expect(createInitialGameState(1001)).toEqual(createInitialGameState(1001))
  })

  it('produces the same hash for the same command sequence', () => {
    const first = runTwoTurns(1001)
    const second = runTwoTurns(1001)

    expect(hashGameState(first)).toBe(hashGameState(second))
    expect(first.turn).toBe(3)
    expect(first.commandLog).toHaveLength(2)
  })
})

function runTwoTurns(seed: number) {
  let state = createInitialGameState(seed)

  state = applyRuleCommand(state, { playerId: 'player:human', type: 'END_TURN' })
  state = applyRuleCommand(state, { playerId: 'player:human', type: 'END_TURN' })

  return state
}
