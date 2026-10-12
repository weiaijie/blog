// Asset families, not revisions, recolors or life stages. Availability comes from GLB manifests.
const groups: { category: string; items: [string, string][] }[] = [
  { category: '地貌', items: [
    ['grassland', '草原'], ['rolling-hills', '缓丘'], ['rocky-mountain', '岩山'], ['snow-peak', '雪峰'],
    ['volcano', '火山'], ['lava-field', '熔岩地'], ['sand-dunes', '沙丘'], ['desert-oasis', '绿洲'],
    ['wetland', '湿地'], ['river-bend', '河湾'], ['waterfall', '瀑布'], ['lake-shore', '湖岸'],
    ['sea-cliff', '海崖'], ['glacier', '冰川'],
  ] },
  { category: '植被', items: [
    ['pine-tree', '针叶树'], ['berry-shrub', '浆果灌木'], ['reeds', '水岸芦苇'], ['apple-tree', '苹果树'],
    ['oak-tree', '橡树'], ['birch-tree', '桦树'], ['willow-tree', '柳树'], ['palm-tree', '棕榈树'],
    ['bamboo', '竹丛'], ['cactus', '仙人掌'], ['fern', '蕨丛'], ['wildflowers', '野花丛'],
    ['mushrooms', '菌菇群'], ['lily-pad', '睡莲'],
  ] },
  { category: '农田', items: [
    ['wheat-field', '麦田'], ['plowed-field', '翻耕田地'], ['vegetable-field', '蔬菜田'],
    ['pumpkin-patch', '南瓜地'], ['sunflower-field', '向日葵'], ['rice-paddy', '水稻田'],
    ['corn-field', '玉米地'], ['vineyard', '葡萄架'], ['cotton-field', '棉花田'], ['potato-field', '土豆田'],
  ] },
  { category: '动物', items: [
    ['sheep', '绵羊'], ['river-fish', '河鱼'], ['cow', '奶牛'], ['horse', '马'], ['goat', '山羊'],
    ['pig', '猪'], ['chicken', '鸡'], ['duck', '鸭'], ['deer', '鹿'], ['rabbit', '兔'],
    ['fox', '狐狸'], ['wolf', '狼'], ['butterfly', '蝴蝶'], ['bee', '蜜蜂'],
  ] },
  { category: '人物', items: [
    ['farmer', '农夫'], ['fisher', '渔夫'], ['woodcutter', '伐木工'], ['merchant', '商人'],
    ['builder', '建筑工'], ['rider', '骑手'], ['town-resident', '城镇居民'], ['engineer', '工程师'],
  ] },
  { category: '建筑', items: [
    ['cottage', '乡村小屋'], ['barn', '谷仓'], ['stable', '马厩'], ['windmill', '风车磨坊'],
    ['watermill', '水磨坊'], ['market-hall', '集市'], ['blacksmith', '铁匠铺'], ['inn', '旅店'],
    ['town-hall', '市政厅'], ['chapel', '教堂'], ['watchtower', '瞭望塔'], ['castle-keep', '城堡主楼'],
    ['castle-gate', '城门'], ['castle-wall', '城墙'], ['palace', '宫殿'], ['amphitheater', '圆形剧场'],
    ['aqueduct', '高架引水渠'], ['harbor', '港口'], ['train-station', '火车站'], ['factory', '工厂'],
    ['power-station', '发电站'], ['apartment', '公寓楼'], ['hospital', '医院'], ['skyscraper', '高层办公楼'],
  ] },
  { category: '运输', items: [
    ['handcart', '双轮手推车'], ['fishing-boat', '近岸渔船'], ['horse-cart', '马车'], ['rickshaw', '人力车'],
    ['sailboat', '帆船'], ['river-barge', '河运货船'], ['bicycle', '自行车'], ['steam-locomotive', '蒸汽机车'],
    ['freight-wagon', '铁路货车厢'], ['early-car', '早期汽车'], ['truck', '货运卡车'], ['electric-train', '电力列车'],
  ] },
  { category: '设施', items: [
    ['timber-bridge', '木制车行桥'], ['village-well', '水井'], ['stone-bridge', '石桥'], ['steel-bridge', '钢桥'],
    ['dirt-road', '土路'], ['stone-road', '石板路'], ['asphalt-road', '柏油路'], ['rail-track', '铁路轨道'],
    ['irrigation-channel', '灌渠'], ['fence', '栅栏'], ['street-lamp', '路灯'], ['dock', '码头栈桥'],
  ] },
]

export const mapElementRoadmap = groups.flatMap(({ category, items }) => items.map(([id, label]) => ({ id, label, category })))
export const mapElementCategories = groups.map((group) => group.category)
export const botanicalFamilies = new Set(['berry-shrub', 'apple-tree', 'pumpkin-patch', 'sunflower-field'])
