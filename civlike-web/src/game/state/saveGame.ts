import { isCommandLog, type CommandLog } from '../commands/ruleCommand'
import { replayCommandLog } from '../simulation/replayCommands'
import type { GameState } from './gameState'

export const SAVE_SCHEMA_VERSION = 1

export type SavedGame = {
  schemaVersion: typeof SAVE_SCHEMA_VERSION
  seed: number
  commandLog: CommandLog
}

export type SaveGameErrorCode =
  | 'INVALID_COMMAND_LOG'
  | 'INVALID_JSON'
  | 'INVALID_SCHEMA_VERSION'
  | 'INVALID_SEED'
  | 'REPLAY_FAILED'

type SaveGameFailure = {
  code: SaveGameErrorCode
  ok: false
  reason: string
}

export type SaveGameResult =
  | {
      ok: true
      savedGame: SavedGame
    }
  | SaveGameFailure

export type LoadGameResult =
  | {
      ok: true
      state: GameState
    }
  | SaveGameFailure

export function createSavedGame(state: GameState): SavedGame {
  return {
    commandLog: state.commandLog,
    schemaVersion: SAVE_SCHEMA_VERSION,
    seed: state.seed,
  }
}

export function serializeSavedGame(state: GameState): string {
  return JSON.stringify(createSavedGame(state))
}

export function parseSavedGame(json: string): SaveGameResult {
  let parsed: unknown

  try {
    parsed = JSON.parse(json)
  } catch {
    return reject('INVALID_JSON', 'Save file is not valid JSON.')
  }

  if (!isRecord(parsed)) {
    return reject('INVALID_JSON', 'Save file must be a JSON object.')
  }

  if (parsed.schemaVersion !== SAVE_SCHEMA_VERSION) {
    return reject('INVALID_SCHEMA_VERSION', 'Save schema version is not supported.')
  }

  const seed = parsed.seed

  if (typeof seed !== 'number' || !Number.isInteger(seed)) {
    return reject('INVALID_SEED', 'Save seed must be an integer.')
  }

  if (!isCommandLog(parsed.commandLog)) {
    return reject('INVALID_COMMAND_LOG', 'Save commandLog contains invalid command records.')
  }

  return {
    ok: true,
    savedGame: {
      commandLog: parsed.commandLog,
      schemaVersion: SAVE_SCHEMA_VERSION,
      seed,
    },
  }
}

export function loadGameFromSave(json: string): LoadGameResult {
  const parsed = parseSavedGame(json)

  if (!parsed.ok) {
    return parsed
  }

  try {
    return {
      ok: true,
      state: replayCommandLog(parsed.savedGame.seed, parsed.savedGame.commandLog),
    }
  } catch (error) {
    return reject(
      'REPLAY_FAILED',
      error instanceof Error ? error.message : 'Saved command log could not be replayed.',
    )
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function reject(code: SaveGameErrorCode, reason: string): SaveGameFailure {
  return {
    code,
    ok: false,
    reason,
  }
}
