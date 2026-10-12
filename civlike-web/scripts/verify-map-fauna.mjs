import { chromium } from 'playwright'
import { mkdir, writeFile } from 'node:fs/promises'
import assert from 'node:assert/strict'

const output='artifacts/map-elements/fauna'
await mkdir(output,{ recursive:true })
const browser=await chromium.launch()
const page=await browser.newPage({ viewport:{ width:1440,height:1000 },reducedMotion:'no-preference' })
const errors=[],results=[],writeRetries=[]
page.on('pageerror',(error) => errors.push(error.message))
page.on('console',(message) => { if (message.type()==='error') errors.push(message.text()) })
async function snapshot(name,fullPage=false) {
  const bytes=await page.screenshot({ fullPage })
  for (let attempt=0;;attempt++) {
    try { await writeFile(`${output}/${name}.png`,bytes); return }
    catch(error) {
      if (attempt>=3 || !['UNKNOWN','EBUSY','EPERM'].includes(error.code)) throw error
      writeRetries.push({ name,code:error.code })
      await page.waitForTimeout(400*(attempt+1))
    }
  }
}
async function state() { return JSON.parse(await page.locator('.element-stage').getAttribute('data-animals')) }
async function pixels() {
  return page.locator('.element-stage canvas').evaluate((canvas) => {
    const gl=canvas.getContext('webgl2'),w=gl.drawingBufferWidth,h=gl.drawingBufferHeight
    const data=new Uint8Array(w*h*4)
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
  for(const id of ['sheep-v5','cow','horse','chicken','goat','pig','duck','deer']) {
    await page.setViewportSize({ width:1440,height:1000 })
    await page.goto(`http://127.0.0.1:5173/?view=map-elements&element=${id}`)
    await page.waitForSelector('.element-stage[data-loaded="true"][data-animals]')
    await page.getByRole('button',{ name:'暂停动画',exact:true }).click()
    await page.getByLabel('成长阶段',{ exact:true }).fill('0')
    await page.waitForTimeout(1700)
    const young=await pixels()
    assert(young.coverage>.007 && young.framed,`${id}: juvenile blank/clipped`)
    assert(await page.getByLabel('繁育预览',{ exact:true }).isDisabled(),`${id}: juvenile breeding enabled`)
    await snapshot(`${id}-young`)
    await page.getByLabel('成长阶段',{ exact:true }).fill('100')
    await page.waitForTimeout(1700)
    const adult=await pixels()
    assert(adult.coverage>young.coverage*1.2 && adult.framed,`${id}: adult proportions/framing`)
    await snapshot(`${id}-adult`)
    for(const view of ['正面','侧面','俯视']) {
      await page.getByRole('button',{ name:view,exact:true }).click()
      await page.waitForTimeout(200)
      const p=await pixels()
      assert(p.coverage>.007 && p.framed,`${id}: ${view} framing`)
      await snapshot(`${id}-${view}`)
    }
    await page.getByRole('button',{ name:'自由视角',exact:true }).click()
    await page.getByRole('button',{ name:'行走',exact:true }).click()
    await page.getByRole('button',{ name:'播放动画',exact:true }).click()
    const walking=await pixels()
    await page.waitForTimeout(380)
    assert.notEqual((await pixels()).hash,walking.hash,`${id}: walk static`)
    await snapshot(`${id}-walk`)
    await page.getByRole('button',{ name:id==='chicken' ? '啄食' : '采食',exact:true }).click()
    await page.waitForTimeout(300)
    await snapshot(`${id}-feed`)
    await page.getByRole('button',{ name:'休息',exact:true }).click()
    await page.getByLabel('繁育预览',{ exact:true }).check()
    await page.waitForFunction(() => JSON.parse(document.querySelector('.element-stage').dataset.animals).breedingProgress>.08)
    await page.getByRole('button',{ name:'暂停动画',exact:true }).click()
    const waiting=await state(),still=await pixels()
    await snapshot(`${id}-waiting`)
    await page.waitForTimeout(300)
    assert.deepEqual(await state(),waiting,`${id}: breeding did not pause`)
    assert.equal((await pixels()).hash,still.hash,`${id}: pose did not pause`)
    await page.getByRole('button',{ name:'播放动画',exact:true }).click()
    await page.waitForFunction(() => JSON.parse(document.querySelector('.element-stage').dataset.animals).offspring>0,{},{ timeout:30000 })
    assert.equal((await state()).offspring,['chicken','duck'].includes(id) ? 3 : 1)
    await page.getByRole('button',{ name:'暂停动画',exact:true }).click()
    const family=await pixels()
    assert(family.coverage>.007 && family.framed,`${id}: family blank/clipped`)
    const drawCalls=Number(await page.locator('.element-stage').getAttribute('data-draw-calls'))
    assert(drawCalls<450,`${id}: family draw-call budget`)
    await snapshot(`${id}-family`)
    if (id==='chicken' || id==='duck') {
      await page.getByRole('button',{ name:'播放动画',exact:true }).click()
      await page.waitForFunction(() => JSON.parse(document.querySelector('.element-stage').dataset.animals).offspringAge>=.99,{},{ timeout:80000 })
      await page.getByRole('button',{ name:'暂停动画',exact:true }).click()
      assert.equal((await state()).offspring,3,'Growing offspring multiplied')
      assert((await pixels()).framed,'Adult offspring family clipped')
      await snapshot(`${id}-grown-family`)
    }
    await page.setViewportSize({ width:390,height:844 })
    await page.waitForTimeout(250)
    const mobile=await pixels()
    assert(mobile.coverage>.007 && mobile.framed,`${id}: mobile family clipped`)
    assert(await page.evaluate(() => document.documentElement.scrollWidth<=innerWidth),`${id}: mobile overflow`)
    await snapshot(`${id}-mobile`,true)
    await page.getByLabel('繁育预览',{ exact:true }).uncheck()
    await page.waitForTimeout(300)
    assert.equal((await state()).offspring,0)
    results.push({ id,young,adult,family,mobile,drawCalls })
  }
  assert.deepEqual(errors,[])
  await writeFile(`${output}/verification.json`,JSON.stringify({ results,errors,writeRetries },null,2)+'\n')
  console.log(JSON.stringify({ models:results.length,errors,writeRetries }))
} finally { await browser.close() }
