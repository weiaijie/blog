import { isCommandLog, type CommandLog } from '../commands/ruleCommand'
import { isUnitId } from '../config/unit'
import { replayCommandLog } from '../simulation/replayCommands'
import type { GameState, ScenarioId } from './gameState'

export const SAVE_SCHEMA_VERSION = 1
export const DEFAULT_SCENARIO_ID: ScenarioId = 'default'

export type SavedGame = {
  schemaVersion: typeof SAVE_SCHEMA_VERSION
  seed: number
  scenarioId?: ScenarioId
  commandLog: CommandLog
}

export type SaveGameErrorCode =
  | 'INVALID_COMMAND_LOG'
  | 'INVALID_JSON'
  | 'INVALID_SCHEMA_VERSION'
  | 'INVALID_SCENARIO_ID'
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
  const savedGame: SavedGame = {
    commandLog: state.commandLog,
    schemaVersion: SAVE_SCHEMA_VERSION,
    seed: state.seed,
  }

  if (state.scenarioId !== DEFAULT_SCENARIO_ID) {
    savedGame.scenarioId = state.scenarioId
  }

  return savedGame
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

  const scenarioId = parsed.scenarioId ?? DEFAULT_SCENARIO_ID

  if (!isScenarioId(scenarioId)) {
    return reject('INVALID_SCENARIO_ID', 'Save scenario id is not supported.')
  }

  if (!isCommandLog(parsed.commandLog)) {
    return reject('INVALID_COMMAND_LOG', 'Save commandLog contains invalid command records.')
  }

  if (!hasValidCommandLogReferences(parsed.commandLog)) {
    return reject('INVALID_COMMAND_LOG', 'Save commandLog contains invalid command references.')
  }

  return {
    ok: true,
    savedGame: {
      commandLog: parsed.commandLog,
      schemaVersion: SAVE_SCHEMA_VERSION,
      seed,
      scenarioId: scenarioId === DEFAULT_SCENARIO_ID ? undefined : scenarioId,
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
      state: replayCommandLog(parsed.savedGame.seed, parsed.savedGame.commandLog, {
        scenarioId: parsed.savedGame.scenarioId,
      }),
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

function hasValidCommandLogReferences(commandLog: CommandLog): boolean {
  return commandLog.every((record) => {
    if (record.command.type !== 'SET_PRODUCTION') {
      return true
    }

    return record.command.productionId !== '' && isUnitId(record.command.productionId)
  })
}

function isScenarioId(value: unknown): value is ScenarioId {
  return value === 'default' || value === 'combat:adjacent-enemy'
}

function reject(code: SaveGameErrorCode, reason: string): SaveGameFailure {
  return {
    code,
    ok: false,
    reason,
  }
}
