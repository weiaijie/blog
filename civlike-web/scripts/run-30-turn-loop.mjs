import { spawn, spawnSync } from 'node:child_process'
import { chromium } from 'playwright'

const port = 5187
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

    await page.mouse.click(364, 404)
    await page.waitForFunction(() => window.__civPerf?.getStats()?.selectedTileId === 'tile:8:9')
    await page.mouse.click(364, 444)
    await page.waitForFunction(() => window.__civPerf?.getStats()?.selectedTileId === 'tile:8:10')
    await expectObjective(page, '选择采矿')

    await page.getByRole('button', { name: '选择采矿' }).click()
    await expectObjective(page, '生产侦察兵')

    await page.getByRole('button', { name: '生产侦察兵' }).click()
    await expectObjective(page, '结束回合')

    await page.getByRole('button', { name: '保存游戏' }).click()
    await expectValue(page, '存档状态', '已保存回合 1 / 命令 3')

    for (let index = 0; index < 14; index += 1) {
      await page.getByRole('button', { name: '结束回合' }).click()
    }

    await expectValue(page, '回合', '15')
    await expectValue(page, '单位数量', '8')
    await expectValue(page, '食物库存', '28')
    await expectValue(page, '已完成科技', 'tech:mining')

    await page.getByRole('button', { name: '读取游戏' }).click()
    await expectValue(page, '回合', '1')
    await expectValue(page, '命令日志', '3')
    await expectValue(page, '单位数量', '1')
    await expectValue(page, '食物库存', '0')
    await expectValue(page, '当前科技', 'tech:mining')
    await expectValue(page, '首都生产', 'unit:scout')
    await expectValue(page, '存档状态', '已读取回合 1 / 命令 3')

    for (let index = 0; index < 29; index += 1) {
      await page.getByRole('button', { name: '结束回合' }).click()
    }

    await expectValue(page, '回合', '30')
    await expectValue(page, '单位数量', '15')
    await expectValue(page, '食物库存', '58')
    await expectValue(page, '科研进度', '26')
    await expectValue(page, '首都进度', '2')
    await expectValue(page, '已完成科技', 'tech:mining')
    await expectValue(page, '命令日志', '32')
    await expectObjective(page, '继续回合')

    console.log('30 turn UI loop passed')
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

async function expectObjective(page, expected) {
  await page.waitForFunction((expected) => {
    const heading = document.querySelector('[aria-label="当前目标"] h2')

    return heading?.textContent === expected
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
