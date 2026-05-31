# 下一步制作执行单

本文件只定义最近一轮真实资产制作，不扩散到整套地图。当前目标是先把 `visual-lab` 中最不像最终效果的水域、岸线和丘陵，从灰盒推进到可导入验收的 Blender/glTF 资产。

参考图的系统化拆解见：

```text
src/render/assets/REFERENCE_BREAKDOWN.md
```

如果使用 AI 图生 3D，必须遵守：

```text
src/render/assets/AI_3D_PIPELINE.md
```

## 一、第一批只做三个资产

| 顺序 | 资产 | 源文件 | 导出文件 | 目的 |
| --- | --- | --- | --- | --- |
| 1 | `terrain-water` | `source/terrain/terrain-water.blend` | `terrain/terrain-water-lod0.glb` | 解决水域像蓝色平片的问题。 |
| 2 | `transition-shoreline` | `source/transitions/transition-shoreline.blend` | `transitions/transition-shoreline-lod0.glb` | 解决水陆硬切问题。 |
| 3 | `terrain-hill` | `source/terrain/terrain-hill.blend` | `terrain/terrain-hill-lod0.glb` | 解决地块没有真实起伏的问题。 |

这三项完成前，不建议继续做单位、城市和资源模型。地图整体质感首先取决于水、岸线和高度。

## 二、制作前准备

1. 选 8-12 张参考图：文明式等距地图、海岸线、水面、丘陵、低多边形微缩景观。
2. 固定相机目标：斜俯视，能看见顶部和侧面，不追求真实比例，追求一眼可读。
3. 固定风格：半写实微缩景观，清晰色块，夸张高度，低面数但边缘干净。
4. 固定尺寸：每个地块以同一个 hex 半径和中心点制作，原点在地块中心。

可先用 Blender 自动化脚本生成第一版可控源文件和 GLB，再进入 Blender 手工清理与二次塑形：

```powershell
npm run assets:terrain:blender
```

脚本默认只生成本执行单的三项资产，不扩散到单位、城市和资源。

## 三、水域 `terrain-water`

Blender 中至少拆成：

```text
terrain-water
  ├── hex_basin_side       低洼水盆侧壁
  ├── shallow_sand_ring    浅滩环
  ├── water_surface        水面
  ├── wave_decals          轻量波纹
  └── reed_or_rock_props   少量岸边小装饰
```

制作要求：

- 水面低于陆地顶面，不要和草地同高。
- 浅滩要在水面和陆地之间形成一圈缓冲。
- 波纹使用少量面片或贴图，不要做复杂水网格。
- 颜色用蓝绿水面、浅米色浅滩、少量白色高光。
- LOD1 可以移除芦苇、小石头，只保留水盆、浅滩、水面。

验收：

- 单块水域不是蓝色圆片。
- 多块水域放在一起像连续水体。
- 和岸线过渡资产组合时不露明显缝。

## 四、岸线 `transition-shoreline`

Blender 中至少拆成：

```text
transition-shoreline
  ├── sand_shelf       可拼接浅滩边
  ├── foam_strip       泡沫线
  ├── wet_ground       湿润岸边
  └── edge_props       少量草、石头或水草
```

制作要求：

- 资产必须沿 hex 边拼接，不要做成只能放一个方向的孤立装饰。
- 泡沫线要轻，不要盖住地块主体。
- 岸线要能服务草地、森林、丘陵三种陆地邻接。
- 需要考虑旋转复用：同一个模型旋转 6 个方向仍然可用。

验收：

- 水陆不硬切。
- 旋转后仍能贴合六边形边。
- 缩小时岸线仍清楚，但不过分抢眼。

## 五、丘陵 `terrain-hill`

Blender 中至少拆成：

```text
terrain-hill
  ├── raised_hex_base   抬高底座
  ├── hill_slope        连续坡面
  ├── ridge_line        山脊线
  ├── rock_faces        岩面
  └── foot_blend        坡脚过渡
```

制作要求：

- 不要在平地上插独立尖锥；山体要从坡脚自然抬起。
- 山脊方向要明显，方便相邻丘陵组成连续山脉。
- 高度要夸张，但不能遮住单位、城市和资源。
- 岩面、土坡和草坡要分材质，不要整块土褐色。

验收：

- 俯视角能看出坡面和山脊。
- 和草地相邻时有坡脚逻辑。
- 相邻两个丘陵不会像两个孤立石块。

## 六、导出规范

每个资产导出：

```text
lod0.glb  用于 normal/near 视角
lod1.glb  用于远距离或性能 fallback
```

导出前检查：

- 原点在地块中心。
- 比例和现有 hex 灰盒一致。
- 模型面数适合批量摆放。
- 材质命名清楚，例如 `water_surface`、`shore_sand`、`hill_rock`。
- 不把未清理的 AI 网格直接导入项目。

## 七、进入 `visual-lab` 的条件

只有当 `.blend` 和 `.glb` 都存在时，才把 manifest 状态从 `source-needed` 或 `graybox` 改为 `ready-for-lab`。

进入 `visual-lab` 后检查：

1. 单块读得清。
2. 相邻组合不硬切。
3. 移动端尺寸可读。
4. 旋转 6 个方向没有明显破绽。
5. 不依赖规则层改动。

通过后再考虑迁入主线 Pixi 地图。

## 八、按当前参考图拆解制作

当前参考图路径：

```text
C:\Users\saber\Downloads\15d60e6d-5bc8-40f3-b55f-5be7877de867.png
```

这张图不要理解成“照着画一张图”，而要拆成资产生产规则：

| 参考区块 | 要吸收的制作规则 | 当前落地方式 |
| --- | --- | --- |
| 整体风格参考 | 半写实微缩景观、色块清楚、地形高度夸张、海岸和山体强识别。 | 所有资产统一到同一色板、同一斜俯视相机、同一 hex 尺寸。 |
| 地块类型参考 | 草原、丘陵、森林、沙漠、山脉、雪地、海岸、海洋都不是平面贴图。 | 第一轮只做水域、岸线、丘陵；后续再扩展森林、沙漠、雪地。 |
| 地块边缘过渡参考 | 草原到沙漠、草原到森林、平地到丘陵、陆地到海岸、河流边缘都要软过渡。 | 第一轮先做 `transition-shoreline`，验证可旋转、可拼接的边缘模型。 |
| 高度层级参考 | 平地、丘陵、高丘陵、低山、高山、雪山形成清楚的高度序列。 | `terrain-hill` 不能只是一个尖锥，要先做坡脚、坡面、山脊和岩面。 |
| 模型结构参考 | 一个完整地块 = 六边形底座 + 地形表面 + 装饰物 + 边缘侧面 + 可选资源/建筑。 | manifest 里的每个资产都必须保留源文件、LOD、材质和验收标准。 |
| 光照与氛围参考 | 清晨/白天/傍晚/夜晚靠光照和色温统一风格，不靠每个模型单独变色。 | 第一轮模型只做中性材质，后续在 `visual-lab` 做灯光预设。 |

## 九、实际制作顺序

### 第 1 天：水域和岸线灰模源文件

产物：

```text
src/render/assets/source/terrain/terrain-water.blend
src/render/assets/source/transitions/transition-shoreline.blend
```

要求：

- 用 Blender 建真实 hex 尺寸，不用网页里的 primitive 当最终资产。
- 水域先做水盆、浅滩、水面、波纹四层。
- 岸线先做一条可旋转复用的 hex 边，不做一整圈不可复用装饰。
- 不做复杂 shader，先把形体和拼接做对。

### 第 2 天：导出 GLB 并进工坊验收

产物：

```text
src/render/assets/terrain/terrain-water-lod0.glb
src/render/assets/terrain/terrain-water-lod1.glb
src/render/assets/transitions/transition-shoreline-lod0.glb
src/render/assets/transitions/transition-shoreline-lod1.glb
```

要求：

- `lod0` 保留浅滩、波纹和少量小装饰。
- `lod1` 去掉小装饰，只保留轮廓和材质分区。
- 在 `visual-lab` 中用三块水 + 两块陆地测试拼接。
- 通过后才把 manifest 状态改为 `ready-for-lab`。

### 第 3 天：丘陵源文件和高度序列

产物：

```text
src/render/assets/source/terrain/terrain-hill.blend
src/render/assets/terrain/terrain-hill-lod0.glb
src/render/assets/terrain/terrain-hill-lod1.glb
```

要求：

- 先做丘陵，不急着做高山/雪山。
- 丘陵必须能和草地过渡，坡脚不能硬切。
- 山脊方向要明显，两个丘陵相邻时能组成连续走势。
- 高度比平地夸张，但给单位和城市留出可读空间。

### 第 4 天：只做验收，不加新资产

检查：

- 参考图里的“海岸”和“高度层级”是否已经有 60% 观感。
- 单块地块是否好看不重要，相邻组合必须先成立。
- 如果水域、岸线、丘陵组合仍然硬切，继续修这三项，不开森林、单位、城市。

## 十、不要做的事

- 不要直接把 AI 生成图当贴图贴到 hex 上。
- 不要先做城市、单位、资源；没有好看的地形底座，它们会显得漂浮。
- 不要在主线 Pixi 地图里边改边试真实资产。
- 不要把未清理的 Meshy/Tripo 模型直接导入项目。
- 不要为了视觉效果改 `src/game` 里的规则状态。
