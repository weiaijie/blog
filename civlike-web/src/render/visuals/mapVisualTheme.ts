export type TerrainAccent = 'none' | 'grass' | 'trees' | 'ridges' | 'waves'

export type TerrainVisualStyle = {
  fill: number
  stroke: number
  strokeAlpha: number
  accent: number
  accentAlpha: number
  accentKind: TerrainAccent
  elevation: number
  highlight: number
  shadow: number
  transition: number
}

export type MapVisualOwner = 'active' | 'enemy' | 'neutral'
export type MapVisualUnitKind = 'scout' | 'warrior' | 'settler' | 'unknown'

export type UnitVisualStyle = {
  fill: number
  stroke: number
  detail: number
}

export type CityVisualStyle = {
  fill: number
  stroke: number
  roof: number
}

const terrainStyles: Record<string, TerrainVisualStyle> = {
  grassland: {
    fill: 0x86b76c,
    stroke: 0x5d7c4d,
    strokeAlpha: 0.42,
    accent: 0xc5d88c,
    accentAlpha: 0.5,
    accentKind: 'grass',
    elevation: 1,
    highlight: 0xcfe29a,
    shadow: 0x557a46,
    transition: 0x9fc177,
  },
  forest: {
    fill: 0x315f42,
    stroke: 0x21462f,
    strokeAlpha: 0.56,
    accent: 0x92b36a,
    accentAlpha: 0.42,
    accentKind: 'trees',
    elevation: 2,
    highlight: 0x6f9a5d,
    shadow: 0x173424,
    transition: 0x406f46,
  },
  hill: {
    fill: 0x94734d,
    stroke: 0x6b543a,
    strokeAlpha: 0.54,
    accent: 0xd0b37a,
    accentAlpha: 0.42,
    accentKind: 'ridges',
    elevation: 3,
    highlight: 0xe0c28a,
    shadow: 0x5c452d,
    transition: 0xb08b5d,
  },
  water: {
    fill: 0x4f91ba,
    stroke: 0x2c5f83,
    strokeAlpha: 0.5,
    accent: 0xa8d4e6,
    accentAlpha: 0.42,
    accentKind: 'waves',
    elevation: 0,
    highlight: 0x9ed0e1,
    shadow: 0x2a5c7e,
    transition: 0x78b9cf,
  },
}

export const mapVisualTheme = {
  background: 0x172129,
  fog: {
    unknownFill: 'rgba(4, 9, 13, 0.9)',
    exploredFill: 'rgba(11, 22, 24, 0.5)',
  },
  selection: {
    stroke: 0xfff0a3,
    width: 3,
  },
  tile: {
    defaultStroke: 0x2a332f,
  },
  buildHint: {
    fill: 0xf2d06b,
    fillAlpha: 0.18,
    stroke: 0xffd36c,
    strokeAlpha: 0.9,
  },
  objectiveHint: {
    fill: 0x77c8ff,
    fillAlpha: 0.14,
    stroke: 0x7fd5ff,
    strokeAlpha: 0.95,
  },
} as const

export function getTerrainVisualStyle(terrainId: string, fallbackFill: number): TerrainVisualStyle {
  return terrainStyles[terrainId] ?? {
    fill: fallbackFill,
    stroke: mapVisualTheme.tile.defaultStroke,
    strokeAlpha: 0.4,
    accent: 0xffffff,
    accentAlpha: 0,
    accentKind: 'none',
    elevation: 1,
    highlight: 0xffffff,
    shadow: mapVisualTheme.tile.defaultStroke,
    transition: fallbackFill,
  }
}

export function getUnitVisualKind(typeId: string): MapVisualUnitKind {
  if (typeId === 'unit:scout') {
    return 'scout'
  }

  if (typeId === 'unit:warrior') {
    return 'warrior'
  }

  if (typeId === 'unit:settler') {
    return 'settler'
  }

  return 'unknown'
}

export function getUnitVisualStyle(owner: MapVisualOwner): UnitVisualStyle {
  if (owner === 'enemy') {
    return {
      detail: 0xffd0c7,
      fill: 0xa83f35,
      stroke: 0x5f1f1a,
    }
  }

  if (owner === 'neutral') {
    return {
      detail: 0xf7f0d8,
      fill: 0x7d8388,
      stroke: 0x3e4548,
    }
  }

  return {
    detail: 0x2d3b30,
    fill: 0xf1d36e,
    stroke: 0x5c4a1a,
  }
}

export function getCityVisualStyle(owner: MapVisualOwner): CityVisualStyle {
  if (owner === 'enemy') {
    return {
      fill: 0xc66a4c,
      roof: 0x7b2e27,
      stroke: 0x4d1b18,
    }
  }

  if (owner === 'neutral') {
    return {
      fill: 0xb7bdba,
      roof: 0x697271,
      stroke: 0x3f4747,
    }
  }

  return {
    fill: 0xf3e5b0,
    roof: 0x8b6a32,
    stroke: 0x58411d,
  }
}
