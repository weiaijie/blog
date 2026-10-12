# 地图美术资产管线

本目录用于收纳地图视觉支线确认后的美术资产。`visual-lab` 中用代码生成的 Three.js 模型只用于灰盒评审，不作为最终精细模型。

## 推荐工具

- Blender：制作地形块、过渡块、单位、建筑和动画源文件。
- Substance 3D / Material Maker：制作草地、岩石、沙地、水岸等 PBR 或风格化材质。
- Meshy / Tripo / ChatGPT Images / Midjourney：做概念参考、小道具草模、贴图参考和风格探索。
- Gaea / World Creator / Houdini：需要更自然的山脉、侵蚀、河谷和程序化地形时再引入。
- glTF/GLB：作为进入项目的运行时资产格式。
- Three.js visual-lab：检查模型比例、俯视可读性、相邻地块过渡、动画状态和 LOD。

## 美术方向

目标不是写实复刻，而是“半写实 + 微缩景观 + 清晰色块 + 夸张地形高度”：

- 草地、沙漠、雪地、岩石、水面要有清晰色块差异。
- 山体、树、河流、城市、资源比真实比例更夸张，保证俯视可读性。
- 逻辑上仍是 hex，视觉上通过过渡边、材质混合和装饰物弱化硬边。
- AI 只用于概念、风格、贴图参考、小道具草模和图标，不直接作为最终可拼接地块资产。

制作路线维护在：

```text
src/render/assets/mapVisualProductionPlan.ts
```

最近一轮真实资产制作执行单维护在：

```text
src/render/assets/NEXT_PRODUCTION.md
```

参考图拆解清单维护在：

```text
src/render/assets/REFERENCE_BREAKDOWN.md
```

AI 图生 3D 管线维护在：

```text
src/render/assets/AI_3D_PIPELINE.md
```

当前不要同时开整套资产库，先完成 `terrain-water`、`transition-shoreline`、`terrain-hill` 三个资产的 Blender 源文件和 glTF/GLB 导出。

## Blender 自动化入口

安装 Blender 并确认 `blender --version` 可运行后，可以用脚本生成第一批真实资产源文件和运行时 GLB：

```powershell
npm run assets:terrain:blender
```

也可以只重跑单个资产：

```powershell
npm run assets:terrain:blender -- terrain-water
npm run assets:terrain:blender -- transition-shoreline
npm run assets:terrain:blender -- terrain-hill
```

如果 Blender 没有加入 PATH，可以临时指定：

```powershell
$env:BLENDER_BIN = "C:\Program Files\Blender Foundation\Blender 4.x\blender.exe"
npm run assets:terrain:blender
```

脚本入口维护在：

```text
scripts/blender/build-terrain-assets.mjs
scripts/blender/generate-first-terrain-assets.py
```

## 目录约定

```text
src/render/assets/
  terrain/
  transitions/
  units/
  buildables/
  textures/
  source/
```

`source/` 存放 Blender 源文件；运行时只消费导出的 glTF/GLB、纹理和必要的 manifest。

## 资产清单

运行时清单维护在：

```text
src/render/assets/mapModelAssetManifest.ts
```

每个资产条目必须包含：

- `priority`：制作顺序，数字越小越优先。
- `sourceFile`：Blender 源文件路径。
- `runtimeFile`：主运行时 glTF/GLB 路径。
- `lodFiles`：低细节版本路径。
- `blocker`：暂时不能迁入主线的原因。
- `silhouette`：俯视视角下最重要的轮廓设计。
- `materialNotes`：材质和色彩约束。
- `acceptance`：进入 `visual-lab` 验收前必须满足的标准。

当前优先顺序：

1. `terrain-water`
2. `transition-shoreline`
3. `terrain-hill`

原因：水域和水陆岸线决定地图是否像完整文明类地图；丘陵起伏决定整体 3D 地形可信度。这三项没有真实 glTF 前，不应急着把灰盒迁入主线地图。

2026-05-31 更新：第一批 Blender 源文件和运行时 GLB 已生成，`visual-lab` 优先加载 `lod0` 做工坊验收；未通过组合验收前仍不得迁入主线 Pixi 地图。

```text
source/terrain/terrain-water.blend
source/transitions/transition-shoreline.blend
source/terrain/terrain-hill.blend
terrain/terrain-water-lod0.glb
transitions/transition-shoreline-lod0.glb
terrain/terrain-hill-lod0.glb
```

状态含义：

- `spec`：规格已定义，尚未制作灰盒或源文件。
- `graybox`：`visual-lab` 已有代码灰盒，可用于比例和组合评审。
- `source-needed`：需要 Blender 源文件。
- `ready-for-lab`：glTF/GLB 已导出，等待工坊验收。

## 命名约定

- 地形：`terrain-grassland-lod0.glb`、`terrain-forest-lod0.glb`
- 过渡：`transition-shoreline-lod0.glb`、`transition-hill-foot-lod0.glb`
- 单位：`unit-scout-idle.glb`、`unit-warrior-idle.glb`
- 建筑：`buildable-city-center-lod0.glb`、`buildable-outpost-lod0.glb`

## 迁入规则

1. 先在 Blender 中完成模型和材质。
2. 导出 glTF/GLB 后进入 `visual-lab`，检查相邻地块组合、镜头距离、移动端尺寸和动画状态。
3. 更新 `27_地图视觉与动画支线计划.md` 的阶段记录。
4. 只在确认后把资产参数迁入主线 Pixi 地图；迁入时不得修改规则层结果。
