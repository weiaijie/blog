import { describe, expect, it } from 'vitest'
import {
  applyRuleCommand,
  tryApplyRuleCommand,
} from '../../src/game/simulation/applyRuleCommand'
import { createInitialGameState } from '../../src/game/state/gameState'
import { hashGameState } from '../../src/game/state/hashGameState'
import {
  validateRuleCommand,
  type ValidationErrorCode,
} from '../../src/game/validation/validateRuleCommand'

describe('RuleCommand validation and replay', () => {
  it('validates the first command set without mutating state', () => {
    const state = createInitialGameState(1001)

    expect(
      validateRuleCommand(state, {
        playerId: 'player:human',
        toTileId: 'tile:8:10',
        type: 'MOVE_UNIT',
        unitId: 'unit:scout:1',
      }),
    ).toEqual({ ok: true })
    expect(
      validateRuleCommand(state, {
        playerId: 'player:human',
        techId: 'tech:mining',
        type: 'CHOOSE_TECH',
      }),
    ).toEqual({ ok: true })
    expect(
      validateRuleCommand(state, {
        cityId: 'city:capital',
        playerId: 'player:human',
        productionId: 'unit:scout',
        type: 'SET_PRODUCTION',
      }),
    ).toEqual({ ok: true })
  })

  it('rejects invalid commands with stable error codes', () => {
    const state = createInitialGameState(1001)
    const cases: Array<{
      code: ValidationErrorCode
      command: Parameters<typeof validateRuleCommand>[1]
    }> = [
      {
        code: 'NOT_ACTIVE_PLAYER',
        command: {
          playerId: 'player:ai:1',
          type: 'END_TURN',
        },
      },
      {
        code: 'UNIT_NOT_FOUND',
        command: {
          playerId: 'player:human',
          toTileId: 'tile:8:10',
          type: 'MOVE_UNIT',
          unitId: 'unit:missing',
        },
      },
      {
        code: 'TILE_NOT_FOUND',
        command: {
          playerId: 'player:human',
          toTileId: 'tile:99:99',
          type: 'MOVE_UNIT',
          unitId: 'unit:scout:1',
        },
      },
      {
        code: 'EMPTY_TECH_ID',
        command: {
          playerId: 'player:human',
          techId: '',
          type: 'CHOOSE_TECH',
        },
      },
      {
        code: 'CITY_NOT_FOUND',
        command: {
          cityId: 'city:missing',
          playerId: 'player:human',
          productionId: 'unit:scout',
          type: 'SET_PRODUCTION',
        },
      },
      {
        code: 'EMPTY_PRODUCTION_ID',
        command: {
          cityId: 'city:capital',
          playerId: 'player:human',
          productionId: '',
          type: 'SET_PRODUCTION',
        },
      },
    ]

    for (const item of cases) {
      expect(validateRuleCommand(state, item.command)).toMatchObject({
        code: item.code,
        ok: false,
      })
    }
  })

  it('keeps hash deterministic for the same command sequence', () => {
    const first = runOpeningCommands(1001)
    const second = runOpeningCommands(1001)

    expect(hashGameState(first)).toBe(hashGameState(second))
    expect(first.commandLog.map((record) => record.command.type)).toEqual([
      'CHOOSE_TECH',
      'SET_PRODUCTION',
      'MOVE_UNIT',
      'END_TURN',
    ])
  })

  it('records command log fields consistently', () => {
    const state = runOpeningCommands(1001)

    expect(state.commandLog).toEqual([
      {
        actorId: 'player:human',
        command: {
          playerId: 'player:human',
          techId: 'tech:mining',
          type: 'CHOOSE_TECH',
        },
        id: 'cmd:1:0:CHOOSE_TECH',
        turn: 1,
      },
      {
        actorId: 'player:human',
        command: {
          cityId: 'city:capital',
          playerId: 'player:human',
          productionId: 'unit:scout',
          type: 'SET_PRODUCTION',
        },
        id: 'cmd:1:1:SET_PRODUCTION',
        turn: 1,
      },
      {
        actorId: 'player:human',
        command: {
          playerId: 'player:human',
          toTileId: 'tile:8:10',
          type: 'MOVE_UNIT',
          unitId: 'unit:scout:1',
        },
        id: 'cmd:1:2:MOVE_UNIT',
        turn: 1,
      },
      {
        actorId: 'player:human',
        command: {
          playerId: 'player:human',
          type: 'END_TURN',
        },
        id: 'cmd:1:3:END_TURN',
        turn: 1,
      },
    ])
  })

  it('returns structured apply results without throwing', () => {
    const state = createInitialGameState(1001)
    const applied = tryApplyRuleCommand(state, {
      playerId: 'player:human',
      techId: 'tech:mining',
      type: 'CHOOSE_TECH',
    })

    expect(applied).toMatchObject({ ok: true })

    if (applied.ok) {
      expect(applied.state.currentTechByPlayerId['player:human']).toBe('tech:mining')
    }

    expect(
      tryApplyRuleCommand(state, {
        playerId: 'player:ai:1',
        type: 'END_TURN',
      }),
    ).toMatchObject({
      code: 'NOT_ACTIVE_PLAYER',
      ok: false,
    })
  })

  it('tracks visible and explored tiles when the scout moves', () => {
    const initial = createInitialGameState(1001)

    expect(initial.explorationByPlayerId['player:human']).toMatchObject({
      exploredTileIds: ['tile:8:8', 'tile:7:9', 'tile:8:9', 'tile:9:9', 'tile:8:10'],
      visibleTileIds: ['tile:8:8', 'tile:7:9', 'tile:8:9', 'tile:9:9', 'tile:8:10'],
    })

    const moved = applyRuleCommand(initial, {
      playerId: 'player:human',
      toTileId: 'tile:8:10',
      type: 'MOVE_UNIT',
      unitId: 'unit:scout:1',
    })

    expect(moved.explorationByPlayerId['player:human']).toMatchObject({
      exploredTileIds: [
        'tile:8:8',
        'tile:7:9',
        'tile:8:9',
        'tile:9:9',
        'tile:7:10',
        'tile:8:10',
        'tile:9:10',
        'tile:8:11',
      ],
      visibleTileIds: ['tile:8:9', 'tile:7:10', 'tile:8:10', 'tile:9:10', 'tile:8:11'],
    })
  })

  it('advances capital production on end turn when production is selected', () => {
    let state = createInitialGameState(1001)

    state = applyRuleCommand(state, {
      cityId: 'city:capital',
      playerId: 'player:human',
      productionId: 'unit:scout',
      type: 'SET_PRODUCTION',
    })

    expect(state.cities[0].productionProgress).toBe(0)

    state = applyRuleCommand(state, {
      playerId: 'player:human',
      type: 'END_TURN',
    })

    expect(state.cities[0]).toMatchObject({
      id: 'city:capital',
      productionId: 'unit:scout',
      productionProgress: 2,
    })
  })

  it('collects city food and science yields on end turn', () => {
    const state = applyRuleCommand(createInitialGameState(1001), {
      playerId: 'player:human',
      type: 'END_TURN',
    })
    const human = state.players.find((player) => player.id === 'player:human')
    const ai = state.players.find((player) => player.id === 'player:ai:1')

    expect(human).toMatchObject({
      foodStockpile: 2,
      scienceProgress: 1,
    })
    expect(ai).toMatchObject({
      foodStockpile: 0,
      scienceProgress: 0,
    })
  })

  it('completes the selected technology when science reaches its cost', () => {
    let state = createInitialGameState(1001)

    state = applyRuleCommand(state, {
      playerId: 'player:human',
      techId: 'tech:mining',
      type: 'CHOOSE_TECH',
    })

    for (let index = 0; index < 3; index += 1) {
      state = applyRuleCommand(state, {
        playerId: 'player:human',
        type: 'END_TURN',
      })
    }

    const human = state.players.find((player) => player.id === 'player:human')

    expect(state.currentTechByPlayerId['player:human']).toBeNull()
    expect(state.completedTechByPlayerId['player:human']).toEqual(['tech:mining'])
    expect(human?.scienceProgress).toBe(0)
  })

  it('creates a scout when production reaches its cost', () => {
    let state = createInitialGameState(1001)

    state = applyRuleCommand(state, {
      cityId: 'city:capital',
      playerId: 'player:human',
      productionId: 'unit:scout',
      type: 'SET_PRODUCTION',
    })
    state = applyRuleCommand(state, {
      playerId: 'player:human',
      type: 'END_TURN',
    })
    state = applyRuleCommand(state, {
      playerId: 'player:human',
      type: 'END_TURN',
    })

    expect(state.cities[0].productionProgress).toBe(0)
    expect(state.units).toContainEqual({
      id: 'unit:scout:2',
      ownerId: 'player:human',
      tileId: 'tile:8:8',
    })
  })

  it('keeps applyRuleCommand throw behavior for existing callers', () => {
    expect(() =>
      applyRuleCommand(createInitialGameState(1001), {
        playerId: 'player:human',
        toTileId: 'tile:missing',
        type: 'MOVE_UNIT',
        unitId: 'unit:scout:1',
      }),
    ).toThrow()
  })
})

function runOpeningCommands(seed: number) {
  let state = createInitialGameState(seed)

  state = applyRuleCommand(state, {
    playerId: 'player:human',
    techId: 'tech:mining',
    type: 'CHOOSE_TECH',
  })
  state = applyRuleCommand(state, {
    cityId: 'city:capital',
    playerId: 'player:human',
    productionId: 'unit:scout',
    type: 'SET_PRODUCTION',
  })
  state = applyRuleCommand(state, {
    playerId: 'player:human',
    toTileId: 'tile:8:10',
    type: 'MOVE_UNIT',
    unitId: 'unit:scout:1',
  })
  state = applyRuleCommand(state, {
    playerId: 'player:human',
    type: 'END_TURN',
  })

  return state
}
