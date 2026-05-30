export type RuleCommandType = 'CHOOSE_TECH' | 'END_TURN' | 'MOVE_UNIT' | 'SET_PRODUCTION'

type PlayerCommand = {
  playerId: string
}

export type EndTurnCommand = PlayerCommand & {
  type: 'END_TURN'
}

export type MoveUnitCommand = PlayerCommand & {
  type: 'MOVE_UNIT'
  unitId: string
  toTileId: string
}

export type ChooseTechCommand = PlayerCommand & {
  type: 'CHOOSE_TECH'
  techId: string
}

export type SetProductionCommand = PlayerCommand & {
  type: 'SET_PRODUCTION'
  cityId: string
  productionId: string
}

export type RuleCommand =
  | ChooseTechCommand
  | EndTurnCommand
  | MoveUnitCommand
  | SetProductionCommand

export type CommandRecord = {
  id: string
  turn: number
  actorId: string
  command: RuleCommand
}

export type CommandLog = CommandRecord[]

export function createCommandRecord(params: {
  command: RuleCommand
  index: number
  turn: number
}): CommandRecord {
  return {
    actorId: params.command.playerId,
    command: params.command,
    id: `cmd:${params.turn}:${params.index}:${params.command.type}`,
    turn: params.turn,
  }
}

export function isRuleCommand(value: unknown): value is RuleCommand {
  if (!isRecord(value) || typeof value.playerId !== 'string') {
    return false
  }

  switch (value.type) {
    case 'CHOOSE_TECH':
      return typeof value.techId === 'string'
    case 'END_TURN':
      return true
    case 'MOVE_UNIT':
      return typeof value.unitId === 'string' && typeof value.toTileId === 'string'
    case 'SET_PRODUCTION':
      return typeof value.cityId === 'string' && typeof value.productionId === 'string'
    default:
      return false
  }
}

export function isCommandRecord(value: unknown): value is CommandRecord {
  return (
    isRecord(value) &&
    typeof value.id === 'string' &&
    typeof value.actorId === 'string' &&
    typeof value.turn === 'number' &&
    Number.isInteger(value.turn) &&
    isRuleCommand(value.command)
  )
}

export function isCommandLog(value: unknown): value is CommandLog {
  return Array.isArray(value) && value.every(isCommandRecord)
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}
