import { describe, expect, it } from 'vitest'
import {
  applyRuleCommand,
  tryApplyRuleCommand,
} from '../../src/game/simulation/applyRuleCommand'
import { createInitialGameState, createUnitState } from '../../src/game/state/gameState'
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
    expect(
      validateRuleCommand(state, {
        cityId: 'city:capital',
        playerId: 'player:human',
        productionId: 'unit:warrior',
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
      {
        code: 'UNKNOWN_PRODUCTION_ID',
        command: {
          cityId: 'city:capital',
          playerId: 'player:human',
          productionId: 'unit:unknown',
          type: 'SET_PRODUCTION',
        },
      },
      {
        code: 'FOUND_CITY_UNIT_REQUIRED',
        command: {
          playerId: 'player:human',
          tileId: 'tile:8:9',
          type: 'FOUND_CITY',
          unitId: 'unit:scout:1',
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

  it('founds a city with a settler on a valid hex tile', () => {
    const state = withSettlerAt('tile:8:5')
    const founded = applyRuleCommand(state, {
      playerId: 'player:human',
      tileId: 'tile:8:5',
      type: 'FOUND_CITY',
      unitId: 'unit:settler:1',
    })

    expect(founded.cities).toContainEqual({
      id: 'city:player:human:2',
      ownerId: 'player:human',
      productionId: null,
      productionProgress: 0,
      tileId: 'tile:8:5',
    })
    expect(founded.units.some((unit) => unit.id === 'unit:settler:1')).toBe(false)
    expect(founded.commandLog.at(-1)).toMatchObject({
      actorId: 'player:human',
      command: {
        playerId: 'player:human',
        tileId: 'tile:8:5',
        type: 'FOUND_CITY',
        unitId: 'unit:settler:1',
      },
      id: 'cmd:1:0:FOUND_CITY',
      turn: 1,
    })
  })

  it('rejects invalid city founding with stable error codes', () => {
    const base = withSettlerAt('tile:8:5')
    const cases: Array<{
      code: ValidationErrorCode
      state: typeof base
      tileId: string
    }> = [
      {
        code: 'FOUND_CITY_TILE_MISMATCH',
        state: base,
        tileId: 'tile:8:4',
      },
      {
        code: 'FOUND_CITY_BLOCKED_TILE',
        state: withTerrain(withSettlerAt('tile:8:6'), 'tile:8:6', 'water'),
        tileId: 'tile:8:6',
      },
      {
        code: 'FOUND_CITY_BLOCKED_TILE',
        state: withSettlerAt('tile:8:8'),
        tileId: 'tile:8:8',
      },
      {
        code: 'FOUND_CITY_TOO_CLOSE',
        state: withSettlerAt('tile:9:9'),
        tileId: 'tile:9:9',
      },
      {
        code: 'CITY_LIMIT_REACHED',
        state: {
          ...base,
          cities: [
            ...base.cities,
            {
              id: 'city:player:human:2',
              ownerId: 'player:human',
              productionId: null,
              productionProgress: 0,
              tileId: 'tile:5:8',
            },
            {
              id: 'city:player:human:3',
              ownerId: 'player:human',
              productionId: null,
              productionProgress: 0,
              tileId: 'tile:11:8',
            },
          ],
        },
        tileId: 'tile:8:5',
      },
    ]

    for (const item of cases) {
      expect(
        validateRuleCommand(item.state, {
          playerId: 'player:human',
          tileId: item.tileId,
          type: 'FOUND_CITY',
          unitId: 'unit:settler:1',
        }),
      ).toMatchObject({
        code: item.code,
        ok: false,
      })
    }
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
      exploredTileIds: ['tile:8:8', 'tile:9:8', 'tile:7:9', 'tile:8:9', 'tile:9:9', 'tile:8:10', 'tile:9:10'],
      visibleTileIds: ['tile:8:8', 'tile:9:8', 'tile:7:9', 'tile:8:9', 'tile:9:9', 'tile:8:10', 'tile:9:10'],
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
        'tile:9:8',
        'tile:7:9',
        'tile:8:9',
        'tile:9:9',
        'tile:7:10',
        'tile:8:10',
        'tile:9:10',
        'tile:7:11',
        'tile:8:11',
      ],
      visibleTileIds: ['tile:7:9', 'tile:8:9', 'tile:7:10', 'tile:8:10', 'tile:9:10', 'tile:7:11', 'tile:8:11'],
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

  it('advances production and yields for a newly founded city', () => {
    let state = withSettlerAt('tile:8:5')

    state = applyRuleCommand(state, {
      playerId: 'player:human',
      tileId: 'tile:8:5',
      type: 'FOUND_CITY',
      unitId: 'unit:settler:1',
    })
    state = applyRuleCommand(state, {
      cityId: 'city:player:human:2',
      playerId: 'player:human',
      productionId: 'unit:scout',
      type: 'SET_PRODUCTION',
    })
    state = applyRuleCommand(state, {
      playerId: 'player:human',
      type: 'END_TURN',
    })

    const foundedCity = state.cities.find((city) => city.id === 'city:player:human:2')
    const human = state.players.find((player) => player.id === 'player:human')

    expect(foundedCity).toMatchObject({
      productionId: 'unit:scout',
      productionProgress: 1,
      tileId: 'tile:8:5',
    })
    expect(human).toMatchObject({
      foodStockpile: 5,
      scienceProgress: 2,
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
      hp: 10,
      id: 'unit:scout:2',
      maxHp: 10,
      ownerId: 'player:human',
      tileId: 'tile:8:8',
      typeId: 'unit:scout',
    })
  })

  it('creates a settler with default hit points when production reaches its cost', () => {
    let state = createInitialGameState(1001)

    state = applyRuleCommand(state, {
      cityId: 'city:capital',
      playerId: 'player:human',
      productionId: 'unit:settler',
      type: 'SET_PRODUCTION',
    })

    for (let index = 0; index < 4; index += 1) {
      state = applyRuleCommand(state, {
        playerId: 'player:human',
        type: 'END_TURN',
      })
    }

    expect(state.units).toContainEqual({
      hp: 8,
      id: 'unit:settler:2',
      maxHp: 8,
      ownerId: 'player:human',
      tileId: 'tile:8:8',
      typeId: 'unit:settler',
    })
  })

  it('creates and moves a warrior through the existing unit rules', () => {
    let state = createInitialGameState(1001)

    state = applyRuleCommand(state, {
      cityId: 'city:capital',
      playerId: 'player:human',
      productionId: 'unit:warrior',
      type: 'SET_PRODUCTION',
    })

    for (let index = 0; index < 3; index += 1) {
      state = applyRuleCommand(state, {
        playerId: 'player:human',
        type: 'END_TURN',
      })
    }

    expect(state.cities[0]).toMatchObject({
      productionId: 'unit:warrior',
      productionProgress: 0,
    })
    expect(state.units).toContainEqual({
      hp: 20,
      id: 'unit:warrior:2',
      maxHp: 20,
      ownerId: 'player:human',
      tileId: 'tile:8:8',
      typeId: 'unit:warrior',
    })

    state = applyRuleCommand(state, {
      playerId: 'player:human',
      toTileId: 'tile:8:7',
      type: 'MOVE_UNIT',
      unitId: 'unit:warrior:2',
    })

    expect(state.units.find((unit) => unit.id === 'unit:warrior:2')).toMatchObject({
      tileId: 'tile:8:7',
      typeId: 'unit:warrior',
    })
    expect(
      validateRuleCommand(state, {
        playerId: 'player:human',
        toTileId: 'tile:8:10',
        type: 'MOVE_UNIT',
        unitId: 'unit:warrior:2',
      }),
    ).toMatchObject({
      code: 'INVALID_MOVE_RANGE',
      ok: false,
    })
  })

  it('attacks a visible adjacent enemy with a warrior', () => {
    const state = withCombatUnits()
    const attacked = applyRuleCommand(state, {
      attackerUnitId: 'unit:attacker:1',
      playerId: 'player:human',
      targetUnitId: 'unit:target:1',
      type: 'ATTACK',
    })

    expect(attacked.units.find((unit) => unit.id === 'unit:target:1')).toMatchObject({
      hp: 4,
      maxHp: 10,
      ownerId: 'player:ai:1',
      tileId: 'tile:8:10',
    })
    expect(attacked.commandLog.at(-1)).toMatchObject({
      actorId: 'player:human',
      command: {
        attackerUnitId: 'unit:attacker:1',
        playerId: 'player:human',
        targetUnitId: 'unit:target:1',
        type: 'ATTACK',
      },
      id: 'cmd:1:0:ATTACK',
      turn: 1,
    })
  })

  it('removes an attacked unit when hit points reach zero', () => {
    let state = withCombatUnits()

    state = applyRuleCommand(state, {
      attackerUnitId: 'unit:attacker:1',
      playerId: 'player:human',
      targetUnitId: 'unit:target:1',
      type: 'ATTACK',
    })
    state = applyRuleCommand(state, {
      attackerUnitId: 'unit:attacker:1',
      playerId: 'player:human',
      targetUnitId: 'unit:target:1',
      type: 'ATTACK',
    })

    expect(state.units.some((unit) => unit.id === 'unit:target:1')).toBe(false)
    expect(state.commandLog.map((record) => record.command.type)).toEqual(['ATTACK', 'ATTACK'])
  })

  it('rejects invalid attacks with stable error codes', () => {
    const cases: Array<{
      code: ValidationErrorCode
      state: ReturnType<typeof withCombatUnits>
      command?: Parameters<typeof validateRuleCommand>[1]
    }> = [
      {
        code: 'ATTACKER_NOT_FOUND',
        state: withCombatUnits(),
        command: {
          attackerUnitId: 'unit:missing',
          playerId: 'player:human',
          targetUnitId: 'unit:target:1',
          type: 'ATTACK',
        },
      },
      {
        code: 'ATTACK_INVALID_TARGET',
        state: withCombatUnits({ attackerTypeId: 'unit:scout' }),
      },
      {
        code: 'TARGET_NOT_FOUND',
        state: withCombatUnits(),
        command: {
          attackerUnitId: 'unit:attacker:1',
          playerId: 'player:human',
          targetUnitId: 'unit:missing',
          type: 'ATTACK',
        },
      },
      {
        code: 'ATTACK_INVALID_TARGET',
        state: withCombatUnits({ targetOwnerId: 'player:human' }),
      },
      {
        code: 'ATTACK_TARGET_NOT_VISIBLE',
        state: withCombatUnits({ targetTileId: 'tile:10:10' }),
      },
      {
        code: 'ATTACK_OUT_OF_RANGE',
        state: withCombatUnits({
          targetTileId: 'tile:10:10',
          visibleTileIds: [
            'tile:8:8',
            'tile:9:8',
            'tile:7:9',
            'tile:8:9',
            'tile:9:9',
            'tile:8:10',
            'tile:9:10',
            'tile:10:10',
          ],
        }),
      },
    ]

    for (const item of cases) {
      expect(
        validateRuleCommand(
          item.state,
          item.command ?? {
            attackerUnitId: 'unit:attacker:1',
            playerId: 'player:human',
            targetUnitId: 'unit:target:1',
            type: 'ATTACK',
          },
        ),
      ).toMatchObject({
        code: item.code,
        ok: false,
      })
    }
  })

  it('keeps attack hash deterministic for the same custom combat state and command sequence', () => {
    const first = runAttackCommands(withCombatUnits())
    const second = runAttackCommands(withCombatUnits())

    expect(hashGameState(first)).toBe(hashGameState(second))
    expect(first.units.some((unit) => unit.id === 'unit:target:1')).toBe(false)
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

function withSettlerAt(tileId: string) {
  const state = createInitialGameState(1001)

  return {
    ...state,
    units: [
      ...state.units,
      createUnitState({
        id: 'unit:settler:1',
        ownerId: 'player:human',
        tileId,
        typeId: 'unit:settler',
      }),
    ],
  }
}

function withTerrain(state: ReturnType<typeof createInitialGameState>, tileId: string, terrainId: 'water') {
  return {
    ...state,
    map: {
      ...state.map,
      tiles: state.map.tiles.map((tile) => (tile.id === tileId ? { ...tile, terrainId } : tile)),
    },
  }
}

function withCombatUnits(params: {
  attackerTypeId?: 'unit:scout' | 'unit:settler' | 'unit:warrior'
  targetOwnerId?: string
  targetTileId?: string
  visibleTileIds?: string[]
} = {}) {
  const state = createInitialGameState(1001)
  const humanExploration = state.explorationByPlayerId['player:human']

  return {
    ...state,
    explorationByPlayerId: {
      ...state.explorationByPlayerId,
      'player:human': {
        exploredTileIds: humanExploration.exploredTileIds,
        visibleTileIds: params.visibleTileIds ?? humanExploration.visibleTileIds,
      },
    },
    units: [
      createUnitState({
        id: 'unit:attacker:1',
        ownerId: 'player:human',
        tileId: 'tile:8:9',
        typeId: params.attackerTypeId ?? 'unit:warrior',
      }),
      createUnitState({
        id: 'unit:target:1',
        ownerId: params.targetOwnerId ?? 'player:ai:1',
        tileId: params.targetTileId ?? 'tile:8:10',
        typeId: 'unit:scout',
      }),
    ],
  }
}

function runAttackCommands(state: ReturnType<typeof withCombatUnits>) {
  let next = state

  next = applyRuleCommand(next, {
    attackerUnitId: 'unit:attacker:1',
    playerId: 'player:human',
    targetUnitId: 'unit:target:1',
    type: 'ATTACK',
  })
  next = applyRuleCommand(next, {
    attackerUnitId: 'unit:attacker:1',
    playerId: 'player:human',
    targetUnitId: 'unit:target:1',
    type: 'ATTACK',
  })

  return next
}
