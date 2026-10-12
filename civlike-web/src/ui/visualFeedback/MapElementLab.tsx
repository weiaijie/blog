import { useEffect, useRef, useState } from 'react'
import { Box, Download, Layers2, ListChecks, Pause, Play, RotateCcw, Shuffle, Sprout, X } from 'lucide-react'
import { elementVersionLabel, initialMapElement, mapElementLibrary, mapElements, type MapElement } from '../../render/assets/mapElementCatalog'
import { mountMapElement, type ElementScene, type ElementView } from '../../render/visuals/mapElementScene'
import { defaultFieldSettings, type FieldSettings } from '../../render/visuals/mapElementGrowth'
import { botanicalStage } from '../../render/visuals/mapElementLifecycle'
import { mapElementCategories, mapElementRoadmap } from '../../render/assets/mapElementRoadmap'
import { defaultAnimalSettings, type AnimalSettings, type AnimalState } from '../../render/visuals/mapElementAnimals'
import { buildingStage, defaultBuildingSettings, type BuildingSettings, type BuildingState } from '../../render/visuals/mapElementBuildings'
import { aridTerrains, defaultTerrainSettings, terrainSeasons, terrainSnow, type TerrainSettings, type TerrainState } from '../../render/visuals/mapElementTerrain'
import './mapElementLab.css'

const views: [ElementView, string][] = [['perspective', '自由视角'], ['front', '正面'], ['side', '侧面'], ['top', '俯视']]

export function MapElementLab() {
  const [selected, setSelected] = useState(() => initialMapElement(location.search))
  const [view, setView] = useState<ElementView>('perspective')
  const roadmap = useRef<HTMLDialogElement>(null)
  useEffect(() => {
    const onPopState = () => setSelected(initialMapElement(location.search))
    window.addEventListener('popstate', onPopState)
    return () => window.removeEventListener('popstate', onPopState)
  }, [])
  function select(asset: MapElement) {
    setSelected(asset)
    const url = new URL(location.href)
    url.searchParams.set('element', asset.family)
    url.searchParams.set('revision', String(asset.revision))
    history.replaceState(null, '', url)
  }
  return <main className="element-lab">
    <header className="element-header"><h1>地图模型库</h1><span>{mapElementLibrary.length} / {mapElementRoadmap.length} 项已建模</span><button className="element-roadmap-toggle" title="资产进度" aria-label="资产进度" onClick={() => roadmap.current?.showModal()}><ListChecks size={18} /></button><a href="?view=terrain-world">返回地图</a></header>
    <nav className="element-library" aria-label="模型列表">
      <select aria-label="选择模型" value={selected.family} onChange={(event) => select(mapElementLibrary.find((a) => a.family === event.target.value)!)}>
        {mapElementLibrary.map((asset) => <option key={asset.family} value={asset.family}>{asset.label}{asset.revision > 1 ? ` · ${elementVersionLabel(asset.revision)}` : ''}</option>)}
      </select>
      <div className="element-list">{mapElementLibrary.map((asset) => <button key={asset.family} aria-pressed={selected.family === asset.family} onClick={() => select(asset)}><span>{asset.label}</span><small>{asset.terrain ? aridTerrains.has(asset.family) ? '动态' : '季相' : asset.building ? '施工' : asset.animal ? '成长' : asset.lifecycle ? '物候' : asset.revision > 1 ? '已更新' : asset.category}</small></button>)}</div>
      <p>{mapElementLibrary.length} 类模型 · {mapElements.length} 个版本</p>
    </nav>
    <ElementPreview key={selected.id} asset={selected} select={select} view={view} setView={setView} />
    <dialog ref={roadmap} className="element-roadmap" aria-labelledby="roadmap-title">
      <header><h2 id="roadmap-title">资产进度</h2><span>{mapElementLibrary.length} / {mapElementRoadmap.length} 已建模</span><button title="关闭" aria-label="关闭资产进度" onClick={() => roadmap.current?.close()}><X size={20} /></button></header>
      <div className="element-roadmap-body">{mapElementCategories.map((category) => <section key={category}><h3>{category}</h3><ul>{mapElementRoadmap.filter((item) => item.category === category).map((item) => {
        const asset = mapElementLibrary.find((candidate) => candidate.family === item.id)
        return <li key={item.id}><button disabled={!asset} onClick={() => { if (asset) select(asset); roadmap.current?.close() }}>{item.label}</button><small>{!asset ? '待制作' : asset.terrain ? aridTerrains.has(asset.family) ? '地貌动态' : '季相样板' : asset.building ? '施工样板' : asset.animal ? '成长样板' : asset.lifecycle ? '物候样板' : asset.revision >= 3 ? '自然动态' : '基础模型 · 待细化'}</small></li>
      })}</ul></section>)}</div>
    </dialog>
  </main>
}

function ElementPreview({ asset, select, view, setView }: {
  asset: MapElement; select: (asset: MapElement) => void
  view: ElementView; setView: (view: ElementView) => void
}) {
  const versions = mapElements.filter((candidate) => candidate.family === asset.family)
  const living = !asset.animal && !asset.building && !asset.terrain && (asset.revision >= 3 || asset.lifecycle)
  const growing = living && asset.family !== 'plowed-field'
  const host = useRef<HTMLDivElement>(null)
  const scene = useRef<ElementScene>()
  const [playing, setPlaying] = useState(!window.matchMedia('(prefers-reduced-motion: reduce)').matches)
  const [wireframe, setWireframe] = useState(false)
  const [cutaway, setCutaway] = useState(false)
  const [status, setStatus] = useState('加载中')
  const [hasAnimation, setHasAnimation] = useState(false)
  const initialGrowth = asset.family==='cotton-field' ? .96 : ['lily-pad','wildflowers'].includes(asset.family) ? .49 : defaultFieldSettings.growth
  const [settings, setSettings] = useState<FieldSettings>({ ...defaultFieldSettings,growth:initialGrowth })
  const [progress, setProgress] = useState(initialGrowth)
  const [animalSettings, setAnimalSettings] = useState<AnimalSettings>({ ...defaultAnimalSettings })
  const [animalState, setAnimalState] = useState<AnimalState>({ age:1,offspring:0,offspringAge:0,breedingProgress:0,breedingState:'single' })
  const [buildingSettings, setBuildingSettings] = useState<BuildingSettings>({ ...defaultBuildingSettings })
  const [buildingState, setBuildingState] = useState<BuildingState>({ progress:1,visible:0,operating:true,tier:1,access:0 })
  const [terrainSettings,setTerrainSettings]=useState<TerrainSettings>(()=>defaultTerrainSettings(asset.family))
  const [terrainState,setTerrainState]=useState<TerrainState>(()=>defaultTerrainSettings(asset.family))
  const stage = asset.lifecycle ? botanicalStage(progress, asset.family) : progress < .08 ? '播种' : progress < .32 ? '幼苗' : progress < .62 ? '生长' : progress < .92 ? (asset.family === 'wheat-field' ? '抽穗' : '结球') : '成熟'
  function updateField(patch: Partial<FieldSettings>) {
    setSettings((previous) => ({ ...previous, growth: previous.automatic ? progress : previous.growth, ...patch }))
  }
  function updateAnimal(patch: Partial<AnimalSettings>) {
    setAnimalSettings((previous) => {
      const next = { ...previous,age:previous.automatic ? animalState.age : previous.age,...patch }
      if (next.age<.72) next.family=false
      return next
    })
  }
  function updateBuilding(patch: Partial<BuildingSettings>) {
    setBuildingSettings((previous) => ({ ...previous,progress:previous.automatic ? buildingState.progress : previous.progress,...patch }))
  }
  function updateTerrain(patch:Partial<TerrainSettings>) {
    setTerrainSettings((previous)=>({...previous,...(previous.automatic ? terrainState : {}),...patch}))
  }
  useEffect(() => {
    if (!host.current) return
    const handle = mountMapElement(host.current, asset.url, (count) => {
      setStatus('已加载'); setHasAnimation(count > 0)
    }, (message) => setStatus(`加载失败：${message}`), setProgress, setAnimalState, setBuildingState, setTerrainState)
    scene.current = handle
    return () => { scene.current = undefined; handle.destroy() }
  }, [asset.url])
  useEffect(() => { scene.current?.setView(view) }, [view])
  useEffect(() => { scene.current?.setFieldSettings(settings) }, [settings])
  useEffect(() => { scene.current?.setAnimalSettings(animalSettings) }, [animalSettings])
  useEffect(() => { scene.current?.setBuildingSettings(buildingSettings) }, [buildingSettings])
  useEffect(() => { scene.current?.setTerrainSettings(terrainSettings) }, [terrainSettings])
  return <section className={`element-workspace${living || asset.animal || asset.building || asset.terrain ? ' element-workspace-living' : ''}`} aria-label={asset.label}>
    <div className="element-toolbar">
      <div className="element-views" role="group" aria-label="相机视角">{views.map(([id, label]) => <button key={id} aria-pressed={view === id} onClick={() => { setView(id); scene.current?.setView(id) }}>{label}</button>)}</div>
      <div className="element-tools">
        <button title={playing ? '暂停动画' : '播放动画'} aria-label={playing ? '暂停动画' : '播放动画'} disabled={!hasAnimation} onClick={() => { setPlaying(!playing); scene.current?.setPlaying(!playing) }}>{playing ? <Pause size={18} /> : <Play size={18} />}</button>
        <button title="线框" aria-label="线框" aria-pressed={wireframe} onClick={() => { setWireframe(!wireframe); scene.current?.setWireframe(!wireframe) }}><Box size={18} /></button>
        {asset.family==='potato-field' && <button title="土层剖面" aria-label="土层剖面" aria-pressed={cutaway} onClick={() => { setCutaway(!cutaway); scene.current?.setCutaway(!cutaway) }}><Layers2 size={18} /></button>}
        <button title="重置视角" aria-label="重置视角" onClick={() => scene.current?.setView(view)}><RotateCcw size={18} /></button>
        <a href={asset.url} download={`${asset.id}.glb`} title="下载 GLB" aria-label="下载 GLB"><Download size={18} /></a>
      </div>
    </div>
    <div className="element-stage" ref={host} data-asset={asset.id} />
    {status !== '已加载' && <div className="element-load-status" role="status">{status}</div>}
    <aside className="element-inspector">
      <div><div className="element-revision-heading"><h2>{asset.label}</h2>{versions.length > 1 && <div className="element-revisions" role="group" aria-label="模型版本">{versions.map((candidate) => <button key={candidate.id} aria-pressed={candidate.id === asset.id} onClick={() => select(candidate)}>{elementVersionLabel(candidate.revision)}</button>)}</div>}</div><dl><div><dt>三角面</dt><dd>{asset.triangles.toLocaleString()}</dd></div><div><dt>GLB</dt><dd>{(asset.glbBytes / 1024).toFixed(0)} KB</dd></div><div><dt>动画</dt><dd>{asset.terrain ? asset.terrainMotion : asset.building ? '施工 / 运行' : asset.animal ? '成长 / 行为' : asset.lifecycle ? '物候 / 风动' : living ? '网页风动' : asset.animatedPivots.length ? 'GLB 动画' : '无'}</dd></div><div><dt>版本</dt><dd>{`V${asset.revision}`}</dd></div></dl>
        {asset.terrain && <div className="element-field-controls">
          {aridTerrains.has(asset.family) ? asset.family!=='sand-dunes' && <label className="element-slider"><span>活动强度 <output>{Math.round(terrainSettings.activity*100)}%</output></span><input aria-label="活动强度" type="range" min="0" max="100" value={Math.round(terrainSettings.activity*100)} onChange={(event)=>updateTerrain({activity:Number(event.target.value)/100})} /></label> : <label className="element-slider"><span>积雪 <output>{Math.round(terrainState.snow*100)}%</output></span><input aria-label="积雪" type="range" min="0" max="100" value={Math.round((terrainSettings.automatic ? terrainState.snow : terrainSettings.snow)*100)} onChange={(event)=>updateTerrain({snow:Number(event.target.value)/100,automatic:false})} /></label>}
          {!['volcano','lava-field'].includes(asset.family) && <label className="element-slider"><span>风力 <output>{Math.round(terrainSettings.wind*100)}%</output></span><input aria-label="风力" type="range" min="0" max="100" value={Math.round(terrainSettings.wind*100)} onChange={(event)=>updateTerrain({wind:Number(event.target.value)/100})} /></label>}
          {!aridTerrains.has(asset.family) && <div className="element-growth-actions"><label><input type="checkbox" checked={terrainSettings.automatic} onChange={(event)=>{updateTerrain({automatic:event.target.checked});if(event.target.checked){setPlaying(true);scene.current?.setPlaying(true)}}} />四季循环</label></div>}
        </div>}
        {asset.building && <div className="element-field-controls">
          <label className="element-slider"><span>施工进度 <output>{buildingStage(buildingState.progress)} · {Math.round(buildingState.progress*100)}%</output></span><input aria-label="施工进度" type="range" min="0" max="100" value={Math.round((buildingSettings.automatic ? buildingState.progress : buildingSettings.progress)*100)} onChange={(event) => updateBuilding({ progress:Number(event.target.value)/100,automatic:false })} /></label>
          <label className="element-slider"><span>运行速度 <output>{Math.round(buildingSettings.speed*100)}%</output></span><input aria-label="运行速度" type="range" min="0" max="100" value={Math.round(buildingSettings.speed*100)} onChange={(event) => updateBuilding({ speed:Number(event.target.value)/100 })} /></label>
          <div className="element-growth-actions"><label><input type="checkbox" checked={buildingSettings.automatic} onChange={(event) => { updateBuilding({ automatic:event.target.checked,progress:event.target.checked && buildingState.progress>=.99 ? 0 : buildingState.progress }); if (event.target.checked) { setPlaying(true); scene.current?.setPlaying(true) } }} />自动施工</label><label><input type="checkbox" checked={buildingSettings.working} onChange={(event) => updateBuilding({ working:event.target.checked })} />功能运行</label><label><input type="checkbox" checked={buildingSettings.tier===2} onChange={(event) => updateBuilding({ tier:event.target.checked ? 2 : 1 })} />升级附件</label></div>
        </div>}
        {asset.gate && <div className="element-growth-actions"><label><input type="checkbox" checked={buildingSettings.gateOpen} disabled={buildingState.progress<.99 || !buildingSettings.working} onChange={(event) => { updateBuilding({ gateOpen:event.target.checked }); setPlaying(true); scene.current?.setPlaying(true) }} />开启通道</label><output>{buildingState.access>.99 ? '可通行' : buildingState.access<.01 ? '已关闭' : '闸门动作中'}</output></div>}
        {asset.animal && <div className="element-animal-controls">
          <label className="element-slider"><span>成长阶段 <output>{animalState.age<.25 ? '幼体' : animalState.age<.72 ? '亚成体' : '成年'} · {Math.round(animalState.age*100)}%</output></span><input aria-label="成长阶段" type="range" min="0" max="100" value={Math.round((animalSettings.automatic ? animalState.age : animalSettings.age)*100)} onChange={(event) => updateAnimal({ age:Number(event.target.value)/100,automatic:false })} /></label>
          <div className="element-behaviors" role="group" aria-label="动物动作">{([['idle','休息'],['walk','行走'],['graze',asset.family==='chicken' ? '啄食' : '采食']] as const).map(([behavior,label]) => <button key={behavior} aria-pressed={animalSettings.behavior===behavior} onClick={() => updateAnimal({ behavior })}>{label}</button>)}</div>
          <div className="element-growth-actions"><label><input type="checkbox" checked={animalSettings.automatic} onChange={(event) => { updateAnimal({ automatic:event.target.checked,age:animalState.age>=.99 ? .04 : animalState.age }); if (event.target.checked) { setPlaying(true); scene.current?.setPlaying(true) } }} />自动成长</label><label><input type="checkbox" checked={animalSettings.family} disabled={animalState.age<.72} onChange={(event) => { updateAnimal({ family:event.target.checked }); if (event.target.checked) { setPlaying(true); scene.current?.setPlaying(true) } }} />繁育预览</label></div>
          {animalSettings.family && <div className="element-breeding-state" role="status"><span>{animalState.breedingState==='nursing' ? `子代 ${animalState.offspring} 只 · 成长 ${Math.round(animalState.offspringAge*100)}%` : ['chicken','duck'].includes(asset.family) ? '孵化中' : '等待幼崽'}</span><progress aria-label="繁育进度" value={animalState.breedingProgress} max="1" /></div>}
        </div>}
        {living && <div className="element-field-controls">
          {growing && <label className="element-slider"><span>生长阶段 <output>{stage} · {Math.round(progress * 100)}%</output></span><input aria-label="生长阶段" type="range" min="0" max="100" value={Math.round((settings.automatic ? progress : settings.growth) * 100)} onChange={(event) => updateField({ growth: Number(event.target.value) / 100, automatic: false })} /></label>}
          <label className="element-slider"><span>风力 <output>{Math.round(settings.wind * 100)}%</output></span><input aria-label="风力" type="range" min="0" max="100" value={Math.round(settings.wind * 100)} onChange={(event) => updateField({ wind: Number(event.target.value) / 100 })} /></label>
          {growing && <div className="element-growth-actions"><label><input type="checkbox" checked={settings.automatic} onChange={(event) => { updateField({ automatic: event.target.checked, growth: progress >= .99 ? .02 : progress }); if (event.target.checked) { setPlaying(true); scene.current?.setPlaying(true) } }} />自动生长</label><button title="重新播种" aria-label="重新播种" onClick={() => updateField({ growth: 0, automatic: false })}><Sprout size={17} /></button><button title="随机长势" aria-label="随机长势" onClick={() => updateField({ seed: settings.seed + 1 })}><Shuffle size={17} /></button></div>}
        </div>}
      </div>
      {asset.referenceUrl ? <figure><a href={asset.referenceUrl} target="_blank" rel="noreferrer"><img src={asset.referenceUrl} alt={`${asset.label}三视参考图`} /></a><figcaption>设计参考</figcaption></figure> : asset.terrain ? !aridTerrains.has(asset.family) && <div className="element-phenology" aria-label="地貌季相">{terrainSeasons.map((label,index)=><button key={label} aria-pressed={Math.abs(terrainState.phase-index/4)<.10} onClick={()=>updateTerrain({phase:index/4,snow:terrainSnow(asset.family,index/4),automatic:false})}>{label}</button>)}</div> : asset.building ? <div className="element-phenology" aria-label="施工阶段">{[.08,.30,.52,.78,1].map((value) => <button key={value} aria-pressed={Math.abs(buildingState.progress-value)<.08} onClick={() => updateBuilding({ progress:value,automatic:false })}>{buildingStage(value)}</button>)}</div> : asset.animal ? <div className="element-phenology" aria-label="年龄阶段">{([['幼体',.04],['亚成体',.5],['成年',1]] as const).map(([label,age]) => <button key={label} aria-pressed={Math.abs(animalState.age-age)<.1} onClick={() => updateAnimal({ age,automatic:false })}>{label}</button>)}</div> : <div className="element-phenology" aria-label="物候阶段">{[.05,.25,.47,.65,.81,.97].map((value) => <button key={value} aria-pressed={Math.abs(progress-value)<.08} onClick={() => updateField({ growth: value, automatic: false })}>{botanicalStage(value, asset.family)}</button>)}</div>}
    </aside>
  </section>
}
