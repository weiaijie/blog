import { chromium } from 'playwright'
import { mkdir, readFile, writeFile } from 'node:fs/promises'
import assert from 'node:assert/strict'

const base = process.env.ELEMENT_PREVIEW_URL || 'http://127.0.0.1:5173'
const manifest = JSON.parse(await readFile('src/render/assets/elements/manifest.json', 'utf8'))
const output = 'artifacts/map-elements'
await mkdir(output, { recursive: true })
const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'no-preference' })
const errors = []
page.on('pageerror', (error) => errors.push(error.message))
page.on('console', (message) => { if (message.type() === 'error') errors.push(message.text()) })

async function pixels() {
  return page.locator('.element-stage canvas').evaluate((canvas) => {
    const gl = canvas.getContext('webgl2') || canvas.getContext('webgl')
    const width = gl.drawingBufferWidth, height = gl.drawingBufferHeight
    const data = new Uint8Array(width * height * 4)
    gl.readPixels(0, 0, width, height, gl.RGBA, gl.UNSIGNED_BYTE, data)
    let painted = 0, hash = 2166136261
    let minX = width, minY = height, maxX = 0, maxY = 0
    for (let i = 0; i < data.length; i += 16) {
      hash = Math.imul(hash ^ data[i], 16777619) >>> 0
      if (Math.abs(data[i] - data[0]) + Math.abs(data[i + 1] - data[1]) + Math.abs(data[i + 2] - data[2]) > 35) {
        painted++
        const x = (i / 4) % width, y = Math.floor(i / 4 / width)
        minX = Math.min(minX, x); maxX = Math.max(maxX, x)
        minY = Math.min(minY, y); maxY = Math.max(maxY, y)
      }
    }
    return { hash, coverage: painted / (width * height / 4), bounds: [minX, minY, maxX, maxY], width, height }
  })
}

const results = []
try {
  for (const asset of manifest.assets) {
    await page.goto(`${base}/?view=map-elements&element=${asset.id}`)
    await page.waitForSelector('.element-stage[data-loaded="true"]', { timeout: 60000 })
    await page.waitForTimeout(450)
    assert(await page.locator('.element-inspector img').evaluate((img) => img.complete && img.naturalWidth > 0), 'Reference did not load')
    const initial = await pixels()
    assert(initial.coverage > .007, `${asset.id}: blank canvas`)
    assert(initial.bounds[0] > 0 && initial.bounds[1] > 0 && initial.bounds[2] < initial.width - 1 && initial.bounds[3] < initial.height - 1, `${asset.id}: clipped model`)
    let animated = false
    if (asset.animatedPivots.length) {
      await page.waitForTimeout(440)
      animated = (await pixels()).hash !== initial.hash
      assert(animated, `${asset.id}: static animation`)
      await page.getByRole('button', { name: '暂停动画', exact: true }).click()
      await page.waitForTimeout(200)
      const paused = await pixels()
      await page.waitForTimeout(250)
      assert.equal((await pixels()).hash, paused.hash, `${asset.id}: pause failed`)
    }
    await page.screenshot({ path: `${output}/${asset.id}.png` })
    results.push({ id: asset.id, ...initial, animated })
  }
  await page.goto(`${base}/?view=map-elements&element=fishing-boat`)
  await page.waitForSelector('.element-stage[data-loaded="true"]')
  for (const view of ['正面', '侧面', '俯视']) {
    await page.getByRole('button', { name: view, exact: true }).click()
    await page.waitForTimeout(350)
    assert((await pixels()).coverage > .007, `${view}: blank`)
  }
  await page.getByRole('button', { name: '线框', exact: true }).click()
  assert.equal(await page.getByRole('button', { name: '线框', exact: true }).getAttribute('aria-pressed'), 'true')
  await page.screenshot({ path: `${output}/wireframe.png` })
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto(`${base}/?view=map-elements&element=sheep`)
  await page.waitForSelector('.element-stage[data-loaded="true"]')
  await page.waitForTimeout(400)
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'Mobile horizontal overflow')
  const mobile = await pixels()
  assert(mobile.coverage > .007 && mobile.bounds[0] > 0 && mobile.bounds[2] < mobile.width - 1, 'Mobile blank/clipped')
  await page.screenshot({ path: `${output}/mobile.png`, fullPage: true })
  await page.getByLabel('选择模型', { exact: true }).selectOption('pine-tree')
  await page.waitForSelector('.element-stage[data-asset="pine-tree"][data-loaded="true"]')
  assert((await pixels()).coverage > .007, 'Mobile model switching failed')
  assert.deepEqual(errors, [], 'Browser errors')
  await writeFile(`${output}/verification.json`, JSON.stringify({ results, mobile, errors, checks: ['12 models', 'reference loading', 'canvas pixels', 'framing', 'animations', 'pause', 'three views', 'wireframe', 'mobile switching'] }, null, 2) + '\n')
  console.log(JSON.stringify({ models: results.length, animated: results.filter((r) => r.animated).length, errors }))
} finally {
  await browser.close()
}
