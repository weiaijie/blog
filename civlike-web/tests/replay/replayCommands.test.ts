import { describe, expect, it } from 'vitest'
import type { RuleCommand } from '../../src/game/commands/ruleCommand'
import { replayCommandLog, replayCommands } from '../../src/game/simulation/replayCommands'
import { hashGameState } from '../../src/game/state/hashGameState'

const openingCommands: RuleCommand[] = [
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
  {
    playerId: 'player:human',
    toTileId: 'tile:8:10',
    type: 'MOVE_UNIT',
    unitId: 'unit:scout:1',
  },
  {
    playerId: 'player:human',
    type: 'END_TURN',
  },
]

describe('replayCommands', () => {
  it('replays a command list into a deterministic state', () => {
    const first = replayCommands(1001, openingCommands)
    const second = replayCommands(1001, openingCommands)

    expect(hashGameState(first)).toBe(hashGameState(second))
    expect(first.commandLog).toHaveLength(openingCommands.length)
    expect(first.turn).toBe(2)
    expect(first.turnTrace).toContain('NEXT_TURN')
  })

  it('replays a saved command log into the same deterministic state', () => {
    const original = replayCommands(1001, openingCommands)
    const replayed = replayCommandLog(1001, original.commandLog)

    expect(hashGameState(replayed)).toBe(hashGameState(original))
    expect(replayed.commandLog.map((record) => record.id)).toEqual(
      original.commandLog.map((record) => record.id),
    )
  })

  it('throws on invalid replay commands', () => {
    expect(() =>
      replayCommands(1001, [
        {
          playerId: 'player:human',
          toTileId: 'tile:missing',
          type: 'MOVE_UNIT',
          unitId: 'unit:scout:1',
        },
      ]),
    ).toThrow('目标地块不存在。')
  })
})
