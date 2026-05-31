import { useMemo, useState } from 'react'
import { ThreeModuleViewer } from './ThreeModuleViewer'

type GrasslandVariant = {
  fertility: number
  foodYield: number
  id: string
  seed: number
}

const DEFAULT_VARIANT_COUNT = 4

export function GrasslandBlockLab() {
  const initialSeed = useMemo(() => getInitialAssetSeed(), [])
  const [baseSeed, setBaseSeed] = useState(initialSeed)
  const [variantCount, setVariantCount] = useState(DEFAULT_VARIANT_COUNT)
  const variants = useMemo(() => createGrasslandVariants(baseSeed, variantCount), [baseSeed, variantCount])

  function regenerateAll(): void {
    setBaseSeed(createRandomAssetSeed())
  }

  function addVariant(): void {
    setVariantCount((currentCount) => Math.min(8, currentCount + 1))
  }

  function removeVariant(): void {
    setVariantCount((currentCount) => Math.max(1, currentCount - 1))
  }

  function rerollVariant(index: number): void {
    const nextSeed = createRandomAssetSeed()
    setBaseSeed((currentSeed) => mixSeed(currentSeed, nextSeed + index * 97))
  }

  return (
    <main className="grassland-lab">
      <header className="grassland-lab-toolbar">
        <div>
          <p>grassland block lab</p>
          <h1>草原六边形区块变体</h1>
        </div>

        <div className="grassland-lab-actions">
          <button type="button" onClick={regenerateAll}>
            生成一组
          </button>
          <button type="button" onClick={removeVariant} aria-label="减少变体数量">
            -
          </button>
          <span>{variantCount}</span>
          <button type="button" onClick={addVariant} aria-label="增加变体数量">
            +
          </button>
        </div>
      </header>

      <section className="grassland-lab-grid" aria-label="草原区块模型变体">
        {variants.map((variant, index) => (
          <article className="grassland-variant-card" key={variant.id}>
            <div className="grassland-variant-stage">
              <ThreeModuleViewer
                spec={{
                  kind: 'terrain',
                  terrainId: 'grassland',
                  variantSeed: variant.seed,
                }}
              />
            </div>

            <div className="grassland-variant-meta">
              <strong>Variant {index + 1}</strong>
              <span className="grassland-fertility-pill">肥力 {variant.fertility}</span>
              <span className="grassland-food-pill">粮食 {variant.foodYield}</span>
              <code>seed {variant.seed}</code>
              <button type="button" onClick={() => rerollVariant(index)}>
                重掷
              </button>
            </div>
          </article>
        ))}
      </section>
    </main>
  )
}

function createGrasslandVariants(baseSeed: number, count: number): GrasslandVariant[] {
  return Array.from({ length: count }, (_, index) => {
    const seed = mixSeed(baseSeed, index * 10_007 + 47)
    const fertility = Math.round(18 + seededUnit(seed, 'fertility') * 82)

    return {
      fertility,
      foodYield: Math.max(1, Math.min(5, Math.ceil(fertility / 20))),
      id: `grassland-variant-${seed}`,
      seed,
    }
  })
}

function getInitialAssetSeed(): number {
  if (typeof window === 'undefined') {
    return 540_130_471
  }

  const explicitSeed = Number(new URLSearchParams(window.location.search).get('assetSeed'))

  return Number.isInteger(explicitSeed) && explicitSeed > 0 ? explicitSeed : createRandomAssetSeed()
}

function createRandomAssetSeed(): number {
  const randomSource =
    typeof window !== 'undefined' && window.crypto
      ? window.crypto.getRandomValues(new Uint32Array(1))[0]
      : Math.floor(Math.random() * 2_147_483_647)

  return Math.max(1, randomSource % 1_000_000_000)
}

function mixSeed(seed: number, salt: number): number {
  let value = Math.imul(seed ^ salt, 1664525) + 1013904223

  value ^= value >>> 16
  value = Math.imul(value, 2246822519)
  value ^= value >>> 13

  return Math.max(1, (value >>> 0) % 1_000_000_000)
}

function seededUnit(seed: number, salt: string): number {
  let value = Math.imul(seed || 1, 1664525) + 1013904223

  for (let index = 0; index < salt.length; index += 1) {
    value = Math.imul(value ^ salt.charCodeAt(index), 2246822519)
    value ^= value >>> 13
  }

  return (value >>> 0) / 4_294_967_295
}
