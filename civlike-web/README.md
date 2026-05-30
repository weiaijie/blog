# Civlike Web

First playable Web prototype for the civilization-style game research project.

The implementation follows `../文明类游戏研究/26_开工总体项目规划.md`:

- `src/game/`: pure rule state, commands, validation, simulation, events, config.
- `src/render/`: PixiJS, camera, coordinates, chunks, overlays.
- `src/ui/`: DOM/React panels, tooltips, debug views.
- `src/storage/`: save/load and migrations.
- `src/workers/`: Worker-like protocol and future worker bridge.
- `src/perf/`: performance sampler, scenarios, browser test API.
- `tests/`: simulation, replay, and performance tests.
- `artifacts/perf/`: local performance trace outputs.

## Scripts

```bash
npm run dev
npm run test
npm run typecheck
npm run lint
npm run build
```

## Current Phase

Phase 0 is bootstrapped and Phase 1 map-engine spike has started:

- Vite + React + TypeScript project.
- PixiJS mounted into a fixed WebGL canvas.
- 16x16 default square map and 20x20 stress scenario.
- Initial terrain config.
- Square coordinate helpers with unit tests.
- Camera pan/zoom controller.
- Viewport and chunk statistics.
- Tile pool skeleton.
- `window.__civPerf` browser performance API with a DOM ready marker.
- `npm run perf:map16` writes `artifacts/perf/PERF-MAP-16-PAN.latest.json`.

Next work should continue with Phase 1 map-engine tasks: investigate the current `PERF-MAP-16-PAN` p95 blocker, add `PERF-MAP-20-ZOOM`, and decide whether tile graphics should be culled or kept pooled for the first version.
