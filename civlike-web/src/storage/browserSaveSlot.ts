import type { GameState } from '../game/state/gameState'
import { loadGameFromSave, serializeSavedGame } from '../game/state/saveGame'

const manualSaveKey = 'civlike-web:manual-save:v1'

export type BrowserSaveSlotResult =
  | {
      bytes: number
      ok: true
      state?: GameState
    }
  | {
      code: 'LOAD_FAILED' | 'NO_SAVE' | 'STORAGE_UNAVAILABLE'
      ok: false
      reason: string
    }

export function saveManualGame(state: GameState): BrowserSaveSlotResult {
  const serialized = serializeSavedGame(state)

  try {
    window.localStorage.setItem(manualSaveKey, serialized)
  } catch {
    return {
      code: 'STORAGE_UNAVAILABLE',
      ok: false,
      reason: 'Browser storage is not available.',
    }
  }

  return {
    bytes: serialized.length,
    ok: true,
  }
}

export function loadManualGame(): BrowserSaveSlotResult {
  let serialized: string | null

  try {
    serialized = window.localStorage.getItem(manualSaveKey)
  } catch {
    return {
      code: 'STORAGE_UNAVAILABLE',
      ok: false,
      reason: 'Browser storage is not available.',
    }
  }

  if (!serialized) {
    return {
      code: 'NO_SAVE',
      ok: false,
      reason: 'No persistent save slot exists.',
    }
  }

  const result = loadGameFromSave(serialized)

  if (!result.ok) {
    return {
      code: 'LOAD_FAILED',
      ok: false,
      reason: `${result.code}: ${result.reason}`,
    }
  }

  return {
    bytes: serialized.length,
    ok: true,
    state: result.state,
  }
}

export function getManualSaveStatus(): string {
  try {
    const serialized = window.localStorage.getItem(manualSaveKey)

    return serialized ? `${serialized.length} 字节` : '空'
  } catch {
    return '不可用'
  }
}
