import { spawn, spawnSync } from 'node:child_process'
import { chromium } from 'playwright'

const port = 5186
const url = `http://127.0.0.1:${port}/?seed=1001`

const server = spawn(
  process.platform === 'win32' ? 'npm.cmd' : 'npm',
  ['run', 'preview', '--', '--host', '127.0.0.1', '--port', String(port)],
  {
    cwd: process.cwd(),
    stdio: 'ignore',
  },
)

try {
  await waitForHttp(url, 20_000)

  const browser = await chromium.launch()
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } })

  try {
    await page.goto(url, { waitUntil: 'load' })
    await page.waitForFunction(() => document.documentElement.dataset.civPerf === 'ready')
    await expectObjective(page, '移动侦察兵')
    await expectObjectiveList(page, ['移动侦察兵', '选择采矿', '生产侦察兵', '结束回合', '保存进度'])
    await expectExplorationHint(page, '地图已高亮侦察兵和推荐目标：先点 tile:8:9，再点 tile:8:10。')
    await expectIntelHelp(page)
    await expectMapAndPanelVisible(page)
    await expectValue(page, '可见地块', '7')
    await expectValue(page, '已探索地块', '7')
    await expectValue(page, '探索进度', '7 / 20')
    await expectValue(page, '新发现', '等待侦察兵移动')
    await expectValue(page, '地图迷雾', '可见 7，已探索 7')
    await expectValue(page, '每回合收益', '食物 2，生产 2，科研 1')
    await expectValue(page, '生产队列', '0 / 1 城市')
    await expectValue(page, 'Map seed', '1001')
    await expectValue(page, '主线推进', '先移动侦察兵，打开第一圈地图。')
    await expectValueContains(page, '探索指引', '可继续开雾：选 unit:scout:1')
    await expectValueContains(page, '阶段摘要', '1 个单位，1 座城市')
    await expectValueContains(page, '阶段摘要', '还没有城市在生产')
    await expectButton(page, '新地图')
    await expectButton(page, '选择可探索侦察兵')
    await expectEvent(page, '等待事件')

    await page.mouse.click(394, 353)
    await page.waitForFunction(() => window.__civPerf?.getStats()?.selectedTileId === 'tile:8:8')
    await expectValue(page, '地块详情', '8, 8 / 森林')
    await expectValue(page, '地块探索状态', '可见')
    await expectValue(page, '地块城市', 'city:capital')

    await page.mouse.click(244, 244)
    await page.waitForFunction(() => {
      const selectedTileId = window.__civPerf?.getStats()?.selectedTileId

      return selectedTileId && selectedTileId !== 'tile:8:8'
    })
    await expectValue(page, '地块详情', '未知地块')
    await expectValue(page, '地块探索状态', '未知')
    await expectValue(page, '地块产出', '未知')
    await expectValue(page, '地块单位', '未知')
    await expectValue(page, '地块城市', '未知')

    await page.getByRole('button', { name: '选择可探索侦察兵' }).click()
    await page.waitForFunction(() => window.__civPerf?.getStats()?.selectedTileId === 'tile:8:9')
    await expectValue(page, '已选单位', 'unit:scout:1 @ tile:8:9')
    await expectValueContains(page, '新发现', '下一步点击地图高亮目标')
    await expectEventContains(page, '已选中可探索侦察兵：unit:scout:1')

    await page.mouse.click(415, 389)
    await page.waitForFunction(() => window.__civPerf?.getStats()?.selectedTileId === 'tile:8:9')
    await expectValue(page, '已选单位', 'unit:scout:1 @ tile:8:9')

    await page.mouse.click(394, 425)
    await page.waitForFunction(() => window.__civPerf?.getStats()?.selectedTileId === 'tile:8:10')
    await expectObjective(page, '选择采矿')
    await expectExplorationHint(page, '侦察兵已探索 10 个地块。点击主按钮“选择采矿”。')
    await expectValue(page, '已选单位', 'unit:scout:1 @ tile:8:10')
    await expectValue(page, '地块单位', 'unit:scout:1')
    await expectValue(page, '可见地块', '7')
    await expectValue(page, '已探索地块', '10')
    await expectValue(page, '探索进度', '10 / 20')
    await expectValue(page, '新发现', '本次新发现 3 个地块，累计 10 / 20')
    await expectValue(page, '地块探索状态', '可见')
    await expectValue(page, '地图迷雾', '可见 7，已探索 10')
    await expectValue(page, '主线推进', '下一步选择采矿，让科研开始推进。')
    await expectValueContains(page, '探索指引', '可继续开雾：选 unit:scout:1')
    await expectValue(page, '上条命令', 'cmd:1:0:MOVE_UNIT / MOVE_UNIT')
    await expectEvent(page, '新发现：3 个地块，累计 10 / 20')

    await page.mouse.click(394, 353)
    await page.waitForFunction(() => window.__civPerf?.getStats()?.selectedTileId === 'tile:8:8')
    await expectValue(page, '地块详情', '8, 8 / 森林')
    await expectValue(page, '地块探索状态', '已探索')
    await expectValue(page, '地块产出', '食物 1，生产 1，科研 0')
    await expectValue(page, '地块单位', '不可见')
    await expectValue(page, '地块城市', 'city:capital')

    await page.getByRole('button', { name: '保存游戏' }).click()
    await expectValue(page, '存档状态', '已保存回合 1 / 命令 1')
    await expectValue(page, '内存存档', '已保存回合 1 / 命令 1')
    await expectEvent(page, '保存：回合 1 / 命令 1')

    await page.getByRole('button', { name: '选择采矿' }).click()
    await expectObjective(page, '生产侦察兵')
    await expectExplorationHint(page, '点击主按钮“生产侦察兵”，让首都开始生产。')
    await expectValue(page, '当前科技', 'tech:mining')
    await expectValue(page, '科技进度', '0 / 3')

    await page.getByRole('button', { exact: true, name: '生产侦察兵' }).click()
    await expectObjective(page, '结束回合')
    await expectExplorationHint(page, '点击主按钮“结束回合”，推进生产和科研。')
    await expectValue(page, '首都生产', 'unit:scout')
    await expectValue(page, '首都进度', '0')
    await expectValue(page, '首都产出', '食物 2，生产 2，科研 1')

    await page.getByRole('button', { name: '结束回合' }).click()
    await expectObjective(page, '继续回合')
    await expectExplorationHint(page, '进度已保存。点击主按钮“结束回合”继续推进。')
    await expectValue(page, '回合', '2')
    await expectValue(page, '食物库存', '2')
    await expectValue(page, '科研进度', '1')
    await expectValue(page, '科技进度', '1 / 3')
    await expectValue(page, '首都进度', '2')
    await expectValue(page, '上条命令', 'cmd:1:3:END_TURN / END_TURN')
    await expectValue(page, '当前进度', '回合 2 / 命令 4')

    await page.getByRole('button', { name: '读取游戏' }).click()
    await expectValue(page, '回合', '1')
    await expectValue(page, '食物库存', '0')
    await expectValue(page, '科研进度', '0')
    await expectValue(page, '命令日志', '1')
    await expectValue(page, '当前科技', '无')
    await expectValue(page, '科技进度', '无')
    await expectValue(page, '已完成科技', '无')
    await expectValue(page, '首都生产', '无')
    await expectValue(page, '首都进度', '0')
    await expectValue(page, '存档状态', '已读取回合 1 / 命令 1')
    await expectValue(page, '内存存档', '已读取回合 1 / 命令 1')
    await expectValue(page, '当前进度', '回合 1 / 命令 1')
    await expectValue(page, '上条命令', 'cmd:1:0:MOVE_UNIT / MOVE_UNIT')
    await expectEvent(page, '读取存档：回合 1 / 命令 1')

    await page.getByRole('button', { exact: true, name: '生产侦察兵' }).click()
    await expectValue(page, '首都生产', 'unit:scout')
    await expectValue(page, '生产队列', '1 / 1 城市')
    await page.getByRole('button', { name: '选择采矿' }).click()
    await page.getByRole('button', { name: '结束回合' }).click()
    await expectValue(page, '首都进度', '2')
    await expectValue(page, '食物库存', '2')
    await expectValue(page, '科技进度', '1 / 3')
    await expectValue(page, '单位数量', '1')
    await page.getByRole('button', { name: '结束回合' }).click()
    await expectValue(page, '回合', '3')
    await expectValue(page, '首都进度', '0')
    await expectValue(page, '食物库存', '4')
    await expectValue(page, '科技进度', '2 / 3')
    await expectValue(page, '单位数量', '2')
    await expectValueContains(page, '阶段摘要', '2 个单位，1 座城市')
    await expectValueContains(page, '阶段摘要', '1 / 1 城市正在生产')
    await expectExplorationHint(page, '新单位已生产完成。继续结束回合，观察生产和资源增长。')
    await expectEvent(page, '生产完成：unit:scout:2')
    await page.getByRole('button', { name: '结束回合' }).click()
    await expectValue(page, '当前科技', '无')
    await expectValue(page, '科技进度', '无')
    await expectValue(page, '已完成科技', 'tech:mining')
    await expectExplorationHint(page, '科技和生产都已见效。继续结束回合，观察资源、科研和新单位增长。')
    await expectEvent(page, '科技完成：tech:mining')

    const persistedHash = await readValue(page, '状态哈希')
    await page.getByRole('button', { name: '持久保存' }).click()
    await expectValueStartsWith(page, '持久存档', '已保存回合 4 / 命令 6 / ')
    await expectEvent(page, '持久保存：回合 4 / 命令 6')

    await page.reload({ waitUntil: 'load' })
    await page.waitForFunction(() => document.documentElement.dataset.civPerf === 'ready')
    await expectValue(page, '回合', '1')
    await expectValueContains(page, '持久存档', '字节')

    await page.getByRole('button', { name: '持久读取' }).click()
    await expectValue(page, '回合', '4')
    await expectValue(page, '命令日志', '6')
    await expectValue(page, '单位数量', '2')
    await expectValue(page, '食物库存', '6')
    await expectValue(page, '科研进度', '0')
    await expectValue(page, '可见地块', '12')
    await expectValue(page, '已探索地块', '13')
    await expectValue(page, '探索进度', '13 / 20')
    await expectValue(page, '新发现', '累计探索 13 / 20')
    await expectValue(page, '地图迷雾', '可见 12，已探索 13')
    await expectValue(page, '已完成科技', 'tech:mining')
    await expectValue(page, '首都进度', '2')
    await expectValue(page, '持久存档', '已读取回合 4 / 命令 6')
    await expectValue(page, '当前进度', '回合 4 / 命令 6')
    await expectValue(page, '状态哈希', persistedHash)
    await expectEvent(page, '持久读取：回合 4 / 命令 6')

    await page.mouse.click(394, 425)
    await page.mouse.click(244, 244)
    await expectValue(page, '命令错误', 'MOVE_UNIT：目标地块必须与已选单位相邻。')
    await expectValue(page, '命令日志', '6')

    await page.reload({ waitUntil: 'load' })
    await page.waitForFunction(() => document.documentElement.dataset.civPerf === 'ready')
    await expectValue(page, '回合', '1')
    await expectValue(page, '命令日志', '0')
    await expectValue(page, '单位数量', '1')
    await expectValue(page, '城市数量', '1')
    await expectValue(page, '场景', 'default')
    await expectNoButton(page, '攻击')

    await page.getByRole('button', { exact: true, name: '生产战士' }).click()
    await expectValue(page, '首都生产', 'unit:warrior')
    await expectValue(page, '上条命令', 'cmd:1:0:SET_PRODUCTION / SET_PRODUCTION')

    for (let index = 0; index < 3; index += 1) {
      await page.getByRole('button', { name: '结束回合' }).click()
    }

    await expectValue(page, '回合', '4')
    await expectValue(page, '首都进度', '0')
    await expectValue(page, '单位数量', '2')
    await expectEvent(page, '生产完成：unit:warrior:2')

    await page.mouse.click(394, 353)
    await page.waitForFunction(() => window.__civPerf?.getStats()?.selectedTileId === 'tile:8:8')
    await expectValue(page, '已选单位', 'unit:warrior:2 @ tile:8:8')
    await page.mouse.click(415, 317)
    await page.waitForFunction(() => window.__civPerf?.getStats()?.selectedTileId === 'tile:8:7')
    await expectValue(page, '已选单位', 'unit:warrior:2 @ tile:8:7')
    await expectValue(page, '上条命令', 'cmd:4:4:MOVE_UNIT / MOVE_UNIT')

    const warriorHash = await readValue(page, '状态哈希')
    await page.getByRole('button', { name: '保存游戏' }).click()
    await expectValue(page, '存档状态', '已保存回合 4 / 命令 5')

    await page.getByRole('button', { name: '结束回合' }).click()
    await expectValue(page, '回合', '5')
    await expectValue(page, '命令日志', '6')
    await page.getByRole('button', { name: '读取游戏' }).click()
    await expectValue(page, '回合', '4')
    await expectValue(page, '命令日志', '5')
    await expectValue(page, '状态哈希', warriorHash)
    await page.mouse.click(415, 317)
    await page.waitForFunction(() => window.__civPerf?.getStats()?.selectedTileId === 'tile:8:7')
    await expectValue(page, '地块单位', 'unit:warrior:2')

    await page.reload({ waitUntil: 'load' })
    await page.waitForFunction(() => document.documentElement.dataset.civPerf === 'ready')
    await expectValue(page, '回合', '1')
    await expectValue(page, '命令日志', '0')
    await expectValue(page, '单位数量', '1')
    await expectValue(page, '城市数量', '1')

    await page.getByRole('button', { exact: true, name: '生产开拓者' }).click()
    await expectValue(page, '首都生产', 'unit:settler')
    await expectValue(page, '上条命令', 'cmd:1:0:SET_PRODUCTION / SET_PRODUCTION')

    for (let index = 0; index < 4; index += 1) {
      await page.getByRole('button', { name: '结束回合' }).click()
    }

    await expectValue(page, '回合', '5')
    await expectValue(page, '首都进度', '0')
    await expectValue(page, '单位数量', '2')
    await expectEvent(page, '生产完成：unit:settler:2')

    await page.mouse.click(394, 353)
    await page.waitForFunction(() => window.__civPerf?.getStats()?.selectedTileId === 'tile:8:8')
    await expectValue(page, '已选单位', 'unit:settler:2 @ tile:8:8')

    await page.getByRole('button', { name: '建立城市' }).click()
    await expectValue(page, '命令错误', 'FOUND_CITY_BLOCKED_TILE: 该地块不能建立城市。')
    await expectValue(page, '命令日志', '5')

    await page.mouse.click(415, 317)
    await page.waitForFunction(() => window.__civPerf?.getStats()?.selectedTileId === 'tile:8:7')
    await expectValue(page, '已选单位', 'unit:settler:2 @ tile:8:7')
    await page.mouse.click(394, 281)
    await page.waitForFunction(() => window.__civPerf?.getStats()?.selectedTileId === 'tile:8:6')
    await expectValue(page, '已选单位', 'unit:settler:2 @ tile:8:6')
    await page.mouse.click(415, 245)
    await page.waitForFunction(() => window.__civPerf?.getStats()?.selectedTileId === 'tile:8:5')
    await expectValue(page, '已选单位', 'unit:settler:2 @ tile:8:5')

    await page.getByRole('button', { name: '建立城市' }).click()
    await expectValue(page, '命令错误', '无')
    await expectValue(page, '命令日志', '9')
    await expectValue(page, '单位数量', '1')
    await expectValue(page, '城市数量', '2')
    await expectValue(page, '已选单位', '无')
    await expectValue(page, '地块城市', 'city:player:human:2')
    await expectValue(page, '地块城市生产', '无')
    await expectValue(page, '地块城市进度', '0')
    await expectValue(page, '地块城市产出', '食物 3，生产 1，科研 1')
    await expectValue(page, '上条命令', 'cmd:5:8:FOUND_CITY / FOUND_CITY')
    await expectEvent(page, '建立城市：city:player:human:2')

    const foundedCityHash = await readValue(page, '状态哈希')
    await page.getByRole('button', { name: '保存游戏' }).click()
    await expectValue(page, '存档状态', '已保存回合 5 / 命令 9')
    await expectEvent(page, '保存：回合 5 / 命令 9')

    await page.getByRole('button', { name: '结束回合' }).click()
    await expectValue(page, '回合', '6')
    await expectValue(page, '命令日志', '10')
    await page.getByRole('button', { name: '读取游戏' }).click()
    await expectValue(page, '回合', '5')
    await expectValue(page, '命令日志', '9')
    await expectValue(page, '单位数量', '1')
    await expectValue(page, '城市数量', '2')
    await expectValue(page, '状态哈希', foundedCityHash)
    await expectValue(page, '地块城市', 'city:player:human:2')
    await expectValue(page, '地块城市生产', '无')
    await expectValue(page, '地块城市进度', '0')
    await expectValue(page, '地块城市产出', '食物 3，生产 1，科研 1')
    await expectEvent(page, '读取存档：回合 5 / 命令 9')

    await page.getByRole('button', { name: '持久保存' }).click()
    await expectValueStartsWith(page, '持久存档', '已保存回合 5 / 命令 9 / ')
    await expectEvent(page, '持久保存：回合 5 / 命令 9')
    await page.reload({ waitUntil: 'load' })
    await page.waitForFunction(() => document.documentElement.dataset.civPerf === 'ready')
    await expectValue(page, '回合', '1')
    await expectValue(page, '命令日志', '0')
    await expectValue(page, '城市数量', '1')
    await expectValueContains(page, '持久存档', '字节')

    await page.getByRole('button', { name: '持久读取' }).click()
    await expectValue(page, '回合', '5')
    await expectValue(page, '命令日志', '9')
    await expectValue(page, '单位数量', '1')
    await expectValue(page, '城市数量', '2')
    await expectValue(page, '状态哈希', foundedCityHash)
    await expectValue(page, '持久存档', '已读取回合 5 / 命令 9')
    await expectEvent(page, '持久读取：回合 5 / 命令 9')
    await page.mouse.click(415, 245)
    await page.waitForFunction(() => window.__civPerf?.getStats()?.selectedTileId === 'tile:8:5')
    await expectValue(page, '地块城市', 'city:player:human:2')
    await expectValue(page, '地块城市生产', '无')
    await expectValue(page, '地块城市进度', '0')
    await expectValue(page, '地块城市产出', '食物 3，生产 1，科研 1')

    await page.getByRole('button', { name: '选中城市生产侦察兵' }).click()
    await expectValue(page, '命令错误', '无')
    await expectValue(page, '命令日志', '10')
    await expectValue(page, '地块城市生产', 'unit:scout')
    await expectValue(page, '地块城市进度', '0')
    await expectValue(page, '上条命令', 'cmd:5:9:SET_PRODUCTION / SET_PRODUCTION')
    const selectedCityProductionHash = await readValue(page, '状态哈希')

    await page.getByRole('button', { name: '保存游戏' }).click()
    await expectValue(page, '存档状态', '已保存回合 5 / 命令 10')
    await expectEvent(page, '保存：回合 5 / 命令 10')

    await page.getByRole('button', { name: '选中城市生产开拓者' }).click()
    await expectValue(page, '命令日志', '11')
    await expectValue(page, '地块城市生产', 'unit:settler')

    await page.getByRole('button', { name: '读取游戏' }).click()
    await expectValue(page, '回合', '5')
    await expectValue(page, '命令日志', '10')
    await expectValue(page, '城市数量', '2')
    await expectValue(page, '状态哈希', selectedCityProductionHash)
    await expectValue(page, '地块城市生产', 'unit:scout')
    await expectValue(page, '地块城市进度', '0')
    await expectValue(page, '地块城市产出', '食物 3，生产 1，科研 1')
    await expectEvent(page, '读取存档：回合 5 / 命令 10')

    await page.getByRole('button', { name: '选中城市生产战士' }).click()
    await expectValue(page, '命令日志', '11')
    await expectValue(page, '地块城市生产', 'unit:warrior')
    await expectValue(page, '上条命令', 'cmd:5:10:SET_PRODUCTION / SET_PRODUCTION')

    await page.getByRole('button', { name: '读取游戏' }).click()
    await expectValue(page, '回合', '5')
    await expectValue(page, '命令日志', '10')
    await expectValue(page, '地块城市生产', 'unit:scout')
    await expectValue(page, '状态哈希', selectedCityProductionHash)

    await page.getByRole('button', { name: '结束回合' }).click()
    await expectValue(page, '回合', '6')
    await expectValue(page, '命令日志', '11')
    await expectValue(page, '食物库存', '13')
    await expectValue(page, '科研进度', '6')
    await expectValue(page, '地块城市生产', 'unit:scout')
    await expectValue(page, '地块城市进度', '1')
    await expectValue(page, '地块城市产出', '食物 3，生产 1，科研 1')
    await expectValue(page, '上条命令', 'cmd:5:10:END_TURN / END_TURN')

    console.log('Playable smoke passed')
  } finally {
    await browser.close()
  }
} finally {
  stopProcessTree(server)
}

async function expectValue(page, label, expected) {
  await page.waitForFunction(
    ({ label, expected }) => {
      const element = Array.from(document.querySelectorAll('dt')).find(
        (item) => item.textContent === label,
      )

      return element?.nextElementSibling?.textContent === expected
    },
    { label, expected },
  )
}

async function expectNoButton(page, name) {
  await page.waitForFunction((name) => {
    const buttons = Array.from(document.querySelectorAll('button')).filter(
      (button) => button.textContent?.trim() === name,
    )

    return buttons.length === 0
  }, name)
}

async function expectButton(page, name) {
  await page.waitForFunction((name) => {
    return Array.from(document.querySelectorAll('button')).some(
      (button) => button.textContent?.trim() === name,
    )
  }, name)
}

async function expectEvent(page, expected) {
  await page.waitForFunction((expected) => {
    const events = Array.from(document.querySelectorAll('[aria-label="最近事件"] li')).map(
      (item) => item.textContent,
    )

    return events.includes(expected)
  }, expected)
}

async function expectEventContains(page, expectedText) {
  await page.waitForFunction((expectedText) => {
    const events = Array.from(document.querySelectorAll('[aria-label="最近事件"] li')).map(
      (item) => item.textContent ?? '',
    )

    return events.some((event) => event.includes(expectedText))
  }, expectedText)
}

async function expectValueStartsWith(page, label, expectedPrefix) {
  await page.waitForFunction(
    ({ label, expectedPrefix }) => {
      const element = Array.from(document.querySelectorAll('dt')).find(
        (item) => item.textContent === label,
      )

      return element?.nextElementSibling?.textContent?.startsWith(expectedPrefix)
    },
    { label, expectedPrefix },
  )
}

async function expectValueContains(page, label, expectedText) {
  await page.waitForFunction(
    ({ label, expectedText }) => {
      const element = Array.from(document.querySelectorAll('dt')).find(
        (item) => item.textContent === label,
      )

      return element?.nextElementSibling?.textContent?.includes(expectedText)
    },
    { label, expectedText },
  )
}

async function readValue(page, label) {
  return page.evaluate((label) => {
    const element = Array.from(document.querySelectorAll('dt')).find(
      (item) => item.textContent === label,
    )

    return element?.nextElementSibling?.textContent ?? ''
  }, label)
}

async function expectObjective(page, expected) {
  await page.waitForFunction((expected) => {
    const heading = document.querySelector('[aria-label="当前目标"] h2')

    return heading?.textContent === expected
  }, expected)
}

async function expectObjectiveList(page, expectedItems) {
  await page.waitForFunction((expectedItems) => {
    const items = Array.from(document.querySelectorAll('[aria-label="当前目标"] li')).map((item) =>
      (item.textContent ?? '').replace(
        /^(?:完成|下一步|DONE|NEXT|STEP\s+\d+)\s*/i,
        '',
      ),
    )

    return expectedItems.every((item) => items.includes(item))
  }, expectedItems)
}

async function expectExplorationHint(page, expected) {
  await page.waitForFunction((expected) => {
    const hint = document.querySelector('[aria-label="探索提示"]')

    return hint?.textContent === expected
  }, expected)
}

async function expectIntelHelp(page) {
  await page.waitForFunction(() => {
    const hint = document.querySelector('[aria-label="情报说明"]')

    return hint?.textContent === '情报说明：可见=当前情报，已探索=历史地形，未知=隐藏详情'
  })
}

async function expectMapAndPanelVisible(page) {
  await page.waitForFunction(() => {
    const map = document.querySelector('.pixi-host')?.getBoundingClientRect()
    const panel = document.querySelector('[aria-label="当前目标"]')?.getBoundingClientRect()

    return Boolean(map && panel && map.width > 500 && map.height > 500 && panel.width > 250)
  })
}

async function waitForHttp(targetUrl, timeoutMs) {
  const startedAt = Date.now()

  while (Date.now() - startedAt < timeoutMs) {
    try {
      const response = await fetch(targetUrl)

      if (response.ok) {
        return
      }
    } catch {
      await delay(250)
    }
  }

  throw new Error(`Timed out waiting for ${targetUrl}`)
}

function delay(ms) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms)
  })
}

function stopProcessTree(childProcess) {
  if (!childProcess.pid) {
    return
  }

  if (process.platform === 'win32') {
    spawnSync('taskkill', ['/pid', String(childProcess.pid), '/T', '/F'], {
      stdio: 'ignore',
    })
    return
  }

  childProcess.kill()
}
