# 地图元素三维模型：第一批

状态：可编辑建模初版，采用 C 风格的非写实、切面低多边形造型。根据三视图重新构造几何，并非图片贴片或自动重建，也不表示已经逐项还原设计稿。

## 预览

在 `civlike-web` 启动 `npm run dev` 后打开 `/?view=map-elements&element=fishing-boat`。

独立页面提供自由旋转、正面、侧面、俯视、线框、动画暂停和 GLB 下载，同时展示对应三视图。此批次没有替换现有 `terrain-world` 地图元素。

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

浏览器检查覆盖 12 款加载、画面非空和完整取景、5 款动画与暂停、三视图、线框、移动端切换及横向溢出。截图和 JSON 结果位于 `artifacts/map-elements/`。这些检查不等于艺术质量验收，也不等于 200 格场景的性能验收。

## 后续工作

- 与设计稿继续比对轮廓和细节，尤其是植被叶簇、屋瓦、水井附件和动物面部。
- 补齐人物与剩余元素，人物单独制作骨架、步态和运输动作。
- 制作 LOD、实例化方案、地形放置锚点及季节变体，再接入大地图。
- 当前没有 UV 烘焙、完整骨骼或地图寻路；不要将这 12 款初版视为全部参考资产已经完成。
