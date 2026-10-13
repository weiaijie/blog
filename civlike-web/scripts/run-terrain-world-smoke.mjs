import assert from 'node:assert/strict'
import { spawn } from 'node:child_process'
import { existsSync } from 'node:fs'
import { mkdir, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { setTimeout as delay } from 'node:timers/promises'
import { chromium } from 'playwright'

// Run from civlike-web after npm run build. This checks the visual lab directly,
// without the skipped gameplay assertions in run-playable-smoke.mjs.
assert.ok(existsSync('dist/index.html'), 'Run npm run build before this smoke test')
const port = 5190
const base = `http://127.0.0.1:${port}`
const output = resolve('.sites-artifacts/terrain-world')
const server = spawn(process.platform === 'win32' ? 'npm.cmd' : 'npm', ['run', 'preview', '--', '--host', '127.0.0.1', '--port', String(port), '--strictPort'], {
  stdio: 'ignore', detached: process.platform !== 'win32',
})
let browser
const report = { renderer: 'Chromium; hardware performance requires a real device', cases: [] }

async function stats(page) {
  return page.locator('[data-testid="terrain-world-canvas"]').evaluate((el) => ({ ...el.dataset }))
}

try {
  await mkdir(output, { recursive: true })
  let ready = false
  for (let attempt = 0; attempt < 100; attempt++) {
    if (server.exitCode !== null) throw new Error('Preview server exited before readiness')
    try {
      if ((await fetch(base)).ok) { ready = true; break }
    } catch { /* Server may still be starting. */ }
    await delay(200)
  }
  assert.ok(ready, 'Preview HTTP readiness timed out')
  const executablePath = process.env.CIVLIKE_CHROMIUM_PATH || (existsSync('/usr/bin/chromium') ? '/usr/bin/chromium' : undefined)
  browser = await chromium.launch({ executablePath, args: ['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] })
  const cases = [
    { seed: 221648817, width: 1440, height: 960, name: 'desktop', interactions: true },
    { seed: 569575877, width: 1024, height: 768, name: 'seed-569575877' },
    { seed: 20261011, width: 1024, height: 768, name: 'seed-20261011' },
    { seed: 221648817, width: 390, height: 844, name: 'mobile-390' },
    { seed: 221648817, width: 320, height: 740, name: 'mobile-320' },
  ]
  for (const entry of cases) {
    console.log(`Checking terrain world: ${entry.name}`)
    const page = await browser.newPage({ viewport: { width: entry.width, height: entry.height }, reducedMotion: 'reduce' })
    page.setDefaultTimeout(60_000)
    const errors = [], failedRequests = []
    page.on('pageerror', (error) => errors.push(error.message))
    page.on('response', (response) => {
      if (response.status() >= 400 && !new URL(response.url()).pathname.endsWith('/favicon.ico')) {
        failedRequests.push({ url: response.url(), status: response.status() })
      }
    })
    page.on('console', (message) => {
      if (message.type() === 'error' && !message.location().url.endsWith('/favicon.ico')) errors.push(message.text())
    })
    const started = performance.now()
    await page.goto(`${base}/?view=terrain-world&assetSeed=${entry.seed}&season=bloom`, { waitUntil: 'load' })
    await page.waitForFunction(() => Number(document.querySelector('[data-testid="terrain-world-canvas"]')?.dataset.drawCalls) > 0)
    const initial = await stats(page)
    const startupMs = Math.round(performance.now() - started)
    assert.equal(Number(initial.tiles), 469, 'Expanded map must render 469 cells')
    assert.ok(Number(initial.buildings) >= 25, 'Settlement buildings must render')
    assert.ok(Number(initial.farms) > 2, 'Farmland must render')
    assert.ok(Number(initial.trees) > 100 && Number(initial.grass) > 500, 'Vegetation must render')
    assert.ok(Number(initial.fishCount) > 0, 'Underwater life must render')
    assert.ok(Number(initial.drawCalls) <= 100, 'Keep scenery batched as the map grows')
    assert.equal(initial.season, 'bloom')
    assert.equal(initial.detailMode, 'far', 'Overview must use the sparse detail layer')
    assert.equal(await page.getByRole('alert').count(), 0)
    const fits = await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)
    assert.ok(fits, 'No horizontal overflow, including narrow mobile viewports')
    await page.screenshot({ path: resolve(output, `${entry.name}.png`) })
    if (entry.interactions) {
      await page.getByRole('combobox', { name: '聚落定位', exact: true }).selectOption('town')
      await page.waitForFunction(() => document.querySelector('[data-testid="terrain-world-canvas"]')?.dataset.detailMode === 'near')
      await page.waitForTimeout(800)
      await page.screenshot({ path: resolve(output, 'town-closeup.png') })
      await page.getByRole('button', { name: '重置视角', exact: true }).click()
      await page.waitForFunction(() => document.querySelector('[data-testid="terrain-world-canvas"]')?.dataset.detailMode === 'far')
      await page.getByRole('button', { name: '俯视', exact: true }).click()
      await page.waitForTimeout(800)
      await page.screenshot({ path: resolve(output, 'top.png') })
      await page.getByRole('combobox', { name: '季节', exact: true }).selectOption('snow')
      await page.waitForFunction(() => document.querySelector('[data-testid="terrain-world-canvas"]')?.dataset.season === 'snow')
      await page.screenshot({ path: resolve(output, 'winter.png') })
      await page.getByRole('combobox', { name: '季节', exact: true }).selectOption('bloom')
      await page.waitForFunction(() => document.querySelector('[data-testid="terrain-world-canvas"]')?.dataset.season === 'bloom')
      await page.getByRole('button', { name: '等距', exact: true }).click()
      await page.getByRole('button', { name: '播放动画', exact: true }).click()
      await page.waitForFunction((before) => {
        const data = document.querySelector('[data-testid="terrain-world-canvas"]')?.dataset
        return Number(data?.simulationTime) > Number(before.simulationTime) && data?.fishPosition !== before.fishPosition
      }, initial)
      await page.getByRole('button', { name: '暂停动画', exact: true }).click()
      await page.waitForTimeout(800)
      const paused = await stats(page)
      await page.waitForTimeout(800)
      const still = await stats(page)
      assert.equal(still.simulationTime, paused.simulationTime, 'Pause must freeze the simulation')
      assert.equal(still.fishPosition, paused.fishPosition, 'Pause must freeze fish motion')
      assert.ok(Number(still.simulationTime) >= 0, 'Initialization must not move time backwards')
      await page.reload({ waitUntil: 'load' })
      await page.waitForFunction(() => Number(document.querySelector('[data-testid="terrain-world-canvas"]')?.dataset.drawCalls) > 0)
      const repeated = await stats(page)
      for (const key of ['tiles', 'trees', 'grass', 'buildings', 'farms', 'fishCount']) {
        assert.equal(repeated[key], initial[key], `Seed must reproduce ${key}`)
      }
    }
    assert.deepEqual(failedRequests, [], 'All application assets must load')
    assert.deepEqual(errors, [], 'No browser runtime or console errors')
    report.cases.push({ ...entry, startupMs, stats: initial, errors, failedRequests })
    await page.close()
  }
  report.passed = true
  await writeFile(resolve(output, 'verification.json'), JSON.stringify(report, null, 2))
  console.log(`Passed ${report.cases.length} terrain-world browser cases; evidence: ${output}`)
} finally {
  await browser?.close()
  // npm starts Vite as a child; stop our whole group so the test port is freed.
  if (process.platform === 'win32') server.kill('SIGTERM')
  else {
    try { process.kill(-server.pid, 'SIGTERM') }
    catch (error) { if (error.code !== 'ESRCH') throw error }
  }
}
