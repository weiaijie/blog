import type { PerfTrace } from './sampler'

export type PerfScenarioId = 'default-16' | 'perf-stress-20' | 'perf-stress-32' | 'perf-stress-64'

export type PerfExplorationSnapshot = {
  exploredTileIds: string[]
  visibleTileIds: string[]
}

export type CivPerfApi = {
  loadScenario: (scenarioId: PerfScenarioId) => void
  setExploration: (exploration: PerfExplorationSnapshot | null) => void
  startTrace: (label: string) => void
  stopTrace: () => PerfTrace
  dragCamera: (deltaX: number, deltaY: number, steps?: number) => void
  zoomCamera: (delta: number, steps?: number) => void
  getStats: () => unknown
}

declare global {
  interface Window {
    __civPerf?: CivPerfApi
  }
}

export function installCivPerfApi(api: CivPerfApi): void {
  window.__civPerf = api
  document.documentElement.dataset.civPerf = 'ready'
}
