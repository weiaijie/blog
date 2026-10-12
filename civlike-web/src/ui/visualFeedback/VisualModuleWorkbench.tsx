import {
  getModelAssetsByGroup,
  getModelAssetProductionQueue,
  getModelAssetStatusCounts,
  modelAssetGroups,
  type ModelAssetDefinition,
  type ModelAssetGroup,
} from '../../render/assets/mapModelAssetManifest'
import {
  aiUsageBoundaries,
  civMapVisualLayers,
  minimumCivilizationAssetPack,
  productionRoute,
  recommendedToolchains,
  targetArtDirection,
  type ProductionPlanCard,
} from '../../render/assets/mapVisualProductionPlan'
import {
  buildableModules,
  terrainModules,
  transitionModules,
  unitModules,
  type TileModuleDefinition,
} from '../../render/visuals/tileModuleCatalog'
import { ThreeModuleViewer } from './ThreeModuleViewer'

const assetProductionQueue = getModelAssetProductionQueue()
const assetStatusCounts = getModelAssetStatusCounts()
const nextProductionAssets = assetProductionQueue.slice(0, 3)

export function VisualModuleWorkbench() {
  return (
    <main className="visual-workbench" aria-label="地图视觉模块工坊">
      <header className="visual-workbench-header">
        <p className="eyebrow">视觉支线</p>
        <h1>地图模块工坊</h1>
        <p>
          先用 Three.js 做地图关系和俯视可读性评审；精细地块、单位和建筑模型走 Blender/glTF
          资产管线，确认后再迁入主线地图。
        </p>
      </header>

      <section className="visual-section visual-review-section" aria-label="3D 地图模型评审台">
        <div className="visual-review-copy">
          <p className="eyebrow">Model Review</p>
          <h2>3D 地图组合评审台</h2>
          <p>
            这里优先看相邻地块是否像一张真实地图：水陆岸线、森林边缘、丘陵坡脚、道路和高度层次必须一起检查，
            不能只看单块贴色。
          </p>
        </div>
        <div className="terrain-review-stage">
          <ThreeModuleViewer spec={{ kind: 'terrain-set' }} />
        </div>
      </section>

      <section className="visual-section" aria-label="美术资产管线">
        <div className="visual-section-heading">
          <p className="eyebrow">Asset Pipeline</p>
          <h2>精细模型不在代码里硬搓</h2>
        </div>
        <div className="asset-pipeline-grid">
          {assetPipelineSteps.map((step) => (
            <article key={step.title} className="pipeline-card">
              <strong>{step.title}</strong>
              <p>{step.detail}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="visual-section" aria-label="文明式地图制作路线">
        <div className="visual-section-heading">
          <p className="eyebrow">Production Route</p>
          <h2>文明式地图制作路线</h2>
        </div>
        <div className="production-route-grid">
          <PlanCardList title="目标美术方向" items={targetArtDirection} />
          <PlanCardList title="地图视觉层次" items={civMapVisualLayers} />
          <PlanCardList title="AI 使用边界" items={aiUsageBoundaries} />
        </div>
        <div className="toolchain-table" aria-label="推荐工具组合">
          {recommendedToolchains.map((toolchain) => (
            <article key={toolchain.id} className="toolchain-row">
              <strong>{toolchain.label}</strong>
              <span>{toolchain.tools}</span>
              <p>{toolchain.useCase}</p>
            </article>
          ))}
        </div>
        <div className="minimum-pack-panel">
          <div>
            <p className="eyebrow">Minimum Pack</p>
            <h3>最小可行资产包</h3>
          </div>
          <div className="minimum-pack-list">
            {minimumCivilizationAssetPack.map((asset) => (
              <span key={asset}>{asset}</span>
            ))}
          </div>
        </div>
        <div className="route-step-grid">
          {productionRoute.map((step) => (
            <article key={step.title} className="route-step-card">
              <strong>{step.title}</strong>
              <p>{step.detail}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="visual-section" aria-label="模型资产清单">
        <div className="visual-section-heading">
          <p className="eyebrow">Model Manifest</p>
          <h2>Blender/glTF 制作清单</h2>
        </div>
        <div className="asset-production-board">
          <div className="asset-status-row" aria-label="资产状态统计">
            {assetStatusOrder.map((status) => (
              <div key={status} className="asset-status-tile">
                <span>{assetStatusLabels[status]}</span>
                <strong>{assetStatusCounts[status]}</strong>
              </div>
            ))}
          </div>
          <div className="asset-next-panel">
            <div>
              <p className="eyebrow">Next Assets</p>
              <h3>下一轮优先制作</h3>
            </div>
            <ol>
              {nextProductionAssets.map((asset) => (
                <li key={asset.id}>
                  <strong>{asset.label}</strong>
                  <span>{asset.blocker}</span>
                </li>
              ))}
            </ol>
          </div>
        </div>
        <div className="asset-manifest-grid">
          {modelAssetGroups.map((group) => (
            <AssetGroupColumn key={group} group={group} assets={getModelAssetsByGroup(group)} />
          ))}
        </div>
      </section>

      <section className="visual-section" aria-label="地形模块">
        <div className="visual-section-heading">
          <p className="eyebrow">Tile Modules</p>
          <h2>地形块灰盒模型</h2>
        </div>
        <div className="module-grid">
          {terrainModules.map((module) => (
            <TerrainModuleCard key={module.id} module={module} />
          ))}
        </div>
      </section>

      <section className="visual-section" aria-label="地形过渡">
        <div className="visual-section-heading">
          <p className="eyebrow">Transitions</p>
          <h2>相邻地形过渡样例</h2>
        </div>
        <div className="transition-grid">
          {transitionModules.map((transition) => (
            <article key={transition.id} className="transition-card">
              <ThreeModuleViewer
                spec={{
                  kind: 'transition',
                  leftTerrainId: transition.left,
                  rightTerrainId: transition.right,
                }}
              />
              <strong>{transition.label}</strong>
            </article>
          ))}
        </div>
      </section>

      <section className="visual-section" aria-label="单位模块">
        <div className="visual-section-heading">
          <p className="eyebrow">Units</p>
          <h2>单位显示与动画状态</h2>
        </div>
        <div className="unit-grid">
          {unitModules.map((unit) => (
            <article key={unit.id} className="unit-card">
              <ThreeModuleViewer spec={{ kind: 'unit', unitId: unit.id }} />
              <strong>{unit.label}</strong>
              <p>{unit.animationNotes}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="visual-section" aria-label="可建设对象模块">
        <div className="visual-section-heading">
          <p className="eyebrow">Buildables</p>
          <h2>可建设对象与占位</h2>
        </div>
        <div className="unit-grid">
          {buildableModules.map((item) => (
            <article key={item.id} className="unit-card">
              <ThreeModuleViewer spec={{ buildableId: item.id, kind: 'buildable' }} />
              <strong>{item.label}</strong>
              <p>{item.placementNotes}</p>
            </article>
          ))}
        </div>
      </section>
    </main>
  )
}

const assetPipelineSteps = [
  {
    title: 'Blender 设计',
    detail: '每类地块、单位、建筑单独建模，统一俯视角、比例、地块半径、材质色板和轮廓语言。',
  },
  {
    title: 'glTF 资产',
    detail: '导出低面数 glTF/GLB，按 terrain、transition、unit、buildable 分目录保存，并保留源文件命名。',
  },
  {
    title: '工坊验收',
    detail: '先在 visual-lab 中检查组合关系、动画状态、LOD 和移动端可读性，再决定是否进入主线 Pixi 地图。',
  },
]

const assetGroupLabels: Record<ModelAssetGroup, string> = {
  buildable: '建筑 / 可建设',
  terrain: '地形块',
  transition: '地形过渡',
  unit: '单位',
}

const assetStatusLabels: Record<ModelAssetDefinition['status'], string> = {
  graybox: '灰盒已有',
  'ready-for-lab': '待工坊验收',
  'source-needed': '待制作源文件',
  spec: '规格已定义',
}

const assetStatusOrder: ModelAssetDefinition['status'][] = ['graybox', 'spec', 'source-needed', 'ready-for-lab']

function AssetGroupColumn({ assets, group }: { assets: ModelAssetDefinition[]; group: ModelAssetGroup }) {
  return (
    <article className="asset-group-column">
      <h3>{assetGroupLabels[group]}</h3>
      <div className="asset-card-list">
        {assets.map((asset) => (
          <AssetManifestCard key={asset.id} asset={asset} />
        ))}
      </div>
    </article>
  )
}

function PlanCardList({ items, title }: { items: ProductionPlanCard[]; title: string }) {
  return (
    <article className="plan-card-list">
      <h3>{title}</h3>
      <div>
        {items.map((item) => (
          <section key={item.title}>
            <strong>{item.title}</strong>
            <p>{item.detail}</p>
          </section>
        ))}
      </div>
    </article>
  )
}

function AssetManifestCard({ asset }: { asset: ModelAssetDefinition }) {
  return (
    <section className="asset-manifest-card">
      <div className="asset-card-header">
        <strong>{asset.label}</strong>
        <span data-status={asset.status}>{assetStatusLabels[asset.status]}</span>
      </div>
      <p className="asset-priority">P{asset.priority}</p>
      <dl>
        <div>
          <dt>源文件</dt>
          <dd>{asset.sourceFile}</dd>
        </div>
        <div>
          <dt>运行时</dt>
          <dd>{asset.runtimeFile}</dd>
        </div>
      </dl>
      <p>{asset.silhouette}</p>
      <details>
        <summary>验收和阻塞</summary>
        <p>{asset.blocker}</p>
        <ul>
          {asset.acceptance.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </details>
    </section>
  )
}

function TerrainModuleCard({ module }: { module: TileModuleDefinition }) {
  return (
    <article className="module-card">
      <div className="module-stage">
        <ThreeModuleViewer spec={{ kind: 'terrain', terrainId: module.id }} />
      </div>
      <div className="module-copy">
        <strong>{module.label}</strong>
        <span>起伏：{module.elevation}</span>
        <p>{module.layers.join(' / ')}</p>
        <p>{module.transitionNotes}</p>
        <p>{module.animationNotes}</p>
      </div>
    </article>
  )
}
