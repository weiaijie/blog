export type TerrainModuleId = 'grassland' | 'forest' | 'hill' | 'water'
export type UnitModuleId = 'scout' | 'warrior' | 'settler'
export type BuildableModuleId = 'city-site' | 'city-center' | 'outpost'

export type TileModuleDefinition = {
  id: TerrainModuleId
  label: string
  elevation: 'low' | 'medium' | 'high' | 'water'
  baseClassName: string
  layers: string[]
  transitionNotes: string
  animationNotes: string
}

export type UnitModuleDefinition = {
  id: UnitModuleId
  label: string
  className: string
  animationNotes: string
}

export type BuildableModuleDefinition = {
  id: BuildableModuleId
  label: string
  className: string
  placementNotes: string
}

export type TransitionModuleDefinition = {
  id: string
  label: string
  left: TerrainModuleId
  right: TerrainModuleId
}

export const terrainModules: TileModuleDefinition[] = [
  {
    id: 'grassland',
    label: '草原 / 平原',
    elevation: 'low',
    baseClassName: 'terrain-grassland',
    layers: ['低起伏地表', '短草纹理', '浅色坡面'],
    transitionNotes: '和森林用林缘碎草过渡；和丘陵用缓坡脚线过渡；和水域用浅岸线过渡。',
    animationNotes: '默认静态；hover 时轻微抬升；selected 时外圈脉冲。',
  },
  {
    id: 'forest',
    label: '森林',
    elevation: 'medium',
    baseClassName: 'terrain-forest',
    layers: ['中起伏地表', '树冠簇', '深色林缘'],
    transitionNotes: '森林边缘不硬切，靠外圈树影和草地碎边压住相邻地形。',
    animationNotes: 'idle 时树冠轻微摆动；hover 时树冠亮度提高。',
  },
  {
    id: 'hill',
    label: '丘陵 / 山脊',
    elevation: 'high',
    baseClassName: 'terrain-hill',
    layers: ['高起伏地表', '山脊高光', '背光坡面'],
    transitionNotes: '丘陵向草地/森林用坡脚线过渡；相邻丘陵连接成连续山脊。',
    animationNotes: '默认静态；selected 时山脊高光增强，不做持续摇动。',
  },
  {
    id: 'water',
    label: '水域',
    elevation: 'water',
    baseClassName: 'terrain-water',
    layers: ['低洼水面', '岸线泡沫', '水波线'],
    transitionNotes: '水陆交界必须显示浅岸线；相邻水域连成连续水面。',
    animationNotes: 'idle 时水波横向缓动；hover 时水面高光增强。',
  },
]

export const transitionModules: TransitionModuleDefinition[] = [
  {
    id: 'shoreline',
    label: '水陆岸线',
    left: 'water',
    right: 'grassland',
  },
  {
    id: 'forest-edge',
    label: '草地到森林',
    left: 'grassland',
    right: 'forest',
  },
  {
    id: 'hill-foot',
    label: '草地到丘陵',
    left: 'grassland',
    right: 'hill',
  },
]

export const unitModules: UnitModuleDefinition[] = [
  {
    id: 'scout',
    label: '侦察兵',
    className: 'unit-scout',
    animationNotes: 'idle 轻微呼吸；移动动画后续做路径插值，不提前改规则坐标。',
  },
  {
    id: 'warrior',
    label: '战士',
    className: 'unit-warrior',
    animationNotes: 'idle 稳定站立；攻击动画只响应已确认 ATTACK 结果。',
  },
  {
    id: 'settler',
    label: '开拓者',
    className: 'unit-settler',
    animationNotes: 'idle 旗帜轻摆；选中后显示可建设地块提示。',
  },
]

export const buildableModules: BuildableModuleDefinition[] = [
  {
    id: 'city-site',
    label: '可建城点',
    className: 'buildable-city-site',
    placementNotes: '只表现 UI 派生候选，不写入 GameState；合法性以后必须来自 Validator。',
  },
  {
    id: 'city-center',
    label: '城市中心',
    className: 'buildable-city-center',
    placementNotes: '显示归属、生产状态和可选中边框；不在地图预览层计算产出。',
  },
  {
    id: 'outpost',
    label: '前哨占位',
    className: 'buildable-outpost',
    placementNotes: '预留资产，不进入当前规则主线。',
  },
]
