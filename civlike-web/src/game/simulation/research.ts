import { getTechConfig } from '../config/tech'
import type { GameState } from '../state/gameState'

export function advanceResearch(state: GameState): GameState {
  let nextState = state

  for (const player of state.players) {
    const currentTechId = nextState.currentTechByPlayerId[player.id]

    if (!currentTechId) {
      continue
    }

    const techConfig = getTechConfig(currentTechId)
    const nextPlayer = nextState.players.find((item) => item.id === player.id)

    if (!techConfig || !nextPlayer || nextPlayer.scienceProgress < techConfig.researchCost) {
      continue
    }

    nextState = {
      ...nextState,
      completedTechByPlayerId: {
        ...nextState.completedTechByPlayerId,
        [player.id]: [...nextState.completedTechByPlayerId[player.id], currentTechId],
      },
      currentTechByPlayerId: {
        ...nextState.currentTechByPlayerId,
        [player.id]: null,
      },
      players: nextState.players.map((item) =>
        item.id === player.id
          ? {
              ...item,
              scienceProgress: item.scienceProgress - techConfig.researchCost,
            }
          : item,
      ),
    }
  }

  return nextState
}
