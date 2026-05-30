import { spawn, spawnSync } from 'node:child_process'
import { chromium } from 'playwright'

const port = 5188
const baseUrl = `http://127.0.0.1:${port}/`
const combatUrl = `${baseUrl}?scenario=combat`

const server = spawn(
  process.platform === 'win32' ? 'npm.cmd' : 'npm',
  ['run', 'preview', '--', '--host', '127.0.0.1', '--port', String(port)],
  {
    cwd: process.cwd(),
    stdio: 'ignore',
  },
)

try {
  await waitForHttp(baseUrl, 20_000)

  const browser = await chromium.launch()
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } })

  try {
    await page.goto(baseUrl, { waitUntil: 'load' })
    await page.waitForFunction(() => document.documentElement.dataset.civPerf === 'ready')
    await expectValue(page, '场景', 'default')
    await expectValue(page, '单位数量', '1')
    await expectValue(page, '攻击状态', '需要选择己方战士')
    await expectNoButton(page, '攻击')

    await page.goto(combatUrl, { waitUntil: 'load' })
    await page.waitForFunction(() => document.documentElement.dataset.civPerf === 'ready')
    await expectValue(page, '场景', 'combat:adjacent-enemy')
    await expectValue(page, '单位数量', '2')
    await expectValue(page, '命令日志', '0')
    await expectValue(page, '攻击状态', '需要选择己方战士')
    await expectNoButton(page, '攻击')

    await page.mouse.click(415, 389)
    await page.waitForFunction(() => window.__civPerf?.getStats()?.selectedTileId === 'tile:8:9')
    await expectValue(page, '已选单位', 'unit:warrior:scenario:1 @ tile:8:9')
    await expectValue(page, '地块单位', 'unit:warrior:scenario:1')
    await expectValue(page, '地块单位生命', 'unit:warrior:scenario:1 20/20')
    await expectValue(page, '攻击状态', '请选择可见相邻敌方单位')
    await expectNoButton(page, '攻击')

    await page.mouse.click(394, 425)
    await page.waitForFunction(() => window.__civPerf?.getStats()?.selectedTileId === 'tile:8:10')
    await expectValue(page, '已选单位', 'unit:warrior:scenario:1 @ tile:8:9')
    await expectValue(page, '地块单位', 'unit:enemy:scout:1')
    await expectValue(page, '地块单位生命', 'unit:enemy:scout:1 10/10')
    await expectValue(page, '攻击状态', '可以攻击 unit:enemy:scout:1')
    await expectButton(page, '攻击')

    await page.getByRole('button', { name: '攻击' }).click()
    await expectValue(page, '命令错误', '无')
    await expectValue(page, '命令日志', '1')
    await expectValue(page, '上条命令', 'cmd:1:0:ATTACK / ATTACK')
    await expectValue(page, '地块单位生命', 'unit:enemy:scout:1 4/10')
    await expectEvent(page, '攻击：unit:warrior:scenario:1 -> unit:enemy:scout:1，HP 10 -> 4')

    await page.getByRole('button', { name: '攻击' }).click()
    await expectValue(page, '命令日志', '2')
    await expectValue(page, '上条命令', 'cmd:1:1:ATTACK / ATTACK')
    await expectValue(page, '单位数量', '1')
    await expectValue(page, '地块单位', '无')
    await expectValue(page, '地块单位生命', '无')
    await expectValue(page, '攻击状态', '请选择可见相邻敌方单位')
    await expectEvent(page, '击败单位：unit:enemy:scout:1')
    await expectNoButton(page, '攻击')

    const attackHash = await readValue(page, '状态哈希')
    await page.getByRole('button', { name: '保存游戏' }).click()
    await expectValue(page, '存档状态', '已保存回合 1 / 命令 2')

    await page.getByRole('button', { name: '结束回合' }).click()
    await expectValue(page, '回合', '2')
    await expectValue(page, '命令日志', '3')

    await page.getByRole('button', { name: '读取游戏' }).click()
    await expectValue(page, '场景', 'combat:adjacent-enemy')
    await expectValue(page, '回合', '1')
    await expectValue(page, '命令日志', '2')
    await expectValue(page, '单位数量', '1')
    await expectValue(page, '状态哈希', attackHash)
    await expectEvent(page, '读取存档：回合 1 / 命令 2')

    await page.mouse.click(415, 389)
    await page.waitForFunction(() => window.__civPerf?.getStats()?.selectedTileId === 'tile:8:9')
    await expectValue(page, '已选单位', 'unit:warrior:scenario:1 @ tile:8:9')

    await page.mouse.click(244, 244)
    await page.waitForFunction(() => {
      const selectedTileId = window.__civPerf?.getStats()?.selectedTileId

      return selectedTileId && selectedTileId !== 'tile:8:10'
    })
    await expectValue(page, '地块单位', '未知')
    await expectValue(page, '攻击状态', '目标不可见')
    await expectNoButton(page, '攻击')

    console.log('Combat smoke passed')
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

async function readValue(page, label) {
  return page.evaluate((label) => {
    const element = Array.from(document.querySelectorAll('dt')).find(
      (item) => item.textContent === label,
    )

    return element?.nextElementSibling?.textContent ?? ''
  }, label)
}

async function expectButton(page, name) {
  await page.waitForFunction((name) => {
    const buttons = Array.from(document.querySelectorAll('button')).filter(
      (button) => button.textContent?.trim() === name,
    )

    return buttons.length === 1
  }, name)
}

async function expectNoButton(page, name) {
  await page.waitForFunction((name) => {
    const buttons = Array.from(document.querySelectorAll('button')).filter(
      (button) => button.textContent?.trim() === name,
    )

    return buttons.length === 0
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
