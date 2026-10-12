import { describe, expect, it } from 'vitest'
import {
  runTenTurnPressure,
  runThirtyTurnPressure,
} from '../../src/game/simulation/tenTurnPressure'

describe('10 turn pressure run', () => {
  it('keeps the fixed command sequence deterministic and replayable', () => {
    const first = runTenTurnPressure(1001)
    const second = runTenTurnPressure(1001)

    expect(first).toEqual(second)
    expect(first).toMatchObject({
      capitalProductionId: 'unit:scout',
      capitalProgress: 0,
      commandCount: 12,
      completedTechs: ['tech:mining'],
      foodStockpile: 20,
      scienceProgress: 7,
      turn: 11,
      unitCount: 6,
    })
    expect(first.replayHash).toBe(first.hash)
  })

  it('keeps a 30 turn fixed sequence stable before the manual 30 turn loop', () => {
    const first = runThirtyTurnPressure(1001)
    const second = runThirtyTurnPressure(1001)

    expect(first).toEqual(second)
    expect(first).toMatchObject({
      capitalProductionId: 'unit:scout',
      capitalProgress: 0,
      commandCount: 32,
      completedTechs: ['tech:mining'],
      foodStockpile: 60,
      scienceProgress: 27,
      turn: 31,
      unitCount: 16,
    })
    expect(first.replayHash).toBe(first.hash)
  })
})
