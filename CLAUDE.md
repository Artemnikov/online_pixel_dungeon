# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Frontend** (dev server on :5173):
```bash
cd frontend && npm run dev
npm run lint
npm run build
```

**Backend** (uvicorn on :8080):
```bash
cd backend && source venv/bin/activate && python app/main.py
```

**Full stack via Docker** (frontend :3000, backend :8080):
```bash
docker compose up
docker compose build
```

**Tests** (run inside Docker):
```bash
./run_tests.sh
```
Test files live in `backend/tests/` — individual tests can be run with `docker compose exec backend python tests/<test_file>.py`.

## Architecture

Real-time multiplayer dungeon crawler. Client-server over WebSockets.

**Backend** (`backend/app/`):
- `main.py` — FastAPI entry point, `ConnectionManager` handles WebSocket connections and broadcasts game state to all players
- `engine/manager.py` — `GameInstance`: central game loop, owns all game state, coordinates systems
- `engine/dungeon/` — procedural level generation (sewers algorithm, rooms, corridors, terrain)
- `engine/entities/base.py` — `Entity` base class; `Player`, `Mob`, `Item`, `Weapon`, `Potion` subclasses
- `engine/systems/` — combat, AI, vision/LOS, inventory systems
- `api/` — REST endpoints (auth, character selection)

**Frontend** (`frontend/src/`):
- `App.jsx` — main canvas game loop, WebSocket client, input handling
- `rendering/sewers/draw.js` — tile rendering, sprite sheets, animations (32×32 tiles, 2× scale)
- `CharacterSelection.jsx`, `WelcomeScreen.jsx` — pre-game screens
- `audio/AudioManager.js` — music and SFX

**Assets** (`assets/` and `frontend/src/assets/pixel-dungeon/`) — Shattered Pixel Dungeon sprites, tilesets, themes, audio.

## Key Patterns

- Game state lives entirely on the server (`GameInstance`); frontend is a pure renderer
- WebSocket messages carry full game state snapshots (not deltas)
- Dungeon is 50 floors; floor gen is in `engine/dungeon/sewers_generation.py`
- Bosses spawn every 5 floors
- Vision uses line-of-sight; factions determine friendly-fire behavior
