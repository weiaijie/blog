// @vitest-environment jsdom

import { describe, expect, it } from 'vitest'
import { installCivPerfApi, type CivPerfApi } from '../../src/perf/civPerfApi'

describe('civ perf browser API', () => {
  it('installs the browser automation API on window', () => {
    const api: CivPerfApi = {
      dragCamera: () => undefined,
      getStats: () => ({}),
      loadScenario: () => undefined,
      setExploration: () => undefined,
      startTrace: () => undefined,
      stopTrace: () => ({
        averageFrameMs: 0,
        frameCount: 0,
        label: 'test',
        maxFrameMs: 0,
        over20MsCount: 0,
        over33MsCount: 0,
        p50FrameMs: 0,
        p95FrameMs: 0,
        topFrameTimesMs: [],
      }),
      zoomCamera: () => undefined,
    }

    installCivPerfApi(api)

    expect(window.__civPerf).toBe(api)
    expect(document.documentElement.dataset.civPerf).toBe('ready')
  })
})
