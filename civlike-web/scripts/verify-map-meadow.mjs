import { chromium } from 'playwright'
import { mkdir, writeFile } from 'node:fs/promises'
import assert from 'node:assert/strict'

const out='artifacts/map-elements/meadow'
await mkdir(out,{recursive:true})
const browser=await chromium.launch()
const page=await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:'no-preference'})
const errors=[],results=[]
page.on('pageerror',(e)=>errors.push(e.message))
page.on('console',(m)=>{if(m.type()==='error')errors.push(m.text())})
async function pixel() {
  return page.locator('.element-stage canvas').evaluate((canvas)=>{
    const gl=canvas.getContext('webgl2'),w=gl.drawingBufferWidth,h=gl.drawingBufferHeight,b=new Uint8Array(w*h*4)
    gl.readPixels(0,0,w,h,gl.RGBA,gl.UNSIGNED_BYTE,b)
    let hash=2166136261,n=0,minX=w,maxX=0,minY=h,maxY=0
    for(let i=0;i<b.length;i+=16){hash=Math.imul(hash^b[i],16777619)>>>0;if(Math.abs(b[i]-b[0])+Math.abs(b[i+1]-b[1])+Math.abs(b[i+2]-b[2])>35){n++;const x=i/4%w,y=Math.floor(i/4/w);minX=Math.min(minX,x);maxX=Math.max(maxX,x);minY=Math.min(minY,y);maxY=Math.max(maxY,y)}}
    return {hash,coverage:n/(w*h/4),bounds:[minX,minY,maxX,maxY],w,h}
  })
}
async function shot(name) {
  const bytes=await page.screenshot({fullPage:true})
  for(let attempt=0;;attempt++) {
    try {await writeFile(`${out}/${name}.png`,bytes);return}
    catch(error){if(attempt>=3||!['UNKNOWN','EBUSY','EPERM'].includes(error.code))throw error;console.log('SCREENSHOT_RETRY',name,error.code,attempt+1);await page.waitForTimeout(400*(attempt+1))}
  }
}
async function growth(value) {
  await page.getByLabel('生长阶段',{exact:true}).fill(String(value))
  await page.waitForFunction((p)=>Math.abs(Number(document.querySelector('.element-stage').dataset.growth)-p)<.0002,value/100)
  await page.waitForTimeout(150)
}
function framed(p) {
  assert(p.coverage>.007 && p.bounds[0]>0 && p.bounds[1]>0 && p.bounds[2]<p.w-1 && p.bounds[3]<p.h-1,'Blank/clipped canvas')
}
try {
  for(const id of ['bamboo','wildflowers','potato-field']) {
    await page.setViewportSize({width:1440,height:1000})
    await page.goto(`${process.env.ELEMENT_PREVIEW_URL||'http://127.0.0.1:5173'}/?view=map-elements&element=${id}`)
    await page.waitForSelector('.element-stage[data-loaded="true"][data-organs]')
    await page.getByRole('button',{name:'暂停动画',exact:true}).click()
    const states=[]
    for(const value of [5,25,49,82,100]){
      await growth(value);const p=await pixel();framed(p);states.push({value,...p});await shot(`${id}-${value}`)
    }
    assert.equal(new Set(states.map(s=>s.hash)).size,5,`${id}: repeated stages`)
    await growth(id==='wildflowers'?49:82)
    if(id==='potato-field') {
      const surface=await pixel()
      await page.getByRole('button',{name:'土层剖面',exact:true}).click()
      assert.equal(await page.locator('.element-stage').getAttribute('data-cutaway'),'true')
      await page.waitForTimeout(200)
      const section=await pixel();framed(section);assert.notEqual(section.hash,surface.hash)
      await shot('potato-section-mature')
      await growth(49);const young=await pixel();assert.notEqual(young.hash,section.hash);await shot('potato-section-forming')
      await growth(82)
      await page.getByRole('button',{name:'土层剖面',exact:true}).click();await page.waitForTimeout(200)
      assert.equal((await pixel()).hash,surface.hash,'Cutaway failed to restore intact soil')
      await page.getByRole('button',{name:'土层剖面',exact:true}).click()
    }
    await page.getByRole('button',{name:'播放动画',exact:true}).click()
    const start=await pixel();await page.waitForTimeout(800);assert.notEqual((await pixel()).hash,start.hash,`${id}: no wind motion`)
    await page.getByRole('button',{name:'暂停动画',exact:true}).click();await page.waitForTimeout(200)
    const still=await pixel();await page.waitForTimeout(500);assert.equal((await pixel()).hash,still.hash,`${id}: pause failed`)
    for(const view of ['正面','侧面','俯视']) {
      await page.getByRole('button',{name:view,exact:true}).click();await page.waitForTimeout(250);framed(await pixel());await shot(`${id}-${view}`)
    }
    await page.getByRole('button',{name:'自由视角',exact:true}).click()
    await page.setViewportSize({width:390,height:844});await page.waitForTimeout(350);framed(await pixel())
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Mobile overflow')
    await shot(`${id}-mobile`)
    await page.setViewportSize({width:320,height:720});await page.waitForTimeout(250);framed(await pixel())
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Narrow mobile overflow')
    await shot(`${id}-mobile-320`)
    results.push({id,states,drawCalls:Number(await page.locator('.element-stage').getAttribute('data-draw-calls'))})
  }
  await page.getByLabel('选择模型',{exact:true}).selectOption('bamboo')
  await page.waitForSelector('.element-stage[data-asset="bamboo"][data-loaded="true"]')
  assert.equal(await page.getByRole('button',{name:'土层剖面',exact:true}).count(),0)
  await page.getByLabel('选择模型',{exact:true}).selectOption('potato-field')
  await page.waitForSelector('.element-stage[data-asset="potato-field"][data-loaded="true"]')
  assert.equal(await page.locator('.element-stage').getAttribute('data-cutaway'),'false','Cutaway leaked across model switching')
  await growth(5)
  await page.getByLabel('自动生长',{exact:true}).check()
  await page.waitForFunction(()=>Number(document.querySelector('.element-stage').dataset.growth)>.10)
  await page.getByRole('button',{name:'暂停动画',exact:true}).click()
  const growthPaused=await page.locator('.element-stage').getAttribute('data-growth')
  await page.waitForTimeout(800)
  assert.equal(await page.locator('.element-stage').getAttribute('data-growth'),growthPaused,'Automatic growth did not pause')
  assert.deepEqual(errors,[])
  await writeFile(`${out}/verification.json`,JSON.stringify({results,errors},null,2)+'\n')
  console.log(JSON.stringify({models:results.length,errors}))
} finally {await browser.close()}
