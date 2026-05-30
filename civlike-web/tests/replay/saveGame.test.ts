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
})
