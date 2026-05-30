export type UiState = {
  selectedTileId: string | null
  mapWidth: number
  mapHeight: number
}

export const initialUiState: UiState = {
  selectedTileId: null,
  mapWidth: 16,
  mapHeight: 16,
}
