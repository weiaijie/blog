import { useEffect, useRef, useState } from 'react'
import { Box, Download, Pause, Play, RotateCcw } from 'lucide-react'
import { mapElements, type MapElement } from '../../render/assets/mapElementCatalog'
import { mountMapElement, type ElementScene, type ElementView } from '../../render/visuals/mapElementScene'
import './mapElementLab.css'

const views: [ElementView, string][] = [['perspective', '自由视角'], ['front', '正面'], ['side', '侧面'], ['top', '俯视']]

export function MapElementLab() {
  const [selected, setSelected] = useState(() => {
    const id = new URLSearchParams(location.search).get('element')
    return mapElements.find((asset) => asset.id === id) ?? mapElements.find((asset) => asset.id === 'fishing-boat') ?? mapElements[0]
  })
  function select(asset: MapElement) {
    setSelected(asset)
    const url = new URL(location.href)
    url.searchParams.set('element', asset.id)
    history.replaceState(null, '', url)
  }
  return <main className="element-lab">
    <header className="element-header"><h1>地图模型库</h1><span>C 风格 / 第一批</span><a href="?view=terrain-world">返回地图</a></header>
    <nav className="element-library" aria-label="模型列表">
      <select aria-label="选择模型" value={selected.id} onChange={(event) => select(mapElements.find((a) => a.id === event.target.value)!)}>
        {mapElements.map((asset) => <option key={asset.id} value={asset.id}>{asset.label}</option>)}
      </select>
      <div className="element-list">{mapElements.map((asset) => <button key={asset.id} aria-pressed={selected.id === asset.id} onClick={() => select(asset)}><span>{asset.label}</span><small>{asset.category}</small></button>)}</div>
      <p>{mapElements.length} 个模型</p>
    </nav>
    <ElementPreview key={selected.id} asset={selected} />
  </main>
}

function ElementPreview({ asset }: { asset: MapElement }) {
  const host = useRef<HTMLDivElement>(null)
  const scene = useRef<ElementScene>()
  const [view, setView] = useState<ElementView>('perspective')
  const [playing, setPlaying] = useState(!window.matchMedia('(prefers-reduced-motion: reduce)').matches)
  const [wireframe, setWireframe] = useState(false)
  const [status, setStatus] = useState('加载中')
  const [hasAnimation, setHasAnimation] = useState(false)
  useEffect(() => {
    if (!host.current) return
    const handle = mountMapElement(host.current, asset.url, (count) => {
      setStatus('已加载'); setHasAnimation(count > 0)
    }, (message) => setStatus(`加载失败：${message}`))
    scene.current = handle
    return () => { scene.current = undefined; handle.destroy() }
  }, [asset.url])
  return <section className="element-workspace" aria-label={asset.label}>
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
      <div><h2>{asset.label}</h2><dl><div><dt>三角面</dt><dd>{asset.triangles.toLocaleString()}</dd></div><div><dt>GLB</dt><dd>{(asset.glbBytes / 1024).toFixed(0)} KB</dd></div><div><dt>动画部件</dt><dd>{asset.animatedPivots.length}</dd></div><div><dt>版本</dt><dd>建模初版</dd></div></dl></div>
      <figure><a href={asset.referenceUrl} target="_blank" rel="noreferrer"><img src={asset.referenceUrl} alt={`${asset.label}三视参考图`} /></a><figcaption>设计参考</figcaption></figure>
    </aside>
  </section>
}
