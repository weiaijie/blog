import { chromium } from 'playwright'
import { mkdir, writeFile } from 'node:fs/promises'
import assert from 'node:assert/strict'

const output='artifacts/map-elements/routes'
await mkdir(output,{recursive:true})
const browser=await chromium.launch(),page=await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:'no-preference'})
const errors=[],results=[],retries=[]
page.on('pageerror',(e)=>errors.push(e.message));page.on('console',(m)=>{if(m.type()==='error')errors.push(m.text())})
async function pixels(){return page.locator('.element-stage canvas').evaluate((c)=>{
  const gl=c.getContext('webgl2'),w=gl.drawingBufferWidth,h=gl.drawingBufferHeight,b=new Uint8Array(w*h*4)
  gl.readPixels(0,0,w,h,gl.RGBA,gl.UNSIGNED_BYTE,b)
  let hash=2166136261,n=0,minX=w,maxX=0,minY=h,maxY=0
  for(let i=0;i<b.length;i+=16){hash=Math.imul(hash^b[i],16777619)>>>0;if(Math.abs(b[i]-b[0])+Math.abs(b[i+1]-b[1])+Math.abs(b[i+2]-b[2])>35){n++;const x=i/4%w,y=Math.floor(i/4/w);minX=Math.min(minX,x);maxX=Math.max(maxX,x);minY=Math.min(minY,y);maxY=Math.max(maxY,y)}}
  return {hash,coverage:n/(w*h/4),bounds:[minX,minY,maxX,maxY],w,h}
})}
function framed(p){assert(p.coverage>.007&&p.bounds[0]>0&&p.bounds[1]>0&&p.bounds[2]<p.w-1&&p.bounds[3]<p.h-1,`Blank or clipped canvas: ${JSON.stringify(p)}`)}
async function state(){return JSON.parse(await page.locator('.element-stage').getAttribute('data-route'))}
async function settle(progress){await page.waitForFunction((p)=>Math.abs(JSON.parse(document.querySelector('.element-stage').dataset.route).progress-p)<.0001,progress)}
async function shot(name){const bytes=await page.screenshot({fullPage:true});for(let i=0;;i++)try{await writeFile(`${output}/${name}.png`,bytes);return}catch(e){if(i>=3||!['UNKNOWN','EBUSY','EPERM'].includes(e.code))throw e;retries.push({name,code:e.code,attempt:i+1});await page.waitForTimeout(400*(i+1))}}
try{
  for(const id of ['dirt-road','stone-road','asphalt-road','rail-track']){
    await page.setViewportSize({width:1440,height:1000})
    await page.goto(`${process.env.ELEMENT_PREVIEW_URL||'http://127.0.0.1:5173'}/?view=map-elements&element=${id}`)
    await page.waitForSelector(`.element-stage[data-asset="${id}"][data-loaded="true"][data-route]`)
    assert.equal(await page.getByLabel('物候阶段',{exact:true}).count(),0)
    await page.getByRole('button',{name:'暂停动画',exact:true}).click();await page.getByLabel('风力',{exact:true}).fill('0')
    const shapes=[]
    for(const label of ['直线','转弯',id==='rail-track'?'道岔':'三岔']){
      await page.getByRole('button',{name:label,exact:true}).click();await page.waitForTimeout(200)
      const pixel=await pixels();framed(pixel);await shot(`${id}-${label}`)
      const drawCalls=Number(await page.locator('.element-stage').getAttribute('data-draw-calls'));assert(drawCalls<450)
      shapes.push({label,...await state(),...pixel,drawCalls})
    }
    assert.equal(new Set(shapes.map((s)=>s.hash)).size,3)
    await page.getByLabel('邻接预览',{exact:true}).check();await page.waitForTimeout(400);const connected=await pixels();framed(connected);await shot(`${id}-connected`)
    connected.drawCalls=Number(await page.locator('.element-stage').getAttribute('data-draw-calls'))
    await page.getByRole('button',{name:'俯视',exact:true}).click();await page.waitForTimeout(200);framed(await pixels());await shot(`${id}-connected-top`)
    await page.getByRole('button',{name:'自由视角',exact:true}).click();await page.getByLabel('邻接预览',{exact:true}).uncheck()
    await page.getByRole('button',{name:'直线',exact:true}).click()
    const stages=[]
    for(const progress of [0,.2,.5,.8,1]){
      await page.getByLabel('铺设进度',{exact:true}).fill(String(progress*100));await settle(progress)
      const pixel=await pixels();framed(pixel);await shot(`${id}-stage-${progress*100}`);stages.push({progress,...pixel})
    }
    assert.equal(new Set(stages.map((s)=>s.hash)).size,5)
    await page.getByRole('button',{name:'播放动画',exact:true}).click();const calm=await pixels();await page.waitForTimeout(500);assert.equal((await pixels()).hash,calm.hash)
    await page.getByLabel('风力',{exact:true}).fill('100');await page.waitForTimeout(400);const wind=await pixels();await page.waitForTimeout(550);assert.notEqual((await pixels()).hash,wind.hash)
    await page.getByRole('button',{name:'暂停动画',exact:true}).click();await page.waitForTimeout(200);const paused=await pixels();await page.waitForTimeout(450);assert.equal((await pixels()).hash,paused.hash)
    await page.getByLabel('自动铺设',{exact:true}).check();await page.waitForTimeout(1300);const building=await state();assert(building.progress>0&&building.progress<.2)
    await page.getByRole('button',{name:'暂停动画',exact:true}).click();await page.waitForTimeout(150);const stopped=await state(),still=await pixels();await page.waitForTimeout(550);assert.deepEqual(await state(),stopped);assert.equal((await pixels()).hash,still.hash)
    await page.getByLabel('自动铺设',{exact:true}).uncheck();await page.getByLabel('铺设进度',{exact:true}).fill('100');await settle(1)
    if(id==='rail-track'){
      await page.getByRole('button',{name:'道岔',exact:true}).click();await page.getByLabel('风力',{exact:true}).fill('0')
      const straight=await pixels();await page.getByLabel('转入支线',{exact:true}).check();await page.waitForFunction(()=>JSON.parse(document.querySelector('.element-stage').dataset.route).switchPosition>.999)
      assert.deepEqual((await state()).ports,[0,2]);assert.notEqual((await pixels()).hash,straight.hash);await shot(`${id}-diverted`)
      await page.getByRole('button',{name:'暂停动画',exact:true}).click()
    }
    for(const label of ['正面','侧面','俯视']){await page.getByRole('button',{name:label,exact:true}).click();await page.waitForTimeout(200);framed(await pixels());await shot(`${id}-${label}`)}
    await page.getByRole('button',{name:'自由视角',exact:true}).click()
    for(const [width,height]of [[390,844],[320,720]]){
      await page.setViewportSize({width,height});await page.waitForTimeout(300);framed(await pixels());assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await shot(`${id}-mobile-${width}`)
      await page.getByLabel('邻接预览',{exact:true}).check();await page.waitForTimeout(200);framed(await pixels());await shot(`${id}-connected-mobile-${width}`)
      await page.getByLabel('邻接预览',{exact:true}).uncheck()
    }
    assert((await page.getByLabel('下载 GLB',{exact:true}).getAttribute('download')).includes(id));results.push({id,shapes,stages,connected})
  }
  await page.getByLabel('选择模型',{exact:true}).selectOption('farmer');await page.waitForSelector('.element-stage[data-asset="farmer"][data-loaded="true"][data-human]')
  assert.equal(await page.getByLabel('道路形态',{exact:true}).count(),0);assert.equal(await page.locator('.element-stage').getAttribute('data-route'),null)
  assert.deepEqual(errors,[]);await writeFile(`${output}/verification.json`,JSON.stringify({results,retries,errors},null,2)+'\n')
  console.log(JSON.stringify({models:results.length,retries,errors}))
}finally{await browser.close()}
