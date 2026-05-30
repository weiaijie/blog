import type { CommandLog, RuleCommand } from '../commands/ruleCommand'
import { createInitialGameState, type GameState } from '../state/gameState'
import { applyRuleCommand } from './applyRuleCommand'

export function replayCommands(seed: number, commands: RuleCommand[]): GameState {
  return commands.reduce(
    (state, command) => applyRuleCommand(state, command),
    createInitialGameState(seed),
  )
}

export function replayCommandLog(seed: number, commandLog: CommandLog): GameState {
  return replayCommands(
    seed,
    commandLog.map((record) => record.command),
  )
}
