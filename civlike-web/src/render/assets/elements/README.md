# 地图元素三维模型库

状态：可编辑建模初版，采用 C 风格的非写实、切面低多边形造型。有三视参考的条目依据参考重新构造几何，无参考条目为程序化建模样板；并非图片贴片或自动重建，也不表示已经逐项还原设计稿。

## 预览

在 `civlike-web` 启动 `npm run dev` 后打开 `/?view=map-elements&element=fishing-boat`。

独立页面提供自由旋转、正面、侧面、俯视、线框、动画暂停和 GLB 下载；已有三视参考的条目同时展示对应图片。此批次没有替换现有 `terrain-world` 地图元素。

### 人物骨架与职业动作

当前累计 57 类独立模型、66 个版本，108 类规划中剩余 51 类。新增农夫 `farmer`、渔夫 `fisher`、伐木工 `woodcutter`、商人 `merchant`，保留可编辑骨架、IK 控制与独立零件的 `.blend`，导出蒙皮 `.glb`。

- 每款包含 3 秒循环的 `Idle` / `Walk` / `Work`，模型库可切换、暂停和调整 0–2 倍速度；切换使用 0.3 秒混合。原地行走不是地图寻路。
- 农夫持锄、渔夫持竿、伐木工持斧、商人持账本和钱币。工具绑定握持骨骼，不依赖网页额外挂载；衣服、帽子、腰带、靴子和随身包具区分职业。
- 四款分别为 1,792 / 1,812 / 1,692 / 1,760 三角面，GLB 约 0.32 MB。分段蒙皮是风格化样板，尚无手指骨骼、面部表情、人物成长、骑乘和搬运配对动作。
- Blender IK 约束经导出采样为骨骼剪辑，可在支持蒙皮动画的查看器中播放。工作土块/树桩的显隐由网页根据动作控制，通用查看器不会自动隐藏这些道具。导出方式参见 [Blender 4.4 glTF Actions 说明](https://developer.blender.org/docs/release_notes/4.4/pipeline_assets_io/)。
- 尚未接入地图人流、城镇运输、工作产出、库存、地形贴合、路径跟随或多人 LOD；不把模型库工作动作当作已经完成生产模拟。

```powershell
blender --background --factory-startup --python-exit-code 1 --python scripts/blender/map_element_kit.py -- --assets farmer fisher woodcutter merchant
node scripts/verify-map-people.mjs
```

### 火山、熔岩地与荒漠

此批完成时为 53 类独立模型、62 个版本。新增 `volcano`、`lava-field`、`sand-dunes`、`desert-oasis`，均保存可编辑 `.blend` / `.glb`。

- 火山为凹陷火口、低于火口边缘的熔池、三条下坡熔岩带和 14 个火山灰粒子；熔岩地为低矮起伏基岩、五条主裂隙与八条支裂隙。熔流沿网格显示移动明暗及自发光变化，不是把整个山体放大或变色。
- 沙丘使用偏向一侧的三条沙脊、细沙纹与 24 个沿表面轨迹移动的沙粒。使用 Blender BVH 从实际三角网格取高，每条轨迹 321 个样本；不依赖原高度公式猜测网格高度，运行时不需要逐帧射线查询。
- 绿洲具有不规则泉池、浅水区、岸边草簇/卵石、三株高度不同的棕榈及独立叶轴/羽状小叶。水面实际顶点有不超过约 1 cm 的轻微起伏，靠岸减弱；24 片棕榈叶及草簇独立风动。
- `terrainEffect` 区分 `lava` / `water` / `ash` / `sand`，由 `mapElementGeodynamics.ts` 驱动。活动强度控制水波/熔流，风力控制风沙/绿洲植被；零值静止，暂停冻结各自时钟。模型库不对这些干旱地貌展示不适用的覆雪或四季控制。
- 最终为 2,830 / 3,362 / 3,434 / 7,148 三角面，约 0.24 / 0.29 / 0.66 / 0.55 MB。沙丘额外体积主要来自贴地轨迹元数据，不是加面；最终专项近景绘制调用采样为 22 / 18 / 27 / 99 次，粒子显隐会造成少量波动。
- 沿用半径 1.75 m、每边 15 段、标高 0.08 m 的六边边界及六向连接锚点。八种地貌的全部配对通过实际边缘顶点/三角面检查，但跨格颜色融合、坡势连续、河网和地图 LOD 仍未完成。
- 当前是风格化动态资产，不是喷发灾害、熔岩冷却结壳、风蚀、泉水补给或生态生长模拟。棕榈为绿洲组合件，本款没有独立植株成长时序；动态元数据需要网页驱动，不是通用 GLB 烘焙动画。

```powershell
blender --background --factory-startup --python-exit-code 1 --python scripts/blender/map_element_kit.py -- --assets volcano lava-field sand-dunes desert-oasis
node scripts/verify-map-arid.mjs
```

### 六边形地貌与季相

此批完成时为 49 类独立模型、58 个版本。新增草原 `grassland`、缓丘 `rolling-hills`、岩山 `rocky-mountain`、雪峰 `snow-peak`，均有 `.blend` / `.glb`。

- 草原为微起伏地表、不规则裸土、疏密草簇和散石；缓丘为双丘与低谷；岩山为多峰山脊、分区岩面和坡脚碎石；雪峰有更高主脊及夏季保留雪冠。不是同一个轮廓换色。
- 平顶六边形半径 1.75 m、边缘标高 0.08 m、底面 -0.16 m；每边 15 段，内部网格扰动，边界顶点固定。六个 `HexEdge` 空节点保存 `connectionKind=terrain`、`profile=hex-flat-3.5-v1`、`normalGltf`、`neighborOffsetGltf`，后两者是 GLB Y-up 坐标。只证明该协议下未旋转地貌彼此对齐，不代表已接入现有地图尺度/道路/河流。
- 网页有春夏秋冬、积雪、风力与四季循环。颜色平滑过渡，覆雪按相对高度、坡面及分区渐显，地形顶点和整体比例不变化；草簇独立风动，重覆雪时隐藏。不是雪深、侵蚀、降水、水文或作物产量模拟。
- 自动循环约 90 秒一轮，暂停冻结季相时钟和风动；关闭循环保留当前状态。`LandformRoot.terrainType`、`snowThreshold`、`terrainTuft` 等元数据由 `mapElementTerrain.ts` 驱动，GLB 中没有烘焙四季动画，通用查看器会同时显示全部雪层。
- 单款最终为 4,760–8,682 三角面、0.43–0.74 MB。源文件保留独立草叶和坡面，可继续编辑；地图批量应用仍需 LOD、合批、边界色彩融合和环境统一。

```powershell
blender --background --factory-startup --python-exit-code 1 --python scripts/blender/map_element_kit.py -- --assets grassland rolling-hills rocky-mountain snow-peak
node scripts/verify-map-landforms.mjs
```

### 针叶树与芦苇重做

此批完成时为 45 类独立模型、54 个版本。`pine-tree-v4`、`reeds-v4` 替换对应 family 的默认预览，原版仍可切换，不把重做版本计作新增资产。

- 针叶树：20 个主枝、60 个侧梢、成束针叶、抽梢芽、花粉球花、4 个种子球果及 72 个可转开的木质鳞片。幼苗建立、枝条伸展、球果长大、绿转褐、鳞片张开和有翅种子展示分别控制；针叶保持常绿，不套用花瓣和水果阶段。
- 芦苇：9 根高低错落的分节秆、45 片弯叶和叶鞘、真正分枝的圆锥花序。不再使用旧版香蒲棒状穗头；花期紫灰小穗退去后留下浅色种穗，穗枝带着小穗一起运动，晚期叶片枯黄下垂。岸边浅水仍是静态底板。
- `lifeRole` 为针叶树新增 `pollen` / `cone` / `scale` 语义，使用现有器官驱动。网页执行生长和风动，通用 GLB 查看器不会自动运行这些元数据。
- 这是风格化缩时展示，松树为泛化的三针束造型，不冒充精确树种；多年幼树建立和成年球果周期压缩在同一时间条中。尚无授粉、种子飞散萌发、松针换叶周期、芦苇地下根茎扩张、地图季节接入或 LOD。

结构参考：[UF/IFAS 松树针束与球果](https://ask.ifas.ufl.edu/publication/FR003)、[King County 芦苇羽状圆锥花序](https://kingcounty.gov/en/dept/dnrp/nature-recreation/environment-ecology-conservation/noxious-weeds/identification-control/phragmites)。只核对结构，未下载第三方网格。

```powershell
blender --background --factory-startup --python-exit-code 1 --python scripts/blender/map_element_kit.py -- --assets pine-tree-v4 reeds-v4
node scripts/verify-map-conifer-reed.mjs
```

### 竹丛、野花与土豆

此批完成时为 45 类独立模型、52 个版本。新增 `bamboo`、`wildflowers`、`potato-field`，由 `scripts/blender/map_element_meadow.py` 生成。

- 竹丛：五根错落竹秆、40 个分节节点、节环、逐步退去的笋箨、侧枝及狭长叶、收细竹梢。竹节沿长度伸长并保持直径，末段维持常绿叶片并出现少量落叶。本样板仅演示出笋到成竹的营养生长，没有把罕见开花强行当作年度阶段。
- 野花丛：12 株菊形草花，基生叶、茎生叶、总苞、花苞、192 个独立舌状花瓣、中心花盘及瘦果种头，默认花期。白色与淡粉作为游戏美术混合，不代表精确单一物种；不复用浆果结构。
- 土豆田：四穴植株，分枝茎、48 组复叶、五裂花冠/黄色花药、地下匍匐茎及 20 个带芽眼的块茎。块茎属于地下茎结构，不套用绿色果实到黄果的颜色动画；地上茎叶后期衰退而地下块茎保留。
- 土豆工具栏的分层图标切换土层剖面，仅隐藏前半土体及土块，不隐藏植物或移动块茎；关闭恢复完整覆土。源文件/GLB 默认包含完整土层，`inspectionCover` 是查看器元数据，不是烘焙剖面动画。
- `lifeRadialGrowth=1` 保持竹节直径，旧模型默认 `.45` 不变。物候、展开及风动仍需网页驱动，不是可直接在任意 GLB 查看器播放的生长剪辑。
- 尚未模拟竹鞭扩张、竹种开花周期、野花播种/授粉、土豆采收与土壤水肥/产量，也未接入地图季节或 LOD。

结构资料：[UMD 竹丛与竹鞭](https://extension.umd.edu/resource/containing-and-removing-bamboo)、[PROSEA 竹秆生长](https://prosea.prota4u.org/view.aspx?id=2070)、[NC State 菊形花序](https://plants.ces.ncsu.edu/plants/leucanthemum-vulgare/)、[UMN 土豆匍匐茎与覆土](https://extension.umn.edu/garden-and-home/yard-and-garden/gardening-in-minnesota/growing-potatoes)。仅核对结构，未下载第三方网格。

```powershell
blender --background --factory-startup --python-exit-code 1 --python scripts/blender/map_element_kit.py -- --assets bamboo wildflowers potato-field
node scripts/verify-map-meadow.mjs
```

### 林下与水生样板

林下水生批次完成时为 42 类独立模型、49 个版本。新增 `cactus`、`fern`、`mushrooms`、`lily-pad`，由 `scripts/blender/map_element_understory.py` 生成。

- 仙人掌：纵肋肉质茎、侧臂、刺座及辐射刺、花瓣和成熟红果，保持茎体绿色，不套用秋季落叶材质。
- 蕨丛：分节叶轴由卷曲姿态逐段舒展，羽叶和背面孢子囊群随叶轴运动；不显示花朵、果实或种子。
- 菌菇：不同高度的菌柄、弧面菌盖和放射菌褶，使用 Blender `ClosedCap` 形态键/GLB morph target 实现闭合到张开，不是整株等比放大；孢子结构独立于菌盖生长，标签不伪装成开花结果。
- 睡莲：有缺口的浮叶、贴合叶面的放射叶脉、分层花瓣及花后种荚；默认展示花期。浮叶有小幅上下漂动，叶片保留水面间隙。浅水面为静态展示底板，不是新水波系统，也不是荷花模型。
- 新增 `lifeUnfurlAngle`、可覆盖的 `lifeUnfoldAngle` 和 `lifeBob` 元数据，旧资产默认行为不变。菌菇导出不应用修改器，以保留形态键；其他资产导出设置不变。
- 这是局部缩时展示：未模拟菌丝扩张、孢子释放/萌发、授粉、仙人掌储水、睡莲果实沉水或地图水位/生态条件；菌菇造型不是食用鉴定依据。所有器官生命周期仍需网页驱动，不是独立烘焙动画剪辑。

结构参考：[NPS 仙人掌](https://www.nps.gov/sagu/learn/nature/cacti-and-desert-succulents.htm)、[USFS 蕨类](https://www.srs.fs.usda.gov/pubs/gtr/uncaptured/gtr_se015.pdf)、[Penn State 菌盖发育](https://extension.psu.edu/seeding-substrate-and-management-of-growing-agaricus-bisporus)、[NParks 睡莲](https://www.nparks.gov.sg/florafaunaweb/flora/2/2/2271)。未下载第三方网格。

```powershell
blender --background --factory-startup --python-exit-code 1 --python scripts/blender/map_element_kit.py -- --assets cactus fern mushrooms lily-pad
```

### 树木扩展样板

新增 `oak-tree`、`birch-tree`、`willow-tree`、`palm-tree`。模型采用独立枝干与折面叶片，不使用实心球体替代整个树冠；源文件由 `scripts/blender/map_element_trees.py` 生成。

树木批次完成时为 38 类独立模型、45 个版本。

- 橡树使用粗主干、根部外扩、侧枝、裂片叶与带杯状果帽的橡子。
- 白桦使用细长白色树皮、深色横向皮孔、细枝、小型尖叶与柔荑花序/种序。
- 垂柳使用展开的主枝、下垂细枝与交替狭长叶；本样板选择雌花序到种子的展示，不把同一株描述为雌雄同株。
- 棕榈使用弯曲主干、环状叶痕、羽状叶轴及成对小叶，花后椰果从绿转褐；末期保留绿色树冠，不能套用落叶休眠。
- 木质分枝的局部生长轴沿各自分枝方向；叶组、花与果实保留父子附着层级和独立阶段。风动、自动进度、暂停和手动回退沿用物候驱动。
- 当前把幼树建立和成年物候压缩在同一展示条；不代表树龄、真实逐年生长、授粉条件、种子传播或生态更新。落叶树末期以叶组渐退表现疏冠，尚无逐片落叶轨迹；棕榈尚无老叶脱落更新。
- GLB 保留阶段元数据，不包含任意查看器可直接播放的生长剪辑；仍未接入地图季节、邻格遮挡、LOD 或实例化。

结构资料：[NC State 橡树](https://plants.ces.ncsu.edu/plants/quercus-alba/)、[NC State 白桦](https://plants.ces.ncsu.edu/plants/betula-pendula/common-name/european-weeping-birch/)、[OSU 垂柳](https://landscapeplants.oregonstate.edu/plants/salix-babylonica/)、[NParks 椰子树](https://www.nparks.gov.sg/florafaunaweb/flora/5/6/5618)。只作形态参考，未下载第三方网格；并非精确植物学复刻。

```powershell
blender --background --factory-startup --python-exit-code 1 --python scripts/blender/map_element_kit.py -- --assets oak-tree birch-tree willow-tree palm-tree
```

### 作物扩展样板

作物批次完成时为 34 类模型、41 个版本，规划 108 个独立资产。新增 `corn-field`、`rice-paddy`、`vineyard`、`cotton-field`，例如 `/?view=map-elements&element=cotton-field`。

- 玉米有节间/叶鞘、交错披垂叶片、顶部雄穗、侧生果穗、苞叶和花丝。花药消退后保留干穗轴，籽粒随灌浆出现；成熟苞叶轻微松开。
- 水稻有九丛分蘖、窄叶、分枝穗轴和独立籽粒。穗轴与附着籽粒一起随成熟下垂，花期也有完整支撑。田埂内是静态风格化浅水，不含灌排模拟或水面波动。
- 葡萄有支架、拉线、木质主干、结果枝、卷须及逐级果柄；花退后果串从绿转紫。多年生建立与一年物候被压缩到同一展示条，不代表真实葡萄逐年修剪系统。
- 棉花有掌状叶外观、花、闭合棉铃、四瓣铃壳和独立棉絮。铃壳以附着点为轴渐开，棉絮在后期出现，不只是绿球变白球。
- 新节点继续使用物候层级，增加 `lifeOpenAngle` / `lifeOpenAxis` / 开裂区间及可选 `lifeDroopAngle` / `lifeDroopStart`。GLB 不含独立播放的生长剪辑，运行时为 `mapElementLifecycle.ts`。
- 源文件、GLB 和阶段回退测试均保留；不接入真实播种、收获、肥力产量或地图级季节时间，也不将阶段计作新资产。

```powershell
blender --background --factory-startup --python-exit-code 1 --python scripts/blender/map_element_kit.py -- --assets corn-field rice-paddy vineyard cotton-field
```

### 建筑施工样板

防御建筑批次完成时为 30 类模型、37 个版本。乡村建筑有村舍、谷仓、风车磨坊、水车磨坊；防御建筑有瞭望塔、城堡主楼、城门、城墙。可用 `/?view=map-elements&element=castle-gate` 预览。

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

浏览器检查覆盖清单中全部版本加载、画面非空和完整取景、动画与暂停、三视图、线框、移动端切换及横向溢出，另验证版本切换、版本链接刷新、下载链接、鼠标旋转、生长几何、自动生长、零风静止、风动、平板控件和单样板绘制调用预算。物候样板按类型验证出芽、展叶/开花/花粉球花、成孢/结籽/果实成熟以及后期阶段的器官可见性与画面差异，不统一假定所有植物都开花结果。截图和 JSON 结果位于 `artifacts/map-elements/`。这些检查不等于艺术质量验收，也不等于 200 格场景的性能验收。

## 后续工作

- 与设计稿继续比对轮廓和细节，尤其是植被叶簇、屋瓦、水井附件和动物面部。
- 补齐人物与剩余元素，人物单独制作骨架、步态和运输动作。
- 制作 LOD、实例化方案、地形放置锚点及季节变体，再接入大地图。
- 当前没有 UV 烘焙、完整骨骼或地图寻路；不要将基础模型或待制作清单视为目标已经完成。
