# 18 MVP 开发路线与任务拆解

## 一、MVP 目标

第一版 MVP 的目标不是做完整《文明》，而是在 Web 上验证：

| 目标 | 验收 |
| --- | --- |
| WebGL 地图可玩 | 默认 16x16 地图可拖拽、缩放、选中、显示单位/资源/迷雾；20x20 作为压力图通过最低性能门槛 |
| 30 回合循环成立 | 玩家能探索、建城、生产、研究、与 AI 竞争并结算 |
| 技术链路闭合 | GameState、Command、Simulation、RenderEngine、React UI、IndexedDB、Debug 面板全部跑通 |
| 试玩可复现 | 固定 seed、CommandLog、Debug Export 能复现问题 |
| 可发链接试玩 | Vite build 可静态部署，资源缓存策略可控 |

## 二、里程碑总览

| 里程碑 | 内容 | 完成标志 |
| --- | --- | --- |
| M0 技术骨架 | Vite + TypeScript + React + PixiJS | 页面显示 WebGL canvas 与基础 DOM UI |
| M0.5 地图引擎 Spike | `CoordinateSystem`、`ViewportManager`、轻量 `ChunkManager`、`TilePool`、active area 统计 | 16x16/20x20 固定地图能记录 active tile/chunk、Sprite 数和 p95 frame time |
| M1 地图与输入 | tilemap、缩放、拖拽、点击命中、选中高亮、MapDebugOverlay | 玩家能选中地块和单位；地图引擎骨架不被 UI/规则耦合 |
| M2 GameState/Command | 可序列化 GameState、Command、Validator、EventLog | 所有操作通过 Command 改状态 |
| M3 回合与城市 | 结束回合、资源结算、城市生产、科技推进、TurnTrace | 10 回合内经济循环正确，并能记录各阶段耗时 |
| M4 单位与战斗 | 侦察兵、战士、建造者、弓手、移动、攻击 | 单位能移动/战斗，日志可解释 |
| M5 AI 与轻外交 | 1 个 AI 能扩张、研究、生产、靠近/宣战；不做外交交易 | Debug 面板能显示 AI 意图、WorkerLike requestId、timeout/stale response 处理 |
| M6 存档与回放 | IndexedDB 存读档、CommandLog、Debug Export | 刷新页面恢复同一局 |
| M7 UI/教学/胜利 | 前 5 分钟教学、Tooltip、胜利进度、复盘 | 新玩家能完成前 5 回合 |
| M8 性能与部署 | Playwright 冒烟、性能面板、压力矩阵必测项、静态部署 | 可发链接试玩，并有性能/压力 trace 产物 |

## 三、任务拆解

| 模块 | 任务 | 依赖 | 优先级 |
| --- | --- | --- | --- |
| 项目骨架 | 初始化 Vite/React/TypeScript | 无 | P0 |
| 项目骨架 | 建立目录：game/render/ui/storage/worker/assets | 无 | P0 |
| 渲染 | PixiJS 初始化与 Resize 管理 | 项目骨架 | P0 |
| 渲染 | CoordinateSystem / ViewportManager / ChunkManager / TilePool 骨架 | 项目骨架 | P0 |
| 渲染 | atlas sprite tilemap | 资源占位图 | P0 |
| 渲染 | camera pan/zoom | PixiJS 初始化 | P0 |
| 渲染 | grid/world/screen 坐标转换 | 地图数据 | P0 |
| 渲染 | active tile/chunk/Sprite 统计与 MapDebugOverlay | 地图引擎骨架 | P0 |
| 渲染 | 选中/移动范围/路径 overlay | Command/单位 | P1 |
| 规则 | GameState schema | 无 | P0 |
| 规则 | Command 类型与 Validator | GameState | P0 |
| 规则 | Simulation 单回合结算 | Command | P0 |
| 规则 | 资源公式与城市生产 | Simulation | P0 |
| 规则 | 科技树样例 | 资源公式 | P1 |
| 规则 | 战斗结算 | 单位系统 | P1 |
| AI | AIReadableState | GameState | P1 |
| AI | 简单扩张/研究/生产评分 | AIReadableState | P1 |
| AI | AI 意图日志 | AI 决策 | P1 |
| AI | WorkerLikeClient mock、requestId、timeout、丢弃过期响应测试 | AIReadableState | P1 |
| 存档 | IndexedDB wrapper | GameState | P0 |
| 存档 | 自动存档/手动存档 | IndexedDB | P1 |
| 存档 | Debug Export | CommandLog/EventLog | P1 |
| UI | 顶部状态栏 | GameState selectors | P0 |
| UI | 城市面板 | 城市系统 | P0 |
| UI | 科技面板 | 科技树 | P1 |
| UI | 胜利进度与复盘 | 胜利检测 | P1 |
| UI | 新手引导任务 | 基础 UI/Command | P1 |
| 测试 | Simulation 单测 | 规则模块 | P0 |
| 测试 | TurnTrace 和 Performance sampler | M0.5/M3 | P0 |
| 测试 | Replay 一致性测试 | CommandLog | P1 |
| 测试 | Playwright 冒烟 | 可运行 Demo | P1 |
| 测试 | `__civPerf` 测试接口和 5 个代表性能用例 | Performance sampler | P1 |
| 测试 | 20x20 压力图、地图/回合/存档压力 trace | 地图/规则/存档完成 | P1 |
| 部署 | Vite build 静态部署 | Demo 可运行 | P1 |

## 四、第一版 Definition of Done

| 维度 | 标准 |
| --- | --- |
| 玩法 | 玩家能完整玩 30 回合 |
| 地图 | 默认 16x16 地图可探索；20x20 压力图可运行并记录 active tile/chunk、Sprite 数和 p95 frame time |
| 城市 | 可生产单位/建筑，可结算粮食、生产力、金币、科技 |
| 科技 | 至少 8 个科技，能解锁单位/建筑/胜利项目 |
| AI | 至少 1 个 AI，有可读意图，会发展和制造压力 |
| 胜利 | 征服胜利、科技胜利、30 回合分数结算 |
| 存档 | 可保存/读取 1 个手动存档，保留自动存档 |
| 调试 | FPS、回合日志、AI 意图、选中对象、Debug Export 可用 |
| 性能 | 桌面目标 60 FPS，低端至少 30 FPS；p95 frame time 低于 33ms；TurnTrace、Worker payload、Storage trace、Render active chunk 字段可导出 |
| 部署 | 静态部署后可通过链接试玩 |

## 五、优先级规则

| 优先级 | 含义 |
| --- | --- |
| P0 | 没有它就无法验证核心循环 |
| P1 | MVP 必须有，但可以在 P0 后实现 |
| P2 | 第二版增强，不阻塞第一版试玩 |

## 六、第一版不做

| 不做项 | 原因 |
| --- | --- |
| 多人 | 网络同步成本高 |
| 完整外交 | AI/UI 工作量大 |
| 大科技树 | 调参成本高 |
| 海战 | 地图和寻路规则扩展大 |
| 宗教系统 | 独立系统过重 |
| 完整 WebGPU 后端 | 兼容风险高 |
| 移动端完整适配 | UI 密度和触控设计需要第二阶段 |

## 七、建议开发顺序

1. 技术骨架与空地图。
2. GameState 和 Command。
3. 地图渲染、点击、拖拽、缩放。
4. 城市、资源、回合结算。
5. 单位移动、探索、战争迷雾。
6. 科技树与生产队列。
7. 简单 AI 与可解释意图。
8. 存档、Debug Export、Replay。
9. 新手引导、胜利进度、复盘。
10. 性能优化、Playwright、静态部署。

## 八、开工前还需要确认

| 问题 | 当前建议 |
| --- | --- |
| 六边形何时评估？ | 第一版方格已定；六边形只作为第二版迁移目标。 |
| 题材风格是什么？ | 第一版先用中性占位，后续决定历史/架空/东方王朝。 |
| UI 框架是否确定 React？ | 当前推荐 React DOM。 |
| 是否要接入远程错误日志？ | 第一版默认不上报，只做本地 Debug Export；公开试玩前再决定远程收集策略。 |
