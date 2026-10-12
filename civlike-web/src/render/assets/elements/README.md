# 地图元素三维模型库

状态：可编辑建模初版，采用 C 风格的非写实、切面低多边形造型。根据三视图重新构造几何，并非图片贴片或自动重建，也不表示已经逐项还原设计稿。

## 预览

在 `civlike-web` 启动 `npm run dev` 后打开 `/?view=map-elements&element=fishing-boat`。

独立页面提供自由旋转、正面、侧面、俯视、线框、动画暂停和 GLB 下载，同时展示对应三视图。此批次没有替换现有 `terrain-world` 地图元素。

### 建筑施工样板

当前 30 类模型、37 个版本，规划 108 个独立资产。乡村建筑有村舍、谷仓、风车磨坊、水车磨坊；防御建筑新增瞭望塔、城堡主楼、城门、城墙。可用 `/?view=map-elements&element=castle-gate` 预览。

- 地基、墙层、木构架/椽架、分层屋瓦、窗框、门扇和附件独立建模。按施工顺序安装，根节点不统一缩放；临时脚手架在竣工时隐藏。
- 支持施工滑条、约 30 秒自动施工、暂停、回退、功能运行与速度。风车帆叶、主轴、水轮、门扇和几何水流分别有转轴或流向，未竣工时不运转。
- 升级附件可切换储物棚、平台，并受施工进度控制；暂不含跨时代升级链、独立升级计时、资源成本或居民调度。
- 入口与进/出水锚点可供后续地图装配使用，尚未接入实际道路水体。门洞射线与水流方向有回归测试。
- GLB 包含施工/临时/升级零件及节点元数据，没有内嵌施工剪辑；通用查看器可能显示所有部件。网页 `mapElementBuildings.ts` 控制当前阶段可见性与运动。
- 防御建筑有分层石砌、拱券、城垛、巡逻道、木楼/木棚与独立旗帜。旗杆边缘固定，布面使用分段顶点波动，不是刚体整片旋转，也不是物理布料模拟。
- 城门可控制通道开闭：先下降吊桥，再提升闸门；关闭时反向执行，拉索上端保持固定。暂停、功能开关、运行速度与施工状态共同控制机构。
- 城墙与城门墙端保存相反法向、同一断面 `curtain-3.2`、3.2 米巡逻道和 1.2 米墙厚。射线检查开放门洞与墙段端部，但尚未完成地图实际组合、塔楼内部楼梯或寻路验收。
- 新防御建筑为 10,910–20,322 三角面，使用既定近景样板 25,000 三角面 / 2.5 MB 上限；不能据此批量铺满地图，仍需 LOD 与实例化。

```powershell
blender --background --factory-startup --python-exit-code 1 --python scripts/blender/map_element_kit.py -- --assets cottage barn windmill watermill
blender --background --factory-startup --python-exit-code 1 --python scripts/blender/map_element_kit.py -- --assets watchtower castle-keep castle-gate castle-wall
node scripts/verify-map-buildings.mjs
```

### 动物成长样板

动物扩展批次完成时为 22 类模型、29 个版本。动物成长样板包括羊、牛、马、鸡、山羊、猪、鸭和鹿。绵羊默认打开 V5；`element=sheep&revision=1` 仍可打开原版。

- 幼体有独立的头身比例和腿长，不是根节点统一缩放；羊毛、角、鬃毛、鸡冠及尾羽分阶段出现，雏鸡与成年鸡羽色不同。
- 模型库提供成长阶段、自动成长、休息/行走/采食（鸡为啄食）和繁育预览。腿部按双段 IK 定位，支撑期脚掌不穿地；行为切换平滑过渡。
- 繁育预览仅对成年阶段开放。约 8 秒等待后显示 1 只子代（鸡 3 只，等待期间有蛋）；子代继续约 45 秒成长，不会无限新增。暂停同时冻结成长和繁育时钟。
- GLB 为节点关节和年龄元数据，网页运行时驱动动作，不包含骨骼蒙皮或可独立播放的成长动画。尚未接入地图寻路、生态繁殖条件或遗传系统。
- 新增动物无独立设计图时只展示年龄选择，不借用其他模型的设计稿。三视相机仍可使用。
- 山羊的后掠角与胡须、猪的鼻盘与卷尾、鸭的扁嘴与蹼足、鹿的分叉角分别建模。幼鹿斑点随成长渐隐；鸭有黄色幼羽与孵化、子代成长，最多 3 只子代。猪等哺乳动物仍限 1 只，仅为有界展示而非真实窝仔数。

```powershell
blender --background --factory-startup --python-exit-code 1 --python scripts/blender/map_element_kit.py -- --assets sheep-v5 cow horse chicken
blender --background --factory-startup --python-exit-code 1 --python scripts/blender/map_element_kit.py -- --assets goat pig duck deer
node scripts/verify-map-fauna.mjs
```

### 器官物候样板

物候批次完成时为 15 类模型、21 个版本，规划 108 个独立资产。页面“资产进度”区分待制作、基础模型和动态样板；版本不重复计数。完整分批计划见 `design/map-element-production-goal.md`。

- 新增 `apple-tree`、`pumpkin-patch`、`sunflower-field`；浆果灌木升级为 `berry-shrub-v4`，保留原版。
- 独立子叶、枝干、叶片、花、果实/种子结构。枝叶分时展开，花瓣退去后结果，成熟后呈现叶色衰退、垂头或地面落叶，支持阶段回退与约 40 秒自动演示。
- 苹果有分叉树冠和独立叶片；南瓜有匍匐藤、宽叶和带棱果实；向日葵有花蕾、放射花瓣及独立种盘；浆果为簇生果实。
- GLB 保存 `lifeRole` 等器官元数据，网页 `mapElementLifecycle.ts` 驱动物候与风动；不是 GLB 内嵌的骨骼/生长动画。未接入真实季节、作物产量或种群模拟。
- 新增三款没有独立设计参考图，页面提供阶段选择，不冒用其他三视图。浆果保留旧参考供风格比较。

```powershell
blender --background --factory-startup --python-exit-code 1 --python scripts/blender/map_element_kit.py -- --assets berry-shrub-v4 apple-tree pumpkin-patch sunflower-field
```

### 自然动态样板 V3

V3 阶段为 12 类、17 个版本；麦田、翻耕地和蔬菜田的无版本链接默认打开 V3。旧 `revision=1/2` 链接仍保持对应版本。

- `/?view=map-elements&element=vegetable-field&revision=3`：不等距菜畦、缺株、大小差异，外叶、中叶和菜心分层建模，不再用球体代表整颗蔬菜。
- `/?view=map-elements&element=wheat-field&revision=3`：轻微弯曲的垄线、不同株高、三层叶片和独立麦穗，成长时由绿转黄。
- 三款地表包含共享边界高度的连续土面、泥土与草地顶点色混合、碎土及短草簇。这是单个样板内部的地表过渡，尚未验收大地图中相邻格的接缝。
- “生长阶段”调整会平滑过渡，菜心/麦穗晚于茎叶出现；“自动生长”约 28 秒走完播种到成熟，到成熟后保持，不突然跳回幼苗。
- 风力影响根部固定的植株和边缘草簇；暂停会停止风动与自动生长。“随机长势”改变大小与成熟差异，不重新排列地块。
- 生长、风动由 `mapElementGrowth.ts` 在网页运行。下载的 GLB 保留 `crop` / `cropPart` 节点及成熟几何，但不包含这些运行时动画剪辑；Blender 源文件仍可编辑。
- V3 单模型预算为 25,000 三角面、2.5 MB，浏览器检查少于 450 次绘制调用。麦田有独立的植株/麦穗节点，尚未实现大地图实例化与 LOD；不得据此推断 200 格性能已合格。

```powershell
blender --background --factory-startup --python-exit-code 1 --python scripts/blender/map_element_kit.py -- --assets plowed-field-v3 wheat-field-v3 vegetable-field-v3
```

### 农田改进样板 V2

V2 阶段有 12 类模型、14 个版本。底部“原版 / 改进版”仍可切换，原版源文件和 GLB 未覆盖。版本切换保留所选正面/侧面/俯视模式，下载链接对应当前版本。

- 麦田：`/?view=map-elements&element=wheat-field&revision=2`。弯曲茎秆、分层折叠叶片、重叠麦粒、成熟色差，底部使用连续田垄表面。
- 翻耕地：`/?view=map-elements&element=plowed-field&revision=2`。连续封闭土面、圆钝田垄、沟底和垄顶色差、嵌入式碎土，外围降低到统一高度。
- 两款分别输出 `wheat-field-v2`、`plowed-field-v2` 的 `.blend` 和 `.glb`；`revision=1` 可直接打开原版。
- 这是本地重建的比较样板，没有下载或使用 Synty、Quaternius 的第三方网格；不是商用成品质量或大地图接缝的验收结论。

单独重新生成两款：

```powershell
blender --background --factory-startup --python-exit-code 1 --python scripts/blender/map_element_kit.py -- --assets plowed-field-v2 wheat-field-v2
```

## 资产

本目录保存 GLB；可编辑 Blender 源文件位于 `../source/elements/<id>.blend`。源文件保留独立零件，导出时按静态父节点合并网格，动画节点保持独立。

| ID | 模型 | 当前动画 |
| --- | --- | --- |
| wheat-field | 成熟麦田 | 无 |
| plowed-field | 翻耕田地 | 无 |
| vegetable-field | 蔬菜田 | 无 |
| timber-bridge | 木制车行桥 | 无 |
| fishing-boat | 近岸渔船 | 两侧船桨摆动 |
| river-fish | 河鱼 | 摆尾 |
| sheep | 绵羊 | 头部和尾部轻动 |
| pine-tree | 针叶树 | 无 |
| berry-shrub | 浆果灌木 | 无 |
| reeds | 水岸芦苇 | 五组茎叶摆动 |
| village-well | 水井 | 无 |
| handcart | 双轮手推车 | 车轮旋转 |

单位为米，Blender 使用 Z 向上、-Y 为正面；GLB 导出为 Y 向上。各资产的尺寸、三角面、文件大小、动画节点和参考图名称记录在 `manifest.json`。动画为 24 fps、3 秒的物体节点循环，不是骨骼动画；船和车没有位移路径，绵羊没有步态。

## 重新生成与验证

以下命令均在 `civlike-web` 执行，需要 Blender 4.5 和项目 Node 依赖：

```powershell
npm run assets:elements:blender

# 只重新生成指定模型，保留其他模型的清单条目
blender --background --factory-startup --python-exit-code 1 --python scripts/blender/map_element_kit.py -- --assets fishing-boat sheep

# Blender 源文件可读性、GLB 回读、三角面及有限坐标
blender --background --factory-startup --python-exit-code 1 --python scripts/blender/verify_map_element_kit.py

# 需先在 5173 启动预览服务
node scripts/verify-map-elements.mjs

node node_modules/vitest/vitest.mjs run --exclude '**/.sites-preview/**'
npm run build
```

浏览器检查覆盖清单中全部版本加载、画面非空和完整取景、动画与暂停、三视图、线框、移动端切换及横向溢出，另验证版本切换、版本链接刷新、下载链接、鼠标旋转、生长几何、自动生长、零风静止、风动、平板控件和单样板绘制调用预算。物候样板额外验证萌芽、开花、成熟、衰败四阶段的器官可见性与画面差异。截图和 JSON 结果位于 `artifacts/map-elements/`。这些检查不等于艺术质量验收，也不等于 200 格场景的性能验收。

## 后续工作

- 与设计稿继续比对轮廓和细节，尤其是植被叶簇、屋瓦、水井附件和动物面部。
- 补齐人物与剩余元素，人物单独制作骨架、步态和运输动作。
- 制作 LOD、实例化方案、地形放置锚点及季节变体，再接入大地图。
- 当前没有 UV 烘焙、完整骨骼或地图寻路；不要将基础模型或待制作清单视为目标已经完成。
