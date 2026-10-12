import { useEffect, useRef, useState } from 'react'
import { Box, Download, Pause, Play, RotateCcw, Shuffle, Sprout } from 'lucide-react'
import { elementVersionLabel, initialMapElement, mapElementLibrary, mapElements, type MapElement } from '../../render/assets/mapElementCatalog'
import { mountMapElement, type ElementScene, type ElementView } from '../../render/visuals/mapElementScene'
import { defaultFieldSettings, type FieldSettings } from '../../render/visuals/mapElementGrowth'
import './mapElementLab.css'

const views: [ElementView, string][] = [['perspective', '自由视角'], ['front', '正面'], ['side', '侧面'], ['top', '俯视']]

export function MapElementLab() {
  const [selected, setSelected] = useState(() => initialMapElement(location.search))
  const [view, setView] = useState<ElementView>('perspective')
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
    <header className="element-header"><h1>地图模型库</h1><span>C 风格 / 第一批</span><a href="?view=terrain-world">返回地图</a></header>
    <nav className="element-library" aria-label="模型列表">
      <select aria-label="选择模型" value={selected.family} onChange={(event) => select(mapElementLibrary.find((a) => a.family === event.target.value)!)}>
        {mapElementLibrary.map((asset) => <option key={asset.family} value={asset.family}>{asset.label}{asset.revision > 1 ? ` · ${elementVersionLabel(asset.revision)}` : ''}</option>)}
      </select>
      <div className="element-list">{mapElementLibrary.map((asset) => <button key={asset.family} aria-pressed={selected.family === asset.family} onClick={() => select(asset)}><span>{asset.label}</span><small>{asset.revision > 1 ? '已更新' : asset.category}</small></button>)}</div>
      <p>{mapElementLibrary.length} 类模型 · {mapElements.length} 个版本</p>
    </nav>
    <ElementPreview key={selected.id} asset={selected} select={select} view={view} setView={setView} />
  </main>
}

function ElementPreview({ asset, select, view, setView }: {
  asset: MapElement; select: (asset: MapElement) => void
  view: ElementView; setView: (view: ElementView) => void
}) {
  const versions = mapElements.filter((candidate) => candidate.family === asset.family)
  const living = asset.revision >= 3
  const growing = living && asset.family !== 'plowed-field'
  const host = useRef<HTMLDivElement>(null)
  const scene = useRef<ElementScene>()
  const [playing, setPlaying] = useState(!window.matchMedia('(prefers-reduced-motion: reduce)').matches)
  const [wireframe, setWireframe] = useState(false)
  const [status, setStatus] = useState('加载中')
  const [hasAnimation, setHasAnimation] = useState(false)
  const [settings, setSettings] = useState<FieldSettings>({ ...defaultFieldSettings })
  const [progress, setProgress] = useState(defaultFieldSettings.growth)
  const stage = progress < .08 ? '播种' : progress < .32 ? '幼苗' : progress < .62 ? '生长' : progress < .92 ? (asset.family === 'wheat-field' ? '抽穗' : '结球') : '成熟'
  function updateField(patch: Partial<FieldSettings>) {
    setSettings((previous) => ({ ...previous, growth: previous.automatic ? progress : previous.growth, ...patch }))
  }
  useEffect(() => {
    if (!host.current) return
    const handle = mountMapElement(host.current, asset.url, (count) => {
      setStatus('已加载'); setHasAnimation(count > 0)
    }, (message) => setStatus(`加载失败：${message}`), setProgress)
    scene.current = handle
    return () => { scene.current = undefined; handle.destroy() }
  }, [asset.url])
  useEffect(() => { scene.current?.setView(view) }, [view])
  useEffect(() => { scene.current?.setFieldSettings(settings) }, [settings])
  return <section className={`element-workspace${living ? ' element-workspace-living' : ''}`} aria-label={asset.label}>
    <div className="element-toolbar">
      <div className="element-views" role="group" aria-label="相机视角">{views.map(([id, label]) => <button key={id} aria-pressed={view === id} onClick={() => { setView(id); scene.current?.setView(id) }}>{label}</button>)}</div>
      <div className="element-tools">
        <button title={playing ? '暂停动画' : '播放动画'} aria-label={playing ? '暂停动画' : '播放动画'} disabled={!hasAnimation} onClick={() => { setPlaying(!playing); scene.current?.setPlaying(!playing) }}>{playing ? <Pause size={18} /> : <Play size={18} />}</button>
        <button title="线框" aria-label="线框" aria-pressed={wireframe} onClick={() => { setWireframe(!wireframe); scene.current?.setWireframe(!wireframe) }}><Box size={18} /></button>
        <button title="重置视角" aria-label="重置视角" onClick={() => scene.current?.setView(view)}><RotateCcw size={18} /></button>
        <a href={asset.url} download={`${asset.id}.glb`} title="下载 GLB" aria-label="下载 GLB"><Download size={18} /></a>
      </div>
    </div>
    <div className="element-stage" ref={host} data-asset={asset.id} />
    {status !== '已加载' && <div className="element-load-status" role="status">{status}</div>}
    <aside className="element-inspector">
      <div><div className="element-revision-heading"><h2>{asset.label}</h2>{versions.length > 1 && <div className="element-revisions" role="group" aria-label="模型版本">{versions.map((candidate) => <button key={candidate.id} aria-pressed={candidate.id === asset.id} onClick={() => select(candidate)}>{elementVersionLabel(candidate.revision)}</button>)}</div>}</div><dl><div><dt>三角面</dt><dd>{asset.triangles.toLocaleString()}</dd></div><div><dt>GLB</dt><dd>{(asset.glbBytes / 1024).toFixed(0)} KB</dd></div><div><dt>动画</dt><dd>{living ? '网页风动' : asset.animatedPivots.length ? 'GLB 动画' : '无'}</dd></div><div><dt>版本</dt><dd>{`V${asset.revision}`}</dd></div></dl>
        {living && <div className="element-field-controls">
          {growing && <label className="element-slider"><span>生长阶段 <output>{stage} · {Math.round(progress * 100)}%</output></span><input aria-label="生长阶段" type="range" min="0" max="100" value={Math.round((settings.automatic ? progress : settings.growth) * 100)} onChange={(event) => updateField({ growth: Number(event.target.value) / 100, automatic: false })} /></label>}
          <label className="element-slider"><span>风力 <output>{Math.round(settings.wind * 100)}%</output></span><input aria-label="风力" type="range" min="0" max="100" value={Math.round(settings.wind * 100)} onChange={(event) => updateField({ wind: Number(event.target.value) / 100 })} /></label>
          {growing && <div className="element-growth-actions"><label><input type="checkbox" checked={settings.automatic} onChange={(event) => { updateField({ automatic: event.target.checked, growth: progress >= .99 ? .02 : progress }); if (event.target.checked) { setPlaying(true); scene.current?.setPlaying(true) } }} />自动生长</label><button title="重新播种" aria-label="重新播种" onClick={() => updateField({ growth: 0, automatic: false })}><Sprout size={17} /></button><button title="随机长势" aria-label="随机长势" onClick={() => updateField({ seed: settings.seed + 1 })}><Shuffle size={17} /></button></div>}
        </div>}
      </div>
      <figure><a href={asset.referenceUrl} target="_blank" rel="noreferrer"><img src={asset.referenceUrl} alt={`${asset.label}三视参考图`} /></a><figcaption>设计参考</figcaption></figure>
    </aside>
  </section>
}
