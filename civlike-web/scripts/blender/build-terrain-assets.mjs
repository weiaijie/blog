import { existsSync, readdirSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { spawnSync } from 'node:child_process'

const scriptDir = dirname(fileURLToPath(import.meta.url))
const repoRoot = resolve(scriptDir, '..', '..')
const blenderScript = join(scriptDir, 'generate-first-terrain-assets.py')
const cliArgs = process.argv.slice(2)
const seedIndex = cliArgs.indexOf('--seed')
const requestedSeed = seedIndex >= 0 ? cliArgs[seedIndex + 1] : null
const requestedAssets = cliArgs.filter((arg, index) => {
  if (seedIndex < 0) {
    return true
  }

  return index !== seedIndex && index !== seedIndex + 1
})
const defaultAssets = ['terrain-water', 'transition-shoreline', 'terrain-hill', 'terrain-grassland']
const assetIds = requestedAssets.length > 0 ? requestedAssets : defaultAssets

const blenderBin = findBlender()

if (!blenderBin) {
  console.error('Blender was not found on PATH or in C:\\Program Files\\Blender Foundation.')
  console.error('Install Blender, then verify `blender --version`, or set BLENDER_BIN to blender.exe.')
  process.exit(1)
}

const blenderArgs = [
  '--background',
  '--factory-startup',
  '--python',
  blenderScript,
  '--',
  '--repo-root',
  repoRoot,
  '--assets',
  ...assetIds,
]

if (requestedSeed) {
  blenderArgs.push('--seed', requestedSeed)
}

const result = spawnSync(blenderBin, blenderArgs, {
  cwd: repoRoot,
  encoding: 'utf8',
  stdio: 'inherit',
})

process.exit(result.status ?? 1)

function findBlender() {
  if (process.env.BLENDER_BIN && existsSync(process.env.BLENDER_BIN)) {
    return process.env.BLENDER_BIN
  }

  const pathCheck = spawnSync('blender', ['--version'], {
    encoding: 'utf8',
    stdio: 'ignore',
  })

  if (!pathCheck.error && pathCheck.status === 0) {
    return 'blender'
  }

  const blenderRoot = 'C:\\Program Files\\Blender Foundation'

  if (!existsSync(blenderRoot)) {
    return null
  }

  const candidates = readdirSync(blenderRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && entry.name.startsWith('Blender'))
    .map((entry) => join(blenderRoot, entry.name, 'blender.exe'))
    .filter((candidate) => existsSync(candidate))
    .sort()
    .reverse()

  return candidates[0] ?? null
}
