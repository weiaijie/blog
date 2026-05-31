import { useEffect, useRef, useState } from 'react'
import {
  mountThreeModuleScene,
  type ModuleSceneSpec,
} from '../../render/visuals/threeModuleScene'

const MAX_ACTIVE_PREVIEWS = 4
const previewRegistry = new Map<
  number,
  {
    host: HTMLElement
    setShouldRender: (value: boolean) => void
  }
>()
let nextPreviewId = 0
let layoutFrame = 0

export function ThreeModuleViewer({ spec }: { spec: ModuleSceneSpec }) {
  const hostRef = useRef<HTMLDivElement | null>(null)
  const [shouldRender, setShouldRender] = useState(false)

  useEffect(() => {
    const host = hostRef.current

    if (!host) {
      return undefined
    }

    return registerPreviewHost(host, setShouldRender)
  }, [])

  useEffect(() => {
    const host = hostRef.current

    if (!host || !shouldRender) {
      return undefined
    }

    const scene = mountThreeModuleScene(host, spec)

    return () => {
      scene.destroy()
    }
  }, [shouldRender, spec])

  return <div ref={hostRef} className="three-module-viewer" />
}

function registerPreviewHost(
  host: HTMLElement,
  setShouldRender: (value: boolean) => void,
): () => void {
  const id = nextPreviewId

  nextPreviewId += 1
  previewRegistry.set(id, { host, setShouldRender })

  if (previewRegistry.size === 1) {
    window.addEventListener('scroll', schedulePreviewLayout, { passive: true })
    window.addEventListener('resize', schedulePreviewLayout)
  }

  schedulePreviewLayout()

  return () => {
    previewRegistry.delete(id)
    setShouldRender(false)

    if (previewRegistry.size === 0) {
      window.removeEventListener('scroll', schedulePreviewLayout)
      window.removeEventListener('resize', schedulePreviewLayout)
    }

    schedulePreviewLayout()
  }
}

function schedulePreviewLayout(): void {
  if (layoutFrame) {
    return
  }

  layoutFrame = window.requestAnimationFrame(() => {
    layoutFrame = 0
    updateActivePreviews()
  })
}

function updateActivePreviews(): void {
  const activeIds = new Set(
    [...previewRegistry.entries()]
      .map(([id, preview]) => {
        const rect = preview.host.getBoundingClientRect()
        const visibleWidth = Math.max(0, Math.min(rect.right, window.innerWidth) - Math.max(rect.left, 0))
        const visibleHeight = Math.max(0, Math.min(rect.bottom, window.innerHeight) - Math.max(rect.top, 0))
        const visibleArea = visibleWidth * visibleHeight
        const centerDistance = Math.abs(rect.top + rect.height / 2 - window.innerHeight / 2)

        return { centerDistance, id, visibleArea }
      })
      .filter((preview) => preview.visibleArea > 0)
      .sort((left, right) => right.visibleArea - left.visibleArea || left.centerDistance - right.centerDistance)
      .slice(0, MAX_ACTIVE_PREVIEWS)
      .map((preview) => preview.id),
  )

  for (const [id, preview] of previewRegistry) {
    preview.setShouldRender(activeIds.has(id))
  }
}
