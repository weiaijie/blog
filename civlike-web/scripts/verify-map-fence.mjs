import { chromium } from 'playwright'
import { mkdir, writeFile } from 'node:fs/promises'
import assert from 'node:assert/strict'

const output='artifacts/map-elements/fence'
await mkdir(output,{recursive:true})
const browser=await chromium.launch(),page=await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:'no-preference'})
const errors=[],stages=[],views=[],mobile=[]
page.on('pageerror',(e)=>errors.push(e.message))
page.on('console',(m)=>{if(m.type()==='error')errors.push(m.text())})
async function state(){return JSON.parse(await page.locator('.element-stage').getAttribute('data-building'))}
async function pixels(){return page.locator('.element-stage canvas').evaluate((c)=>{
  const gl=c.getContext('webgl2'),w=gl.drawingBufferWidth,h=gl.drawingBufferHeight,b=new Uint8Array(w*h*4)
  gl.readPixels(0,0,w,h,gl.RGBA,gl.UNSIGNED_BYTE,b)
  let hash=2166136261,n=0,minX=w,maxX=0,minY=h,maxY=0
  for(let i=0;i<b.length;i+=16){hash=Math.imul(hash^b[i],16777619)>>>0;if(Math.abs(b[i]-b[0])+Math.abs(b[i+1]-b[1])+Math.abs(b[i+2]-b[2])>35){n++;const x=i/4%w,y=Math.floor(i/4/w);minX=Math.min(minX,x);maxX=Math.max(maxX,x);minY=Math.min(minY,y);maxY=Math.max(maxY,y)}}
  return {hash,coverage:n/(w*h/4),framed:minX>0&&minY>0&&maxX<w-1&&maxY<h-1}
})}
async function shot(name){const image=await page.screenshot({fullPage:true});await writeFile(`${output}/${name}.png`,image)}
async function settle(value){await page.waitForFunction((v)=>Math.abs(JSON.parse(document.querySelector('.element-stage').dataset.building).progress-v)<.00001,value)}
async function access(value){await page.waitForFunction((v)=>Math.abs(JSON.parse(document.querySelector('.element-stage').dataset.building).access-v)<.00001,value)}
function framed(p,minimum=.002){assert(p.coverage>minimum&&p.framed,`Blank or clipped model: ${JSON.stringify(p)}`)}
try {
  await page.goto(`${process.env.ELEMENT_PREVIEW_URL||'http://127.0.0.1:5173'}/?view=map-elements&element=fence`)
  await page.waitForSelector('.element-stage[data-asset="fence"][data-loaded="true"][data-building]')
  await page.getByRole('button',{name:'暂停动画',exact:true}).click()
  for(const progress of [0,30,52,78,100]) {
    await page.getByLabel('施工进度',{exact:true}).fill(String(progress));await settle(progress/100)
    const p=await pixels();await shot(`stage-${progress}`);framed(p,progress===0 ? .001 : .002);stages.push({progress,...p,...await state()})
  }
  assert.equal(new Set(stages.map((s)=>s.hash)).size,5)
  await page.getByLabel('升级附件',{exact:true}).check();await page.waitForTimeout(200)
  assert.notEqual((await pixels()).hash,stages.at(-1).hash);await shot('upgraded-closed')
  await page.getByLabel('开启通道',{exact:true}).check();await page.waitForTimeout(250)
  const moving=await pixels();await page.waitForTimeout(250);assert.notEqual((await pixels()).hash,moving.hash)
  await page.getByRole('button',{name:'暂停动画',exact:true}).click();await page.waitForTimeout(150)
  const stopped=await pixels(),paused=await state();await page.waitForTimeout(350)
  assert.equal((await pixels()).hash,stopped.hash);assert.deepEqual(await state(),paused)
  await page.getByRole('button',{name:'播放动画',exact:true}).click();await access(1)
  await shot('open-desktop')
  for(const view of ['正面','侧面','俯视']) {
    await page.getByRole('button',{name:view,exact:true}).click();await page.waitForTimeout(250)
    const p=await pixels();framed(p);views.push({view,...p});await shot(view)
  }
  await page.getByRole('button',{name:'自由视角',exact:true}).click()
  await page.getByLabel('开启通道',{exact:true}).uncheck();await access(0)
  await page.getByLabel('功能运行',{exact:true}).uncheck();assert(await page.getByLabel('开启通道',{exact:true}).isDisabled())
  await page.getByLabel('功能运行',{exact:true}).check()
  await page.getByLabel('运行速度',{exact:true}).fill('0')
  await page.getByLabel('开启通道',{exact:true}).check();await page.waitForTimeout(400);assert.equal((await state()).access,0)
  await page.getByLabel('运行速度',{exact:true}).fill('100');await access(1)
  const drawCalls=Number(await page.locator('.element-stage').getAttribute('data-draw-calls'));assert(drawCalls<120)
  for(const [width,height]of [[390,844],[320,720]]) {
    await page.setViewportSize({width,height});await page.waitForTimeout(300)
    const p=await pixels();framed(p);assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth))
    mobile.push({width,...p});await shot(`mobile-${width}`)
  }
  await page.getByLabel('自动施工',{exact:true}).check();await page.waitForTimeout(600)
  await page.getByRole('button',{name:'暂停动画',exact:true}).click();await page.waitForTimeout(150)
  const construction=await state();await page.waitForTimeout(350);assert.deepEqual(await state(),construction)
  assert((await page.getByLabel('下载 GLB',{exact:true}).getAttribute('download')).includes('fence'))
  await page.getByLabel('选择模型',{exact:true}).selectOption('wheat-field')
  await page.waitForSelector('.element-stage[data-asset="wheat-field-v3"][data-loaded="true"]')
  assert.equal(await page.getByLabel('开启通道',{exact:true}).count(),0)
  assert.deepEqual(errors,[])
  await writeFile(`${output}/verification.json`,JSON.stringify({stages,views,mobile,drawCalls,errors},null,2)+'\n')
  console.log(JSON.stringify({stages:stages.length,views:views.length,mobile:mobile.length,drawCalls,errors}))
} finally {await browser.close()}
