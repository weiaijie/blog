# 16 WebGL 渲染专项方案

本文档细化第一版 Web 文明类原型的地图渲染方案。它承接现有文档的核心决策：

| 决策 | 结论 |
| --- | --- |
| 渲染技术 | `PixiJS + WebGL/WebGL2`。 |
| UI 技术 | `React/DOM` 承担复杂面板、Tooltip、调试面板、百科。 |
| 规则边界 | `GameState + Command + Validator + Simulation` 是规则层，渲染层只读状态。 |
| 坐标边界 | 规则层使用 `GridCoord`，渲染层使用 `WorldPoint`，输入层使用 `ScreenPoint`。 |
| 第一版规模 | 默认 16x16，支持 12x12 到 20x20；1 玩家 + 1 AI；每方最多 3 城、10 单位。 |
| 渲染目标 | 桌面 60 FPS，低端设备不低于 30 FPS。 |

核心原则：**PixiJS 是地图表现层，不是规则引擎。** Tile、Unit、City 的真实状态来自 `GameState`；Sprite、Container、Graphics、Texture 都是 `RenderEngine` 内部缓存，不进入存档、Worker 或 Simulation。

## 一、渲染目标

| 目标 | 说明 | 验收方式 |
| --- | --- | --- |
| 地图清晰 | 地形、资源、城市、单位、可见性状态能一眼区分。 | 16x16 地图下截图检查，UI 面板不遮挡核心区域。 |
| 操作顺滑 | 拖拽平移、滚轮缩放、Hover、选中、路径预览不卡顿。 | Debug Panel 显示 FPS、p95 frame time、命中耗时。 |
| 可调试 | 能显示坐标、tileId、可见性、路径、AI 目标、渲染对象数量。 | Debug Render 页签和地图 Overlay 可开关。 |
| 可恢复 | WebGL context lost 后不白屏失控，至少能提示刷新，第二版可尝试恢复。 | 手动触发或模拟 context lost，记录错误事件。 |
| 可扩展 | 后续可以从方格切六边形，从半透明迷雾升级到 Shader，从 CPU 命中升级到 GPU picking。 | 坐标和渲染接口集中在 `RenderEngine` 与 `CoordinateSystem`。 |

## 二、渲染层级表

第一版采用一个 PixiJS `stage`，下面拆出稳定的地图世界容器和若干显示层。DOM UI 不放进 PixiJS 画布。

```txt
PixiJS Application
  stage
    rootWorldContainer              // camera 平移/缩放作用在这里
      terrainLayer                  // 地形 tile sprite
      terrainDetailLayer            // 河流、海岸、资源底图、地貌细节
      ownershipLayer                // 领土边界、城市范围
      cityLayer                     // 城市图标、城市名底板可选
      unitLayer                     // 单位 sprite、血条、移动力小标
      fogLayer                      // 未探索/已探索不可见/当前可见
      overlayLayer                  // 选中格、可移动范围、攻击范围、路径预览
      debugWorldLayer               // 坐标、tileId、AI 目标、寻路网格
    screenOverlayLayer              // 不随地图缩放的 Pixi overlay，第一版尽量少用
React DOM
  topBar / sidePanel / actionBar / tooltip / debugPanel
```

| 层级 | 内容 | PixiJS 对象建议 | 更新频率 | 第一版要求 |
| --- | --- | --- | --- | --- |
| `terrainLayer` | 平原、森林、丘陵、山脉、水域等基础地形。 | `Sprite` 池或 tile container。 | 地图生成、读档时重建；一般不逐帧更新。 | 必须。 |
| `terrainDetailLayer` | 资源底座、河流边、海岸、道路预留。 | `Sprite`，资源来自 atlas。 | 资源变化或地图变化时更新。 | 资源图标必须；道路第二版。 |
| `ownershipLayer` | 城市边界、领土色块、可工作地块。 | 少量 `Graphics` 或半透明 Sprite。 | 建城、领土变化、选中城市时更新。 | 建议。 |
| `cityLayer` | 城市图标、城防、生产提示、首都标记。 | `Sprite` + 少量 `BitmapText` 或 DOM Tooltip。 | 城市状态变化时更新。 | 必须。 |
| `unitLayer` | 侦察兵、战士、建造者、弓手。 | `Sprite` 池，必要时加血条子对象。 | 单位移动、受伤、创建、死亡时更新。 | 必须。 |
| `fogLayer` | 未探索黑幕、已探索灰幕、当前可见透明。 | 第一版半透明 Sprite/Graphics；第二版 RenderTexture 或 Shader。 | 视野变化时更新。 | 必须。 |
| `overlayLayer` | Hover、选中、可移动格、攻击范围、路径箭头。 | 复用 `GraphicsContext` 或 atlas Sprite。 | Hover/选择/路径变化时更新。 | 必须。 |
| `debugWorldLayer` | 坐标文字、tileId、可见性、AI 路径。 | `Graphics` + `BitmapText`，开发模式才创建。 | 调试开关或状态变化时更新。 | 必须可开关。 |
| `screenOverlayLayer` | 不随地图缩放的临时标记。 | 少量 `Container`。 | 少量事件反馈。 | 第一版尽量不用。 |

层级顺序固定，不在每帧动态排序大量对象。若局部对象需要前后关系，优先通过容器拆层解决；`zIndex/sortableChildren` 只用于少量对象。

## 三、WebGL 功能表

| 功能 | 游戏用途 | 第一版是否需要 | 推荐实现 |
| --- | --- | --- | --- |
| Tilemap 批量渲染 | 渲染地形格子。 | 必须 | 先用 PixiJS `Sprite` + atlas + 对象池；地图规模小，不急着自研 Mesh。 |
| 地图缩放/平移 | 拖拽地图、滚轮查看局势。 | 必须 | `rootWorldContainer.position/scale` + `CameraState`。 |
| 单位 Sprite 渲染 | 显示单位、阵营色、血量、移动力。 | 必须 | 单位 Sprite 池，阵营色用 tint 或独立帧。 |
| 资源图标渲染 | 在地块上显示粮食、矿产、特殊资源。 | 必须 | `icons-map` atlas，按可见性控制透明度。 |
| 选中高亮 | 当前单位、城市、地块、可行动目标。 | 必须 | `overlayLayer` 复用少量 Graphics/atlas 边框。 |
| 路径预览 | 显示移动路线、剩余移动力、不可达原因。 | 建议第一版做 | 寻路结果转折线/箭头；鼠标移动节流。 |
| 战争迷雾 | 区分未探索、已探索不可见、当前可见。 | 必须 | 第一版半透明覆盖；第二版 Shader/RenderTexture。 |
| Culling | 大地图只绘制视口附近对象。 | 第一版轻量 | 第一版可按 camera 计算可见 tile，隐藏视口外高频对象；第二版系统化。 |
| Texture Atlas | 减少纹理切换，统一资源 key。 | 必须 | 使用 `map-core`、`icons-map`、`units-core`。 |
| Minimap | 全局地图。 | 第二版 | 用缩略 RenderTexture 或 DOM canvas。 |
| 粒子/动效 | 建造完成、战斗、科技完成反馈。 | 第二版 | 少量 Pixi 动画或 sprite sheet。 |
| GPU Picking | 用颜色 ID 渲染离屏命中。 | 第一版不做 | 第一版 CPU 坐标换算；地图变复杂后再评估。 |
| Context Lost 处理 | WebGL 上下文丢失后的恢复。 | 第一版记录并提示 | 监听 canvas 事件；第二版尝试重建 renderer 和资源。 |
| WebGPU 后端 | 未来现代 GPU 能力。 | 不进第一版 | 只在 `RenderEngine` 接口和资源管线预留。 |

## 四、PixiJS 对象边界

| 对象 | 可以做 | 不可以做 |
| --- | --- | --- |
| `Application` | 初始化 canvas、renderer、ticker、resize。 | 保存规则状态或直接结算回合。 |
| `Container` | 管理地图层、相机变换、对象分组。 | 成为城市/单位的真实数据源。 |
| `Sprite` | 表示 tile、单位、资源、城市图标。 | 持有血量、移动力、产出等规则字段。 |
| `Graphics` | 绘制高亮、路径、调试线、边界。 | 每帧无脑 clear/rebuild 大量复杂图形。 |
| `Texture` / `Spritesheet` | 来自 atlas，由 `AssetManager` 管理。 | 写入 `GameState` 或普通存档。 |
| `Ticker` | 驱动动画、相机惯性、性能采样。 | 驱动规则结算；回合规则必须由 Command 触发。 |

推荐 `RenderEngine` 接口：

```ts
type RenderEngine = {
  init(options: RenderInitOptions): Promise<void>;
  mount(canvasHost: HTMLElement): void;
  resize(size: ViewportSize): void;
  sync(state: GameState, ui: RenderUIState): void;
  setCamera(camera: CameraState): void;
  getCamera(): CameraState;
  screenToTile(point: ScreenPoint): TileHitResult;
  tileToWorld(coord: GridCoord): WorldPoint;
  worldToScreen(point: WorldPoint): ScreenPoint;
  rebuildFromState(state: GameState): void;
  captureDiagnostics(): RenderDiagnostics;
  destroy(): void;
};
```

`sync` 只接受 `GameState` 和渲染用 `UIState`，例如选中对象、Hover 地块、路径预览、调试开关。它不能执行 `MOVE_UNIT`、`ATTACK_UNIT`、`END_TURN` 等规则动作。

## 五、坐标系统

第一版默认方格地图，保留六边形扩展点。

| 坐标 | 类型 | 归属 | 示例 |
| --- | --- | --- | --- |
| 规则坐标 | `GridCoord` | `GameState`、Simulation、寻路。 | `{ kind: "square", x: 3, y: 5 }` |
| 世界坐标 | `WorldPoint` | PixiJS 地图世界。 | `{ x: 192, y: 320 }` |
| 屏幕坐标 | `ScreenPoint` | 浏览器输入、Tooltip 锚点。 | `{ x: 640, y: 360 }` |
| 相机状态 | `CameraState` | UIState/RenderEngine。 | `{ x: -120, y: -80, zoom: 1.25 }` |

### 方格转换

第一版建议：

| 参数 | 推荐值 | 说明 |
| --- | --- | --- |
| `tileSize` | 64 px | 16x16 地图在桌面下清晰，缩放后仍好读。 |
| `tileOrigin` | `{ x: 0, y: 0 }` | 地图左上角世界坐标。 |
| `minZoom` | 0.6 | 能看全局。 |
| `maxZoom` | 2.0 | 能查看单位和资源细节。 |
| `defaultZoom` | 根据视口适配到 16x16 可见。 | 新局居中首都附近。 |

```ts
function gridToWorld(coord: GridCoord, tileSize: number): WorldPoint {
  return {
    x: coord.x * tileSize,
    y: coord.y * tileSize,
  };
}

function worldToGrid(point: WorldPoint, tileSize: number): GridCoord {
  return {
    kind: "square",
    x: Math.floor(point.x / tileSize),
    y: Math.floor(point.y / tileSize),
  };
}
```

屏幕坐标到地块：

```txt
PointerEvent.clientX/clientY
  -> 减去 canvas bounding rect
  -> 得到 ScreenPoint
  -> 应用 camera 逆变换
  -> 得到 WorldPoint
  -> worldToGrid
  -> 校验地图边界与可见性
  -> TileHitResult
```

`CameraState` 不进入 `GameState`，可以进入 LocalStorage 设置或 `UIState`。存档读档后默认定位首都，或者恢复上次相机设置，但不影响规则复现。

## 六、点击命中方案

### 第一版：CPU 坐标换算

第一版不做 GPU Picking。原因：

| 判断 | 结论 |
| --- | --- |
| 地图规模 | 12x12 到 20x20，CPU 计算足够快。 |
| 地形形态 | 默认方格，命中公式简单。 |
| 开发效率 | CPU 命中更容易调试，能直接输出坐标、tileId、失败原因。 |
| 可维护性 | 不需要额外离屏 framebuffer、颜色 ID、读像素同步开销。 |

命中结果结构：

```ts
type TileHitResult =
  | {
      kind: "tile";
      tileId: TileId;
      coord: GridCoord;
      world: WorldPoint;
      screen: ScreenPoint;
      visibleState: "unexplored" | "explored" | "visible";
      topObject?: { kind: "unit" | "city" | "resource"; id: string };
    }
  | {
      kind: "outside";
      screen: ScreenPoint;
      reason: "outside_canvas" | "outside_map" | "blocked_by_dom";
    };
```

### 命中优先级

| 优先级 | 对象 | 行为 |
| --- | --- | --- |
| 1 | DOM 面板和按钮 | DOM 自己处理，不透传到地图。 |
| 2 | 当前可见单位 | 点击选中单位；不可见敌军不能命中。 |
| 3 | 城市 | 点击打开城市面板。 |
| 4 | 地块资源/地块 | 点击地块面板；若已有单位选中，可预览移动。 |
| 5 | 未探索地块 | 不显示具体信息，只显示未探索。 |

### 右键移动

| 步骤 | 说明 |
| --- | --- |
| 1 | 当前 `UIState.selectedObject` 必须是己方可行动单位。 |
| 2 | `screenToTile` 得到目标地块。 |
| 3 | 请求寻路，第一版可主线程同步；若超过预算，迁移 Worker。 |
| 4 | 显示路径预览和移动力消耗。 |
| 5 | 玩家释放或确认后 dispatch `MOVE_UNIT` Command。 |
| 6 | Validator 拒绝时显示错误 Tooltip，不移动 Sprite。 |

### GPU Picking 评估

| 条件 | 是否需要 GPU Picking |
| --- | --- |
| 方格/六边形地块，地图小于 64x64 | 不需要。 |
| 地块形状规则，单位可通过空间索引命中 | 不需要。 |
| 大量不规则多边形、复杂遮挡、立体地图 | 可评估。 |
| 需要像素级命中透明区域 | 可评估。 |
| CPU 命中 p95 超过 2ms 且无法靠索引优化 | 可评估。 |

第二版仍优先优化 CPU 命中：空间索引、可见对象列表、命中缓存。GPU Picking 只有在地图形态复杂后再做。

## 七、Tilemap 批量渲染方案

第一版不要从零写 WebGL Tilemap。用 PixiJS Sprite + atlas 足够支撑 20x20，但要从一开始按可批处理的方式组织。

| 项 | 第一版做法 | 第二版升级 |
| --- | --- | --- |
| 地形 Sprite | 每个 tile 一个 Sprite，来自 `map-core` atlas。 | 视地图规模改为 Chunk Container、Mesh 或第三方 tilemap 插件。 |
| Tile 对象池 | 初始创建或读档重建；地形少变，不频繁销毁。 | 地图编辑器或大地图时做 chunk pool。 |
| 纹理来源 | 同一 atlas，减少纹理切换。 | 按 biome/era 拆 atlas，但控制同屏 atlas 数。 |
| 绘制顺序 | 同类 Sprite 尽量连续，减少 Sprite/Graphics 交错。 | 按层和材质分组。 |
| 静态缓存 | 16x16 可不缓存；若 terrain 很静态，可 cache as texture。 | chunk 级 `cacheAsTexture` 或 RenderTexture。 |
| 地图变更 | 地形变化少，直接替换 Sprite texture。 | 局部 dirty chunk 更新。 |

### 轻量 Chunk 骨架

第一版必须实现轻量 `ViewportManager + ChunkManager + TilePool` 骨架，但只服务 16x16/20x20，不做复杂 streaming。是否真正卸载视口外地形 Sprite 由 20x20 Spike 数据决定；接口、统计和 Debug 字段必须从第一版存在。

```ts
type TileChunkId = `chunk_${number}_${number}`;

type RenderChunk = {
  id: TileChunkId;
  bounds: GridRect;
  container: Container;
  dirty: boolean;
  visible: boolean;
};
```

第二版当地图超过 32x32 或地形层对象明显变多时，再把骨架升级为真实 chunk culling、cache texture、局部重建或 streaming。

## 八、战争迷雾方案

`GameState.map.tiles[tileId]` 已保存 `exploredBy` 和 `visibleBy`。渲染层只读取这些字段。

| 状态 | 玩家看到什么 | 第一版表现 | 规则限制 |
| --- | --- | --- | --- |
| 未探索 | 不知道地形、资源、单位。 | 黑色或深色覆盖，地形可完全隐藏。 | Tooltip 只显示“未探索”。 |
| 已探索但当前不可见 | 记得地形和城市旧信息，看不到新单位。 | 灰色半透明覆盖，资源/城市降低透明度。 | 敌军不显示，动态信息可能标记为旧情报。 |
| 当前可见 | 正常显示。 | 无覆盖或极轻覆盖。 | 可选中己方单位，可看到敌方单位。 |

第一版实现：

| 层 | 做法 |
| --- | --- |
| 未探索 | 每个未探索 tile 放一个深色半透明 Sprite 或 Graphics rect。 |
| 已探索不可见 | 每个不可见 tile 放一个灰色半透明 Sprite。 |
| 当前可见 | 不放 fog 覆盖。 |
| 更新时机 | 单位移动、城市视野变化、回合切换、读档。 |

第二版升级：

| 方向 | 说明 |
| --- | --- |
| RenderTexture | 把 fog mask 绘制到低分辨率纹理，再覆盖地图。 |
| Shader | 用可见性纹理采样，实现柔边、圆形视野、平滑过渡。 |
| 动画 | 新探索区域淡入，不影响规则。 |
| 性能 | 大地图时只更新 dirty 区域，不每回合重建全图。 |

注意：迷雾只改变表现，不能阻止 Simulation 访问自己的规则数据。AI 可见性由 AIReadableState 裁剪，不由 fogLayer 决定。

## 九、选中高亮与路径预览

### 高亮类型

| 类型 | 触发 | 表现 | 数据来源 |
| --- | --- | --- | --- |
| Hover 地块 | 鼠标悬停地图格。 | 细边框或浅色覆盖。 | `screenToTile`。 |
| 选中单位 | 点击己方单位。 | 单位描边、脚下圆环、可移动范围。 | `UIState.selectedObject` + Validator/Pathfinding。 |
| 选中城市 | 点击城市。 | 城市范围、工作地块、生产提示。 | City selector。 |
| 可移动范围 | 单位被选中。 | 蓝/绿色半透明 tile。 | 移动力、地形消耗、阻挡。 |
| 攻击范围 | 军事单位被选中。 | 红色边框或目标标记。 | 单位射程、敌我关系。 |
| 路径预览 | Hover/右键目标地块。 | 线段、箭头、回合分段、不可达叉号。 | PathResult。 |
| 教学高亮 | 新手任务。 | 推荐地块脉冲或边框。 | TutorialState。 |
| AI 调试高亮 | Debug 开启。 | AI 目标、威胁范围、规划路径。 | `aiIntentLog`。 |

### 实现建议

| 元素 | 第一版实现 | 注意事项 |
| --- | --- | --- |
| Hover 边框 | 1 个可复用 Graphics，跟随当前 tile。 | 不为每格创建 Hover 对象。 |
| 可移动范围 | 复用一组 overlay Sprite/Graphics，数量等于当前范围。 | 单位取消选择时隐藏，不销毁。 |
| 路径线 | 1 个 Graphics 绘制折线和箭头。 | 鼠标移动节流到 30Hz 或路径变化才重画。 |
| 攻击范围 | 半透明红色 tile overlay。 | 不和可移动范围混色到难读。 |
| 教学高亮 | 单独 tutorial overlay 层。 | 普通 UI 关闭时也能清理。 |

路径预览不能直接移动单位。只有 `MOVE_UNIT` Command 成功后，`GameState.unit.tileId` 改变，渲染层才同步 Sprite 位置。

## 十、Culling 与视口控制

第一版地图小，但仍建议实现轻量 culling 统计，方便以后扩地图。

| 对象 | 第一版 culling | 第二版 culling |
| --- | --- | --- |
| 地形 tile | 16x16/20x20 可先全显示，但必须通过 ChunkManager 统计 active area；是否隐藏视口外 Sprite 由 Spike 决定。 | 按 chunk visible 开关。 |
| 资源图标 | 视口外隐藏，或随 tile 一起显示。 | chunk 级控制。 |
| 单位/城市 | 数量少，全显示可以接受。 | 空间索引 + 视口 bounds。 |
| Overlay | 只创建当前选择相关对象。 | dirty region 更新。 |
| Debug 文本 | 只在视口内显示。 | 必须 culling，否则文本最容易拖慢。 |

相机需要考虑 DOM 面板遮挡区：

| 场景 | 处理 |
| --- | --- |
| 右侧面板展开 | `CameraViewport` 的可用宽度减少，定位城市/单位时不要被面板盖住。 |
| Tooltip 出现 | Tooltip 使用 DOM 定位，不影响 Pixi 世界坐标。 |
| 缩放到边界 | clamp camera，避免地图完全拖出视口。 |
| 以鼠标为中心缩放 | 缩放前后保持鼠标下的 world point 稳定。 |

## 十一、Texture Atlas 与资源使用

承接 `11_资源管线与部署方案.md`，地图渲染优先使用 atlas。

| Atlas | 内容 | 渲染层用途 |
| --- | --- | --- |
| `map-core` | 地形 tile、基础地貌、占位地形。 | `terrainLayer`。 |
| `icons-map` | 资源图标、移动/攻击/路径小图标、警告标记。 | `terrainDetailLayer`、`overlayLayer`。 |
| `units-core` | 侦察兵、战士、建造者、弓手。 | `unitLayer`。 |
| `ui-core` | 可选，小型 UI 图标。 | DOM 可直接用 SVG；地图 overlay 才进 Pixi。 |

### Atlas 规则

| 规则 | 原因 |
| --- | --- |
| 同一高频层尽量来自同一 atlas。 | 减少纹理切换，利于批处理。 |
| 每个 frame 留 1-2px padding。 | 避免缩放采样串色。 |
| atlas key 稳定，不直接把路径写进 GameState。 | 存档只保存 `terrainId`、`unitType`、`resourceId`。 |
| 缺失贴图统一走 `placeholder.missingTexture`。 | 避免资源缺失导致白屏。 |
| 不在每帧创建 Texture。 | Texture 由 AssetManager 加载和缓存。 |

### 资源映射

```ts
type RenderAssetResolver = {
  terrainFrame(terrainId: TerrainId, variant?: string): TextureKey;
  resourceFrame(resourceId: ResourceId): TextureKey;
  unitFrame(unitType: UnitType, ownerId: PlayerId, state: UnitVisualState): TextureKey;
  cityFrame(city: CityState): TextureKey;
};
```

`RenderAssetResolver` 读取配置表和 manifest，不读取硬编码 URL。读档后 `RenderEngine.rebuildFromState` 通过 resolver 重建 Sprite texture。

## 十二、性能指标

渲染指标进入 Debug Panel 的 Render/Performance 页签。

| 指标 | 目标 | 警戒线 | 采样方式 |
| --- | --- | --- | --- |
| 平均 FPS | 60 | 低于 30 | `requestAnimationFrame` 10 秒滑动窗口。 |
| p95 frame time | 16.7ms 左右 | 高于 33ms | 最近 600 帧。 |
| render sync 耗时 | 5ms 内 | 高于 12ms | 每次 `RenderEngine.sync` trace。 |
| pointer hit 耗时 | 0.5ms 内 | 高于 2ms | Hover/点击采样。 |
| path preview 耗时 | 20ms 内 | 高于 50ms | 路径请求 trace。 |
| Sprite 数 | 第一版 1000 以下 | 异常增长 | 每次 sync 或每 2 秒统计。 |
| Graphics 数 | 第一版 100 以下 | 异常增长 | Debug Render 页签。 |
| Texture/atlas 数 | 核心 3-4 个 atlas | 同屏过多 | AssetManager diagnostics。 |
| context lost 次数 | 0 | 任何发生都记录 | canvas 事件。 |
| 内存趋势 | 读档/重开后不持续上涨 | 连续上涨 | 浏览器可用 API + 对象计数。 |

第一版性能测试基准：

| 场景 | 地图 | 单位 | Overlay | 验收 |
| --- | --- | --- | --- | --- |
| 默认局 | 16x16 | 每方 5 单位 | 迷雾 + 选中 + 路径 | 平均 60 FPS。 |
| 上限局 | 20x20 | 每方 10 单位 | 迷雾 + 城市范围 + Debug 坐标关闭 | 不低于 30 FPS。 |
| 调试局 | 20x20 | 每方 10 单位 | Debug 坐标、AI 路径开启 | 允许低于 60，但不能低于 30 太久。 |
| 读档重建 | 16x16 | 每方 10 单位 | 全量重建 | 500ms 内完成渲染重建。 |

## 十三、性能优化表

| 风险 | 表现 | 优先处理 |
| --- | --- | --- |
| 每帧重建 Graphics | Hover/路径时掉帧。 | 只在状态变化时重建；复用 GraphicsContext 或对象池。 |
| 地图对象混排 | draw call 增加。 | 按层分组，同类对象连续绘制。 |
| atlas 过碎 | 拖拽时纹理切换多。 | 高频地图资源合并进少数 atlas。 |
| Text 太多 | 坐标层或城市名拖慢。 | Debug 文本只在视口内；必要时用 BitmapText。 |
| 事件系统遍历过深 | Hover 命中变慢。 | 地图命中走 CPU 坐标，不给每个 tile 开 Pixi interactive。 |
| culling 过度 | CPU 计算比绘制还贵。 | 第一版小地图不要复杂 culling，只做统计和简单隐藏。 |
| 路径预览频繁寻路 | 鼠标移动卡顿。 | 节流、缓存同一目标、忽略过期请求。 |
| 读档后 Sprite 泄漏 | 内存上涨、重复绘制。 | `rebuildFromState` 先清理/回收旧对象。 |
| 透明覆盖太多 | 迷雾和 overlay 混合成本上升。 | 合并 fog 层，第二版用 RenderTexture/Shader。 |
| 滤镜和 Mask 滥用 | GPU 压力升高。 | 第一版不用复杂滤镜；矩形遮罩优先。 |

PixiJS 性能资料里强调：spritesheet/atlas 有利于减少纹理数量；对象顺序会影响批处理；culling 不是永远免费，应结合 CPU/GPU 瓶颈判断。这和本项目“第一版先有轻量地图引擎骨架和统计，是否做真实卸载由 Spike 决定”的路线一致。

## 十四、Context Lost 处理

WebGL context lost 必须进入错误日志和 Debug Export。

### 第一版处理

| 步骤 | 行为 |
| --- | --- |
| 监听 | 在 canvas 上监听 `webglcontextlost` 和 `webglcontextrestored`。 |
| 丢失时 | 阻止默认行为可按恢复策略决定；暂停 ticker；DOM UI 显示“地图渲染已中断”。 |
| 记录 | 写入 `EventLog`/`errorLog`：浏览器、renderer、地图规模、Sprite 数、atlas 数。 |
| 玩家反馈 | 提供刷新按钮；当前 `GameState` 仍在内存中，若 Storage 可用则允许尝试保存。 |
| 恢复 | 第一版只要求提示刷新并保留 Debug Export；自动重建 renderer 和资源放第二版。 |

### 第二版增强

| 方向 | 说明 |
| --- | --- |
| 自动重建 | 销毁旧 renderer，重新 init，重新加载 critical atlas，从 GameState 重建。 |
| 降级画质 | context lost 后降低分辨率、关闭 debug text、减少动画。 |
| 远程日志 | 外部试玩版本记录硬件和浏览器信息，定位低端设备问题。 |

注意：context lost 恢复不能靠存档里的 Texture，因为存档不保存 Texture。恢复路径必须是 `GameState + AssetManager + RenderEngine.rebuildFromState`。

## 十五、第一版与第二版边界

| 模块 | 第一版 | 第二版 |
| --- | --- | --- |
| 渲染后端 | PixiJS WebGL/WebGL2。 | 继续 WebGL；评估 WebGPU renderer 或局部自研。 |
| 地图规模 | 12x12 到 20x20，默认 16x16。 | 32x32+ 或更大地图。 |
| Tilemap | Sprite + atlas + 对象池 + 轻量 Chunk/Viewport/TilePool 骨架。 | 真实 chunk culling、cache texture、Mesh 或 tilemap 插件。 |
| 迷雾 | 半透明覆盖。 | RenderTexture/Shader、柔边、动画。 |
| 命中 | CPU 坐标换算。 | CPU 空间索引；复杂地图再评估 GPU Picking。 |
| 路径 | 主线程寻路 + 节流，接口预留 Worker。 | Worker 寻路、路径缓存、可视化调试。 |
| Culling | active area 统计、debug 文本隐藏；是否卸载视口外 Sprite 由 Spike 决定。 | chunk culling、dirty region。 |
| Minimap | 不做或只在调试里简化。 | 正式小地图。 |
| 动效 | 简单移动插值、选中脉冲可选。 | 战斗/建造/科技反馈动画。 |
| Context Lost | 记录、提示刷新、保留 Debug Export。 | 尝试自动恢复和降级画质。 |
| WebGPU | 只预留接口。 | 有明确收益后再实验。 |

## 十六、调试 Overlay

| Overlay | 内容 | 默认状态 |
| --- | --- | --- |
| 坐标层 | `x,y`、tileId、chunkId 预留。 | 关闭，开发可开。 |
| 可见性层 | unexplored/explored/visible 状态。 | 关闭。 |
| 移动成本层 | 每格移动消耗和阻挡原因。 | 关闭。 |
| 产出层 | 粮食、生产力、金币、科技数值。 | 关闭。 |
| 路径层 | 当前单位路径、A* open/closed 调试预留。 | 路径预览时开启局部。 |
| AI 目标层 | AI 目标地块、威胁范围、规划路径。 | 关闭，Debug AI 页签控制。 |
| 渲染统计层 | Sprite 数、可见 tile 数、当前 zoom。 | Debug Panel 显示，画布上可选。 |

Debug overlay 不能进入普通存档；开关可进入 LocalStorage 设置。Debug Export 可以带 overlay 开关状态和渲染诊断摘要。

## 十七、错误与日志事件

| 事件 | 触发 | 关键字段 |
| --- | --- | --- |
| `render_context_created` | PixiJS 初始化成功。 | renderer、resolution、webglVersion。 |
| `render_context_failed` | PixiJS 初始化失败。 | error、browser、devicePixelRatio。 |
| `render_context_lost` | WebGL context lost。 | spriteCount、textureCount、mapSize、memoryHint。 |
| `render_context_restored` | WebGL context restored。 | durationMs、rebuildResult。 |
| `render_budget_exceeded` | FPS/p95/frame sync 超预算。 | metric、value、threshold、sceneSummary。 |
| `render_asset_missing` | texture key 找不到。 | assetKey、fallbackKey、objectKind。 |
| `render_hit_test_failed` | 输入无法命中。 | screen、camera、reason。 |
| `render_rebuild_completed` | 读档或新局重建完成。 | durationMs、tileCount、unitCount、cityCount。 |

## 十八、实现顺序

| 顺序 | 任务 | 验收 |
| --- | --- | --- |
| 1 | 定义 `CoordinateSystem` 和 `CameraState`。 | `screenToTile`、`tileToWorld` 单测通过。 |
| 2 | 初始化 PixiJS Application 和固定层级。 | 空地图 canvas 可 resize，Debug 显示 renderer 信息。 |
| 3 | 加载 `map-core`、`icons-map`、`units-core` atlas。 | 缺失资源走 fallback。 |
| 4 | 绘制 16x16 地形层。 | 地图可拖拽缩放，FPS 采样可见。 |
| 5 | 接入 Hover/点击命中。 | Hover 高亮和地块 Tooltip 锚点正确。 |
| 6 | 绘制城市、单位、资源。 | 读 `GameState` 重建，无 Pixi 对象进入状态。 |
| 7 | 接入迷雾层。 | 单位移动后可见性变化能刷新。 |
| 8 | 接入选中高亮和路径预览。 | 选中单位可显示可达范围，右键移动走 Command。 |
| 9 | 接入 Debug Render 页签和 Overlay。 | 坐标、Sprite 数、frame time 可见。 |
| 10 | 处理读档重建和 context lost 记录。 | 刷新读档后地图恢复；context lost 有日志。 |

## 十九、风险清单

| 风险 | 影响 | 优先级 | 应对 |
| --- | --- | --- | --- |
| 渲染层修改规则状态 | 存档、回放、AI 全部不可信。 | 高 | `RenderEngine` 只读 `GameState`；移动必须 dispatch Command。 |
| 坐标转换散落 | 后续六边形/缩放/面板遮挡难维护。 | 高 | 所有转换集中到 `CoordinateSystem`。 |
| 每个 tile 都开 Pixi interactive | Hover 性能差，事件系统复杂。 | 高 | 地图命中统一走 CPU 坐标换算。 |
| Atlas key 和配置 ID 混乱 | 读档后贴图找不到。 | 高 | `terrainId/unitType/resourceId -> TextureKey` 通过 resolver。 |
| Fog 和 overlay 透明层过多 | 低端设备掉帧。 | 中高 | 第一版控制地图规模；第二版合并 RenderTexture/Shader。 |
| Debug 文本常驻 | 画面卡顿，干扰玩家体验。 | 中 | Debug overlay 默认关闭，只显示视口内。 |
| 读档不清理旧 Sprite | 内存泄漏、重复对象。 | 中 | Sprite 池、`destroy`/回收策略、对象计数报警。 |
| Context lost 未处理 | 黑屏，试玩失败。 | 中 | 第一版至少监听、提示、记录、允许导出。 |
| 过早自研 Mesh/Shader | 拖慢玩法验证。 | 中 | 先用 PixiJS Sprite/Graphics，瓶颈明确后局部升级。 |
| GPU Picking 过早引入 | 复杂度上升，读像素可能卡顿。 | 中 | 第一版 CPU 命中，超过预算再评估。 |
| 相机和 DOM 面板不协同 | 定位对象被面板遮住。 | 中 | CameraViewport 计算可用区域。 |
| WebGPU 进入核心依赖 | 兼容和调试风险。 | 中 | 第一版 WebGL，WebGPU 只预留接口。 |

## 二十、资料来源

| 来源 | 内容价值 |
| --- | --- |
| PixiJS Renderers | PixiJS renderer 可使用 WebGL/WebGL2 或 WebGPU；WebGLRenderer 稳定且推荐生产使用，WebGPU 仍需谨慎。https://pixijs.com/8.x/guides/components/renderers |
| PixiJS Assets | PixiJS `Assets` 支持异步加载、缓存、manifest bundles、spritesheet 和资源别名。https://pixijs.com/8.x/guides/components/assets |
| PixiJS Container | Container 适合组织场景图、层级、transform；`zIndex/sortableChildren` 可控但不宜滥用。https://pixijs.com/8.x/guides/components/scene-objects/container |
| PixiJS Graphics | Graphics 适合形状、高亮、路径；不要每帧反复 clear/rebuild 复杂图形。https://pixijs.com/8.x/guides/components/scene-objects/graphics |
| PixiJS Performance Tips | spritesheet、对象顺序、culling、filters、masks、events 都会影响性能，需按瓶颈优化。https://pixijs.com/8.x/guides/concepts/performance-tips |
| PixiJS Render Layers | RenderLayers 可让渲染顺序独立于逻辑父子关系，但需要显式管理。https://pixijs.com/8.x/guides/concepts/render-layers |
| MDN WebGL | WebGL 是浏览器中通过 canvas 使用硬件加速绘制 2D/3D 图形的 API。https://developer.mozilla.org/en-US/docs/Web/API/WebGL_API |
| MDN WebGL context lost | canvas 会触发 `webglcontextlost` 事件，应用应监听并处理上下文丢失。https://developer.mozilla.org/en-US/docs/Web/API/HTMLCanvasElement/webglcontextlost_event |

## 二十一、结论

第一版推荐实现为：

> **PixiJS WebGL + atlas Sprite tilemap + CPU 坐标命中 + 半透明战争迷雾 + 轻量 overlay + Debug Render 面板。**

这条路线足够支撑 30 回合 Web 原型，也不会把项目过早拖入自研 WebGL、WebGPU、GPU Picking 或复杂 Shader。最重要的是保持边界干净：**GameState 负责事实，Simulation 负责规则，RenderEngine 负责把事实画出来。**
