import { chromium } from 'playwright'
import { mkdir, writeFile } from 'node:fs/promises'
import assert from 'node:assert/strict'

const output='artifacts/map-elements/mounted'
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
async function state(){return JSON.parse(await page.locator('.element-stage').getAttribute('data-mounted'))}
async function shot(name){const bytes=await page.screenshot({fullPage:true});for(let i=0;;i++)try{await writeFile(`${output}/${name}.png`,bytes);return}catch(e){if(i>=3||!['UNKNOWN','EBUSY','EPERM'].includes(e.code))throw e;retries.push({name,code:e.code,attempt:i+1});await page.waitForTimeout(400*(i+1))}}
try{
  for(const id of ['rider','horse-cart']){
    await page.setViewportSize({width:1440,height:1000})
    await page.goto(`${process.env.ELEMENT_PREVIEW_URL||'http://127.0.0.1:5173'}/?view=map-elements&element=${id}`)
    await page.waitForSelector(`.element-stage[data-asset="${id}"][data-loaded="true"][data-mounted]`)
    assert.equal(await page.getByLabel('物候阶段',{exact:true}).count(),0);assert.equal(await page.getByLabel('成长阶段',{exact:true}).count(),0)
    const first=await pixels();framed(first);await page.waitForTimeout(450);assert.notEqual((await pixels()).hash,first.hash)
    await shot(`${id}-walking`)
    await page.getByRole('button',{name:'暂停动画',exact:true}).click();await page.waitForTimeout(200)
    const paused=await pixels(),ps=await state();await page.waitForTimeout(450);assert.equal((await pixels()).hash,paused.hash);assert.deepEqual(await state(),ps)
    await page.getByLabel('步行速度',{exact:true}).fill('0');await page.waitForTimeout(200)
    const zero=await pixels(),zs=await state();await page.waitForTimeout(400);assert.equal((await pixels()).hash,zero.hash);assert.deepEqual(await state(),zs)
    const distances=[]
    for(const speed of [35,140]){await page.getByLabel('步行速度',{exact:true}).fill(String(speed));await page.waitForTimeout(180);const start=(await state()).distance;await page.waitForTimeout(600);distances.push((await state()).distance-start)}
    assert(distances[1]>distances[0]*2);await page.getByLabel('步行速度',{exact:true}).fill('0');await page.waitForTimeout(200)
    if(id==='horse-cart'){
      const loaded=await pixels();await page.getByLabel('装载',{exact:true}).fill('0');await page.waitForTimeout(200);assert.equal((await state()).cargo,0);assert.notEqual((await pixels()).hash,loaded.hash);await shot(`${id}-empty`)
      await page.getByLabel('装载',{exact:true}).fill('4');await page.waitForTimeout(200);assert.equal((await state()).cargo,4)
    }
    const drawCalls=Number(await page.locator('.element-stage').getAttribute('data-draw-calls'));assert(drawCalls<110)
    for(const view of ['正面','侧面','俯视']){await page.getByRole('button',{name:view,exact:true}).click();await page.waitForTimeout(200);framed(await pixels());await shot(`${id}-${view}`)}
    await page.getByRole('button',{name:'自由视角',exact:true}).click()
    for(const [width,height]of [[390,844],[320,720]]){await page.setViewportSize({width,height});await page.waitForTimeout(250);framed(await pixels());assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await shot(`${id}-mobile-${width}`)}
    assert((await page.getByLabel('下载 GLB',{exact:true}).getAttribute('download')).includes(id));results.push({id,drawCalls,first,distances})
  }
  await page.getByLabel('选择模型',{exact:true}).selectOption('horse');await page.waitForSelector('.element-stage[data-asset="horse"][data-loaded="true"][data-animals]')
  assert.equal(await page.getByLabel('步行速度',{exact:true}).count(),0);assert.equal(await page.locator('.element-stage').getAttribute('data-mounted'),null)
  assert.equal(await page.getByLabel('成长阶段',{exact:true}).count(),1)
  assert.deepEqual(errors,[]);await writeFile(`${output}/verification.json`,JSON.stringify({results,retries,errors},null,2)+'\n');console.log(JSON.stringify({models:results.length,retries,errors}))
}finally{await browser.close()}
