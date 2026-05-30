import type { RuleCommand } from '../commands/ruleCommand'
import { isUnitId } from '../config/unit'
import type { GameState } from '../state/gameState'
import { areHexNeighbors, getHexDistance } from '../simulation/hexGrid'

export type ValidationErrorCode =
  | 'ATTACKER_NOT_FOUND'
  | 'ATTACK_INVALID_TARGET'
  | 'ATTACK_OUT_OF_RANGE'
  | 'ATTACK_TARGET_NOT_VISIBLE'
  | 'CITY_NOT_FOUND'
  | 'CITY_LIMIT_REACHED'
  | 'EMPTY_PRODUCTION_ID'
  | 'EMPTY_TECH_ID'
  | 'FOUND_CITY_BLOCKED_TILE'
  | 'FOUND_CITY_TILE_MISMATCH'
  | 'FOUND_CITY_TOO_CLOSE'
  | 'FOUND_CITY_UNIT_REQUIRED'
  | 'INVALID_MOVE_RANGE'
  | 'NOT_ACTIVE_PLAYER'
  | 'TARGET_NOT_FOUND'
  | 'TILE_NOT_FOUND'
  | 'UNIT_NOT_FOUND'
  | 'UNKNOWN_PRODUCTION_ID'

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
    case 'ATTACK': {
      const attacker = state.units.find(
        (unit) => unit.id === command.attackerUnitId && unit.ownerId === command.playerId,
      )

      if (!attacker) {
        return reject('ATTACKER_NOT_FOUND', '攻击单位不存在或不属于当前玩家。')
      }

      if (attacker.typeId !== 'unit:warrior') {
        return reject('ATTACK_INVALID_TARGET', '第一版只有战士可以攻击。')
      }

      const target = state.units.find((unit) => unit.id === command.targetUnitId)

      if (!target) {
        return reject('TARGET_NOT_FOUND', '攻击目标不存在。')
      }

      if (target.ownerId === command.playerId) {
        return reject('ATTACK_INVALID_TARGET', '不能攻击自己的单位。')
      }

      const visibleTileIds = state.explorationByPlayerId[command.playerId]?.visibleTileIds ?? []

      if (!visibleTileIds.includes(target.tileId)) {
        return reject('ATTACK_TARGET_NOT_VISIBLE', '攻击目标必须在当前可见范围内。')
      }

      const attackerTile = state.map.tiles.find((tile) => tile.id === attacker.tileId)
      const targetTile = state.map.tiles.find((tile) => tile.id === target.tileId)

      if (!attackerTile || !targetTile || getHexDistance(attackerTile, targetTile) !== 1) {
        return reject('ATTACK_OUT_OF_RANGE', '攻击目标必须与战士相邻。')
      }

      return accept()
    }
    case 'CHOOSE_TECH':
      return command.techId ? accept() : reject('EMPTY_TECH_ID', '科技 ID 不能为空。')
    case 'END_TURN':
      return accept()
    case 'FOUND_CITY': {
      const unit = state.units.find((item) => item.id === command.unitId && item.ownerId === command.playerId)

      if (!unit) {
        return reject('UNIT_NOT_FOUND', '单位不存在或不属于当前玩家。')
      }

      if (unit.typeId !== 'unit:settler') {
        return reject('FOUND_CITY_UNIT_REQUIRED', '只有开拓者可以建立城市。')
      }

      const targetTile = state.map.tiles.find((tile) => tile.id === command.tileId)

      if (!targetTile) {
        return reject('TILE_NOT_FOUND', '目标地块不存在。')
      }

      if (unit.tileId !== command.tileId) {
        return reject('FOUND_CITY_TILE_MISMATCH', '开拓者必须在当前所在地块建城。')
      }

      if (
        targetTile.terrainId === 'water' ||
        state.cities.some((city) => city.tileId === command.tileId)
      ) {
        return reject('FOUND_CITY_BLOCKED_TILE', '该地块不能建立城市。')
      }

      if (state.cities.filter((city) => city.ownerId === command.playerId).length >= 3) {
        return reject('CITY_LIMIT_REACHED', '城市数量已达到第一版上限。')
      }

      const isTooClose = state.cities
        .filter((city) => city.ownerId === command.playerId)
        .some((city) => {
          const cityTile = state.map.tiles.find((tile) => tile.id === city.tileId)

          return cityTile ? getHexDistance(cityTile, targetTile) < 3 : false
        })

      if (isTooClose) {
        return reject('FOUND_CITY_TOO_CLOSE', '新城市距离已有城市太近。')
      }

      return accept()
    }
    case 'MOVE_UNIT': {
      const unit = state.units.find((item) => item.id === command.unitId && item.ownerId === command.playerId)

      if (!unit) {
        return reject('UNIT_NOT_FOUND', '单位不存在或不属于当前玩家。')
      }

      const fromTile = state.map.tiles.find((tile) => tile.id === unit.tileId)
      const toTile = state.map.tiles.find((tile) => tile.id === command.toTileId)

      if (!toTile) {
        return reject('TILE_NOT_FOUND', '目标地块不存在。')
      }

      if (!fromTile || !areHexNeighbors(fromTile, toTile)) {
        return reject('INVALID_MOVE_RANGE', '目标地块必须与单位相邻。')
      }

      return accept()
    }
    case 'SET_PRODUCTION':
      if (!state.cities.some((city) => city.id === command.cityId && city.ownerId === command.playerId)) {
        return reject('CITY_NOT_FOUND', '城市不存在或不属于当前玩家。')
      }

      if (!command.productionId) {
        return reject('EMPTY_PRODUCTION_ID', '生产项目 ID 不能为空。')
      }

      return isUnitId(command.productionId)
        ? accept()
        : reject('UNKNOWN_PRODUCTION_ID', '生产项目不存在。')
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
