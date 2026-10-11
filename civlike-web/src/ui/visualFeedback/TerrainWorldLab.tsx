import { useEffect, useRef, useState } from 'react'
import { Boxes, Focus, Grid2X2, Mountain, Move, Pause, Play, RotateCcw, Shuffle, Trees, Waves, Wind, ZoomIn, ZoomOut } from 'lucide-react'
import { mountTerrainWorldScene, type TerrainWorldHandle, type TerrainWorldSelection, type TerrainWorldSettings, type TerrainWorldStats } from '../../render/visuals/mountTerrainWorldScene'
import { TERRAIN_BIOMES, TERRAIN_SEASONS, type TerrainBiome } from '../../render/visuals/terrainWorldClimate'
import { initialWorldDay, worldCalendar } from '../../render/visuals/terrainWorldTime'
import type { LifeKind } from '../../render/visuals/terrainWorldLife'
import './terrainWorldLab.css'

function initialSeed() {
  const value = Number(new URLSearchParams(window.location.search).get('assetSeed'))
  return Number.isSafeInteger(value) && value > 0 && value <= 1_000_000_000 ? value : 20261011
}

export function TerrainWorldLab() {
  const [seed, setSeed] = useState(initialSeed)
  const [seedInput, setSeedInput] = useState(String(seed))
  const [settings, setSettings] = useState<TerrainWorldSettings>(() => ({
    animated: !window.matchMedia('(prefers-reduced-motion: reduce)').matches, wind: 1.2, flow: 1, grid: true, pan: false,
    day:initialWorldDay(seed,new URLSearchParams(window.location.search).get('season')),dayRevision:0,autoSeason:true,timeSpeed:5,
  }))
  const [calendar,setCalendar]=useState(()=>worldCalendar(settings.day))
  const [view, setView] = useState<'isometric' | 'top'>('isometric')
  const [stats, setStats] = useState<TerrainWorldStats | null>(null)
  const [selection, setSelection] = useState<TerrainWorldSelection | null>(null)
  const [biomeFocus, setBiomeFocus] = useState<TerrainBiome | ''>('')
  const [placeFocus, setPlaceFocus] = useState('')
  const [lifeFocus,setLifeFocus]=useState('')
  const [error, setError] = useState('')
  const host = useRef<HTMLDivElement>(null)
  const handle = useRef<TerrainWorldHandle | null>(null)
  const latestSettings = useRef(settings)
  useEffect(() => {
    latestSettings.current = settings
    handle.current?.update(settings)
  }, [settings])
  useEffect(() => {
    if (!host.current) return
    setError('')
    setSelection(null)
    setBiomeFocus('')
    setPlaceFocus('')
    setLifeFocus('')
    setView('isometric')
    try {
      handle.current = mountTerrainWorldScene(host.current, seed, latestSettings.current, setStats, (next)=> {
        setSelection(next)
        setPlaceFocus('')
        setBiomeFocus(TERRAIN_BIOMES.find(({label})=>label===next.label)?.id??'')
      },setCalendar)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : '三维场景无法加载')
    }
    return () => { handle.current?.destroy(); handle.current = null }
  }, [seed])

  function changeSeed(next: number) {
    const day=initialWorldDay(next)
    setSettings((previous)=>({...previous,day,dayRevision:previous.dayRevision+1}))
    setCalendar(worldCalendar(day))
    setSeed(next)
    setSeedInput(String(next))
    const url = new URL(window.location.href)
    url.searchParams.set('view', 'terrain-world')
    url.searchParams.set('assetSeed', String(next))
    url.searchParams.delete('season')
    window.history.replaceState(null, '', url)
  }
  function changeView(next: 'isometric' | 'top') { setView(next); setBiomeFocus(''); setPlaceFocus(''); setLifeFocus(''); handle.current?.view(next) }
  const toggle = (key: 'animated' | 'grid' | 'pan') => setSettings((previous) => ({ ...previous, [key]: !previous[key] }))
  function changeSeason(season: string) {
    const day=initialWorldDay(seed,season)
    setSettings((previous)=>({...previous,day,dayRevision:previous.dayRevision+1,autoSeason:false}))
    setCalendar(worldCalendar(day))
    const url=new URL(window.location.href)
    url.searchParams.set('season',season)
    window.history.replaceState(null,'',url)
  }

  return (
    <main className="terrain-world-lab">
      <header className="terrain-world-header">
        <div className="terrain-world-title"><Mountain size={23} /><h1>地形样区</h1><span>C · 低多边形</span></div>
        <div className="terrain-world-header-actions">
          <button className="terrain-world-icon" title={settings.animated ? '暂停动画' : '播放动画'} aria-label={settings.animated ? '暂停动画' : '播放动画'} onClick={() => toggle('animated')}>
            {settings.animated ? <Pause size={18} /> : <Play size={18} />}
          </button>
          <button className="terrain-world-generate" onClick={() => changeSeed(1 + window.crypto.getRandomValues(new Uint32Array(1))[0] % 1_000_000_000)}><Shuffle size={17} />重新生成</button>
        </div>
      </header>

      <div className="terrain-world-body">
        <section className="terrain-world-stage" aria-label="连续地形预览">
          <div className="terrain-world-canvas" ref={host} data-testid="terrain-world-canvas" />
          {error && <div className="terrain-world-error" role="alert">{error}</div>}
          {selection && <div className="terrain-world-mobile-selection">{selection.label} · {selection.id} · 肥力 {selection.fertility}</div>}
          <div className="terrain-world-viewbar">
            <div className="terrain-world-segments" role="group" aria-label="观察角度">
              <button aria-pressed={view === 'isometric'} onClick={() => changeView('isometric')}>等距</button>
              <button aria-pressed={view === 'top'} onClick={() => changeView('top')}>俯视</button>
            </div>
            <button className="terrain-world-icon" title="显示网格" aria-label="显示网格" aria-pressed={settings.grid} onClick={() => toggle('grid')}><Grid2X2 size={18} /></button>
            <button className="terrain-world-icon" title="重置视角" aria-label="重置视角" onClick={() => changeView('isometric')}><RotateCcw size={18} /></button>
            <button className="terrain-world-icon" title="放大" aria-label="放大" onClick={() => handle.current?.zoom(1.2)}><ZoomIn size={18} /></button>
            <button className="terrain-world-icon" title="缩小" aria-label="缩小" onClick={() => handle.current?.zoom(1 / 1.2)}><ZoomOut size={18} /></button>
            <button className="terrain-world-icon" title="地块近景" aria-label="地块近景" onClick={() => { setView('isometric'); handle.current?.focus() }}><Focus size={18} /></button>
            <button className="terrain-world-icon" title="平移地图" aria-label="平移地图" aria-pressed={settings.pan} onClick={() => toggle('pan')}><Move size={18} /></button>
          </div>
          <div className="terrain-world-legend" aria-label="地形图例">
            {TERRAIN_BIOMES.map(({color,label,id}) => <span key={id}><i style={{ background: color }} />{label}</span>)}
          </div>
        </section>

        <aside className="terrain-world-panel">
          <section>
            <h2><Boxes size={16} />样区</h2>
            <form className="terrain-world-seed" onSubmit={(event) => {
              event.preventDefault()
              const next = Number(seedInput)
              if (Number.isSafeInteger(next) && next > 0 && next <= 1_000_000_000) changeSeed(next)
            }}>
              <label htmlFor="terrain-seed">种子</label>
              <div><input id="terrain-seed" type="number" min="1" max="1000000000" step="1" required value={seedInput} onChange={(event) => setSeedInput(event.target.value)} /><button type="submit" className="terrain-world-icon" title="应用种子" aria-label="应用种子"><RotateCcw size={16} /></button></div>
            </form>
            <dl className="terrain-world-metrics"><div><dt>区块</dt><dd>{stats?.tiles ?? '—'}</dd></div><div><dt>树木</dt><dd>{stats?.trees ?? '—'}</dd></div><div><dt>草丛</dt><dd>{stats?.grass ?? '—'}</dd></div></dl>
            <label className="terrain-world-select">季节<select aria-label="季节" value={calendar.season.id} onChange={(event)=>changeSeason(event.target.value)}>{TERRAIN_SEASONS.map(({id,label})=><option value={id} key={id}>{label}</option>)}</select></label>
            <label className="terrain-world-select">聚落定位<select aria-label="聚落定位" value={placeFocus} onChange={(event)=> {
              handle.current?.focusPlace(event.target.value);setPlaceFocus(event.target.value);setBiomeFocus('');setView('isometric')
            }}><option value="">{stats?.places.length??0} 处聚落与遗迹</option>{stats?.places.map(({id,label})=><option value={id} key={id}>{label}</option>)}</select></label>
            <div className="terrain-world-scenery-count">建筑 {stats?.buildings??0} · 农田 {stats?.farms??0} · 桥梁 {stats?.bridges??0}</div>
          </section>
          <section>
            <h2><Wind size={16} />环境动态</h2>
            <div className="terrain-world-calendar"><span>第 {calendar.year} 年 · {calendar.day} 日</span><progress aria-label="季节进度" max="1" value={calendar.progress} /></div>
            <div className="terrain-world-clock"><label className="terrain-world-toggle"><input type="checkbox" checked={settings.autoSeason} onChange={(event)=>setSettings((previous)=>({...previous,autoSeason:event.target.checked}))} />季节流转</label><select aria-label="时间速度" value={settings.timeSpeed} onChange={(event)=>setSettings((previous)=>({...previous,timeSpeed:Number(event.target.value)}))}>{[1,5,20].map((speed)=><option key={speed} value={speed}>{speed}×</option>)}</select></div>
            <label className="terrain-world-select">活动定位<select aria-label="活动定位" value={lifeFocus} onChange={(event)=>{handle.current?.focusLife(event.target.value as LifeKind);setLifeFocus(event.target.value);setPlaceFocus('');setBiomeFocus('');setSelection(null)}}><option value="">人{stats?.people??0} · 动物{stats?.animals??0}</option><option value="traveler">行人与村道</option><option value="cart">运输车队</option><option value="deer">林缘鹿群</option><option value="sheep">草地羊群</option><option value="bird">盘旋飞鸟</option></select></label>
            <label className="terrain-world-range"><span>风力<output>{settings.wind.toFixed(1)}</output></span><input aria-label="风力" type="range" min="0" max="2.5" step="0.1" value={settings.wind} onChange={(event) => setSettings((previous) => ({ ...previous, wind: Number(event.target.value) }))} /></label>
            <label className="terrain-world-range"><span><Waves size={15} />水流<output>{settings.flow.toFixed(1)}</output></span><input aria-label="水流" type="range" min="0" max="2" step="0.1" value={settings.flow} onChange={(event) => setSettings((previous) => ({ ...previous, flow: Number(event.target.value) }))} /></label>
            <label className="terrain-world-toggle"><input type="checkbox" checked={settings.animated} onChange={() => toggle('animated')} />环境动画</label>
            <label className="terrain-world-select">地貌定位<select aria-label="地貌定位" value={biomeFocus} onChange={(event)=> {
              if(!event.target.value) return
              setView('isometric'); setPlaceFocus(''); handle.current?.focusBiome(event.target.value as TerrainBiome)
            }}><option value="">{stats?.biomes.filter(({count})=>count>0).length??0} 种地貌</option>{TERRAIN_BIOMES.map(({id,label})=> {
              const count=stats?.biomes.find((biome)=>biome.id===id)?.count??0
              return <option value={id} key={id} disabled={!count}>{label} · {count}</option>
            })}</select></label>
          </section>
          <section className="terrain-world-selection">
            <h2><Trees size={16} />{selection ? selection.label : '地块属性'}</h2>
            <dl><div><dt>坐标</dt><dd>{selection?.id ?? '未选中'}</dd></div><div><dt>高度</dt><dd>{selection?.elevation ?? '—'}</dd></div><div><dt>肥力</dt><dd>{selection?.fertility ?? '—'}</dd></div></dl>
          </section>
        </aside>
      </div>
      <footer className="terrain-world-footer"><span><i className={settings.animated ? 'is-live' : ''} />{settings.animated ? '动态预览' : '已暂停'}</span><span>{stats ? `${stats.triangles.toLocaleString()} 地表三角面` : '构建地形'}</span></footer>
    </main>
  )
}
