export type UnitId = 'unit:scout' | 'unit:settler' | 'unit:warrior'

export type UnitConfig = {
  attack: number
  id: UnitId
  maxHp: number
  productionCost: number
}

export const unitConfigs: UnitConfig[] = [
  {
    attack: 2,
    id: 'unit:scout',
    maxHp: 10,
    productionCost: 4,
  },
  {
    attack: 0,
    id: 'unit:settler',
    maxHp: 8,
    productionCost: 8,
  },
  {
    attack: 6,
    id: 'unit:warrior',
    maxHp: 20,
    productionCost: 6,
  },
]

export function getUnitConfig(id: string): UnitConfig | null {
  return unitConfigs.find((unit) => unit.id === id) ?? null
}

export function isUnitId(id: string): id is UnitId {
  return getUnitConfig(id) !== null
}
