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
| M4 单位与战斗 | 侦察兵、开拓者、战士、建造者、弓手、移动、建城、攻击 | 单位能移动/建城/战斗，日志可解释 |
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
| 规则 | `FOUND_CITY` 最小命令、建城 Validator、hex 城市间距 | GameState / Command 类型 | P0 |
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

## 七点一、最小建城前置切入

当前 Phase 2/3 已经能完成 30 回合可试玩闭环，并且地图已经迁移为 offset hex。下一阶段不要直接扩展完整城市系统，先做一个可验证的 `FOUND_CITY` 小闭环。

| 项目 | 最小范围 | 验收 |
| --- | --- | --- |
| RuleCommand | 新增 `FOUND_CITY`，payload 只包含 `playerId`、`unitId`、`tileId`。 | `isRuleCommand` 能识别；CommandLog 记录成功建城命令。 |
| Validator | 只检查当前玩家、settler 所属权、tile 存在、tile 与 settler 当前位置一致、非 water、无城市、与同玩家城市 hex 距离至少 3。 | 单测覆盖成功建城、非 settler、water、已有城市、距离过近。 |
| Simulation | 成功后新增城市并消耗 settler；新城使用稳定 ID 和最小 `CityState` 字段。 | replay/hash/save 后结果一致；城市数量 +1、settler 数量 -1。 |
| UI | 选中 settler 时显示“建立城市”按钮；按钮调用 `tryApplyRuleCommand`。 | production-preview smoke 验证按钮出现、建城成功、CommandLog 增加、新城市显示在地块详情。 |
| 不做 | 不做文化边界、城市命名 UI、建筑树、AI 建城、正式资源平衡。 | 不新增范围外状态，不破坏现有 30 回合 smoke。 |

建议实现顺序：

1. 文档和测试先行：确认 `10_数据结构与存档方案.md` 的 `FOUND_CITY` schema 和错误码。
2. 规则层先行：`RuleCommand`、Validator、`applyRuleCommand`、单测。
3. 再接 UI：只在 settler 当前地块允许点击“建立城市”。
4. 最后扩展 smoke：验证建城成功和非法建城错误，不扩展复杂城市面板。

## 七点二、最小战士单位前置切入

当前已经有侦察兵、开拓者、生产、移动、建城、存档和 30 回合 UI 闭环。下一步可以加入 `unit:warrior`，但第一版目标只是补齐“战士作为可生产、可移动、可存读回放的单位”，不是做完整战斗系统。

| 项目 | 最小范围 | 验收 |
| --- | --- | --- |
| Unit config | 新增 `unit:warrior`，只配置 `productionCost`，不改 `unit:scout` / `unit:settler` 成本。 | `isUnitId('unit:warrior')` 为 true；未知单位仍被拒绝。 |
| UnitState | 暂不扩展字段；继续使用 `id`、`ownerId`、`tileId`、`typeId`。 | 生产完成后生成 `typeId: 'unit:warrior'`。 |
| 规则 | 复用现有 `SET_PRODUCTION`、`END_TURN`、`MOVE_UNIT`。 | warrior 可被生产，可按相邻 hex 移动，非法远距离移动仍失败。 |
| 存档/回放 | 不新增 Command 类型；CommandLog 仍只记录生产、结束回合和移动。 | 包含 warrior 生产/移动的 replay/hash/save 稳定。 |
| UI | 增加“生产战士 / 选中城市生产战士”入口。 | production-preview smoke 能看到 warrior 生产完成、移动、读档恢复。 |
| 不做 | 本轮不做 `ATTACK`、hp、attack、range、movementLeft、hasAttackedThisTurn、敌我关系、经验、远程攻击、战争外交。 | 不新增战斗 schema，不破坏现有 30 回合 smoke。 |

建议实现顺序：

1. 配置和规则测试先行：新增 `unit:warrior`，补生产、移动、save/replay/hash 测试。
2. 再接 UI 生产入口：首都和选中城市都能设置 warrior 生产。
3. 最后扩展 smoke：验证 warrior 生产完成、可移动、读档后仍存在。
4. `ATTACK` 单独作为后续小闭环，先做文档和错误码评估，再改 `RuleCommand`。

## 七点三、ATTACK 前置切入

当前已经有 `unit:warrior` 的生产、移动、保存/回放闭环，但还没有单位生命值、攻击数值、敌我关系、战争状态或战斗 UI。下一步不能直接做完整战斗系统，必须先把 `ATTACK` 的第一版边界切窄。

| 项目 | 第一版最小范围 | 推迟内容 |
| --- | --- | --- |
| Command | 可新增 `ATTACK`，payload 建议为 `{ playerId, attackerUnitId, targetUnitId }`。 | 不做城市攻击、占城、远程攻击、战斗预览。 |
| UnitState | 若实现攻击，先只补 `hp`、`maxHp`；数值基准放在 unit config。 | 不做 `movementLeft`、经验、fortify、状态机、动态射程。 |
| Unit config | 可补 `attack`、`maxHp`，第一版 `attackRange` 固定为 1 或配置为 1。 | 不做正式平衡，不改已有 scout/settler/warrior 生产成本。 |
| Validator | attacker 必须属于当前玩家；target 必须存在、非己方、当前可见；hex 距离必须 1；第一版只允许 warrior 攻击。 | `NOT_AT_WAR` 等外交状态落地后再启用。 |
| Simulation | 固定伤害，目标 hp <= 0 时从 `units` 移除；命令写入 `CommandLog`。 | 不做反击、地形防御、城市防御、胜利结算。 |
| UI | 只在选中 warrior 且目标为可见相邻敌方单位时提供明确攻击入口。 | 不复用普通地块点击做隐式攻击，避免误触移动。 |
| 存档/回放 | replay/hash/save 必须覆盖攻击、死亡移除和旧命令序列稳定性。 | 不新增规则级 EventLog，除非另开日志小闭环。 |

建议顺序：

1. 文档和测试计划先行：确认 `10_数据结构与存档方案.md` 的字段、错误码和兼容策略。
2. 如果开始代码，第一轮只补 `hp/maxHp` 默认值、unit config 数值和旧 replay/hash 测试，不新增 `ATTACK`。
3. 第二轮再新增 `ATTACK` RuleCommand、Validator、apply 和规则单测。
4. 第三轮再接 UI/smoke；仍不引入外交、AI 攻击、城市攻防或胜利。

## 七点四、ATTACK UI 前置评估

当前 `ATTACK` 规则层、`combat:adjacent-enemy` scenario 和 replay/save/load 回归已经完成。下一步如果接 UI，必须先保护默认可玩流程：普通 `default` 开局不出现敌方单位、不出现攻击按钮，也不把战斗场景混进 30 回合 smoke。

| 项目 | 第一版边界 | 验收 |
| --- | --- | --- |
| 场景 | `combat:adjacent-enemy` 只作为显式 debug/test 战斗演示入口。 | 默认 playable smoke 不出现敌人和攻击按钮。 |
| 选择 | 先选中己方 warrior，再点击可见相邻敌方单位所在地块。 | 不复用普通地块点击做隐式攻击，避免误触移动。 |
| 按钮 | 只在 selected warrior + visible adjacent enemy 且目标唯一时显示“攻击”。 | scout/settler、未知地块、已探索不可见地块、多目标地块都不显示攻击按钮。 |
| 命令 | 按钮调用 `tryApplyRuleCommand({ type: 'ATTACK' })`。 | 成功写入规则 `CommandLog`；失败显示结构化错误。 |
| 反馈 | EventLog 可显示攻击、剩余生命和击败单位。 | EventLog 仍是 UI 派生状态，不写入 `GameState` 或规则 `CommandLog`。 |
| 存档 | combat UI smoke 需要覆盖攻击后的 Save/Load 或 Persistent Load。 | hash、目标单位移除、`scenarioId` 重放保持稳定。 |

建议顺序：

1. 文档和 subagent 复核先行，确认默认 UI 不被 combat scenario 污染。
2. 如果开始实现，先做显式 combat 场景入口或独立 combat smoke，不改默认新游戏。
3. 再做攻击按钮和 EventLog，按钮只在严格合法的 UI 条件下出现。
4. 最后跑 `typecheck`、`test`、`lint`、combat smoke、默认 `smoke:playable`；阶段收尾再跑 `verify:phase2`。

## 七点五、战斗下一小闭环评估

当前 `ATTACK` UI 最小闭环已经可以在显式 combat scenario 中选择 warrior、选择相邻可见敌方单位、攻击并保存/读取回归。下一步不能直接扩成完整战斗系统，应先补一个能提升可用性、同时不改变规则 schema 的小闭环。

| 候选 | 第一版价值 | 风险 | 结论 |
| --- | --- | --- | --- |
| 攻击非法原因展示 | 解释为什么当前没有攻击按钮或不能攻击，例如未选 warrior、目标不可见、目标不相邻、目标不明确。 | 低。复用 UI 派生状态和现有 Validator 错误码，不改 `RuleCommand`、`GameState`、`CommandLog` 或存档。 | 优先做。 |
| 轻量生命条/战斗预览 | 帮玩家理解 HP 和伤害。 | 中。若只在侧栏显示可控；若做到 Pixi 地图血条会触及渲染和性能。 | 推迟到非法原因展示之后单独评估。 |
| 多目标选择 UI | 解决一个 hex 上多个敌方单位时的目标选择。 | 中高。需要新增目标选择状态、堆叠单位呈现、点击语义和 smoke 场景。 | 推迟。 |

攻击非法原因展示的边界：

1. 只在 UI 层新增派生状态，例如 `attackUnavailableReason` 或“攻击状态”字段。
2. 覆盖现有前置条件：未选单位、选中单位不是己方 warrior、未选目标地块、目标地块不可见、无敌方单位、目标不相邻、多个敌方目标不明确。
3. 合法目标时原因消失并显示“攻击”按钮；按钮仍调用 `tryApplyRuleCommand({ type: 'ATTACK' })`。
4. 不新增 `ATTACK` 字段，不改 Validator 返回结构，不把提示写入 `GameState`、规则 `CommandLog`、存档或 replay/hash。
5. `smoke:combat` 需要覆盖至少三个非法状态和一个合法状态；默认 `smoke:playable` 继续确认 default 场景不出现攻击按钮。

必须继续推迟：多目标选择 UI、地图血条、胜负预测、反击、伤害公式扩展、地形修正、城市攻击、占城、AI 进攻、外交战争和正式数值平衡。

## 八、开工前还需要确认

| 问题 | 当前建议 |
| --- | --- |
| 六边形何时评估？ | 已决策并完成第一版迁移；默认地图为 offset hex，后续规则、寻路、迷雾和 UI 都以六边形为前提。 |
| 题材风格是什么？ | 第一版先用中性占位，后续决定历史/架空/东方王朝。 |
| UI 框架是否确定 React？ | 当前推荐 React DOM。 |
| 是否要接入远程错误日志？ | 第一版默认不上报，只做本地 Debug Export；公开试玩前再决定远程收集策略。 |
