export type UnitId = 'unit:scout'

export type UnitConfig = {
  id: UnitId
  productionCost: number
}

export const unitConfigs: UnitConfig[] = [
  {
    id: 'unit:scout',
    productionCost: 4,
  },
]

export function getUnitConfig(id: string): UnitConfig | null {
  return unitConfigs.find((unit) => unit.id === id) ?? null
}
