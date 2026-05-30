import type { RuleCommand } from '../commands/ruleCommand'
import type { GameState } from '../state/gameState'

export type ValidationErrorCode =
  | 'CITY_NOT_FOUND'
  | 'EMPTY_PRODUCTION_ID'
  | 'EMPTY_TECH_ID'
  | 'NOT_ACTIVE_PLAYER'
  | 'TILE_NOT_FOUND'
  | 'UNIT_NOT_FOUND'

export type ValidationResult =
  | {
      ok: true
    }
  | {
      code: ValidationErrorCode
      ok: false
      reason: string
    }

export function validateRuleCommand(state: GameState, command: RuleCommand): ValidationResult {
  if (command.playerId !== state.activePlayerId) {
    return reject('NOT_ACTIVE_PLAYER', '不是当前玩家的行动阶段。')
  }

  switch (command.type) {
    case 'CHOOSE_TECH':
      return command.techId ? accept() : reject('EMPTY_TECH_ID', '科技 ID 不能为空。')
    case 'END_TURN':
      return accept()
    case 'MOVE_UNIT':
      if (!state.units.some((unit) => unit.id === command.unitId && unit.ownerId === command.playerId)) {
        return reject('UNIT_NOT_FOUND', '单位不存在或不属于当前玩家。')
      }

      if (!state.map.tiles.some((tile) => tile.id === command.toTileId)) {
        return reject('TILE_NOT_FOUND', '目标地块不存在。')
      }

      return accept()
    case 'SET_PRODUCTION':
      if (!state.cities.some((city) => city.id === command.cityId && city.ownerId === command.playerId)) {
        return reject('CITY_NOT_FOUND', '城市不存在或不属于当前玩家。')
      }

      return command.productionId
        ? accept()
        : reject('EMPTY_PRODUCTION_ID', '生产项目 ID 不能为空。')
  }
}

function accept(): ValidationResult {
  return { ok: true }
}

function reject(code: ValidationErrorCode, reason: string): ValidationResult {
  return {
    code,
    ok: false,
    reason,
  }
}
