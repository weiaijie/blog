export type ModelAssetGroup = 'terrain' | 'transition' | 'unit' | 'buildable'
export type ModelAssetStatus = 'spec' | 'graybox' | 'source-needed' | 'ready-for-lab'

export type ModelAssetDefinition = {
  id: string
  label: string
  group: ModelAssetGroup
  priority: number
  sourceFile: string
  runtimeFile: string
  lodFiles: string[]
  status: ModelAssetStatus
  blocker: string
  silhouette: string
  materialNotes: string
  acceptance: string[]
}

export const modelAssetManifest: ModelAssetDefinition[] = [
  {
    id: 'terrain-grassland',
    label: '草原 / 平原地块',
    group: 'terrain',
    priority: 4,
    sourceFile: 'source/terrain/terrain-grassland.blend',
    runtimeFile: 'terrain/terrain-grassland-lod0.glb',
    lodFiles: ['terrain/terrain-grassland-lod1.glb'],
    status: 'ready-for-lab',
    blocker: 'Blender source and GLB have been generated from the grassland reference; keep in visual-lab validation until top readability, side layering, and adjacency fit are accepted.',
    silhouette: '平坦开阔的六边形草地，顶部有微起伏草皮、成熟草丛、野花点缀、散落小石和裸土斑，侧面保留清晰土壤分层。',
    materialNotes: '草绿色主调叠加黄绿草叶、白/黄/紫小花、干草色裸土、灰褐小石；侧壁分为草皮土壤、腐殖土、黏土、碎石和基岩层。',
    acceptance: [
      '俯视 45 度仍能看到地表起伏和坡边厚度。',
      '和森林、丘陵、水域相邻时边缘有过渡空间。',
      '移动端小尺寸下不和森林混淆。',
    ],
  },
  {
    id: 'terrain-forest',
    label: '森林地块',
    group: 'terrain',
    priority: 5,
    sourceFile: 'source/terrain/terrain-forest.blend',
    runtimeFile: 'terrain/terrain-forest-lod0.glb',
    lodFiles: ['terrain/terrain-forest-lod1.glb'],
    status: 'graybox',
    blocker: '需要确定树冠数量、树高上限和单位遮挡规则，再进入源文件制作。',
    silhouette: '地表上有 4-6 组不同高度树冠，外圈留林缘碎边，不能只放三个圆锥。',
    materialNotes: '深绿、灰绿和少量暖色树干；树冠要有明暗层次，林缘压住草地。',
    acceptance: [
      '森林边界不硬切，单块和连片森林都能读出来。',
      '树冠高度不遮住单位轮廓。',
      '低 LOD 仍保留林冠团块而不是退化成纯色块。',
    ],
  },
  {
    id: 'terrain-hill',
    label: '丘陵 / 山脊地块',
    group: 'terrain',
    priority: 3,
    sourceFile: 'source/terrain/terrain-hill.blend',
    runtimeFile: 'terrain/terrain-hill-lod0.glb',
    lodFiles: ['terrain/terrain-hill-lod1.glb'],
    status: 'ready-for-lab',
    blocker: 'Blender source and GLB have been generated; keep in visual-lab validation until slope direction, ridge readability, and adjacency fit are accepted.',
    silhouette: '连续坡面和山脊线，山体从坡脚抬起，不能像独立尖锥插在平地上。',
    materialNotes: '土褐、浅岩面和背光坡面分层；高光只放在山脊，不铺满顶部。',
    acceptance: [
      '草地到丘陵有坡脚缓冲。',
      '相邻丘陵能连成山脉方向。',
      '山体高度明显但不压过城市和单位识别。',
    ],
  },
  {
    id: 'terrain-water',
    label: '水域地块',
    group: 'terrain',
    priority: 1,
    sourceFile: 'source/terrain/terrain-water.blend',
    runtimeFile: 'terrain/terrain-water-lod0.glb',
    lodFiles: ['terrain/terrain-water-lod1.glb'],
    status: 'ready-for-lab',
    blocker: 'Blender source and GLB have been generated; keep in visual-lab validation until water body continuity, shoal readability, and shoreline fit are accepted.',
    silhouette: '低洼水盆、连续水面、浅滩岸线和少量水草，不能是蓝色圆片。',
    materialNotes: '深浅蓝绿水面叠加浅滩米色；波纹用轻量材质或贴图，不靠复杂网格。',
    acceptance: [
      '水陆相邻时岸线清楚，不像两个硬拼六边形。',
      '多块水域相邻时视觉上连成水体。',
      '水面动画只改变材质/UV，不改变规则坐标。',
    ],
  },
  {
    id: 'transition-shoreline',
    label: '水陆岸线过渡',
    group: 'transition',
    priority: 2,
    sourceFile: 'source/transitions/transition-shoreline.blend',
    runtimeFile: 'transitions/transition-shoreline-lod0.glb',
    lodFiles: ['transitions/transition-shoreline-lod1.glb'],
    status: 'ready-for-lab',
    blocker: 'Blender source and GLB have been generated; keep in visual-lab validation until stitchable shoreline, foam line, and land-water transition are accepted.',
    silhouette: '浅滩、泡沫线、岸边草和水面边缘组成一条可拼接边。',
    materialNotes: '米色浅滩过渡到蓝绿水面，泡沫线要轻，不抢地块主体。',
    acceptance: [
      '岸线能沿六边形边拼接。',
      '和草地、森林、丘陵岸边都能共用或派生。',
      '缩放时不闪烁、不出现明显缝隙。',
    ],
  },
  {
    id: 'transition-forest-edge',
    label: '草地到森林林缘',
    group: 'transition',
    priority: 6,
    sourceFile: 'source/transitions/transition-forest-edge.blend',
    runtimeFile: 'transitions/transition-forest-edge-lod0.glb',
    lodFiles: ['transitions/transition-forest-edge-lod1.glb'],
    status: 'spec',
    blocker: '需要和森林地块一起确定树影、林缘密度和连片森林去边线策略。',
    silhouette: '碎草、低矮树丛和树影形成软边，不用直线切开草地与森林。',
    materialNotes: '草绿到深绿之间要有中间色，树影压暗边缘。',
    acceptance: [
      '单块森林边界自然。',
      '连片森林内部不重复显示过多边线。',
      '单位站在林缘附近仍可读。',
    ],
  },
  {
    id: 'transition-hill-foot',
    label: '草地到丘陵坡脚',
    group: 'transition',
    priority: 7,
    sourceFile: 'source/transitions/transition-hill-foot.blend',
    runtimeFile: 'transitions/transition-hill-foot-lod0.glb',
    lodFiles: ['transitions/transition-hill-foot-lod1.glb'],
    status: 'spec',
    blocker: '需要和丘陵地块统一坡脚高度、坡向和山脊拼接方向。',
    silhouette: '缓坡、碎石和草坡脚，说明高度从平地逐步抬起。',
    materialNotes: '草色、土褐和浅岩面按坡向分布，不做单条硬边。',
    acceptance: [
      '丘陵高度变化有原因，不像平地上插模型。',
      '坡脚方向在俯视视角可判断。',
      '和山脊模型拼接时不露缝。',
    ],
  },
  {
    id: 'unit-scout',
    label: '侦察兵单位',
    group: 'unit',
    priority: 8,
    sourceFile: 'source/units/unit-scout.blend',
    runtimeFile: 'units/unit-scout-idle.glb',
    lodFiles: ['units/unit-scout-lod1.glb'],
    status: 'source-needed',
    blocker: '需要先完成单位比例规范，避免单位在地块起伏上过大或被遮挡。',
    silhouette: '小体量、背包或望远镜符号、轻装轮廓，和战士明显区分。',
    materialNotes: '中性色衣物加阵营色小旗或肩章，避免大面积高饱和色。',
    acceptance: [
      '在森林和丘陵上仍能看清单位类型。',
      'idle 动画是轻微呼吸或观察动作。',
      '选中态来自表现层，不写规则状态。',
    ],
  },
  {
    id: 'unit-warrior',
    label: '战士单位',
    group: 'unit',
    priority: 9,
    sourceFile: 'source/units/unit-warrior.blend',
    runtimeFile: 'units/unit-warrior-idle.glb',
    lodFiles: ['units/unit-warrior-lod1.glb'],
    status: 'source-needed',
    blocker: '需要确定阵营色、武器/盾牌轮廓和攻击动画触发方式。',
    silhouette: '盾牌或武器形成强识别轮廓，站姿稳定，不和侦察兵混淆。',
    materialNotes: '阵营色放在盾牌、布条或头盔细节上，不覆盖整个模型。',
    acceptance: [
      '俯视远距离能读出战斗单位。',
      '攻击动画只能响应已确认规则结果。',
      '和城市/森林叠放时层级清楚。',
    ],
  },
  {
    id: 'unit-settler',
    label: '开拓者单位',
    group: 'unit',
    priority: 10,
    sourceFile: 'source/units/unit-settler.blend',
    runtimeFile: 'units/unit-settler-idle.glb',
    lodFiles: ['units/unit-settler-lod1.glb'],
    status: 'source-needed',
    blocker: '需要和可建城点提示一起设计，避免选中态和建城提示互相遮挡。',
    silhouette: '旗帜、行囊或推车形成非战斗轮廓，强调建设用途。',
    materialNotes: '暖色布料和阵营色旗帜；旗帜动画独立于规则状态。',
    acceptance: [
      '选中后可建设提示清楚但不误导合法性。',
      'idle 旗帜轻摆，不影响点击区域。',
      '和 city-site 提示共存时不遮挡。',
    ],
  },
  {
    id: 'buildable-city-site',
    label: '可建城点提示',
    group: 'buildable',
    priority: 11,
    sourceFile: 'source/buildables/buildable-city-site.blend',
    runtimeFile: 'buildables/buildable-city-site-lod0.glb',
    lodFiles: ['buildables/buildable-city-site-lod1.glb'],
    status: 'source-needed',
    blocker: '需要未来 Validator 或规则层合法性结果作为数据来源，当前只能做表现占位。',
    silhouette: '地表投影、木桩或规划线，表现候选地点而不是已经建成的城市。',
    materialNotes: '半透明暖色提示，必须弱于真实城市模型。',
    acceptance: [
      '只表现 UI 派生候选，不写入 GameState。',
      '合法/非法状态由规则层或 Validator 提供。',
      '提示不会遮住地形和单位。',
    ],
  },
  {
    id: 'buildable-city-center',
    label: '城市中心',
    group: 'buildable',
    priority: 12,
    sourceFile: 'source/buildables/buildable-city-center.blend',
    runtimeFile: 'buildables/buildable-city-center-lod0.glb',
    lodFiles: ['buildables/buildable-city-center-lod1.glb'],
    status: 'ready-for-lab',
    blocker: 'Blender source and GLB have been generated; keep in visual-lab validation until city scale, faction color, and tile readability are accepted.',
    silhouette: '六边形厚底座上的主城堡、中心高塔、城墙、角塔、蓝色屋顶、旗帜和少量道路/农田点缀，能看出这是主城而不是普通建筑。',
    materialNotes: '暖石材墙体、蓝色屋顶、木门、红色旗帜、浅色道路和少量金色农田；城市体量要高于单位但不能压过整块地形。',
    acceptance: [
      '城市中心比单位更稳重，但不遮挡相邻地块。',
      '归属色清楚。',
      '生产状态只显示已有 UI 数据。',
    ],
  },
  {
    id: 'buildable-outpost',
    label: '前哨占位',
    group: 'buildable',
    priority: 13,
    sourceFile: 'source/buildables/buildable-outpost.blend',
    runtimeFile: 'buildables/buildable-outpost-lod0.glb',
    lodFiles: ['buildables/buildable-outpost-lod1.glb'],
    status: 'source-needed',
    blocker: '当前规则主线未启用前哨，先保留资产规格，不迁入主线。',
    silhouette: '瞭望塔、小旗和围栏，作为后续规则资产预留。',
    materialNotes: '木材和布旗，整体小于城市中心。',
    acceptance: [
      '不进入当前规则主线。',
      '作为可读占位可被独立开关。',
      '未来迁入前必须补规则来源。',
    ],
  },
]

export const modelAssetGroups: ModelAssetGroup[] = ['terrain', 'transition', 'unit', 'buildable']

export function getModelAssetsByGroup(group: ModelAssetGroup): ModelAssetDefinition[] {
  return modelAssetManifest.filter((asset) => asset.group === group).sort(sortModelAssetsByPriority)
}

export function getModelAssetProductionQueue(): ModelAssetDefinition[] {
  return [...modelAssetManifest].sort(sortModelAssetsByPriority)
}

export function getModelAssetStatusCounts(): Record<ModelAssetStatus, number> {
  return modelAssetManifest.reduce<Record<ModelAssetStatus, number>>(
    (counts, asset) => {
      counts[asset.status] += 1
      return counts
    },
    {
      graybox: 0,
      'ready-for-lab': 0,
      'source-needed': 0,
      spec: 0,
    },
  )
}

function sortModelAssetsByPriority(left: ModelAssetDefinition, right: ModelAssetDefinition): number {
  return left.priority - right.priority
}
