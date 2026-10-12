import { chromium } from 'playwright'
import { mkdir, writeFile } from 'node:fs/promises'
import assert from 'node:assert/strict'

const output='artifacts/map-elements/transport'
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
function framed(p){assert(p.coverage>.005&&p.bounds[0]>0&&p.bounds[1]>0&&p.bounds[2]<p.w-1&&p.bounds[3]<p.h-1,`Blank or clipped: ${JSON.stringify(p)}`)}
async function state(){return JSON.parse(await page.locator('.element-stage').getAttribute('data-transport'))}
async function shot(name){const bytes=await page.screenshot({fullPage:true});for(let i=0;;i++)try{await writeFile(`${output}/${name}.png`,bytes);return}catch(e){if(i>=3||!['UNKNOWN','EBUSY','EPERM'].includes(e.code))throw e;retries.push({name,code:e.code,attempt:i+1});await page.waitForTimeout(400*(i+1))}}
try{
  for(const id of ['rickshaw','bicycle','early-car','freight-wagon']){
    await page.setViewportSize({width:1440,height:1000})
    await page.goto(`${process.env.ELEMENT_PREVIEW_URL||'http://127.0.0.1:5173'}/?view=map-elements&element=${id}`)
    await page.waitForSelector(`.element-stage[data-asset="${id}"][data-loaded="true"][data-transport]`)
    assert.equal(await page.getByLabel('物候阶段',{exact:true}).count(),0)
    const first=await pixels();framed(first);await page.waitForTimeout(550);assert.notEqual((await pixels()).hash,first.hash)
    await page.getByRole('button',{name:'暂停动画',exact:true}).click();await page.waitForTimeout(150)
    const paused=await pixels(),ps=await state();await page.waitForTimeout(500);assert.equal((await pixels()).hash,paused.hash);assert.deepEqual(await state(),ps)
    await shot(`${id}-default`)
    await page.getByLabel('轮速',{exact:true}).fill('0');await page.waitForTimeout(200)
    const zero=await pixels();await page.waitForTimeout(500);assert.equal((await pixels()).hash,zero.hash)
    await page.getByLabel('轮速',{exact:true}).fill('-70');const before=(await state()).distance;await page.waitForTimeout(700);assert((await state()).distance<before)
    await page.getByLabel('轮速',{exact:true}).fill('0')
    if(['bicycle','early-car'].includes(id)){
      const straight=await pixels();await page.getByLabel('转向',{exact:true}).fill('24');await page.waitForTimeout(1300);assert((await state()).steering>.40);assert.notEqual((await pixels()).hash,straight.hash);await shot(`${id}-steering`)
      await page.getByLabel('转向',{exact:true}).fill('0');await page.waitForTimeout(1400)
    }
    const access={rickshaw:'收起车篷','early-car':'打开车门','freight-wagon':'放下侧板'}[id]
    if(access){
      const closed=await pixels();await page.getByLabel(access,{exact:true}).check();await page.waitForTimeout(180);await shot(`${id}-opening`)
      await page.getByRole('button',{name:'暂停动画',exact:true}).click();await page.waitForTimeout(180);const mid=await state(),still=await pixels();assert(mid.access>0&&mid.access<.99);await page.waitForTimeout(400);assert.deepEqual(await state(),mid);assert.equal((await pixels()).hash,still.hash)
      await page.getByRole('button',{name:'播放动画',exact:true}).click();await page.waitForFunction(()=>JSON.parse(document.querySelector('.element-stage').dataset.transport).access>.9999)
      const opened=await pixels();framed(opened);assert.notEqual(opened.hash,closed.hash);await shot(`${id}-open`)
      await page.getByLabel('轮速',{exact:true}).fill('70');assert.equal(await page.getByLabel(access,{exact:true}).isChecked(),false)
      await page.waitForFunction(()=>JSON.parse(document.querySelector('.element-stage').dataset.transport).access<.001)
      await page.getByLabel('轮速',{exact:true}).fill('0');await page.waitForTimeout(500)
    }
    if(['early-car','freight-wagon'].includes(id)){
      const loaded=await pixels();await page.getByLabel('装载',{exact:true}).fill('0');await page.waitForTimeout(200);assert.equal((await state()).cargo,0);assert.notEqual((await pixels()).hash,loaded.hash);await shot(`${id}-empty`)
      await page.getByLabel('装载',{exact:true}).fill(id==='freight-wagon'?'6':'1');await page.waitForTimeout(200)
    }
    await page.getByRole('button',{name:'暂停动画',exact:true}).click();await page.waitForTimeout(150)
    const drawCalls=Number(await page.locator('.element-stage').getAttribute('data-draw-calls'));assert(drawCalls<100)
    for(const view of ['正面','侧面','俯视']){await page.getByRole('button',{name:view,exact:true}).click();await page.waitForTimeout(200);framed(await pixels());await shot(`${id}-${view}`)}
    await page.getByRole('button',{name:'自由视角',exact:true}).click()
    for(const [width,height]of [[390,844],[320,720]]){await page.setViewportSize({width,height});await page.waitForTimeout(200);framed(await pixels());assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await shot(`${id}-mobile-${width}`)}
    assert((await page.getByLabel('下载 GLB',{exact:true}).getAttribute('download')).includes(id));results.push({id,drawCalls,first})
  }
  await page.getByLabel('选择模型',{exact:true}).selectOption('rail-track');await page.waitForSelector('.element-stage[data-asset="rail-track"][data-loaded="true"][data-route]')
  assert.equal(await page.getByLabel('轮速',{exact:true}).count(),0);assert.equal(await page.locator('.element-stage').getAttribute('data-transport'),null)
  assert.deepEqual(errors,[]);await writeFile(`${output}/verification.json`,JSON.stringify({results,retries,errors},null,2)+'\n');console.log(JSON.stringify({models:results.length,retries,errors}))
}finally{await browser.close()}
