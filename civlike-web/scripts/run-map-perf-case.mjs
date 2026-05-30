import { mkdir, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { spawn, spawnSync } from 'node:child_process'
import { chromium } from 'playwright'

const cases = {
  'PERF-MAP-16-PAN': {
    scenarioId: 'default-16',
    artifactName: 'PERF-MAP-16-PAN.latest.json',
    setup: async () => {
      window.__civPerf.zoomCamera(0.7, 10)
      window.__civPerf.dragCamera(-120, -120, 12)
    },
    runFrame: async (index) => {
      window.__civPerf.dragCamera(index % 2 === 0 ? -6 : 5, index % 3 === 0 ? -3 : 2, 1)
    },
  },
  'PERF-MAP-16-FOG-PAN': {
    scenarioId: 'default-16',
    artifactName: 'PERF-MAP-16-FOG-PAN.latest.json',
    explorationSize: 16,
    setup: async () => {
      window.__civPerf.zoomCamera(0.7, 10)
      window.__civPerf.dragCamera(-120, -120, 12)
    },
    runFrame: async (index) => {
      window.__civPerf.dragCamera(index % 2 === 0 ? -6 : 5, index % 3 === 0 ? -3 : 2, 1)
    },
  },
  'PERF-MAP-20-ZOOM': {
    scenarioId: 'perf-stress-20',
    artifactName: 'PERF-MAP-20-ZOOM.latest.json',
    setup: async () => {
      window.__civPerf.dragCamera(-160, -160, 16)
    },
    runFrame: async (index) => {
      window.__civPerf.zoomCamera(index % 2 === 0 ? 0.025 : -0.02, 1)
      window.__civPerf.dragCamera(index % 2 === 0 ? -4 : 4, index % 3 === 0 ? -3 : 2, 1)
    },
  },
  'PERF-MAP-32-PAN': {
    scenarioId: 'perf-stress-32',
    artifactName: 'PERF-MAP-32-PAN.latest.json',
    setup: async () => {
      window.__civPerf.zoomCamera(0.45, 10)
      window.__civPerf.dragCamera(-280, -280, 16)
    },
    runFrame: async (index) => {
      window.__civPerf.dragCamera(index % 2 === 0 ? -8 : 7, index % 3 === 0 ? -5 : 4, 1)
    },
  },
  'PERF-MAP-32-FOG-PAN': {
    scenarioId: 'perf-stress-32',
    artifactName: 'PERF-MAP-32-FOG-PAN.latest.json',
    explorationSize: 32,
    setup: async () => {
      window.__civPerf.zoomCamera(0.45, 10)
      window.__civPerf.dragCamera(-280, -280, 16)
    },
    runFrame: async (index) => {
      window.__civPerf.dragCamera(index % 2 === 0 ? -8 : 7, index % 3 === 0 ? -5 : 4, 1)
    },
  },
  'PERF-MAP-32-ZOOM': {
    scenarioId: 'perf-stress-32',
    artifactName: 'PERF-MAP-32-ZOOM.latest.json',
    setup: async () => {
      window.__civPerf.dragCamera(-280, -280, 16)
    },
    runFrame: async (index) => {
      window.__civPerf.zoomCamera(index % 2 === 0 ? 0.025 : -0.02, 1)
      window.__civPerf.dragCamera(index % 2 === 0 ? -5 : 5, index % 3 === 0 ? -4 : 3, 1)
    },
  },
  'PERF-MAP-64-PAN': {
    scenarioId: 'perf-stress-64',
    artifactName: 'PERF-MAP-64-PAN.latest.json',
    setup: async () => {
      window.__civPerf.zoomCamera(0.3, 10)
      window.__civPerf.dragCamera(-640, -640, 24)
    },
    runFrame: async (index) => {
      window.__civPerf.dragCamera(index % 2 === 0 ? -10 : 9, index % 3 === 0 ? -6 : 5, 1)
    },
  },
  'PERF-MAP-64-FOG-PAN': {
    scenarioId: 'perf-stress-64',
    artifactName: 'PERF-MAP-64-FOG-PAN.latest.json',
    explorationSize: 64,
    setup: async () => {
      window.__civPerf.zoomCamera(0.3, 10)
      window.__civPerf.dragCamera(-640, -640, 24)
    },
    runFrame: async (index) => {
      window.__civPerf.dragCamera(index % 2 === 0 ? -10 : 9, index % 3 === 0 ? -6 : 5, 1)
    },
  },
}

const caseId = process.argv[2] ?? 'PERF-MAP-16-PAN'
const perfCase = cases[caseId]

if (!perfCase) {
  throw new Error(`Unknown perf case: ${caseId}`)
}

const portByCase = {
  'PERF-MAP-16-PAN': 5174,
  'PERF-MAP-16-FOG-PAN': 5179,
  'PERF-MAP-20-ZOOM': 5175,
  'PERF-MAP-32-PAN': 5176,
  'PERF-MAP-32-FOG-PAN': 5180,
  'PERF-MAP-32-ZOOM': 5177,
  'PERF-MAP-64-PAN': 5178,
  'PERF-MAP-64-FOG-PAN': 5181,
}
const port = portByCase[caseId]
const url = `http://127.0.0.1:${port}/`
const artifactDir = resolve('artifacts/perf')
const artifactPath = resolve(artifactDir, perfCase.artifactName)

const server = spawn(
  process.platform === 'win32' ? 'npm.cmd' : 'npm',
  ['run', 'preview', '--', '--host', '127.0.0.1', '--port', String(port)],
  {
    cwd: process.cwd(),
    stdio: 'ignore',
  },
)

try {
  await waitForHttp(url, 20_000)

  const browser = await chromium.launch({
    args: [
      '--disable-background-timer-throttling',
      '--disable-renderer-backgrounding',
      '--disable-frame-rate-limit',
    ],
  })
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } })

  try {
    await page.goto(url, { waitUntil: 'load' })
    await page.waitForFunction(() => document.documentElement.dataset.civPerf === 'ready')

    const result = await page.evaluate(async ({ caseId, perfCase }) => {
      if (!window.__civPerf) {
        throw new Error('window.__civPerf is not installed')
      }

      const setup = new Function(`return (${perfCase.setup})`)()
      const runFrame = new Function(`return (${perfCase.runFrame})`)()

      window.__civPerf.loadScenario(perfCase.scenarioId)

      if (perfCase.explorationSize) {
        window.__civPerf.setExploration(createFogExploration(perfCase.explorationSize))
      }

      await setup()

      for (let index = 0; index < 10; index += 1) {
        await new Promise((resolveFrame) => requestAnimationFrame(resolveFrame))
      }

      window.__civPerf.startTrace(caseId)

      for (let index = 0; index < 120; index += 1) {
        await runFrame(index)
        await new Promise((resolveFrame) => requestAnimationFrame(resolveFrame))
      }

      const trace = window.__civPerf.stopTrace()
      const stats = window.__civPerf.getStats()

      return { stats, trace }

      function createFogExploration(size) {
        const center = Math.floor(size / 2)
        const visibleRange = Math.max(2, Math.floor(size / 8))
        const exploredRange = Math.max(4, Math.floor(size / 3))
        const visibleTileIds = []
        const exploredTileIds = []

        for (let y = 0; y < size; y += 1) {
          for (let x = 0; x < size; x += 1) {
            const distance = Math.abs(x - center) + Math.abs(y - center)
            const tileId = `tile:${x}:${y}`

            if (distance <= exploredRange) {
              exploredTileIds.push(tileId)
            }

            if (distance <= visibleRange) {
              visibleTileIds.push(tileId)
            }
          }
        }

        return { exploredTileIds, visibleTileIds }
      }
    }, {
      caseId,
      perfCase: {
        explorationSize: perfCase.explorationSize,
        scenarioId: perfCase.scenarioId,
        setup: perfCase.setup.toString(),
        runFrame: perfCase.runFrame.toString(),
      },
    })

    const threshold = {
      p95FrameMsWarning: 20,
      p95FrameMsBlocker: 33,
    }
    const payload = {
      caseId,
      createdAt: new Date().toISOString(),
      url,
      mode: 'production-preview',
      viewport: { width: 1280, height: 720 },
      ...result,
      threshold,
      status:
        result.trace.p95FrameMs >= threshold.p95FrameMsBlocker
          ? 'BLOCKER'
          : result.trace.p95FrameMs >= threshold.p95FrameMsWarning
            ? 'WARNING'
            : 'PASS',
    }

    await mkdir(artifactDir, { recursive: true })
    await writeFile(artifactPath, `${JSON.stringify(payload, null, 2)}\n`, 'utf8')
    console.log(`Wrote ${artifactPath}`)
  } finally {
    await browser.close()
  }
} finally {
  stopProcessTree(server)
}

async function waitForHttp(targetUrl, timeoutMs) {
  const startedAt = Date.now()

  while (Date.now() - startedAt < timeoutMs) {
    try {
      const response = await fetch(targetUrl)

      if (response.ok) {
        return
      }
    } catch {
      await delay(250)
    }
  }

  throw new Error(`Timed out waiting for ${targetUrl}`)
}

function delay(ms) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms)
  })
}

function stopProcessTree(childProcess) {
  if (!childProcess.pid) {
    return
  }

  if (process.platform === 'win32') {
    spawnSync('taskkill', ['/pid', String(childProcess.pid), '/T', '/F'], {
      stdio: 'ignore',
    })
    return
  }

  childProcess.kill()
}
