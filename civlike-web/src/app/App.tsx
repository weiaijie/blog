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
import { areHexNeighbors } from '../game/simulation/hexGrid'
import { createInitialGameState, type GameState, type ScenarioId } from '../game/state/gameState'
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
  const [gameState, setGameState] = useState(() =>
    createInitialGameState(1001, { scenarioId: getInitialScenarioId() }),
  )
  const [selectedUnitId, setSelectedUnitId] = useState<string | null>(null)
  const [commandError, setCommandError] = useState<string | null>(null)
  const [savedGameJson, setSavedGameJson] = useState<string | null>(null)
  const [saveStatus, setSaveStatus] = useState('无')
  const [persistentSaveStatus, setPersistentSaveStatus] = useState('检查中')
  const [discoveryStatus, setDiscoveryStatus] = useState('等待侦察兵移动')
  const [eventLog, setEventLog] = useState<string[]>(['等待事件'])

  function runCommand(command: RuleCommand): boolean {
    const exploredBefore = getExploredTileCount(gameState, command.playerId)
    const result = tryApplyRuleCommand(gameState, command)

    if (!result.ok) {
      setCommandError(`${result.code}: ${result.reason}`)
      return false
    }

    setCommandError(null)
    const discoveryEvent = updateDiscoveryStatus(command, result.state, exploredBefore)
    pushEvents([
      ...getCommandEvents(gameState, result.state, command),
      ...(discoveryEvent ? [discoveryEvent] : []),
    ])
    if (command.type === 'FOUND_CITY') {
      setSelectedUnitId(null)
    }
    setGameState(result.state)
    return true
  }

  function pushEvents(events: string[]): void {
    if (events.length === 0) {
      return
    }

    setEventLog((currentEvents) => [...events, ...currentEvents.filter((event) => event !== '等待事件')].slice(0, 5))
  }

  function updateDiscoveryStatus(
    command: RuleCommand,
    nextState: GameState,
    exploredBefore: number,
  ): string | null {
    if (command.type !== 'MOVE_UNIT') {
      return null
    }

    const exploredAfter = getExploredTileCount(nextState, command.playerId)
    const newTiles = Math.max(0, exploredAfter - exploredBefore)
    const target = Math.min(20, nextState.map.tiles.length)

    if (newTiles > 0) {
      setDiscoveryStatus(`本次新发现 ${newTiles} 个地块，累计 ${Math.min(exploredAfter, target)} / ${target}`)
      return `新发现：${newTiles} 个地块，累计 ${Math.min(exploredAfter, target)} / ${target}`
    }

    setDiscoveryStatus(`本次没有新发现，累计 ${Math.min(exploredAfter, target)} / ${target}`)
    return null
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

  function setCapitalSettlerProduction(): void {
    runCommand({
      cityId: 'city:capital',
      playerId: gameState.activePlayerId,
      productionId: 'unit:settler',
      type: 'SET_PRODUCTION',
    })
  }

  function setCapitalWarriorProduction(): void {
    runCommand({
      cityId: 'city:capital',
      playerId: gameState.activePlayerId,
      productionId: 'unit:warrior',
      type: 'SET_PRODUCTION',
    })
  }

  function setSelectedCityProduction(productionId: 'unit:scout' | 'unit:settler' | 'unit:warrior'): void {
    if (!selectedCityCanShowDetails || !selectedCity) {
      setCommandError('SET_PRODUCTION：需要先选择自己的城市。')
      return
    }

    runCommand({
      cityId: selectedCity.id,
      playerId: gameState.activePlayerId,
      productionId,
      type: 'SET_PRODUCTION',
    })
  }

  function foundCity(): void {
    if (!selectedUnit) {
      setCommandError('FOUND_CITY：需要先选择开拓者。')
      return
    }

    runCommand({
      playerId: gameState.activePlayerId,
      tileId: selectedUnit.tileId,
      type: 'FOUND_CITY',
      unitId: selectedUnit.id,
    })
  }

  function attackSelectedTarget(): void {
    if (!selectedUnit || !selectedAttackTarget) {
      setCommandError('ATTACK：需要先选择战士和一个可见相邻敌方单位。')
      return
    }

    runCommand({
      attackerUnitId: selectedUnit.id,
      playerId: gameState.activePlayerId,
      targetUnitId: selectedAttackTarget.id,
      type: 'ATTACK',
    })
  }

  function saveGame(): void {
    const serialized = serializeSavedGame(gameState)

    setSavedGameJson(serialized)
    setSaveStatus(`已保存回合 ${gameState.turn} / 命令 ${gameState.commandLog.length}`)
    setCommandError(null)
    pushEvents([`保存：回合 ${gameState.turn} / 命令 ${gameState.commandLog.length}`])
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
    setDiscoveryStatus(getExplorationSummary(result.state, result.state.activePlayerId))
    setSaveStatus(`已读取回合 ${result.state.turn} / 命令 ${result.state.commandLog.length}`)
    pushEvents([`读取存档：回合 ${result.state.turn} / 命令 ${result.state.commandLog.length}`])
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
    pushEvents([`持久保存：回合 ${gameState.turn} / 命令 ${gameState.commandLog.length}`])
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
    setDiscoveryStatus(getExplorationSummary(result.state, result.state.activePlayerId))
    setPersistentSaveStatus(`已读取回合 ${result.state.turn} / 命令 ${result.state.commandLog.length}`)
    pushEvents([`持久读取：回合 ${result.state.turn} / 命令 ${result.state.commandLog.length}`])
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
  const canFoundCity = selectedUnit?.typeId === 'unit:settler'
  const currentTech = gameState.currentTechByPlayerId[gameState.activePlayerId]
  const currentTechConfig = currentTech ? getTechConfig(currentTech) : null
  const completedTechs = gameState.completedTechByPlayerId[gameState.activePlayerId] ?? []
  const capitalCity = gameState.cities.find((city) => city.id === 'city:capital')
  const currentHash = hashGameState(gameState)
  const capitalYield = capitalCity ? getCityYield(gameState, capitalCity) : null
  const activeExploration = gameState.explorationByPlayerId[gameState.activePlayerId]
  const exploredTileCount = activeExploration?.exploredTileIds.length ?? 0
  const visibleTileCount = activeExploration?.visibleTileIds.length ?? 0
  const explorationTarget = Math.min(20, gameState.map.tiles.length)
  const explorationTargetStatus =
    exploredTileCount >= explorationTarget
      ? `探索目标完成 ${explorationTarget} / ${explorationTarget}`
      : `探索目标未完成 ${Math.min(exploredTileCount, explorationTarget)} / ${explorationTarget}`
  const selectedTileIsVisible = selectedTile
    ? activeExploration?.visibleTileIds.includes(selectedTile.id) ?? false
    : false
  const selectedTileIsExplored = selectedTile
    ? activeExploration?.exploredTileIds.includes(selectedTile.id) ?? false
    : false
  const selectedTileCanShowMapMemory = selectedTileIsVisible || selectedTileIsExplored
  const selectedTileHasOwnCity = selectedCity?.ownerId === gameState.activePlayerId
  const selectedCityCanShowDetails =
    selectedCity?.ownerId === gameState.activePlayerId &&
    (selectedTileIsVisible || selectedTileHasOwnCity)
  const selectedCityYield = selectedCityCanShowDetails && selectedCity
    ? getCityYield(gameState, selectedCity)
    : null
  const selectedTileExplorationStatus = selectedTile
    ? getExplorationStatusLabel(selectedTileIsVisible, selectedTileIsExplored)
    : '无'
  const visibleEnemyUnitsOnSelectedTile = selectedTileIsVisible
    ? selectedUnits.filter((unit) => unit.ownerId !== gameState.activePlayerId)
    : []
  const selectedUnitTile = selectedUnit
    ? gameState.map.tiles.find((tile) => tile.id === selectedUnit.tileId)
    : undefined
  const selectedAttackTarget =
    selectedUnit?.typeId === 'unit:warrior' &&
    selectedUnit.ownerId === gameState.activePlayerId &&
    selectedTile &&
    selectedUnitTile &&
    visibleEnemyUnitsOnSelectedTile.length === 1 &&
    areAdjacentTiles(selectedUnitTile, selectedTile)
      ? visibleEnemyUnitsOnSelectedTile[0]
      : undefined
  const hasAmbiguousAttackTargets =
    selectedUnit?.typeId === 'unit:warrior' &&
    selectedTileIsVisible &&
    visibleEnemyUnitsOnSelectedTile.length > 1
  const attackStatus = getAttackStatus({
    activePlayerId: gameState.activePlayerId,
    hasAmbiguousAttackTargets,
    selectedAttackTargetId: selectedAttackTarget?.id,
    selectedTile,
    selectedTileIsVisible,
    selectedUnit,
    selectedUnitTile,
    visibleEnemyUnitCount: visibleEnemyUnitsOnSelectedTile.length,
  })
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

    const enemyUnitsOnTile = gameState.units.filter(
      (unit) => unit.tileId === tileId && unit.ownerId !== gameState.activePlayerId,
    )

    if (enemyUnitsOnTile.length > 0) {
      setCommandError(null)
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

    let cancelled = false
    let dispose: (() => void) | undefined

    mountPixiStage(host, {
      onStats: setStats,
      onTileSelect: (tileId) => {
        handleTileSelectRef.current(tileId)
      },
    }).then((stage) => {
      if (cancelled) {
        stage.destroy()
        return
      }

      dispose = stage.destroy
      stageRef.current = stage
      stage.setExploration(latestExplorationRef.current)
      setStats(stage.stats)
    })

    return () => {
      cancelled = true
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
          <button type="button" onClick={setCapitalSettlerProduction}>
            生产开拓者
          </button>
          <button type="button" onClick={setCapitalWarriorProduction}>
            生产战士
          </button>
          {canFoundCity ? (
            <button type="button" onClick={foundCity}>
              建立城市
            </button>
          ) : null}
          {selectedAttackTarget ? (
            <button type="button" onClick={attackSelectedTarget}>
              攻击
            </button>
          ) : null}
          {selectedCityCanShowDetails ? (
            <>
              <button type="button" onClick={() => setSelectedCityProduction('unit:scout')}>
                选中城市生产侦察兵
              </button>
              <button type="button" onClick={() => setSelectedCityProduction('unit:settler')}>
                选中城市生产开拓者
              </button>
              <button type="button" onClick={() => setSelectedCityProduction('unit:warrior')}>
                选中城市生产战士
              </button>
            </>
          ) : null}
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
            <p className="objective-hint" aria-label="探索进度">
              探索进度 {Math.min(exploredTileCount, explorationTarget)} / {explorationTarget}
            </p>
            <p className="objective-hint" aria-label="探索目标状态">
              {explorationTargetStatus}
            </p>
            <p className="objective-hint" aria-label="新发现提示">
              {discoveryStatus}
            </p>
            <p className="objective-hint" aria-label="情报说明">
              情报说明：可见=当前情报，已探索=历史地形，未知=隐藏详情
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

        <section className="event-panel" aria-label="最近事件">
          <p className="eyebrow">最近事件</p>
          <ol>
            {eventLog.map((event, index) => (
              <li key={`${event}-${index}`}>{event}</li>
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
            <dt>场景</dt>
            <dd>{gameState.scenarioId}</dd>
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
            <dt>攻击状态</dt>
            <dd>{attackStatus}</dd>
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
            <dt>城市数量</dt>
            <dd>{gameState.cities.length}</dd>
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
            <dt>探索进度</dt>
            <dd>
              {Math.min(exploredTileCount, explorationTarget)} / {explorationTarget}
            </dd>
          </div>
          <div>
            <dt>新发现</dt>
            <dd>{discoveryStatus}</dd>
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
              {selectedTile && selectedTerrain && selectedTileCanShowMapMemory
                ? `${selectedTile.x}, ${selectedTile.y} / ${selectedTerrain.label}`
                : selectedTile ? '未知地块' : '无'}
            </dd>
          </div>
          <div>
            <dt>地块探索状态</dt>
            <dd>{selectedTileExplorationStatus}</dd>
          </div>
          <div>
            <dt>地块产出</dt>
            <dd>
              {selectedTerrain && selectedTileCanShowMapMemory
                ? `食物 ${selectedTerrain.food}，生产 ${selectedTerrain.production}，科研 ${selectedTerrain.science}`
                : selectedTile ? '未知' : '无'}
            </dd>
          </div>
          <div>
            <dt>地块单位</dt>
            <dd>
              {selectedTileIsVisible
                ? selectedUnits.length > 0
                  ? selectedUnits.map((unit) => unit.id).join(', ')
                  : '无'
                : selectedTile
                  ? selectedTileCanShowMapMemory
                    ? '不可见'
                    : '未知'
                  : '无'}
            </dd>
          </div>
          <div>
            <dt>地块单位生命</dt>
            <dd>
              {selectedTileIsVisible
                ? selectedUnits.length > 0
                  ? selectedUnits.map((unit) => `${unit.id} ${unit.hp}/${unit.maxHp}`).join(', ')
                  : '无'
                : selectedTile
                  ? selectedTileCanShowMapMemory
                    ? '不可见'
                    : '未知'
                  : '无'}
            </dd>
          </div>
          <div>
            <dt>地块城市</dt>
            <dd>
              {selectedTileIsVisible
                ? selectedCity
                  ? selectedCity.id
                  : '无'
                : selectedTileHasOwnCity
                  ? selectedCity.id
                : selectedTile
                  ? selectedTileCanShowMapMemory
                    ? '不可见'
                    : '未知'
                  : '无'}
            </dd>
          </div>
          <div>
            <dt>地块城市生产</dt>
            <dd>
              {selectedCityCanShowDetails && selectedCity
                ? selectedCity.productionId ?? '无'
                : selectedTile
                  ? selectedTileCanShowMapMemory
                    ? selectedCity
                      ? '不可见'
                      : '无'
                    : '未知'
                  : '无'}
            </dd>
          </div>
          <div>
            <dt>地块城市进度</dt>
            <dd>
              {selectedCityCanShowDetails && selectedCity
                ? selectedCity.productionProgress
                : selectedTile
                  ? selectedTileCanShowMapMemory
                    ? selectedCity
                      ? '不可见'
                      : '无'
                    : '未知'
                  : '无'}
            </dd>
          </div>
          <div>
            <dt>地块城市产出</dt>
            <dd>
              {selectedCityYield
                ? `食物 ${selectedCityYield.food}，生产 ${selectedCityYield.production}，科研 ${selectedCityYield.science}`
                : selectedTile
                  ? selectedTileCanShowMapMemory
                    ? selectedCity
                      ? '不可见'
                      : '无'
                    : '未知'
                  : '无'}
            </dd>
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
  return areHexNeighbors(from, to)
}

function getAttackStatus({
  activePlayerId,
  hasAmbiguousAttackTargets,
  selectedAttackTargetId,
  selectedTile,
  selectedTileIsVisible,
  selectedUnit,
  selectedUnitTile,
  visibleEnemyUnitCount,
}: {
  activePlayerId: string
  hasAmbiguousAttackTargets: boolean
  selectedAttackTargetId?: string
  selectedTile?: MapTile
  selectedTileIsVisible: boolean
  selectedUnit?: GameState['units'][number]
  selectedUnitTile?: MapTile
  visibleEnemyUnitCount: number
}): string {
  if (selectedAttackTargetId) {
    return `可以攻击 ${selectedAttackTargetId}`
  }

  if (!selectedUnit) {
    return '需要选择己方战士'
  }

  if (selectedUnit.ownerId !== activePlayerId) {
    return '需要选择己方战士'
  }

  if (selectedUnit.typeId !== 'unit:warrior') {
    return '只有战士可以攻击'
  }

  if (!selectedTile || selectedTile.id === selectedUnit.tileId) {
    return '请选择可见相邻敌方单位'
  }

  if (!selectedTileIsVisible) {
    return '目标不可见'
  }

  if (visibleEnemyUnitCount === 0) {
    return '请选择可见相邻敌方单位'
  }

  if (hasAmbiguousAttackTargets) {
    return '目标不明确'
  }

  if (!selectedUnitTile || !areAdjacentTiles(selectedUnitTile, selectedTile)) {
    return '目标不相邻'
  }

  return '请选择可见相邻敌方单位'
}

function getExplorationStatusLabel(isVisible: boolean, isExplored: boolean): string {
  if (isVisible) {
    return '可见'
  }

  if (isExplored) {
    return '已探索'
  }

  return '未知'
}

function getExploredTileCount(state: GameState, playerId: string): number {
  return state.explorationByPlayerId[playerId]?.exploredTileIds.length ?? 0
}

function getExplorationSummary(state: GameState, playerId: string): string {
  const explored = getExploredTileCount(state, playerId)
  const target = Math.min(20, state.map.tiles.length)

  return `累计探索 ${Math.min(explored, target)} / ${target}`
}

function getInitialScenarioId(): ScenarioId {
  if (typeof window === 'undefined') {
    return 'default'
  }

  const scenario = new URLSearchParams(window.location.search).get('scenario')

  return scenario === 'combat' || scenario === 'combat:adjacent-enemy'
    ? 'combat:adjacent-enemy'
    : 'default'
}

function getCommandEvents(previousState: GameState, nextState: GameState, command: RuleCommand): string[] {
  const events: string[] = []
  const previousExplored = getExploredTileCount(previousState, previousState.activePlayerId)
  const nextExplored = getExploredTileCount(nextState, previousState.activePlayerId)
  const target = Math.min(20, nextState.map.tiles.length)

  if (previousExplored < target && nextExplored >= target) {
    events.push(`探索目标完成：${target} / ${target}`)
  }

  const previousUnitIds = new Set(previousState.units.map((unit) => unit.id))
  const newUnits = nextState.units.filter((unit) => !previousUnitIds.has(unit.id))

  for (const unit of newUnits) {
    events.push(`生产完成：${unit.id}`)
  }

  const previousCityIds = new Set(previousState.cities.map((city) => city.id))
  const newCities = nextState.cities.filter((city) => !previousCityIds.has(city.id))

  for (const city of newCities) {
    events.push(`建立城市：${city.id}`)
  }

  if (command.type === 'ATTACK') {
    const previousTarget = previousState.units.find((unit) => unit.id === command.targetUnitId)
    const nextTarget = nextState.units.find((unit) => unit.id === command.targetUnitId)

    if (previousTarget && nextTarget) {
      events.push(
        `攻击：${command.attackerUnitId} -> ${command.targetUnitId}，HP ${previousTarget.hp} -> ${nextTarget.hp}`,
      )
    } else if (previousTarget) {
      events.push(`击败单位：${command.targetUnitId}`)
    }
  }

  const playerIds = nextState.players.map((player) => player.id)

  for (const playerId of playerIds) {
    const previousTechs = new Set(previousState.completedTechByPlayerId[playerId] ?? [])
    const completedTechs = nextState.completedTechByPlayerId[playerId] ?? []

    for (const techId of completedTechs) {
      if (!previousTechs.has(techId)) {
        events.push(`科技完成：${techId}`)
      }
    }
  }

  return events
}
