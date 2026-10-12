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

const foundingCommands: RuleCommand[] = [
  {
    cityId: 'city:capital',
    playerId: 'player:human',
    productionId: 'unit:settler',
    type: 'SET_PRODUCTION',
  },
  {
    playerId: 'player:human',
    type: 'END_TURN',
  },
  {
    playerId: 'player:human',
    type: 'END_TURN',
  },
  {
    playerId: 'player:human',
    type: 'END_TURN',
  },
  {
    playerId: 'player:human',
    type: 'END_TURN',
  },
  {
    playerId: 'player:human',
    toTileId: 'tile:8:7',
    type: 'MOVE_UNIT',
    unitId: 'unit:settler:2',
  },
  {
    playerId: 'player:human',
    toTileId: 'tile:8:6',
    type: 'MOVE_UNIT',
    unitId: 'unit:settler:2',
  },
  {
    playerId: 'player:human',
    toTileId: 'tile:8:5',
    type: 'MOVE_UNIT',
    unitId: 'unit:settler:2',
  },
  {
    playerId: 'player:human',
    tileId: 'tile:8:5',
    type: 'FOUND_CITY',
    unitId: 'unit:settler:2',
  },
]

const warriorCommands: RuleCommand[] = [
  {
    cityId: 'city:capital',
    playerId: 'player:human',
    productionId: 'unit:warrior',
    type: 'SET_PRODUCTION',
  },
  {
    playerId: 'player:human',
    type: 'END_TURN',
  },
  {
    playerId: 'player:human',
    type: 'END_TURN',
  },
  {
    playerId: 'player:human',
    type: 'END_TURN',
  },
  {
    playerId: 'player:human',
    toTileId: 'tile:8:7',
    type: 'MOVE_UNIT',
    unitId: 'unit:warrior:2',
  },
]

const attackCommands: RuleCommand[] = [
  {
    attackerUnitId: 'unit:warrior:scenario:1',
    playerId: 'player:human',
    targetUnitId: 'unit:enemy:scout:1',
    type: 'ATTACK',
  },
  {
    attackerUnitId: 'unit:warrior:scenario:1',
    playerId: 'player:human',
    targetUnitId: 'unit:enemy:scout:1',
    type: 'ATTACK',
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

  it('replays city founding into the same deterministic state', () => {
    const first = replayCommands(1001, foundingCommands)
    const second = replayCommands(1001, foundingCommands)

    expect(hashGameState(first)).toBe(hashGameState(second))
    expect(first.cities).toContainEqual({
      id: 'city:player:human:2',
      ownerId: 'player:human',
      productionId: null,
      productionProgress: 0,
      tileId: 'tile:8:5',
    })
    expect(first.units.some((unit) => unit.id === 'unit:settler:2')).toBe(false)
    expect(first.commandLog.map((record) => record.command.type)).toContain('FOUND_CITY')
  })

  it('replays warrior production and movement into the same deterministic state', () => {
    const first = replayCommands(1001, warriorCommands)
    const second = replayCommands(1001, warriorCommands)

    expect(hashGameState(first)).toBe(hashGameState(second))
    expect(first.units).toContainEqual({
      hp: 20,
      id: 'unit:warrior:2',
      maxHp: 20,
      ownerId: 'player:human',
      tileId: 'tile:8:7',
      typeId: 'unit:warrior',
    })
    expect(first.commandLog.map((record) => record.command.type)).toEqual([
      'SET_PRODUCTION',
      'END_TURN',
      'END_TURN',
      'END_TURN',
      'MOVE_UNIT',
    ])
  })

  it('replays attacks from a combat scenario into the same deterministic state', () => {
    const first = replayCommands(1001, attackCommands, { scenarioId: 'combat:adjacent-enemy' })
    const second = replayCommands(1001, attackCommands, { scenarioId: 'combat:adjacent-enemy' })

    expect(hashGameState(first)).toBe(hashGameState(second))
    expect(first.scenarioId).toBe('combat:adjacent-enemy')
    expect(first.units).toContainEqual({
      hp: 20,
      id: 'unit:warrior:scenario:1',
      maxHp: 20,
      ownerId: 'player:human',
      tileId: 'tile:8:9',
      typeId: 'unit:warrior',
    })
    expect(first.units.some((unit) => unit.id === 'unit:enemy:scout:1')).toBe(false)
    expect(first.commandLog.map((record) => record.command.type)).toEqual(['ATTACK', 'ATTACK'])
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

  it('throws on attack replays without a reproducible target source', () => {
    expect(() =>
      replayCommands(1001, [
        {
          attackerUnitId: 'unit:warrior:2',
          playerId: 'player:human',
          targetUnitId: 'unit:target:1',
          type: 'ATTACK',
        },
      ]),
    ).toThrow('攻击单位不存在或不属于当前玩家。')
  })
})
