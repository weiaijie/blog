export type TilePoolStats = {
  allocatedTileGraphics: number
}

export class TilePool {
  private allocatedTileGraphics = 0

  setAllocatedTileGraphics(count: number): void {
    this.allocatedTileGraphics = count
  }

  getStats(): TilePoolStats {
    return {
      allocatedTileGraphics: this.allocatedTileGraphics,
    }
  }
}
