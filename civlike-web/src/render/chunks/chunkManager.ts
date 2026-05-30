import type { ActiveTileRect } from './viewportManager'

export type ChunkStats = {
  chunkSize: number
  activeChunkCount: number
}

export function calculateChunkStats(activeRect: ActiveTileRect, chunkSize: number): ChunkStats {
  const minChunkX = Math.floor(activeRect.minX / chunkSize)
  const minChunkY = Math.floor(activeRect.minY / chunkSize)
  const maxChunkX = Math.ceil(activeRect.maxX / chunkSize)
  const maxChunkY = Math.ceil(activeRect.maxY / chunkSize)

  return {
    chunkSize,
    activeChunkCount: Math.max(0, maxChunkX - minChunkX) * Math.max(0, maxChunkY - minChunkY),
  }
}
