# AI 图生 3D 管线

本文件定义“图片设计稿 -> AI 3D 草模 -> Blender 标准化 -> glTF/GLB -> visual-lab 验收”的流程。AI 生成模型只作为草模或参考，不能直接作为最终可拼接地块资产。

## 一、推荐工具分层

| 用途 | 推荐工具 | 说明 |
| --- | --- | --- |
| 快速试效果 | Tripo、Meshy、Copilot 3D | 用裁切后的单个地块图快速判断 AI 是否理解结构。 |
| 游戏资产草模 | Meshy、Tripo、Rodin | 适合生成树、石头、矿物、建筑、小资源和地块草模。 |
| 高质量/PBR 草模 | Rodin、Hunyuan3D-2.1、TRELLIS.2 | 适合更高质量模型和材质实验，但仍需 Blender 清理。 |
| 商业生产服务 | Kaedim | 偏团队/外包式资产生产，成本和流程更重。 |
| 本地研究/批量生成 | Hunyuan3D-2.1、TRELLIS.2、Stable Fast 3D、SPAR3D、Wonder3D | 适合后续研究，当前不作为第一轮阻塞项。 |

当前项目优先顺序：

1. Tripo / Meshy：拿单个地块裁图快速试风格。
2. Rodin：尝试更完整的水域、岸线、丘陵草模。
3. Blender：统一 hex 底座、比例、原点、材质、LOD 和导出。
4. `visual-lab`：检查组合关系和迁入风险。

## 二、输入图准备

不要把整张参考图直接上传给 AI。整张图里有多个地块、文字、UI 面板、边框和对比说明，AI 会把这些都当成模型信息。

正确输入：

```text
单个地块裁图
  -> 去掉文字、标签、边框、背景
  -> 保留完整 hex 地块
  -> 尽量让地块居中
  -> 背景透明或纯色
```

第一批建议裁切：

```text
terrain-water-reference.png
transition-shoreline-reference.png
terrain-hill-reference.png
```

后续再裁切：

```text
terrain-grassland-reference.png
terrain-forest-reference.png
terrain-desert-reference.png
resource-wheat-reference.png
resource-iron-reference.png
buildable-city-center-reference.png
road-edge-reference.png
river-edge-reference.png
```

## 三、推荐 Prompt

### 水域地块

```text
Create a stylized semi-realistic hexagonal ocean terrain tile for a turn-based strategy game.
Clean six-sided hex base, flat bottom, lowered water basin, shallow turquoise water,
sandy shoal ring, subtle wave decals, small coastal rocks or reeds, readable from isometric camera.
Keep it modular and game-ready. No text, no UI, no characters, no background.
Export as GLB or FBX.
```

### 水陆岸线

```text
Create a modular shoreline edge asset for a hexagonal strategy game terrain tile.
It should fit along one side of a clean six-sided hex tile, with sandy shelf, wet ground,
soft foam strip, shallow water transition, small rocks and grass details.
The asset must be reusable by rotation around a hex grid. No text, no UI, no characters, no background.
Export as GLB or FBX.
```

### 丘陵地块

```text
Create a stylized semi-realistic hexagonal hill terrain tile for a turn-based strategy game.
Clean six-sided base, flat bottom, raised terrain, natural slope foot, rocky faces,
clear ridge line, grass and dirt patches, small rocks and flowers, readable from isometric camera.
Do not make it a cone on flat land. Keep it modular and game-ready.
No text, no UI, no characters, no background. Export as GLB or FBX.
```

## 四、AI 输出验收

AI 输出进入项目之前必须先过 Blender 清理：

1. 删除背景、文字、UI、浮空碎片和错误几何。
2. 统一比例，hex 原点放在地块中心。
3. 底部必须是平的，能放在地图平面上。
4. 六边形边界必须规整，能和相邻地块拼接。
5. 重命名 mesh 和材质，例如 `water_surface`、`shore_sand`、`hill_rock`。
6. 减面或重拓扑，避免把 AI 高密度脏网格直接进游戏。
7. 修 UV 和材质，必要时重做贴图。
8. 导出 `lod0.glb` 和 `lod1.glb`。

没有经过上述清理的 AI 结果，只能放在 `source/reference/` 或外部参考目录，不能进入 `terrain/`、`transitions/`、`units/`、`buildables/` 运行时目录。

## 五、和 Blender 自动化的关系

Blender 自动化脚本用于生成可控模板：

```powershell
npm run assets:terrain:blender
```

AI 3D 草模用于提供形体和细节参考。最终资产应以 Blender 模板为标准，把 AI 草模中可用的轮廓、装饰和材质转移进去，而不是用 AI 输出替换模板。

推荐流程：

```text
Blender 自动化模板
  + AI 生成草模
  + 手工清理/重拓扑/统一材质
  -> lod0/lod1 GLB
  -> visual-lab 验收
```

## 六、第一轮执行

第一轮只试三个输入：

| 输入裁图 | AI 工具 | 输出用途 |
| --- | --- | --- |
| `terrain-water-reference.png` | Tripo / Meshy | 判断水盆、浅滩、水面层次是否可用。 |
| `transition-shoreline-reference.png` | Meshy / Rodin | 判断岸线泡沫和浅滩边是否可转成模块化边缘。 |
| `terrain-hill-reference.png` | Tripo / Rodin | 判断坡面、山脊和岩面结构是否比灰盒更接近目标。 |

第一轮成功标准：

- 至少有 1 个 AI 输出能被清理成标准 hex。
- 不破坏 hex 边界和底部平面。
- 能和 Blender 模板对齐。
- 能导出 GLB 并进入 `visual-lab` 单独查看。

失败也可接受：如果 AI 不能稳定理解 hex 结构，就只保留它作为概念参考，继续用 Blender 手工/脚本化建模。
