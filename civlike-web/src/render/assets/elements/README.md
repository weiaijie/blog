# 地图元素三维模型库

状态：可编辑建模初版，采用 C 风格的非写实、切面低多边形造型。有三视参考的条目依据参考重新构造几何，无参考条目为程序化建模样板；并非图片贴片或自动重建，也不表示已经逐项还原设计稿。

## 预览

在 `civlike-web` 启动 `npm run dev` 后打开 `/?view=map-elements&element=fishing-boat`。

独立页面提供自由旋转、正面、侧面、俯视、线框、动画暂停和 GLB 下载；已有三视参考的条目同时展示对应图片。此批次没有替换现有 `terrain-world` 地图元素。

### 火车站与工厂

当前累计 75 类独立模型、84 个版本，108 类规划剩余 33 类。新增 `train-station`、`factory`，不将站台、内部机器或升级货台重复计为独立资产。

- 火车站：砖砌候车室、开放柱廊、长椅、台阶式地基、连续上站坡道、玻璃雨棚、时钟、窄轨站线和臂板信号机。两端 `rail` 接点沿用 `narrow-rail-0668-v1`，轨中心距 0.72 m、内侧轨距 0.668 m、轨顶 0.28 m；实际钢轨射线及现有机车/货车厢包围盒检查平台、雨棚和信号机净空。没有把列车缩放后塞进站台。
- 时钟分针/时针按 12:1 角速度运转，属于缩时表现，不对应现实钟表时间。发车信号通过控件在水平停车与下斜通行位置之间转换，暂停、停止功能和未竣工限制动作；它不是已接入交通调度的信号联锁。
- 工厂：三个锯齿采光屋顶、侧面窗带、砖墙和钢架；内部电机、冷却片、独立飞轮、轴承、等径带轮、闭合皮带与车床。带轮、飞轮和主轴同速，皮带缝线沿实际两轮及公切线组成的闭合路径移动，线速度等于轮缘速度；没有拉长、缩短皮带或缩放厂房。外墙排风扇独立转动。
- 工厂升级增加装卸雨棚、货台、托盘和货箱，侧墙留出实际开口，货箱与门柱避开装卸接口。火车站升级增加站灯与行李；施工、升级附件均复用分件装配，根节点不缩放。
- 两款均提供屋顶剖面，保留内部结构；`.blend` 保留独立构件，GLB 按静态父节点与材质合并。机构依靠 `mapElementBuildings.ts` 元数据驱动，不是通用 GLB 烘焙剪辑。
- 最终三角面为 14,604 / 15,273，GLB 为 1,095,008 / 1,098,072 字节。当前是近景样板，尚无生产库存、电力消耗、人员上下车、列车时刻表、跨区交通、真实地图装配或 LOD 验收。

结构参考：[York 车站建筑记录](https://her.york.gov.uk/Monument/MYO825)用于核对站台、候车/售票空间与铁构雨棚的关系；[Science Museum 的工厂皮带驱动藏品](https://collection.sciencemuseumgroup.org.uk/objects/co52168/mill-engine-staionary-engine)用于核对飞轮与带传动关系。此处是游戏尺度电机驱动工厂，不是藏品蒸汽机或历史车站的复刻；没有下载第三方网格或冒用三视参考。

```powershell
blender --background --factory-startup --python-exit-code 1 --python scripts/blender/map_element_kit.py -- --assets train-station factory
node scripts/verify-map-buildings.mjs
```

预览：`/?view=map-elements&element=train-station`、`/?view=map-elements&element=factory`。专项完整检查输出在 `artifacts/map-elements/buildings/verification.json`；不传 ID 时覆盖当前全部 13 款建筑。最终 377 项源码测试、84 个版本 Blender 回读和全库浏览器检查通过，两款升级态绘制调用为 88 / 82。截图写入重试记录见制作目标文档，不等同页面错误或大地图性能结论。

### 马厩、铁匠铺与集市

此批完成时累计 73 类独立模型、82 个版本，108 类规划剩余 35 类。新增 `stable`、`blacksmith`、`market-hall`，不是同一房屋的换色，也不将施工阶段或升级附件计为新资产。

- 马厩：前部通道、三间木隔栏、低门/铰链、草料槽、斜草架、散草与垫草、屋架、风向标；升级为后部储草阁及侧面登阁梯。通过三处 `animal` 接点可放置既有成年马，使用实际顶点包围盒检查栏门、草架、分隔与阁底静态净空。另逐顶点检查草捆/绑绳不穿瓦面。建筑尺寸已在 Blender 烘焙，运行时根节点仍为单位缩放。尚未验证马匹转身、走入或采食动作。
- 铁匠铺：石砌后墙/侧墙、开放工作区、炉床/炉罩/烟道、煤火、带尖角的铁砧、工具台/锤钳、风箱及升级遮棚。固定下叶板、绕喷嘴铰接的上叶板、折叠皮囊为不同网格；皮囊上下边界分别贴合叶板，不整体缩放模型。炉火随运行变化，未加入火焰物理或生产库存。
- 集市：开放柱廊、前后通道、四处交易位、独立柜台/货箱、水果蔬菜、面包、陶罐与升级散货。中央通道在升级后仍通过实际网格射线贯通检查。条纹遮棚固定在前后两根横梁，只有中段起伏。
- 三款均支持逐件施工、回退、自动施工、功能运行、运行速度、暂停及升级附件。新增屋顶剖面按钮可隐藏瓦面并保留屋架与内部构件，不影响施工状态；默认展示完整屋顶。
- 基于原有建筑驱动新增 `sway`、`bellows`、`bellows-skin`、`ember`、`awning` 类型；风箱变形先换算至铰链局部坐标，兼容 GLB 按材质分拆后的子节点变换。旧建筑和城门动作路径不改变。
- 三款 8,309 / 8,964 / 9,620 三角面，617,348 / 644,808 / 770,528 字节，升级状态近景绘制调用 64 / 51 / 51。没有提高预算；不是地图缩尺、实例化、LOD 或 200 格性能已合格。
- `.blend` 和 `.glb` 均保留分件及接口。功能运动由网页读取元数据运行，没有通用 GLB 烘焙动作；没有工作人员、马匹自动入住、交易/锻造产出、火灾或经济系统。

结构参考：[National Trust 马厩隔栏、草架与通道记录](https://heritagerecords.nationaltrust.org.uk/HBSMR/MonRecord.aspx?uid=MNA125153)、[Weald & Downland 铁匠铺维护记录](https://www.wealddown.co.uk/wp-content/uploads/2020/12/2019-WDLM-Magazine-%E2%80%93-SpringSummer.pdf)、[博物馆公共建筑与集市介绍](https://www.wealddown.co.uk/discover/buildings/public-buildings/)。只参考用途和构件关系，游戏样板并非这些建筑的复刻，没有下载第三方网格。

```powershell
blender --background --factory-startup --python-exit-code 1 --python scripts/blender/map_element_kit.py -- --assets stable blacksmith market-hall
node scripts/verify-map-buildings.mjs stable blacksmith market-hall
```

预览：`/?view=map-elements&element=stable`、`/?view=map-elements&element=blacksmith`、`/?view=map-elements&element=market-hall`。指定模型的专项结果保存为 `artifacts/map-elements/buildings/verification-selected.json`，不覆盖此前完整建筑专项结果。

### 蒸汽机车与船舶

此批完成时累计 70 类独立模型、79 个版本，108 类规划剩余 38 类。新增 `steam-locomotive`、`sailboat`、`river-barge`，均保留分件 Blender 源文件。不同装载和帆角状态不重复计数。

- 蒸汽机车为三轴动轮的游戏缩尺罐式机车，区分锅炉、烟箱、水箱、驾驶室、煤斗、汽缸、十字头、活塞杆和联动杆。两侧曲柄相差四分之一转，连杆端点根据实际曲柄销求解，不是互不关联的摆动。蒸汽粒子随运行上升、扩散和淡出。
- 轮面中心距 0.72 m，牵引接点高 0.42 m，与既有铁路货车厢一致。轮面 Y=0，装入直线铁路需整体抬至轨顶 0.28 m；六只轮子的真实轮面和钢轨做射线接触检查。完整一转逐帧检查杆长与实际几何端点。
- 帆船包含有厚度的船壳、开放驾驶舱、舱口、座板、甲板接缝、桅杆/支索、主帆/前帆、帆桁、鳍式龙骨和尾舵。帆网格以三角重心权重鼓起，三条边保持固定；主帆随帆桁转动，桅侧边仍位于桅杆轴。
- 河运货船为宽底货舱轮廓，包含六件独立货箱、侧通道、护舷绳、透明驾驶室、舵轮/控制台、舱门、排气管、三叶螺旋桨、尾舵上支架与底部支架。底支架位于螺旋桨扫掠范围下方，舵轮与尾舵联动。
- 船舶 `waterline=0`、`routeProfile=water-channel-v1`，四个系泊接点保留法向。网页分别控制风力、帆角、波浪、舵角、推进速度和装载，船体有小幅升沉/纵摇/横摇，不缩放船体。负推进速度倒转螺旋桨；零动力且零波浪时静止。
- 三款分别 13,032 / 2,888 / 5,417 三角面，802,484 / 191,428 / 410,228 字节，未提高基础预算。机构由网页驱动，没有烘焙蒸汽/船舶剪辑。
- 当前没有水面流体、浮力求解、推进力学、帆船自动航向、地图航线、列车移动/连挂、交通调度或 LOD。系泊/轨道接口只是后续装配基础，不代表 200 格地图已通过性能验收。

结构参考：[Science Museum 罐式机车藏品](https://collection.sciencemuseumgroup.org.uk/objects/co205737/london-brighton-and-south-coast-railway-locomotive-boxhill)、[Science Museum 蒸汽机构组件](https://collection.sciencemuseumgroup.org.uk/objects/co51790)、[Royal Museums Greenwich 平头货驳模型](https://www.rmg.co.uk/collections/objects/rmgc-object-67520)。这些仅供一般轮廓和构件关系参考，本批并非历史实船/实车复刻；没有下载第三方网格或伪造三视参考。

```powershell
blender --background --factory-startup --python-exit-code 1 --python scripts/blender/map_element_kit.py -- --assets steam-locomotive sailboat river-barge
node scripts/verify-map-marine-steam.mjs
```

预览：`/?view=map-elements&element=steam-locomotive`、`/?view=map-elements&element=sailboat`、`/?view=map-elements&element=river-barge`。

### 骑手与双轮马车

此批完成时累计 67 类独立模型、76 个版本，108 类规划剩余 41 类。新增 `rider` 和 `horse-cart`；骑姿、车架及马具为新建几何，共用已有马匹躯干/头部/腿部模型，不另计重复的马或货物。

- 骑手有马鞍、贴合实际躯干表面的鞍垫、肚带、独立马镫踏面、骑靴和握缰姿态；骨盆与鞍位同步，靴底与踏面做实际射线核对。人物采用分件坐姿与上身平衡，不是复用站姿强行穿过马背。
- 马车为双轮木制货车，有车轴/板簧、前座/脚踏、车辕、胸带、后鞧、辕环、导缰环、牵引横木和四件货箱。轮圈是连续网格，车轮独立滚动。
- `MountedAssembly` 保存 `mountKind`、`routeProfile=road-145-v1`、`strideMeters`、`cargoSlots`。`mountedHorse` 仅有一匹成年马，复用 `mapElementAnimals.ts` 的腿部 IK，不开启家庭或成长模式。原独立马的成长繁育不受影响。
- `mapElementMounted.ts` 将前后左右蹄分成四拍相位；支撑相后移速度与 `distance / wheelRadius` 滚轮对应。速度范围 0–1.4 m/s，为原地预览等效速度。骑手/马鞍、车座/车夫保持连接，轻微平衡动作不改变骨盆坐点。
- `mountAnchor` 标记口衔、手、导环和牵引点；`mountCable` 管状几何每次随这些端点重新计算。导出可能因硬边重排/拆分顶点，驱动按初始位置绑定各圈，不能假定 GLB 顶点顺序等于 Blender 顺序。暂停及零速不重复重建缰绳。
- 8,054 / 14,938 三角面，约 0.70 / 1.16 MB，专项绘制调用 51 / 75。总宽符合既有公路宽度限制，不代表转弯扫掠、坡道、多人 LOD 或 200 格性能合格。
- 不含上下马、人物成长、疾驰、马车转向/碰撞/力学、货物库存、城镇运输或地图寻路。不是工程马具或骑术教学模型；通用 GLB 查看器需接入网页驱动才能运动，没有烘焙骑乘剪辑。

结构参考：[Science Museum 双轮马车藏品](https://collection.sciencemuseumgroup.org.uk/objects/co25949)、[British Horse Society 骑手姿态与马镫/缰绳基础](https://www.bhs.org.uk/media/5rijjjt5/introduction-about-the-rider-checklist-guidance.pdf)。只是结构参考，非实物复刻；没有下载第三方网格。

```powershell
blender --background --factory-startup --python-exit-code 1 --python scripts/blender/map_element_kit.py -- --assets rider horse-cart
node scripts/verify-map-mounted.mjs
```

预览：`/?view=map-elements&element=rider` 或 `/?view=map-elements&element=horse-cart`。

### 运输车辆与机构

此批完成时为 65 类独立模型、74 个版本。新增人力车 `rickshaw`、自行车 `bicycle`、早期汽车 `early-car`、铁路货车厢 `freight-wagon`，均有可编辑 `.blend` 与分件 `.glb`。

- 人力车有辐条轮、车辕、踏板、座垫/扶手和五根同轴篷架。布面顶点沿铰链扇形折叠，并保留小褶皱；不是整个车篷统一缩放。折叠时更新法线、包围球与包围盒。
- 自行车有前后三角车架、前叉、座管、车把、曲柄/脚踏、前链盘、后链轮及 56 个运动链节。轮转角为滚动距离/轮半径；曲柄按 2.5:1 比例联动，脚踏反向补偿保持水平，链节按弧长沿闭环运动。
- 早期汽车有散热器格栅、头灯、弧形挡泥板、透明风挡、双排座位和薄弧形布顶。前轮内外转角按轴距/轮距分别计算，方向盘随之转动；车门绕独立铰链打开，后部行李可移除。
- 货车厢有两根车轴、带内侧轮缘的车轮、轴箱/板簧、木板地板、三层侧板、缓冲器/牵引接点和六件独立货箱。侧板打开和货箱逐件装卸由独立节点控制。
- `TransportRoot` 保存 `routeProfile`、`wheelbase`、`track`、`cargoSlots`。货车轮面中心距 0.72 m，与已有轨道一致；轮面接触平面为 Y=0，轮缘下伸 0.017 m，放入直线轨道需整体抬至轨顶 0.28 m。实际轮面和钢轨通过射线接触测试，不只比较元数据。
- 车辆使用游戏缩尺，不是上述历史实车复刻；路面总宽校验不等于双向车道或驾驶员尺寸适配。自行车头管采用简化竖直转向轴，没有后倾/拖曳距模型。钢轮、链节与转向均为机构展示，不是动力学求解。
- 网页轮速表示等效滚动线速度，车体保持原地；支持倒转和暂停。开合只在轮速为零时允许；再次加速会先闭合机构，闭合前轮轴保持停止。装载为有限件数显隐，不包含搬运/货物库存系统。
- 动态由 `mapElementTransport.ts` 读取节点元数据运行，GLB 没有烘焙剪辑，通用查看器不会自行播放。尚无驾乘者、马匹牵引、地图路径跟随、车轮碰撞、悬挂压缩、制动、车厢连挂或车辆 LOD。
- 四款分别为 2,892 / 3,820 / 5,604 / 6,812 三角面，约 0.19 / 0.29 / 0.36 / 0.45 MB；最终专项绘制调用为 22 / 69 / 30 / 30。

结构参考：[Science Museum 安全自行车](https://collection.sciencemuseumgroup.org.uk/objects/co25833/rover-safety-bicycle-1885)、[The Henry Ford 1913 旅行汽车](https://www.thehenryford.org/collections/explore/artifact/231335)、[Science Museum 敞式货车](https://collection.sciencemuseumgroup.org.uk/objects/co205953/12-ton-3-plank-open-wagon)。所有几何由本地脚本制作，没有下载第三方网格，也没有把网页图片冒充三视设计图。

```powershell
blender --background --factory-startup --python-exit-code 1 --python scripts/blender/map_element_kit.py -- --assets rickshaw bicycle early-car freight-wagon
node scripts/verify-map-transport.mjs
```

预览：`/?view=map-elements&element=early-car`，另三款可从模型列表切换。

### 道路、轨道与邻接预览

此批完成时为 61 类独立模型、70 个版本。新增土路 `dirt-road`、石板路 `stone-road`、柏油路 `asphalt-road`、铁路 `rail-track`；每款包含直线、弯道及岔口，形态不重复计数。

- 土路有实际车辙起伏、贴合地表的磨损带与散石；石路有错缝铺石、缝隙和收边石；柏油路区分路基、面层、标线与反光柱。三岔路面做网格布尔合并，不叠放共面路面。
- 铁路有道砟、枕木、扣件、轨底/轨腰/轨头，岔口包含可移动尖轨和方向标。结构参考 [Network Rail 铁路构成](https://www.networkrail.co.uk/our-work/living-by-the-railway/)，所有网格由本地脚本制作，没有下载第三方模型。
- 共用半径 1.75 m 六边形底块，地表标高 0.08 m。道路宽 1.45 m、端部面高 0.145 m；轨道中心距 0.72 m、轨头内侧净距 0.668 m、轨顶高 0.28 m。这是游戏缩尺接口，不是标准轨距或真实公路车道尺寸。
- `RoutePort` 的 `normalGltf` / `neighborOffsetGltf` 使用 Y-up 坐标，`road-145-v1` 与 `narrow-rail-0668-v1` 不互通。`RouteShape.ports` 记录实际开口；网页提供同类邻接预览，接点和路面端部顶点分别测试。
- 施工按路基、铺装、收边或轨件逐件出现并小幅落位，支持进度回退、自动铺设与暂停。草簇独立风动；道岔移动期间没有开放的出口。驱动为 `mapElementRoutes.ts`，不是整体缩放或烘焙动画剪辑。
- `.blend` 保留独立零件，`.glb` 保留三套形态及动作元数据。通用查看器会同时显示三种形态，必须按 `routeShape` 选择一套；网页的 GLB 下载不是单独形态导出。
- 邻接预览共享原模型几何和材质，仍增加绘制次数；尚无地图路网、交通寻路、车辆尺度适配、桥坡衔接、跨材质融合及 LOD。道岔为压缩造型，尚未完成真实辙叉、轮缘槽和联锁，不作为工程轨道模型。

```powershell
blender --background --factory-startup --python-exit-code 1 --python scripts/blender/map_element_kit.py -- --assets dirt-road stone-road asphalt-road rail-track
node scripts/verify-map-routes.mjs
```

预览：`/?view=map-elements&element=rail-track`，可切换道路形态、邻接预览、施工进度及道岔方向。

### 人物骨架与职业动作

此批完成时为 57 类独立模型、66 个版本。新增农夫 `farmer`、渔夫 `fisher`、伐木工 `woodcutter`、商人 `merchant`，保留可编辑骨架、IK 控制与独立零件的 `.blend`，导出蒙皮 `.glb`。

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

## 第二十批桥梁

- `stone-bridge`：双拱、48 块拱石、水平砌石层、分块坡面铺装、分水墩、护墙和升级灯具。旗帜可风动，桥体不会做无意义摇晃。
- `steel-bridge`：双叶 70 度开启桥、侧桁架、铆钉、横梁、转轴和下沉配重；路障先落下才抬桥，闭合后再放行道路。施工和开桥均可暂停、回退。
- 两端道路宽 1.45 m、端面高 0.145 m，`road-145-v1` 对应已有三种道路；河床基准 -1.8 m。桥墩按跨河结构建模，没有把实体底座填满桥洞。水面需要地图另行装配，不把风动旗帜计为水流模拟。
- Blender 保留独立零件及施工/连接元数据；网页执行功能动画，通用 GLB 查看器不自动执行路障时序。当前是游戏尺度的风格化结构，不是工程设计。
- 结构参考：[Tower Bridge 开启桥机构](https://www.towerbridge.org.uk/stories/how-does-tower-bridge-work)、[配重室](https://www.towerbridge.org.uk/stories/the-bascule-chambers)、[NPS 桥梁结构说明](https://www.nps.gov/blri/learn/historyculture/bridges.htm)。仅参考承重和运动关系，未使用第三方模型或贴图，不是地标复刻。
- 页面：`/?view=map-elements&element=stone-bridge`、`/?view=map-elements&element=steel-bridge`。

## 第二十一批水利设施

- `aqueduct`：三拱承重、逐层桥墩、连续渠槽、同断面进出水口，可升级检修步道和护栏。
- `irrigation-channel`：渠床、分段渠壁、草土岸边、U 形导轨、升降闸板、丝杆与固定高度手轮。闸板升程 0.36 m，对应手轮三圈和 0.12 m 螺距；支持施工、开闸、中途暂停、升级养护附件。
- 新水面由连续细分网格组成，波峰沿渠道移动、靠边界衰减，底面保持在渠床。下游随开度延迟蓄水和退水；关闭仍可保留少量静水，不以循环移动的白色长条代替整个水面。
- 使用 `open-channel-064-v1`，净宽 0.64 m、正常水深 0.18 m。端口位置取渠床，高架渠为 2.08 m、灌渠为 0.12 m；仅断面相同，**不同地面高程不能直接平放相接**。地图仍需台地放置或另做跌水连接。
- 这是风格化预览动画，不是流体求解器、真实供水网络或农田产量模拟。水面几何与控制状态由网页驱动，GLB 自身不包含通用查看器可播放的水利逻辑。
- 参考：[NPS Washington Aqueduct](https://www.nps.gov/places/washington-aqueduct.htm)、[FAO Irrigation System](https://www.fao.org/4/r4082e/r4082e06.htm)。仅参考结构用途与水量控制关系，没有第三方模型或贴图，也不复刻可行船的大型运河渡槽。
- 页面：`/?view=map-elements&element=aqueduct`、`/?view=map-elements&element=irrigation-channel`。

## 第二十二批聚落建筑

- `inn`：二层廊式旅店，分层墙体、真实门窗洞口、外楼梯及平台、三个独立客房、床铺与餐桌、悬挂杯形招牌；升级为外廊花箱。客房门向内打开，避免占用外廊栏杆空间；招牌单独摆动。
- `chapel`：长厅、侧扶壁、分格彩窗、中间过道、长椅、祭台、独立钟架与空心铜钟；升级庭院花坛。钟体绕轴摆动，钟舌在钟内单独转动。摆钟为预览运动，不模拟敲击碰撞或音频。
- 两款均支持分件施工、屋顶剖面、升级附件、运行/停止、暂停与零速，根模型不整体缩放。保留可编辑 Blender 源文件；功能动作由网页元数据驱动，未烘焙为通用 GLB 动画剪辑。
- 门洞按现有人物尺度制作，为 1.20 m 宽、2.20 m 高；旅店二层楼面 2.55 m、外廊深 1.30 m、踏步宽 1.24 m、床垫长 1.90 m。测试四种人物各 24 帧行走姿态的网格包围范围与门洞、开门状态及外廊净空，不缩小人物；这不是完整导航或上下楼动画。
- 结构参考：[National Trust 廊式旅店](https://www.nationaltrust.org.uk/visit/london/george-inn)、[National Bell Festival 钟体构件](https://www.bells.org/activity/learn-about-different-parts-bell)。仅参考空间用途与构件关系，没有第三方网格、贴图或地标复刻。
- 页面：`/?view=map-elements&element=inn`、`/?view=map-elements&element=chapel`。尚未接入地图居民住宿、宗教、访问调度或完整跨时代建筑升级。

## 后续工作

- 与设计稿继续比对轮廓和细节，尤其是植被叶簇、屋瓦、水井附件和动物面部。
- 补齐人物与剩余元素，人物单独制作骨架、步态和运输动作。
- 制作 LOD、实例化方案、地形放置锚点及季节变体，再接入大地图。
- 当前没有 UV 烘焙、完整骨骼或地图寻路；不要将基础模型或待制作清单视为目标已经完成。
