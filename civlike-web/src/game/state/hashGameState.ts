import type { GameState } from './gameState'

export function hashGameState(state: GameState): string {
  return stableStringify(state)
}

function stableStringify(value: unknown): string {
  if (Array.isArray(value)) {
    return `[${value.map((item) => stableStringify(item)).join(',')}]`
  }

  if (value && typeof value === 'object') {
    const record = value as Record<string, unknown>
    const entries = Object.keys(record)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${stableStringify(record[key])}`)

    return `{${entries.join(',')}}`
  }

  return JSON.stringify(value)
}
