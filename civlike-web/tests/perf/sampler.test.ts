import { describe, expect, it } from 'vitest'
import { PerformanceSampler } from '../../src/perf/sampler'

describe('PerformanceSampler', () => {
  it('summarizes frame timings', () => {
    const sampler = new PerformanceSampler()

    sampler.start('PERF-MAP-16-PAN')
    sampler.sample(100)
    sampler.sample(116)
    sampler.sample(132)
    sampler.sample(164)

    expect(sampler.stop()).toEqual({
      averageFrameMs: 64 / 3,
      frameCount: 3,
      label: 'PERF-MAP-16-PAN',
      maxFrameMs: 32,
      over20MsCount: 1,
      over33MsCount: 0,
      p50FrameMs: 16,
      p95FrameMs: 32,
      topFrameTimesMs: [32, 16, 16],
    })
  })
})
