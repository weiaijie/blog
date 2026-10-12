export type PerfTrace = {
  label: string
  frameCount: number
  averageFrameMs: number
  p50FrameMs: number
  p95FrameMs: number
  maxFrameMs: number
  over20MsCount: number
  over33MsCount: number
  topFrameTimesMs: number[]
}

export class PerformanceSampler {
  private label = 'idle'
  private lastFrameAt = 0
  private frameTimes: number[] = []

  start(label: string): void {
    this.label = label
    this.lastFrameAt = 0
    this.frameTimes = []
  }

  sample(now: number): void {
    if (this.lastFrameAt > 0) {
      this.frameTimes.push(now - this.lastFrameAt)
    }

    this.lastFrameAt = now
  }

  stop(): PerfTrace {
    const frameTimes = [...this.frameTimes].sort((a, b) => a - b)
    const frameCount = frameTimes.length
    const total = frameTimes.reduce((sum, frameTime) => sum + frameTime, 0)
    const p50Index = Math.max(0, Math.ceil(frameCount * 0.5) - 1)
    const p95Index = Math.max(0, Math.ceil(frameCount * 0.95) - 1)

    return {
      label: this.label,
      frameCount,
      averageFrameMs: frameCount > 0 ? total / frameCount : 0,
      p50FrameMs: frameTimes[p50Index] ?? 0,
      p95FrameMs: frameTimes[p95Index] ?? 0,
      maxFrameMs: frameTimes[frameTimes.length - 1] ?? 0,
      over20MsCount: frameTimes.filter((frameTime) => frameTime > 20).length,
      over33MsCount: frameTimes.filter((frameTime) => frameTime > 33).length,
      topFrameTimesMs: frameTimes.slice(-5).reverse(),
    }
  }
}
