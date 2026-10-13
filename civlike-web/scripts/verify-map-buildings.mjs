import { chromium } from 'playwright'
import { mkdir, writeFile } from 'node:fs/promises'
import assert from 'node:assert/strict'

const output='artifacts/map-elements/buildings'
await mkdir(output,{ recursive:true })
const browser=await chromium.launch()
const page=await browser.newPage({ viewport:{ width:1440,height:1000 },reducedMotion:'no-preference' })
const errors=[],results=[],writeRetries=[]
const requested=process.argv.slice(2)
page.on('pageerror',(error) => errors.push(error.message))
page.on('console',(message) => { if(message.type()==='error') errors.push(message.text()) })
async function shot(name,fullPage=false) {
  const bytes=await page.screenshot({ fullPage })
  for(let attempt=0;;attempt++) {
    try { await writeFile(`${output}/${name}.png`,bytes); return }
    catch(error) {
      if(attempt>=3 || !['UNKNOWN','EBUSY','EPERM'].includes(error.code)) throw error
      writeRetries.push({ name,code:error.code }); await page.waitForTimeout(400*(attempt+1))
    }
  }
}
async function state() { return JSON.parse(await page.locator('.element-stage').getAttribute('data-building')) }
async function settle(progress) {
  await page.waitForFunction((target) => Math.abs(JSON.parse(document.querySelector('.element-stage').dataset.building).progress-target)<.00001,progress,{ timeout:15000 })
  await page.waitForTimeout(150)
}
async function pixels() {
  return page.locator('.element-stage canvas').evaluate((canvas) => {
    const gl=canvas.getContext('webgl2'),w=gl.drawingBufferWidth,h=gl.drawingBufferHeight,data=new Uint8Array(w*h*4)
    gl.readPixels(0,0,w,h,gl.RGBA,gl.UNSIGNED_BYTE,data)
    let hash=2166136261,painted=0,minX=w,minY=h,maxX=0,maxY=0
    for(let i=0;i<data.length;i+=16) {
      hash=Math.imul(hash^data[i],16777619)>>>0
      if(Math.abs(data[i]-data[0])+Math.abs(data[i+1]-data[1])+Math.abs(data[i+2]-data[2])>35) {
        painted++;const x=(i/4)%w,y=Math.floor(i/4/w)
        minX=Math.min(minX,x);minY=Math.min(minY,y);maxX=Math.max(maxX,x);maxY=Math.max(maxY,y)
      }
    }
    return { hash,coverage:painted/(w*h/4),framed:minX>0&&minY>0&&maxX<w-1&&maxY<h-1 }
  })
}
try {
  for(const id of requested.length ? requested : ['cottage','barn','windmill','watermill','watchtower','castle-keep','castle-gate','castle-wall','stable','blacksmith','market-hall','train-station','factory']) {
    await page.setViewportSize({ width:1440,height:1000 })
    await page.goto(`http://127.0.0.1:5173/?view=map-elements&element=${id}`)
    await page.waitForSelector('.element-stage[data-loaded="true"][data-building]')
    await page.getByRole('button',{ name:'暂停动画',exact:true }).click()
    const stages=[]
    for(const progress of [0,30,52,78,100]) {
      await page.getByLabel('施工进度',{ exact:true }).fill(String(progress))
      await settle(progress/100)
      const p=await pixels(),s=await state()
      assert(p.coverage>.007 && p.framed,`${id}: stage ${progress} blank/clipped`)
      assert(Math.abs(s.progress-progress/100)<.005,`${id}: slider not applied`)
      stages.push({ progress,...p,visible:s.visible })
      await shot(`${id}-stage-${progress}`)
    }
    assert.equal(new Set(stages.map((s) => s.hash)).size,stages.length,`${id}: identical construction stages`)
    assert(stages.at(-1).visible>stages[0].visible,`${id}: no assembled parts`)
    const base=await pixels()
    await page.getByLabel('升级附件',{ exact:true }).check()
    await page.waitForTimeout(300)
    const upgraded=await pixels()
    assert(upgraded.framed && upgraded.hash!==base.hash,`${id}: upgrade missing/clipped`)
    await shot(`${id}-upgraded`)
    if(['stable','blacksmith','market-hall','train-station','factory'].includes(id)){
      await page.getByRole('button',{name:'屋顶剖面',exact:true}).click()
      await page.waitForTimeout(300)
      const interior=await pixels();assert(interior.framed&&interior.hash!==upgraded.hash,`${id}: roof inspection has no effect`)
      await shot(`${id}-interior`)
      await page.getByRole('button',{name:'播放动画',exact:true}).click();await page.waitForTimeout(300)
      assert.equal(await page.locator('.element-stage').getAttribute('data-cutaway'),'true')
      await page.getByRole('button',{name:'暂停动画',exact:true}).click()
      await page.getByRole('button',{name:'屋顶剖面',exact:true}).click()
    }
    for(const view of ['正面','侧面','俯视']) {
      await page.getByRole('button',{ name:view,exact:true }).click()
      await page.waitForTimeout(250)
      assert((await pixels()).framed,`${id}: ${view} clipped`)
      await shot(`${id}-${view}`)
    }
    await page.getByRole('button',{ name:'自由视角',exact:true }).click()
    await page.getByRole('button',{ name:'播放动画',exact:true }).click()
    const moving=await pixels()
    await page.waitForTimeout(750)
    assert.notEqual((await pixels()).hash,moving.hash,`${id}: operating mechanism static`)
    await page.getByLabel('功能运行',{ exact:true }).uncheck()
    await page.waitForTimeout(300)
    const stopped=await pixels()
    await page.waitForTimeout(350)
    assert.equal((await pixels()).hash,stopped.hash,`${id}: working toggle ignored`)
    await page.getByLabel('功能运行',{ exact:true }).check()
    await page.getByLabel('运行速度',{ exact:true }).fill('0')
    await page.waitForTimeout(300)
    const zero=await pixels()
    await page.waitForTimeout(350)
    assert.equal((await pixels()).hash,zero.hash,`${id}: zero speed ignored`)
    await page.getByLabel('运行速度',{ exact:true }).fill('60')
    await page.getByLabel('自动施工',{ exact:true }).check()
    await page.waitForTimeout(2000)
    await page.getByRole('button',{ name:'暂停动画',exact:true }).click()
    await page.waitForTimeout(250)
    const paused=await state(),still=await pixels()
    assert(paused.progress<.20 && paused.progress>0,`${id}: auto construction not reset/advancing`)
    await page.waitForTimeout(300)
    assert.deepEqual(await state(),paused,`${id}: auto construction did not pause`)
    assert.equal((await pixels()).hash,still.hash,`${id}: construction changed while paused`)
    if (id==='watermill') {
      await page.getByRole('button',{ name:'播放动画',exact:true }).click()
      await page.waitForFunction(() => JSON.parse(document.querySelector('.element-stage').dataset.building).progress===1,{},{ timeout:90000 })
      await page.getByRole('button',{ name:'暂停动画',exact:true }).click()
      await page.waitForTimeout(250)
      await page.getByLabel('自动施工',{ exact:true }).uncheck()
      await page.waitForTimeout(500)
      assert.equal((await state()).progress,1,'Disabling completed auto construction reset the building')
      await shot('watermill-auto-completed')
    }
    await page.getByLabel('施工进度',{ exact:true }).fill('100')
    await settle(1)
    const drawCalls=Number(await page.locator('.element-stage').getAttribute('data-draw-calls'))
    assert(drawCalls<450,`${id}: draw-call budget`)
    await page.setViewportSize({ width:390,height:844 })
    await page.waitForTimeout(300)
    const mobile=await pixels()
    assert(mobile.coverage>.007 && mobile.framed,`${id}: mobile clipped/blank`)
    assert(await page.evaluate(() => document.documentElement.scrollWidth<=innerWidth),`${id}: mobile horizontal overflow`)
    await shot(`${id}-mobile`,true)
    await page.setViewportSize({ width:320,height:720 })
    await page.waitForTimeout(300)
    const narrow=await pixels()
    assert(narrow.coverage>.007 && narrow.framed,`${id}: narrow mobile clipped/blank`)
    assert(await page.evaluate(() => document.documentElement.scrollWidth<=innerWidth),`${id}: narrow mobile overflow`)
    assert((await page.getByLabel('下载 GLB',{exact:true}).getAttribute('download')).includes(id))
    await shot(`${id}-mobile-320`,true)
    await page.setViewportSize({ width:390,height:844 })
    if(id==='train-station'){
      await page.getByLabel('发车信号',{exact:true}).check()
      await page.waitForFunction(()=>JSON.parse(document.querySelector('.element-stage').dataset.building).access===1,{},{timeout:15000})
      assert(await page.getByText('允许通行',{exact:true}).isVisible())
      await page.getByRole('button',{name:'暂停动画',exact:true}).click()
      await page.waitForTimeout(150);assert((await pixels()).framed,'Station signal clipped');await shot('train-station-signal-open',true)
      await page.getByLabel('发车信号',{exact:true}).uncheck()
      await page.waitForFunction(()=>JSON.parse(document.querySelector('.element-stage').dataset.building).access===0,{},{timeout:15000})
      assert(await page.getByText('停车信号',{exact:true}).isVisible())
    }
    if (id==='castle-gate') {
      await page.getByLabel('开启通道',{ exact:true }).check()
      await page.waitForFunction(() => JSON.parse(document.querySelector('.element-stage').dataset.building).access===1,{},{ timeout:15000 })
      await page.getByRole('button',{ name:'暂停动画',exact:true }).click()
      await page.waitForTimeout(200)
      const open=await pixels()
      assert(open.framed && open.hash!==mobile.hash,'Gate did not open or bridge clipped on mobile')
      await shot('castle-gate-open-mobile',true)
      await page.setViewportSize({ width:1440,height:1000 })
      await page.waitForTimeout(200)
      assert((await pixels()).framed,'Open bridge clipped on desktop')
      await shot('castle-gate-open')
      await page.getByLabel('开启通道',{ exact:true }).uncheck()
      await page.waitForFunction(() => JSON.parse(document.querySelector('.element-stage').dataset.building).access===0,{},{ timeout:15000 })
      assert(await page.getByText('已关闭',{ exact:true }).isVisible())
    }
    results.push({ id,stages,upgraded,mobile,drawCalls })
    console.log(`BUILDING_VERIFIED ${id}`)
  }
  assert.deepEqual(errors,[])
  await writeFile(`${output}/${requested.length?'verification-selected':'verification'}.json`,JSON.stringify({ results,errors,writeRetries },null,2)+'\n')
  console.log(JSON.stringify({ models:results.length,errors,writeRetries }))
} finally { await browser.close() }
