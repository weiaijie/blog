import { spawn, spawnSync } from 'node:child_process'
import { chromium } from 'playwright'

const port = 5186
const url = `http://127.0.0.1:${port}/`

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
    await expectExplorationHint(page, '移动侦察兵以揭示附近地块')
    await expectMapAndPanelVisible(page)
    await expectValue(page, '可见地块', '5')
    await expectValue(page, '已探索地块', '5')
    await expectValue(page, '地图迷雾', '可见 5，已探索 5')

    await page.mouse.click(380, 380)
    await page.waitForFunction(() => window.__civPerf?.getStats()?.selectedTileId === 'tile:8:8')
    await expectValue(page, '地块详情', '8, 8 / 森林')
    await expectValue(page, '地块城市', 'city:capital')

    await page.mouse.click(364, 404)
    await page.waitForFunction(() => window.__civPerf?.getStats()?.selectedTileId === 'tile:8:9')
    await expectValue(page, '已选单位', 'unit:scout:1 @ tile:8:9')

    await page.mouse.click(364, 444)
    await page.waitForFunction(() => window.__civPerf?.getStats()?.selectedTileId === 'tile:8:10')
    await expectObjective(page, '选择采矿')
    await expectExplorationHint(page, '侦察兵已探索 8 个地块')
    await expectValue(page, '已选单位', 'unit:scout:1 @ tile:8:10')
    await expectValue(page, '地块单位', 'unit:scout:1')
    await expectValue(page, '可见地块', '5')
    await expectValue(page, '已探索地块', '8')
    await expectValue(page, '地图迷雾', '可见 5，已探索 8')
    await expectValue(page, '上条命令', 'cmd:1:0:MOVE_UNIT / MOVE_UNIT')

    await page.getByRole('button', { name: '保存游戏' }).click()
    await expectValue(page, '存档状态', '已保存回合 1 / 命令 1')

    await page.getByRole('button', { name: '选择采矿' }).click()
    await expectObjective(page, '生产侦察兵')
    await expectValue(page, '当前科技', 'tech:mining')
    await expectValue(page, '科技进度', '0 / 3')

    await page.getByRole('button', { name: '生产侦察兵' }).click()
    await expectObjective(page, '结束回合')
    await expectValue(page, '首都生产', 'unit:scout')
    await expectValue(page, '首都进度', '0')
    await expectValue(page, '首都产出', '食物 2，生产 2，科研 1')

    await page.getByRole('button', { name: '结束回合' }).click()
    await expectObjective(page, '继续回合')
    await expectValue(page, '回合', '2')
    await expectValue(page, '食物库存', '2')
    await expectValue(page, '科研进度', '1')
    await expectValue(page, '科技进度', '1 / 3')
    await expectValue(page, '首都进度', '2')
    await expectValue(page, '上条命令', 'cmd:1:3:END_TURN / END_TURN')

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
    await expectValue(page, '上条命令', 'cmd:1:0:MOVE_UNIT / MOVE_UNIT')

    await page.getByRole('button', { name: '生产侦察兵' }).click()
    await expectValue(page, '首都生产', 'unit:scout')
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
    await page.getByRole('button', { name: '结束回合' }).click()
    await expectValue(page, '当前科技', '无')
    await expectValue(page, '科技进度', '无')
    await expectValue(page, '已完成科技', 'tech:mining')

    const persistedHash = await readValue(page, '状态哈希')
    await page.getByRole('button', { name: '持久保存' }).click()
    await expectValueStartsWith(page, '持久存档', '已保存回合 4 / 命令 6 / ')

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
    await expectValue(page, '可见地块', '9')
    await expectValue(page, '已探索地块', '11')
    await expectValue(page, '地图迷雾', '可见 9，已探索 11')
    await expectValue(page, '已完成科技', 'tech:mining')
    await expectValue(page, '首都进度', '2')
    await expectValue(page, '持久存档', '已读取回合 4 / 命令 6')
    await expectValue(page, '状态哈希', persistedHash)

    await page.mouse.click(364, 444)
    await page.mouse.click(244, 244)
    await expectValue(page, '命令错误', 'MOVE_UNIT：目标地块必须与已选单位相邻。')
    await expectValue(page, '命令日志', '6')

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
    const items = Array.from(document.querySelectorAll('[aria-label="当前目标"] li')).map(
      (item) => item.textContent?.replace(/^(完成|下一步)/, '') ?? '',
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
