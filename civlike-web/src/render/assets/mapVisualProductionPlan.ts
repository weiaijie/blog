export type ProductionPlanCard = {
  title: string
  detail: string
}

export type ToolchainOption = {
  id: string
  label: string
  tools: string
  useCase: string
}

export const targetArtDirection: ProductionPlanCard[] = [
  {
    title: '半写实微缩景观',
    detail: '地形自然但色块清晰，山体、树、河流、资源和城市都比真实比例更夸张，优先保证策略地图一眼可读。',
  },
  {
    title: '模块化资产库',
    detail: '逻辑仍是六边形格子，画面由基础地块、高度变体、边缘过渡、装饰物和特效层自动组合。',
  },
  {
    title: '弱化格子硬边',
    detail: '通过过渡边模型、材质混合、泡沫、草丛、岩石和树影遮住硬切边，不把每个 hex 做成孤立积木。',
  },
]

export const civMapVisualLayers: ProductionPlanCard[] = [
  { title: '六边形逻辑格子', detail: '规则层只提供地块数据和相邻关系，视觉层负责组合模型和过渡。' },
  { title: '地形高度变化', detail: '平地、丘陵、山脉、海岸和水域必须有明确高度层次。' },
  { title: '材质变化', detail: '草地、沙漠、雪地、岩石、水面使用统一色板，但保留可读差异。' },
  { title: '边缘过渡', detail: '草地到沙漠、水陆岸线、山脚到平原都需要过渡资产或 shader 混合。' },
  { title: '装饰物', detail: '树、石头、资源、道路、河流、城市和单位用模块插槽挂载。' },
  { title: '光照与气氛', detail: '柔和太阳光、AO、接触阴影、轻雾、水面高光和边缘描边统一最终风格。' },
]

export const recommendedToolchains: ToolchainOption[] = [
  {
    id: 'starter',
    label: '新手 / 独立开发',
    tools: 'Blender + Godot/Unity + Meshy/Tripo + ChatGPT Images/Midjourney',
    useCase: '低成本快速做统一风格的 hex 地块资产库和可玩原型。',
  },
  {
    id: 'prototype',
    label: '3D 策略游戏原型',
    tools: 'Blender + Unity + Shader Graph + 程序化六边形生成',
    useCase: '适合先验证地块组合、过渡边、单位占位和点击反馈。',
  },
  {
    id: 'indie',
    label: '商业独立游戏',
    tools: 'Blender + Unity + Substance 3D + Gaea + Meshy/Tripo',
    useCase: '适合制作可发布级别的地形、材质、水岸和资源道具。',
  },
  {
    id: 'professional',
    label: '专业高质量方案',
    tools: 'Houdini + Unreal PCG + Gaea/World Creator + Substance + SpeedTree',
    useCase: '适合大世界、复杂生物群系、程序化城市/森林和高质量地形。',
  },
]

export const aiUsageBoundaries: ProductionPlanCard[] = [
  {
    title: '适合 AI',
    detail: '概念图、风格探索、颜色方案、贴图参考、资源图标、小道具草模和地图缩略图。',
  },
  {
    title: '不适合 AI 直接定稿',
    detail: '整套可商用地块模型、精确拓扑 hex、道路/河流连接系统、最终 shader 和地图生成算法。',
  },
  {
    title: '进入游戏前必须清理',
    detail: 'AI 3D 草模需要进 Blender 做减面、拓扑、UV、比例统一、材质重做和 glTF/GLB 导出。',
  },
]

export const minimumCivilizationAssetPack = [
  'Grass_Flat',
  'Grass_Hill',
  'Forest',
  'Desert',
  'Mountain',
  'Coast',
  'Ocean',
  'River_Edge',
  'Road_Edge',
  'City_Center',
  'Farm',
  'Mine',
  'Iron_Resource',
  'Wheat_Resource',
]

export const productionRoute: ProductionPlanCard[] = [
  { title: '1. 风格参考', detail: '先生成或收集 20 张文明式地图参考图，选 1 张作为色彩、比例和光照目标。' },
  { title: '2. 基础地块', detail: '在 Blender 里制作草地、水域、丘陵、森林和海岸的基础 hex 与变体。' },
  { title: '3. 过渡系统', detail: '制作水陆岸线、林缘、坡脚、道路和河流边缘，保证相邻地块不硬切。' },
  { title: '4. 工坊验收', detail: '导出 glTF/GLB 后进入 visual-lab 检查组合关系、LOD、移动端可读性和动画状态。' },
  { title: '5. 主线迁入', detail: '只有通过工坊验收的资产和参数才能迁入 Pixi 地图，且不得改变规则层结果。' },
]
