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
const screenshotWriteRetries = []
page.on('pageerror', (error) => errors.push(error.message))
page.on('console', (message) => { if (message.type() === 'error') errors.push(message.text()) })

async function screenshot(name, fullPage = false) {
  const bytes = await page.screenshot({ fullPage })
  for (let attempt = 0; ; attempt++) {
    try {
      await writeFile(`${output}/${name}.png`, bytes)
      return
    } catch (error) {
      if (attempt >= 3 || !['UNKNOWN', 'EBUSY', 'EPERM'].includes(error.code)) throw error
      screenshotWriteRetries.push({ name, code: error.code, attempt: attempt + 1 })
      await new Promise((resolve) => setTimeout(resolve, 400 * (attempt + 1)))
    }
  }
}

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
    await page.goto(`${base}/?view=map-elements&element=${asset.id}&revision=${asset.id.match(/-v(\d+)$/)?.[1] ?? 1}`)
    await page.waitForSelector(`.element-stage[data-loaded="true"][data-asset="${asset.id}"]`, { timeout: 60000 })
    await page.waitForTimeout(450)
    if (asset.reference) assert(await page.locator('.element-inspector img').evaluate((img) => img.complete && img.naturalWidth > 0), 'Reference did not load')
    const initial = await pixels()
    assert(initial.coverage > .007, `${asset.id}: blank canvas`)
    assert(initial.bounds[0] > 0 && initial.bounds[1] > 0 && initial.bounds[2] < initial.width - 1 && initial.bounds[3] < initial.height - 1, `${asset.id}: clipped model`)
    let animated = false
    if (asset.animatedPivots.length || asset.id.endsWith('-v3') || await page.locator('.element-stage').getAttribute('data-organs') || await page.locator('.element-stage').getAttribute('data-animals') || await page.locator('.element-stage').getAttribute('data-building') || await page.locator('.element-stage').getAttribute('data-terrain') || await page.locator('.element-stage').getAttribute('data-route') || await page.locator('.element-stage').getAttribute('data-transport') || await page.locator('.element-stage').getAttribute('data-mounted') || await page.locator('.element-stage').getAttribute('data-vessel')) {
      await page.waitForTimeout(440)
      animated = (await pixels()).hash !== initial.hash
      assert(animated, `${asset.id}: static animation`)
      await page.getByRole('button', { name: '暂停动画', exact: true }).click()
      await page.waitForTimeout(200)
      if (await page.getByLabel('生长阶段',{exact:true}).count()) {
        await page.waitForFunction(() => {
          const value=Number(document.querySelector('input[aria-label="生长阶段"]').value)/100
          return Math.abs(Number(document.querySelector('.element-stage').dataset.growth)-value)<.0001
        })
      }
      const paused = await pixels()
      await page.waitForTimeout(250)
      assert.equal((await pixels()).hash, paused.hash, `${asset.id}: pause failed`)
    }
    await screenshot(asset.id)
    const drawCalls = Number(await page.locator('.element-stage').getAttribute('data-draw-calls'))
    assert(drawCalls < 450, `${asset.id}: preview draw-call budget exceeded`)
    results.push({ id: asset.id, ...initial, animated, drawCalls })
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
  await screenshot('wireframe')
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto(`${base}/?view=map-elements&element=sheep`)
  await page.waitForSelector('.element-stage[data-loaded="true"]')
  await page.waitForTimeout(400)
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'Mobile horizontal overflow')
  const mobile = await pixels()
  assert(mobile.coverage > .007 && mobile.bounds[0] > 0 && mobile.bounds[2] < mobile.width - 1, 'Mobile blank/clipped')
  await screenshot('mobile', true)
  await page.getByLabel('选择模型', { exact: true }).selectOption('pine-tree')
  await page.waitForSelector('.element-stage[data-asset="pine-tree-v4"][data-loaded="true"]')
  assert((await pixels()).coverage > .007, 'Mobile model switching failed')
  await page.goto(`${base}/?view=map-elements&element=wheat-field&revision=2`)
  await page.waitForSelector('.element-stage[data-asset="wheat-field-v2"][data-loaded="true"]')
  await page.waitForTimeout(300)
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'V2 mobile overflow')
  await screenshot('wheat-v2-mobile', true)
  await page.getByRole('button', { name: '俯视', exact: true }).click()
  await page.getByRole('button', { name: '原版', exact: true }).click()
  await page.waitForSelector('.element-stage[data-asset="wheat-field"][data-loaded="true"]')
  assert.equal(await page.getByRole('button', { name: '俯视', exact: true }).getAttribute('aria-pressed'), 'true', 'Version switching reset view')
  assert(new URL(page.url()).searchParams.get('revision') === '1', 'Original URL not persisted')
  await page.reload()
  await page.waitForSelector('.element-stage[data-asset="wheat-field"][data-loaded="true"]')
  await page.getByRole('button', { name: '改进版', exact: true }).click()
  await page.waitForSelector('.element-stage[data-asset="wheat-field-v2"][data-loaded="true"]')
  assert((await page.getByLabel('下载 GLB', { exact: true }).getAttribute('download')).includes('wheat-field-v2'), 'Wrong revision download')
  await page.setViewportSize({ width: 1440, height: 1000 })
  await page.getByRole('button', { name: '自由视角', exact: true }).click()
  await page.waitForTimeout(300)
  const stationary = await pixels()
  const rect = await page.locator('.element-stage canvas').boundingBox()
  await page.mouse.move(rect.x + rect.width / 2, rect.y + rect.height / 2)
  await page.mouse.down()
  await page.mouse.move(rect.x + rect.width / 2 + 140, rect.y + rect.height / 2 + 30, { steps: 12 })
  await page.mouse.up()
  await page.waitForTimeout(500)
  assert.notEqual((await pixels()).hash, stationary.hash, 'Orbit interaction failed')
  await page.goto(`${base}/?view=map-elements&element=vegetable-field&revision=3`)
  await page.waitForSelector('.element-stage[data-asset="vegetable-field-v3"][data-loaded="true"]')
  await page.getByRole('button', { name: '暂停动画', exact: true }).click()
  await page.getByLabel('生长阶段', { exact: true }).focus()
  await page.keyboard.press('Home')
  await page.keyboard.press('ArrowRight')
  await page.keyboard.press('ArrowRight')
  await page.waitForTimeout(1700)
  const seedling = await pixels()
  await screenshot('vegetables-seedling')
  await page.getByLabel('生长阶段', { exact: true }).press('End')
  await page.waitForTimeout(1700)
  assert.notEqual((await pixels()).hash, seedling.hash, 'Growth did not alter geometry')
  assert(Number(await page.locator('.element-stage').getAttribute('data-growth')) > .99, 'Did not reach maturity')
  assert(Number(await page.locator('.element-stage').getAttribute('data-draw-calls')) < 450, 'Preview draw-call budget exceeded')
  await screenshot('vegetables-mature')
  await page.getByRole('button', { name: '重新播种', exact: true }).click()
  await page.waitForTimeout(1700)
  await page.getByLabel('自动生长', { exact: true }).check()
  await page.waitForTimeout(1600)
  assert(Number(await page.locator('.element-stage').getAttribute('data-growth')) > .02, 'Automatic growth stopped')
  await page.getByLabel('自动生长', { exact: true }).uncheck()
  await page.getByLabel('生长阶段', { exact: true }).press('End')
  await page.waitForTimeout(1700)
  await page.getByLabel('风力', { exact: true }).press('Home')
  await page.waitForTimeout(200)
  const calm = await pixels()
  await page.waitForTimeout(300)
  assert.equal((await pixels()).hash, calm.hash, 'Zero wind is not still')
  await page.getByLabel('风力', { exact: true }).press('End')
  await page.waitForTimeout(300)
  assert.notEqual((await pixels()).hash, calm.hash, 'Wind is not moving')
  await page.getByRole('button', { name: '随机长势', exact: true }).click()
  await page.setViewportSize({ width: 900, height: 900 })
  await page.waitForTimeout(300)
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'Tablet overflow')
  const controlBounds = await page.getByRole('button', { name: '随机长势', exact: true }).boundingBox()
  const inspectorBounds = await page.locator('.element-inspector').boundingBox()
  assert(controlBounds.y + controlBounds.height <= inspectorBounds.y + inspectorBounds.height, 'Tablet controls clipped')
  await page.setViewportSize({ width: 390, height: 844 })
  await page.waitForTimeout(300)
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'Living field mobile overflow')
  const livingMobile = await pixels()
  assert(livingMobile.bounds[0] > 0 && livingMobile.bounds[2] < livingMobile.width - 1, 'Living field clipped on mobile')
  await screenshot('living-field-mobile', true)
  const phenology = []
  await page.setViewportSize({ width: 1440, height: 1000 })
  for (const id of ['berry-shrub-v4','apple-tree','pumpkin-patch','sunflower-field','corn-field','rice-paddy','vineyard','cotton-field','oak-tree','birch-tree','willow-tree','palm-tree','cactus','fern','mushrooms','lily-pad','bamboo','wildflowers','potato-field','pine-tree-v4','reeds-v4']) {
    await page.goto(`${base}/?view=map-elements&element=${id}`)
    await page.waitForSelector('.element-stage[data-loaded="true"][data-organs]')
    await page.getByRole('button', { name:'暂停动画', exact:true }).click()
    const states = []
    for (const value of ['fern','pine-tree-v4'].includes(id) ? [5,25,49,82,100] : [5,49,82,100]) {
      await page.getByLabel('生长阶段', { exact:true }).fill(String(value))
      await page.waitForFunction((target) => Math.abs(Number(document.querySelector('.element-stage').dataset.growth)-target)<.0002,value/100,{ timeout:15000 })
      await page.waitForTimeout(150)
      const organs = JSON.parse(await page.locator('.element-stage').getAttribute('data-organs'))
      const pixel = await pixels()
      states.push({ value, organs, hash:pixel.hash })
      await screenshot(`${id}-stage-${value}`)
      if (value === 5) assert(organs.shoot > 0 && !organs.fruit && !organs.blossom, `${id}: not a seedling`)
      if (value === 25) assert(organs.foliage > 0 && !organs.spore, `${id}: unfurling stage missing`)
      if (value === 49) assert(organs[['fern','bamboo'].includes(id) ? 'foliage' : id==='pine-tree-v4' ? 'pollen' : id==='mushrooms' ? 'cap' : 'blossom'] > 0 && !organs.fruit, `${id}: developed organs missing`)
      if (value === 82) assert(organs[id==='bamboo' ? 'foliage' : id==='pine-tree-v4' ? 'cone' : id==='potato-field' ? 'tuber' : ['fern','mushrooms'].includes(id) ? 'spore' : ['sunflower-field','rice-paddy','cotton-field','birch-tree','willow-tree','wildflowers','reeds-v4'].includes(id) ? 'seed' : 'fruit'] > 0, `${id}: mature organs missing`)
      if (id==='pine-tree-v4') {
        assert(!organs.blossom && !organs.fruit, 'Pine incorrectly has flowers or fruit')
        if (value===100) assert(organs.scale>0 && organs.seed>0 && !organs.pollen, 'Pine did not open seed cones')
      }
      if (['fern','mushrooms','bamboo'].includes(id)) assert(!organs.blossom && !organs.fruit && !organs.seed, `${id}: nonflowering lifecycle mislabeled`)
      if (value === 100) assert(!organs.blossom, `${id}: petals persisted into senescence`)
    }
    if (id==='fern') {
      assert(new Set(states.map((state) => state.hash)).size>=4, `${id}: visually identical life stages`)
      assert.notEqual(states.find((s) => s.value===25).hash,states.find((s) => s.value===49).hash, 'Fern failed to unfurl')
      assert(!states.find((s) => s.value===49).organs.spore && states.find((s) => s.value===82).organs.spore>0, 'Fern failed to develop sori')
    } else assert.equal(new Set(states.map((state) => state.hash)).size,states.length, `${id}: visually identical life stages`)
    await page.getByLabel('风力',{ exact:true }).fill('0')
    await page.getByRole('button',{ name:'播放动画',exact:true }).click()
    await page.waitForTimeout(300)
    const calm=await pixels()
    await page.waitForTimeout(350)
    assert.equal((await pixels()).hash,calm.hash,`${id}: zero wind drifted`)
    await page.getByLabel('风力',{ exact:true }).fill('60')
    await page.waitForTimeout(300)
    assert.notEqual((await pixels()).hash,calm.hash,`${id}: wind did not move organs`)
    await page.getByRole('button',{ name:'暂停动画',exact:true }).click()
    await page.getByLabel('生长阶段', { exact:true }).fill('82')
    await page.waitForTimeout(1700)
    for (const view of ['正面','侧面','俯视']) {
      await page.getByRole('button', { name:view, exact:true }).click()
      await page.waitForTimeout(250)
      const pixel = await pixels()
      assert(pixel.coverage>.007 && pixel.bounds[0]>0 && pixel.bounds[2]<pixel.width-1, `${id}: ${view} blank/clipped`)
    }
    await page.getByRole('button', { name:'自由视角', exact:true }).click()
    await page.setViewportSize({ width:390,height:844 })
    await page.getByLabel('生长阶段', { exact:true }).fill(id==='cotton-field' ? '100' : id==='lily-pad' ? '49' : '82')
    await page.waitForTimeout(1700)
    const pixel = await pixels()
    assert(pixel.coverage>.007 && pixel.bounds[0]>0 && pixel.bounds[2]<pixel.width-1, `${id}: mobile blank/clipped`)
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${id}: mobile overflow`)
    await screenshot(`${id}-mobile`,true)
    await page.setViewportSize({ width:1440,height:1000 })
    phenology.push({ id,states })
  }
  await page.getByRole('button', { name:'资产进度', exact:true }).click()
  assert.equal(await page.locator('.element-roadmap li').count(),108)
  assert.equal(await page.locator('.element-roadmap li button:enabled').count(),87)
  await screenshot('roadmap')
  await page.setViewportSize({ width:390,height:844 })
  assert(await page.evaluate(() => document.querySelector('.element-roadmap').scrollWidth <= innerWidth), 'Mobile roadmap overflow')
  await screenshot('roadmap-mobile',true)
  await page.getByRole('button', { name:'关闭资产进度', exact:true }).click()
  assert.deepEqual(errors, [], 'Browser errors')
  await writeFile(`${output}/verification.json`, JSON.stringify({ results, mobile, errors, checks: [`${results.length} models`, 'reference loading', 'canvas pixels', 'framing', 'animations', 'pause', 'three views', 'wireframe', 'mobile switching', 'original/refined switching', 'revision URL reload', 'revision download', 'orbit interaction', 'growth geometry', 'automatic growth', 'calm/wind', 'living mobile', 'draw call budget'] }, null, 2) + '\n')
  await writeFile(`${output}/phenology.json`, JSON.stringify(phenology,null,2)+'\n')
  console.log(JSON.stringify({ models: results.length, animated: results.filter((r) => r.animated).length, botanical:phenology.length, screenshotWriteRetries, errors }))
} finally {
  await browser.close()
}
