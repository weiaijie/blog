# 07 Web 游戏引擎选型调研

## 一、调研结论

第一版推荐路线：

| 方向 | 推荐决策 |
| --- | --- |
| 游戏类型 | 2D/2.5D 回合制文明类 Web 策略游戏。 |
| 首选引擎 | PixiJS 作为地图渲染引擎。 |
| UI 方案 | React/DOM 负责复杂面板、Tooltip、百科、科技树、外交界面、调试面板。 |
| 规则架构 | 自建 GameState + Simulation，不把核心规则写进渲染引擎对象。 |
| 渲染底座 | WebGL2 优先；WebGPU 只做接口预留。 |
| 不推荐第一版 | Unity WebGL、Godot Web、重 3D 引擎、纯自研 WebGL/WebGPU。 |

核心判断：这个项目第一版最需要验证的是“文明类回合循环是否成立”，不是先做完整大引擎。PixiJS 足够承担地图、单位、资源、战争迷雾、选中高亮和路径预览；React/DOM 更适合承载策略游戏的大量文本、表格、按钮和解释型 UI。

## 二、候选方案表

| 方案 | 定位 | 适合本项目的部分 | 主要优点 | 主要风险 | 第一版建议 |
| --- | --- | --- | --- | --- | --- |
| PixiJS | 2D WebGL/WebGPU 渲染引擎 | 地图、Tilemap、单位 Sprite、资源图标、战争迷雾、路径预览、选中高亮 | 轻量、贴近 Web 前端、WebGL 稳定、易与 React/DOM 分层；官方文档说明 WebGLRenderer 稳定且推荐用于生产 | 不是完整游戏引擎，回合、AI、寻路、资源加载规范、存档都要自己设计 | 首选 |
| Phaser | HTML5 2D 游戏框架 | 场景、输入、资源加载、音频、简单动画 | 框架完整，WebGL/Canvas、桌面/移动浏览器支持成熟；TypeScript 友好 | 框架会更强地接管游戏结构，复杂策略 UI 与外部 DOM 状态同步需要额外设计 | 备选 |
| Three.js | Web 3D 图形库 | 未来伪 3D 地形、3D 奇观、可旋转视角 | 3D 生态强，相机、材质、模型、光照、场景图成熟 | 对 2D/2.5D Tilemap 策略游戏偏重，复杂 UI、批量格子、地图命中需要较多自建 | 第一版不选 |
| Babylon.js | 完整 Web 3D 引擎 | 未来重 3D、WebGPU、复杂 Picking、物理、WebXR | 功能完整，支持 WebGL/WebGPU、场景图、GUI、Picking、物理等 | 第一版包袱较重，概念和资源管线复杂度高；2D 文明类原型用不上大量能力 | 第一版不选 |
| PlayCanvas | Web 3D 引擎与编辑器生态 | 未来在线编辑器、3D 地图、WebGPU 双后端 | 运行时轻、TypeScript、WebGPU + WebGL2 fallback、React 集成、在线工具链 | 更偏 3D 内容生产；如果第一版仍是 2D/2.5D，收益不如 PixiJS 直接 | 第二梯队 |
| Godot Web | 完整开源游戏引擎 Web 导出 | 如果团队已熟悉 Godot，可快速做完整游戏原型 | 编辑器、场景、2D/3D、动画、UI、脚本系统成熟 | Web 导出依赖 WebAssembly/WebGL2；Godot 4 Web 不能导出 C# 项目；线程、缓存、移动端、音频等有 Web 平台限制；DOM UI 融合弱 | 不推荐第一版 |
| Unity WebGL | 大型商业游戏引擎 Web 导出 | 如果已有 Unity 团队、资产和工具链 | 生态大，编辑器、资产、动画、工具链成熟 | WebGL 包体和加载重，网页 UI 融合成本高；官方文档说明 Unity WebGL 不支持移动设备 | 不推荐第一版 |
| 自研 WebGL/WebGPU 层 | 完全自定义渲染底层 | 极致定制 Tilemap、战争迷雾 Shader、批处理、GPU Picking | 控制力最高，长期性能上限高 | 第一版风险最大，会把时间消耗在渲染、兼容、资源、调试上，拖慢玩法验证 | 第一版不做整体自研，可局部自研 Shader |

## 三、推荐排序

| 排名 | 方案 | 结论 |
| --- | --- | --- |
| 1 | PixiJS + React/DOM | 第一版首选。最贴合 2D/2.5D 文明类 Web 原型。 |
| 2 | Phaser + 独立 GameState + DOM UI | 备选。如果更想要完整场景、输入、资源、音频框架，可考虑。 |
| 3 | PlayCanvas | 若未来确认做 3D 地图、WebGPU、在线编辑器，可进入第二梯队。 |
| 4 | Three.js | 适合未来伪 3D/真 3D 地图，不适合作为第一版默认。 |
| 5 | Babylon.js | 适合重 3D Web 游戏，第一版偏重。 |
| 6 | 自研 WebGL/WebGPU 层 | 长期可局部自研，但第一版不应从零写整套渲染。 |
| 7 | Godot Web | 不推荐作为 Web 优先项目的第一选择。 |
| 8 | Unity WebGL | 不推荐第一版，除非团队已经强依赖 Unity。 |

## 四、版本路线

| 阶段 | 技术路线 | 目标 | 退出标准 |
| --- | --- | --- | --- |
| 第一版 | TypeScript + Vite + PixiJS WebGL + React DOM UI + IndexedDB + Web Worker 预留 | 快速验证 30 回合核心循环、WebGL 地图、单位移动、城市生产、科技、AI、存档、调试面板 | 12x12 到 20x20 地图可拖拽缩放；30 回合不卡；能保存读档；能复盘胜负 |
| 第二版 | PixiJS 深化：Tilemap 批处理、Texture Atlas、战争迷雾 Shader、Minimap、Worker AI/寻路、性能面板 | 提升地图表现、性能和可维护性 | 中等地图稳定 60 FPS；AI 思考不阻塞；资源图集和调试地图稳定 |
| 长期版 | 保持 PixiJS，或按方向迁移：3D 走 Three.js/Babylon/PlayCanvas；高性能渲染局部自研 WebGPU | 根据美术方向和性能瓶颈再升级 | 有明确 3D 需求或 WebGL 性能瓶颈时，再启动迁移评估 |

## 五、为什么第一版推荐 PixiJS + React DOM

| 判断点 | PixiJS + React DOM 的优势 |
| --- | --- |
| 项目形态 | 文明类第一版更像 2D/2.5D 地图策略，不需要完整 3D 场景引擎。 |
| 地图性能 | PixiJS 适合 Sprite、容器、图集、滤镜、批量渲染和交互命中，能承担地图层。 |
| UI 密度 | 科技树、城市面板、外交、Tooltip、百科、回合日志、调试表格更适合 DOM/React。 |
| Web 原生 | TypeScript、Vite、React、IndexedDB、Web Worker、静态部署都能自然组合。 |
| 规则清晰 | PixiJS 只负责表现，不接管规则；GameState 和 Simulation 可独立测试、存档、回放。 |
| 风险控制 | 比 Unity/Godot 包体轻，比自研 WebGL 快，比 Three.js/Babylon 更贴近 2D 策略地图。 |
| 升级空间 | PixiJS v8 有 WebGPU renderer，但官方仍建议生产用 WebGL renderer；这正好符合“WebGL 稳定、WebGPU 预留”的路线。 |

推荐的第一版技术边界：

```text
玩家输入 -> Command -> Simulation -> GameState -> RenderEngine/PixiJS
                                      -> React UI
                                      -> Storage/IndexedDB
                                      -> AI Worker
```

## 六、引擎边界

| 模块 | 负责内容 | 不负责内容 |
| --- | --- | --- |
| PixiJS RenderEngine | 地图渲染、单位 Sprite、资源图标、战争迷雾、选中高亮、路径预览、地图坐标命中 | 回合规则、资源结算、AI 决策、存档 schema、科技解锁逻辑 |
| React/DOM UI | 城市面板、科技树、外交面板、Tooltip、百科、回合日志、调试面板、主菜单 | 大地图批量渲染、战争迷雾 Shader、单位批处理 |
| GameState | 地图、城市、单位、玩家、科技、外交、资源、胜利进度、回合数 | 直接引用 PixiJS Sprite、DOM 节点、浏览器事件对象 |
| Simulation | 命令校验、回合结算、生产、研究、移动、战斗、胜利检测、日志生成 | 画面动画、按钮状态、音频播放 |
| AI Worker | AI 计划、寻路、目标评分、扩张/战争/研究决策 | 直接操作 DOM、直接操作 PixiJS 对象、持久化存档 |
| Storage | IndexedDB 存档、schemaVersion、自动存档、读档恢复 | 解释规则、修复损坏玩法状态 |
| Asset Pipeline | 地形图集、单位图集、资源图标、音频、配置表、manifest | 动态决定游戏规则；规则应来自配置和 Simulation |

关键约束：

| 约束 | 决策 |
| --- | --- |
| 渲染对象不能成为规则对象 | Unit、City、Tile 是 GameState 数据；Sprite 只是它们的视图。 |
| UI 操作必须走命令 | 例如 `MoveUnitCommand`、`ChooseResearchCommand`、`EndTurnCommand`。 |
| 回合结算必须可复现 | 同一个 GameState + 同一个命令序列 + 同一个随机种子，应得到同样结果。 |
| 引擎替换要可控 | 通过 `RenderEngine` 接口包住 PixiJS，避免未来迁移时规则层被拖垮。 |

## 七、候选方案进一步说明

### PixiJS

适合做第一版地图层。PixiJS 官方文档说明 renderer 负责把场景绘制到 canvas，可使用 WebGL/WebGL2 或 WebGPU；WebGLRenderer 是默认、稳定且推荐的生产方案，WebGPURenderer 仍有浏览器实现差异风险。因此第一版使用 PixiJS WebGL 是稳妥选择。

适合承担：

| 功能 | 第一版处理方式 |
| --- | --- |
| Tilemap | 使用 Sprite/Container 或成熟 tilemap 扩展，必要时第二版做批处理优化。 |
| 缩放平移 | PixiJS 容器缩放 + 自建 camera 状态。 |
| 点击命中 | 第一版 CPU 坐标换算；复杂后再考虑 GPU picking。 |
| 战争迷雾 | 第一版半透明图层；第二版 Shader/RenderTexture。 |
| 路径预览 | Graphics/Line 或 Sprite marker。 |
| 资源图标 | Texture Atlas + Sprite。 |

### Phaser

Phaser 官方定位是 HTML5 游戏框架，支持 WebGL 和 Canvas，面向桌面和移动 Web 浏览器。它比 PixiJS 更“游戏引擎”，自带场景、资源、输入、动画、音频等能力。如果第一版团队希望更快拿到完整游戏框架，可以作为备选。

不作为首选的原因：文明类游戏复杂 UI 很多，且规则需要独立、可存档、可回放。Phaser 的场景和对象模型会更强地影响架构，容易把规则和表现混在一起。

### Three.js

Three.js 适合真 3D 或伪 3D 地图，例如可旋转相机、3D 地形、奇观模型、光照和材质。但第一版的核心不是 3D 表现，而是回合循环和地图策略。若直接使用 Three.js，需要自己搭 Tilemap、2D UI、点击命中、图集、批处理和大量策略游戏工具，投入偏大。

### Babylon.js

Babylon.js 更像完整 3D Web 引擎，官方规格覆盖 WebGL/WebGPU、场景图、物理、Picking、粒子、GUI、WebXR 等。它适合长期重 3D 版本，但第一版用它会引入很多暂时用不上的概念和管线。

### PlayCanvas

PlayCanvas 的优势是轻量 3D runtime、WebGPU 后端、WebGL2 fallback、TypeScript、React 集成和在线编辑器。它适合未来如果项目转向 3D 地图或在线内容制作工具。当前 2D/2.5D 文明类原型阶段，PixiJS 更直接。

### Godot Web

Godot 适合用编辑器做完整 2D/3D 游戏，但作为 Web 优先项目有额外限制：Web 导出需要浏览器支持 WebAssembly 和 WebGL2；Godot 4 Web 不能导出 C# 项目；多线程导出涉及 SharedArrayBuffer 和跨源隔离；移动 Web 需要额外性能优化；音频和持久化也有浏览器限制。若团队已经熟悉 Godot，可以另开原型比较，但不建议作为第一版默认。

### Unity WebGL

Unity 的强项是大型跨平台游戏生产，但 WebGL 版本对本项目不划算。Unity 官方文档说明 WebGL 需要 WebGL2、HTML5、64 位和 WebAssembly，并且 Unity WebGL 不支持移动设备。对轻量 Web 原型来说，包体、加载时间、网页 UI 融合和调试成本都偏高。

### 自研 WebGL/WebGPU 层

自研的长期价值在局部，例如战争迷雾 Shader、Tilemap 批处理、GPU picking、特殊地图效果。但第一版不应从零写完整引擎。第一版最危险的不是渲染不够极致，而是玩法循环还没验证就被底层工程拖住。

## 八、风险清单

| 风险 | 影响 | 预防措施 |
| --- | --- | --- |
| PixiJS 不是完整游戏引擎 | 需要自建 Simulation、命令系统、AI、寻路、存档 | 尽早写 `GameState`、`Command`、`Simulation` 文档和单元测试 |
| 规则和渲染混在一起 | 存档、回放、AI、测试都会变难 | 渲染对象只读 GameState；所有修改走命令 |
| React 和 PixiJS 双状态 | UI 显示与地图显示不一致 | 统一订阅 GameState 快照；避免 UI 和 Pixi 各自保存规则状态 |
| WebGPU 过早进入核心 | 浏览器兼容、调试和 CI 风险增加 | 第一版 WebGL2；WebGPU 只在 `RenderEngine` 接口层预留 |
| Tilemap 性能不足 | 大地图拖拽缩放掉帧 | 第一版控制地图 12x12 到 20x20；第二版做图集、批处理和 culling |
| 复杂 UI 进 WebGL | 科技树、面板、Tooltip 难维护 | 复杂 UI 全部 DOM/React |
| Worker 通信过重 | AI 思考或序列化卡顿 | Worker 输入用轻量快照；只传必要字段 |
| 存档绑定引擎对象 | 版本迁移困难，读档失败 | 存档只保存纯数据，不保存 Sprite、Texture、DOM 引用 |
| Unity/Godot 方案包体重 | Web Demo 首屏加载慢，试玩门槛高 | 第一版使用静态 Web 前端技术栈 |
| 自研底层拖慢进度 | 玩法验证延后 | 先用 PixiJS，性能瓶颈出现后局部自研 |

## 九、需要继续补足的问题

| 分类 | 问题 | 推荐决策 |
| --- | --- | --- |
| GameState | 地图、城市、单位、科技、外交的最小 schema 是什么？ | 由工程架构文档定义，必须纯 JSON 可序列化。 |
| Command | UI、地图、快捷键提交哪些命令？ | 至少包含移动、生产、研究、结束回合、外交、存档。 |
| RenderEngine | PixiJS 封装接口有哪些？ | `init`、`render`、`resize`、`setCamera`、`screenToTile`、`destroy`。 |
| Worker | AI 和寻路什么时候进 Worker？ | 第一版架构预留，AI 复杂后迁移；寻路可先主线程实现并做耗时统计。 |
| 资源 | 是否第一版就做 texture atlas？ | 是，至少按 atlas/manifest 组织，允许先用占位图。 |
| 测试 | 如何验证引擎层没有污染规则层？ | Simulation 单测不加载 PixiJS；存档读写不依赖 DOM。 |

## 十、资料来源

| 来源 | 用途 | 链接 |
| --- | --- | --- |
| PixiJS Renderers | 说明 PixiJS renderer 支持 WebGL/WebGL2 和 WebGPU，WebGLRenderer 稳定且推荐生产使用。 | https://pixijs.com/8.x/guides/components/renderers |
| Phaser 官方介绍 | 说明 Phaser 是 HTML5 游戏框架，支持 WebGL 和 Canvas，面向桌面和移动 Web 浏览器。 | https://docs.phaser.io/phaser/getting-started/what-is-phaser |
| Three.js Fundamentals | 说明 Three.js 的 Scene、Camera、Mesh、Geometry、Material、Texture 等 3D 场景图基础。 | https://threejs.org/manual/en/fundamentals.html |
| Babylon.js Specifications | 说明 Babylon.js 支持 WebGL/WebGPU、场景图、物理、Picking、粒子、GUI 等完整 3D 能力。 | https://www.babylonjs.com/specifications/ |
| PlayCanvas Engine | 说明 PlayCanvas Engine 的 TypeScript、轻量 runtime、WebGPU 后端和 WebGL2 fallback。 | https://playcanvas.com/products/engine |
| Godot Web Export | 说明 Godot Web 导出需要 WebAssembly/WebGL2，并列出 C#、线程、移动端、音频、持久化等限制。 | https://docs.godotengine.org/en/stable/tutorials/export/exporting_for_web.html |
| Unity WebGL Browser Compatibility | 说明 Unity WebGL 的浏览器条件，以及 Unity WebGL 不支持移动设备。 | https://docs.unity3d.com/cn/2023.1/Manual/webgl-browsercompatibility.html |
| MDN WebGL | 说明 WebGL 是浏览器中用于高性能 2D/3D 图形的 JavaScript API，可利用硬件加速。 | https://developer.mozilla.org/en-US/docs/Web/API/WebGL_API |
| MDN WebGPU | 说明 WebGPU 是 WebGL 的后继方向，但不是所有主流浏览器都完整支持。 | https://developer.mozilla.org/en-US/docs/Web/API/WebGPU_API |
