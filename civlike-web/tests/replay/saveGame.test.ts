import { describe, expect, it } from 'vitest'
import type { RuleCommand } from '../../src/game/commands/ruleCommand'
import { replayCommands } from '../../src/game/simulation/replayCommands'
import { hashGameState } from '../../src/game/state/hashGameState'
import {
  loadGameFromSave,
  parseSavedGame,
  SAVE_SCHEMA_VERSION,
  serializeSavedGame,
} from '../../src/game/state/saveGame'

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
]

const foundingCommands: RuleCommand[] = [
  {
    cityId: 'city:capital',
    playerId: 'player:human',
    productionId: 'unit:settler',
    type: 'SET_PRODUCTION',
  },
  { playerId: 'player:human', type: 'END_TURN' },
  { playerId: 'player:human', type: 'END_TURN' },
  { playerId: 'player:human', type: 'END_TURN' },
  { playerId: 'player:human', type: 'END_TURN' },
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
  { playerId: 'player:human', type: 'END_TURN' },
  { playerId: 'player:human', type: 'END_TURN' },
  { playerId: 'player:human', type: 'END_TURN' },
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

describe('saveGame', () => {
  it('serializes the minimal replayable save shape', () => {
    const state = replayCommands(1001, openingCommands)
    const parsed = parseSavedGame(serializeSavedGame(state))

    expect(parsed).toMatchObject({
      ok: true,
      savedGame: {
        schemaVersion: SAVE_SCHEMA_VERSION,
        seed: 1001,
      },
    })

    if (parsed.ok) {
      expect(parsed.savedGame.commandLog).toHaveLength(openingCommands.length)
    }
  })

  it('loads a saved command log into the same deterministic state', () => {
    const original = replayCommands(1001, openingCommands)
    const loaded = loadGameFromSave(serializeSavedGame(original))

    expect(loaded.ok).toBe(true)

    if (loaded.ok) {
      expect(hashGameState(loaded.state)).toBe(hashGameState(original))
    }
  })

  it('loads a saved city founding command log into the same deterministic state', () => {
    const original = replayCommands(1001, foundingCommands)
    const loaded = loadGameFromSave(serializeSavedGame(original))

    expect(loaded.ok).toBe(true)

    if (loaded.ok) {
      expect(hashGameState(loaded.state)).toBe(hashGameState(original))
      expect(loaded.state.cities.some((city) => city.id === 'city:player:human:2')).toBe(true)
    }
  })

  it('loads a saved warrior command log into the same deterministic state', () => {
    const original = replayCommands(1001, warriorCommands)
    const parsed = parseSavedGame(serializeSavedGame(original))
    const loaded = loadGameFromSave(serializeSavedGame(original))

    expect(parsed.ok).toBe(true)
    expect(loaded.ok).toBe(true)

    if (loaded.ok) {
      expect(hashGameState(loaded.state)).toBe(hashGameState(original))
      expect(loaded.state.units).toContainEqual({
        hp: 20,
        id: 'unit:warrior:2',
        maxHp: 20,
        ownerId: 'player:human',
        tileId: 'tile:8:7',
        typeId: 'unit:warrior',
      })
    }
  })

  it('loads a saved combat scenario attack command log into the same deterministic state', () => {
    const original = replayCommands(1001, attackCommands, { scenarioId: 'combat:adjacent-enemy' })
    const serialized = serializeSavedGame(original)
    const parsed = parseSavedGame(serialized)
    const loaded = loadGameFromSave(serialized)

    expect(parsed).toMatchObject({
      ok: true,
      savedGame: {
        scenarioId: 'combat:adjacent-enemy',
      },
    })
    expect(loaded.ok).toBe(true)

    if (loaded.ok) {
      expect(hashGameState(loaded.state)).toBe(hashGameState(original))
      expect(loaded.state.scenarioId).toBe('combat:adjacent-enemy')
      expect(loaded.state.units.some((unit) => unit.id === 'unit:enemy:scout:1')).toBe(false)
    }
  })

  it('rejects unsupported save schema versions', () => {
    const result = parseSavedGame(
      JSON.stringify({
        commandLog: [],
        schemaVersion: 999,
        seed: 1001,
      }),
    )

    expect(result).toMatchObject({
      code: 'INVALID_SCHEMA_VERSION',
      ok: false,
    })
  })

  it('rejects unsupported scenario ids', () => {
    const result = parseSavedGame(
      JSON.stringify({
        commandLog: [],
        scenarioId: 'combat:unknown',
        schemaVersion: SAVE_SCHEMA_VERSION,
        seed: 1001,
      }),
    )

    expect(result).toMatchObject({
      code: 'INVALID_SCENARIO_ID',
      ok: false,
    })
  })

  it('rejects command logs with invalid record shape', () => {
    const result = parseSavedGame(
      JSON.stringify({
        commandLog: [
          {
            actorId: 'player:human',
            command: {
              playerId: 'player:human',
              type: 'UNKNOWN_COMMAND',
            },
            id: 'cmd:1:0:UNKNOWN_COMMAND',
            turn: 1,
          },
        ],
        schemaVersion: SAVE_SCHEMA_VERSION,
        seed: 1001,
      }),
    )

    expect(result).toMatchObject({
      code: 'INVALID_COMMAND_LOG',
      ok: false,
    })
  })

  it('rejects command logs with missing command fields', () => {
    const result = parseSavedGame(
      JSON.stringify({
        commandLog: [
          {
            actorId: 'player:human',
            command: {
              playerId: 'player:human',
              toTileId: 'tile:8:10',
              type: 'MOVE_UNIT',
            },
            id: 'cmd:1:0:MOVE_UNIT',
            turn: 1,
          },
        ],
        schemaVersion: SAVE_SCHEMA_VERSION,
        seed: 1001,
      }),
    )

    expect(result).toMatchObject({
      code: 'INVALID_COMMAND_LOG',
      ok: false,
    })
  })

  it('rejects city founding commands with missing command fields', () => {
    const result = parseSavedGame(
      JSON.stringify({
        commandLog: [
          {
            actorId: 'player:human',
            command: {
              playerId: 'player:human',
              type: 'FOUND_CITY',
              unitId: 'unit:settler:2',
            },
            id: 'cmd:1:0:FOUND_CITY',
            turn: 1,
          },
        ],
        schemaVersion: SAVE_SCHEMA_VERSION,
        seed: 1001,
      }),
    )

    expect(result).toMatchObject({
      code: 'INVALID_COMMAND_LOG',
      ok: false,
    })
  })

  it('rejects attack commands with missing command fields', () => {
    const result = parseSavedGame(
      JSON.stringify({
        commandLog: [
          {
            actorId: 'player:human',
            command: {
              attackerUnitId: 'unit:warrior:2',
              playerId: 'player:human',
              type: 'ATTACK',
            },
            id: 'cmd:1:0:ATTACK',
            turn: 1,
          },
        ],
        schemaVersion: SAVE_SCHEMA_VERSION,
        seed: 1001,
      }),
    )

    expect(result).toMatchObject({
      code: 'INVALID_COMMAND_LOG',
      ok: false,
    })
  })

  it('rejects command logs with unknown production ids', () => {
    const result = parseSavedGame(
      JSON.stringify({
        commandLog: [
          {
            actorId: 'player:human',
            command: {
              cityId: 'city:capital',
              playerId: 'player:human',
              productionId: 'unit:unknown',
              type: 'SET_PRODUCTION',
            },
            id: 'cmd:1:0:SET_PRODUCTION',
            turn: 1,
          },
        ],
        schemaVersion: SAVE_SCHEMA_VERSION,
        seed: 1001,
      }),
    )

    expect(result).toMatchObject({
      code: 'INVALID_COMMAND_LOG',
      ok: false,
    })
  })

  it('returns a structured error when saved commands cannot replay', () => {
    const result = loadGameFromSave(
      JSON.stringify({
        commandLog: [
          {
            actorId: 'player:human',
            command: {
              playerId: 'player:human',
              toTileId: 'tile:missing',
              type: 'MOVE_UNIT',
              unitId: 'unit:scout:1',
            },
            id: 'cmd:1:0:MOVE_UNIT',
            turn: 1,
          },
        ],
        schemaVersion: SAVE_SCHEMA_VERSION,
        seed: 1001,
      }),
    )

    expect(result).toMatchObject({
      code: 'REPLAY_FAILED',
      ok: false,
    })
  })

  it('returns a structured error when saved attack commands cannot replay without a target source', () => {
    const result = loadGameFromSave(
      JSON.stringify({
        commandLog: [
          {
            actorId: 'player:human',
            command: {
              attackerUnitId: 'unit:warrior:2',
              playerId: 'player:human',
              targetUnitId: 'unit:target:1',
              type: 'ATTACK',
            },
            id: 'cmd:1:0:ATTACK',
            turn: 1,
          },
        ],
        schemaVersion: SAVE_SCHEMA_VERSION,
        seed: 1001,
      }),
    )

    expect(result).toMatchObject({
      code: 'REPLAY_FAILED',
      ok: false,
    })
  })
})
