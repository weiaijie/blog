export type TechId = 'tech:mining'

export type TechConfig = {
  id: TechId
  researchCost: number
}

export const techConfigs: TechConfig[] = [
  {
    id: 'tech:mining',
    researchCost: 3,
  },
]

export function getTechConfig(id: string): TechConfig | null {
  return techConfigs.find((tech) => tech.id === id) ?? null
}
