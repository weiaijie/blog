import type { CommandLog, RuleCommand } from '../commands/ruleCommand'
import { createInitialGameState, type GameState, type ScenarioId } from '../state/gameState'
import { applyRuleCommand } from './applyRuleCommand'

export function replayCommands(
  seed: number,
  commands: RuleCommand[],
  options: {
    scenarioId?: ScenarioId
  } = {},
): GameState {
  return commands.reduce(
    (state, command) => applyRuleCommand(state, command),
    createInitialGameState(seed, { scenarioId: options.scenarioId }),
  )
}

export function replayCommandLog(
  seed: number,
  commandLog: CommandLog,
  options: {
    scenarioId?: ScenarioId
  } = {},
): GameState {
  return replayCommands(
    seed,
    commandLog.map((record) => record.command),
    { scenarioId: options.scenarioId },
  )
}
