import { createCommandRecord, type RuleCommand } from '../commands/ruleCommand'
import type { GameState } from '../state/gameState'
import {
  validateRuleCommand,
  type ValidationErrorCode,
} from '../validation/validateRuleCommand'
import { advanceCityProduction, collectCityYields } from './cityProduction'
import { refreshExploration } from './exploration'
import { advanceResearch } from './research'
import { advanceEndTurnPhases } from './turnStateMachine'

export type ApplyRuleCommandResult =
  | {
      ok: true
      state: GameState
    }
  | {
      code: ValidationErrorCode
      ok: false
      reason: string
    }

export function applyRuleCommand(state: GameState, command: RuleCommand): GameState {
  const result = tryApplyRuleCommand(state, command)

  if (!result.ok) {
    throw new Error(result.reason)
  }

  return result.state
}

export function tryApplyRuleCommand(
  state: GameState,
  command: RuleCommand,
): ApplyRuleCommandResult {
  const validation = validateRuleCommand(state, command)

  if (!validation.ok) {
    return validation
  }

  const commandRecord = createCommandRecord({
    command,
    index: state.commandLog.length,
    turn: state.turn,
  })

  switch (command.type) {
    case 'CHOOSE_TECH':
      return {
        ok: true,
        state: {
          ...state,
          commandLog: [...state.commandLog, commandRecord],
          currentTechByPlayerId: {
            ...state.currentTechByPlayerId,
            [command.playerId]: command.techId,
          },
        },
      }
    case 'END_TURN':
      return {
        ok: true,
        state: advanceEndTurnPhases(
          refreshExploration(
            advanceCityProduction(
              advanceResearch(
                collectCityYields({
                  ...state,
                  commandLog: [...state.commandLog, commandRecord],
                  turn: state.turn + 1,
                }),
              ),
            ),
          ),
        ),
      }
    case 'MOVE_UNIT':
      return {
        ok: true,
        state: refreshExploration({
          ...state,
          commandLog: [...state.commandLog, commandRecord],
          units: state.units.map((unit) =>
            unit.id === command.unitId ? { ...unit, tileId: command.toTileId } : unit,
          ),
        }),
      }
    case 'SET_PRODUCTION':
      return {
        ok: true,
        state: {
          ...state,
          cities: state.cities.map((city) =>
            city.id === command.cityId
              ? { ...city, productionId: command.productionId, productionProgress: 0 }
              : city,
          ),
          commandLog: [...state.commandLog, commandRecord],
        },
      }
  }
}
