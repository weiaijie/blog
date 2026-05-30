import { useEffect, useRef, useState } from 'react'
import {
  mountPixiStage,
  type PixiExplorationSnapshot,
  type PixiStageHandle,
  type PixiStageStats,
} from '../render/pixi/mountPixiStage'
import { getTerrainConfig, terrainConfigs } from '../game/config/terrain'
import { getTechConfig } from '../game/config/tech'
import { tryApplyRuleCommand } from '../game/simulation/applyRuleCommand'
import { getCityYield } from '../game/simulation/cityProduction'
import { createInitialGameState } from '../game/state/gameState'
import { hashGameState } from '../game/state/hashGameState'
import { loadGameFromSave, serializeSavedGame } from '../game/state/saveGame'
import type { RuleCommand } from '../game/commands/ruleCommand'
import type { MapTile } from '../game/state/map'
import { getManualSaveStatus, loadManualGame, saveManualGame } from '../storage/browserSaveSlot'
import { initialUiState } from './stores/uiState'

export function App() {
  const hostRef = useRef<HTMLDivElement | null>(null)
  const handleTileSelectRef = useRef<(tileId: string) => void>(() => undefined)
  const stageRef = useRef<PixiStageHandle | null>(null)
  const latestExplorationRef = useRef<PixiExplorationSnapshot | null>(null)
  const [stats, setStats] = useState<PixiStageStats | null>(null)
  const [gameState, setGameState] = useState(() => createInitialGameState(1001))
  const [selectedUnitId, setSelectedUnitId] = useState<string | null>(null)
  const [commandError, setCommandError] = useState<string | null>(null)
  const [savedGameJson, setSavedGameJson] = useState<string | null>(null)
  const [saveStatus, setSaveStatus] = useState('无')
  const [persistentSaveStatus, setPersistentSaveStatus] = useState('检查中')

  function runCommand(command: RuleCommand): boolean {
    const result = tryApplyRuleCommand(gameState, command)

    if (!result.ok) {
      setCommandError(`${result.code}: ${result.reason}`)
      return false
    }

    setCommandError(null)
    setGameState(result.state)
    return true
  }

  function endTurn(): void {
    runCommand({
      playerId: gameState.activePlayerId,
      type: 'END_TURN',
    })
  }

  function chooseMining(): void {
    runCommand({
      playerId: gameState.activePlayerId,
      techId: 'tech:mining',
      type: 'CHOOSE_TECH',
    })
  }

  function setCapitalProduction(): void {
    runCommand({
      cityId: 'city:capital',
      playerId: gameState.activePlayerId,
      productionId: 'unit:scout',
      type: 'SET_PRODUCTION',
    })
  }

  function saveGame(): void {
    const serialized = serializeSavedGame(gameState)

    setSavedGameJson(serialized)
    setSaveStatus(`已保存回合 ${gameState.turn} / 命令 ${gameState.commandLog.length}`)
    setCommandError(null)
  }

  function loadSavedGame(): void {
    if (!savedGameJson) {
      setSaveStatus('没有存档槽')
      return
    }

    const result = loadGameFromSave(savedGameJson)

    if (!result.ok) {
      setSaveStatus(`读取失败：${result.code}`)
      setCommandError(`${result.code}: ${result.reason}`)
      return
    }

    setGameState(result.state)
    setSelectedUnitId(null)
    setCommandError(null)
    setSaveStatus(`已读取回合 ${result.state.turn} / 命令 ${result.state.commandLog.length}`)
  }

  function savePersistentGame(): void {
    const result = saveManualGame(gameState)

    if (!result.ok) {
      setPersistentSaveStatus(`保存失败：${result.code}`)
      setCommandError(`${result.code}: ${result.reason}`)
      return
    }

    setCommandError(null)
    setPersistentSaveStatus(`已保存回合 ${gameState.turn} / 命令 ${gameState.commandLog.length} / ${result.bytes} 字节`)
  }

  function loadPersistentGame(): void {
    const result = loadManualGame()

    if (!result.ok) {
      setPersistentSaveStatus(`读取失败：${result.code}`)
      setCommandError(`${result.code}: ${result.reason}`)
      return
    }

    if (!result.state) {
      setPersistentSaveStatus('读取失败：LOAD_FAILED')
      setCommandError('LOAD_FAILED：持久存档没有返回游戏状态。')
      return
    }

    setGameState(result.state)
    setSelectedUnitId(null)
    setCommandError(null)
    setPersistentSaveStatus(`已读取回合 ${result.state.turn} / 命令 ${result.state.commandLog.length}`)
  }

  const activePlayer = gameState.players.find((player) => player.id === gameState.activePlayerId)
  const lastCommand = gameState.commandLog[gameState.commandLog.length - 1]
  const selectedTile = gameState.map.tiles.find((tile) => tile.id === stats?.selectedTileId)
  const selectedTerrain = selectedTile ? getTerrainConfig(selectedTile.terrainId) : null
  const selectedUnits = selectedTile
    ? gameState.units.filter((unit) => unit.tileId === selectedTile.id)
    : []
  const selectedCity = selectedTile
    ? gameState.cities.find((city) => city.tileId === selectedTile.id)
    : undefined
  const selectedUnit = selectedUnitId
    ? gameState.units.find((unit) => unit.id === selectedUnitId)
    : undefined
  const currentTech = gameState.currentTechByPlayerId[gameState.activePlayerId]
  const currentTechConfig = currentTech ? getTechConfig(currentTech) : null
  const completedTechs = gameState.completedTechByPlayerId[gameState.activePlayerId] ?? []
  const capitalCity = gameState.cities.find((city) => city.id === 'city:capital')
  const currentHash = hashGameState(gameState)
  const capitalYield = capitalCity ? getCityYield(gameState, capitalCity) : null
  const activeExploration = gameState.explorationByPlayerId[gameState.activePlayerId]
  const exploredTileCount = activeExploration?.exploredTileIds.length ?? 0
  const visibleTileCount = activeExploration?.visibleTileIds.length ?? 0
  latestExplorationRef.current = activeExploration ?? null
  const objectives = [
    {
      done: gameState.units.some((unit) => unit.id === 'unit:scout:1' && unit.tileId !== 'tile:8:9'),
      label: '移动侦察兵',
    },
    {
      done: currentTech === 'tech:mining' || completedTechs.includes('tech:mining'),
      label: '选择采矿',
    },
    {
      done: capitalCity?.productionId === 'unit:scout' || gameState.units.length > 1,
      label: '生产侦察兵',
    },
    {
      done: gameState.turn > 1,
      label: '结束回合',
    },
    {
      done: savedGameJson !== null,
      label: '保存进度',
    },
  ]
  const nextObjective = objectives.find((objective) => !objective.done)?.label ?? '继续回合'
  const explorationHint = objectives[0].done
    ? `侦察兵已探索 ${exploredTileCount} 个地块`
    : '移动侦察兵以揭示附近地块'

  function handleTileSelect(tileId: string): void {
    const clickedTile = gameState.map.tiles.find((tile) => tile.id === tileId)

    if (!clickedTile) {
      return
    }

    const unitOnTile = gameState.units.find(
      (unit) => unit.tileId === tileId && unit.ownerId === gameState.activePlayerId,
    )

    if (unitOnTile) {
      setSelectedUnitId(unitOnTile.id)
      setCommandError(null)
      return
    }

    if (!selectedUnit) {
      return
    }

    const fromTile = gameState.map.tiles.find((tile) => tile.id === selectedUnit.tileId)

    if (!fromTile || !areAdjacentTiles(fromTile, clickedTile)) {
      setCommandError('MOVE_UNIT：目标地块必须与已选单位相邻。')
      return
    }

    runCommand({
      playerId: gameState.activePlayerId,
      toTileId: clickedTile.id,
      type: 'MOVE_UNIT',
      unitId: selectedUnit.id,
    })
  }

  handleTileSelectRef.current = handleTileSelect

  useEffect(() => {
    setPersistentSaveStatus(getManualSaveStatus())
  }, [])

  useEffect(() => {
    const host = hostRef.current

    if (!host) {
      return
    }

    let dispose: (() => void) | undefined

    mountPixiStage(host, {
      onStats: setStats,
      onTileSelect: (tileId) => {
        handleTileSelectRef.current(tileId)
      },
    }).then((stage) => {
      dispose = stage.destroy
      stageRef.current = stage
      stage.setExploration(latestExplorationRef.current)
      setStats(stage.stats)
    })

    return () => {
      stageRef.current = null
      dispose?.()
    }
  }, [])

  useEffect(() => {
    stageRef.current?.setExploration(activeExploration ?? null)
  }, [activeExploration])

  return (
    <main className="app-shell">
      <section className="map-workspace" aria-label="文明原型地图">
        <div ref={hostRef} className="pixi-host" />
      </section>

      <aside className="side-panel" aria-label="调试摘要">
        <header>
          <p className="eyebrow">可玩主线</p>
          <h1>Civlike Web</h1>
        </header>

        <section className="turn-controls" aria-label="回合控制">
          <button type="button" onClick={endTurn}>
            结束回合
          </button>
          <button type="button" onClick={chooseMining}>
            选择采矿
          </button>
          <button type="button" onClick={setCapitalProduction}>
            生产侦察兵
          </button>
          <button type="button" onClick={saveGame}>
            保存游戏
          </button>
          <button type="button" onClick={loadSavedGame}>
            读取游戏
          </button>
          <button type="button" onClick={savePersistentGame}>
            持久保存
          </button>
          <button type="button" onClick={loadPersistentGame}>
            持久读取
          </button>
          {commandError ? <p className="command-error">{commandError}</p> : null}
        </section>

        <section className="objective-panel" aria-label="当前目标">
          <div>
            <p className="eyebrow">当前目标</p>
            <h2>{nextObjective}</h2>
            <p className="objective-hint" aria-label="探索提示">
              {explorationHint}
            </p>
          </div>
          <ol>
            {objectives.map((objective) => (
              <li key={objective.label} data-complete={objective.done ? 'true' : 'false'}>
                <span>{objective.done ? '完成' : '下一步'}</span>
                {objective.label}
              </li>
            ))}
          </ol>
        </section>

        <dl className="debug-list">
          <div>
            <dt>回合</dt>
            <dd>{gameState.turn}</dd>
          </div>
          <div>
            <dt>阶段</dt>
            <dd>{gameState.turnPhase}</dd>
          </div>
          <div>
            <dt>当前玩家</dt>
            <dd>{activePlayer?.name ?? gameState.activePlayerId}</dd>
          </div>
          <div>
            <dt>食物库存</dt>
            <dd>{activePlayer?.foodStockpile ?? 0}</dd>
          </div>
          <div>
            <dt>科研进度</dt>
            <dd>{activePlayer?.scienceProgress ?? 0}</dd>
          </div>
          <div>
            <dt>命令日志</dt>
            <dd>{gameState.commandLog.length}</dd>
          </div>
          <div>
            <dt>状态哈希</dt>
            <dd>{currentHash}</dd>
          </div>
          <div>
            <dt>存档槽</dt>
            <dd>{savedGameJson ? `${savedGameJson.length} 字节` : '空'}</dd>
          </div>
          <div>
            <dt>存档状态</dt>
            <dd>{saveStatus}</dd>
          </div>
          <div>
            <dt>持久存档</dt>
            <dd>{persistentSaveStatus}</dd>
          </div>
          <div>
            <dt>当前科技</dt>
            <dd>{currentTech ?? '无'}</dd>
          </div>
          <div>
            <dt>科技进度</dt>
            <dd>
              {currentTechConfig && activePlayer
                ? `${activePlayer.scienceProgress} / ${currentTechConfig.researchCost}`
                : '无'}
            </dd>
          </div>
          <div>
            <dt>已完成科技</dt>
            <dd>{completedTechs.length > 0 ? completedTechs.join(', ') : '无'}</dd>
          </div>
          <div>
            <dt>首都生产</dt>
            <dd>{capitalCity?.productionId ?? '无'}</dd>
          </div>
          <div>
            <dt>首都进度</dt>
            <dd>{capitalCity ? capitalCity.productionProgress : '无'}</dd>
          </div>
          <div>
            <dt>首都产出</dt>
            <dd>
              {capitalYield
                ? `食物 ${capitalYield.food}，生产 ${capitalYield.production}，科研 ${capitalYield.science}`
                : '无'}
            </dd>
          </div>
          <div>
            <dt>上条命令</dt>
            <dd>{lastCommand ? `${lastCommand.id} / ${lastCommand.command.type}` : '无'}</dd>
          </div>
          <div>
            <dt>命令错误</dt>
            <dd>{commandError ?? '无'}</dd>
          </div>
          <div>
            <dt>已选单位</dt>
            <dd>{selectedUnit ? `${selectedUnit.id} @ ${selectedUnit.tileId}` : '无'}</dd>
          </div>
          <div>
            <dt>单位数量</dt>
            <dd>{gameState.units.length}</dd>
          </div>
          <div>
            <dt>可见地块</dt>
            <dd>{visibleTileCount}</dd>
          </div>
          <div>
            <dt>已探索地块</dt>
            <dd>{exploredTileCount}</dd>
          </div>
          <div>
            <dt>地图迷雾</dt>
            <dd>
              {stats
                ? `可见 ${stats.fogVisibleTileCount}，已探索 ${stats.fogExploredTileCount}`
                : '等待中'}
            </dd>
          </div>
          <div>
            <dt>画布</dt>
            <dd>{stats ? `${stats.width} x ${stats.height}` : '挂载中'}</dd>
          </div>
          <div>
            <dt>默认地图</dt>
            <dd>{stats ? `${Math.sqrt(stats.tileCount)} x ${Math.sqrt(stats.tileCount)}` : `${initialUiState.mapWidth} x ${initialUiState.mapHeight}`}</dd>
          </div>
          <div>
            <dt>地形配置</dt>
            <dd>{terrainConfigs.length}</dd>
          </div>
          <div>
            <dt>视口</dt>
            <dd>{stats ? `${stats.activeTileCount} 地块 / ${stats.activeChunkCount} 区块` : '等待中'}</dd>
          </div>
          <div>
            <dt>相机</dt>
            <dd>{stats ? `${stats.cameraX}, ${stats.cameraY}, ${stats.zoom}x` : '等待中'}</dd>
          </div>
          <div>
            <dt>地块池</dt>
            <dd>{stats ? stats.allocatedTileGraphics : '等待中'}</dd>
          </div>
          <div>
            <dt>p95 帧耗时</dt>
            <dd>{stats ? `${stats.p95FrameMs} ms` : '等待中'}</dd>
          </div>
          <div>
            <dt>已选地块</dt>
            <dd>{stats?.selectedTileId ?? '无'}</dd>
          </div>
          <div>
            <dt>地块详情</dt>
            <dd>
              {selectedTile && selectedTerrain
                ? `${selectedTile.x}, ${selectedTile.y} / ${selectedTerrain.label}`
                : '无'}
            </dd>
          </div>
          <div>
            <dt>地块产出</dt>
            <dd>
              {selectedTerrain
                ? `食物 ${selectedTerrain.food}，生产 ${selectedTerrain.production}，科研 ${selectedTerrain.science}`
                : '无'}
            </dd>
          </div>
          <div>
            <dt>地块单位</dt>
            <dd>{selectedUnits.length > 0 ? selectedUnits.map((unit) => unit.id).join(', ') : '无'}</dd>
          </div>
          <div>
            <dt>地块城市</dt>
            <dd>{selectedCity ? selectedCity.id : '无'}</dd>
          </div>
          <div>
            <dt>模块边界</dt>
            <dd>game/render/ui/storage/workers/perf</dd>
          </div>
        </dl>
      </aside>
    </main>
  )
}

function areAdjacentTiles(from: MapTile, to: MapTile): boolean {
  const deltaX = Math.abs(from.x - to.x)
  const deltaY = Math.abs(from.y - to.y)

  return deltaX + deltaY === 1
}
