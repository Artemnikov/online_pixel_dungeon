# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Important
This project is a remake of the original shattered pixel dungeon game.
Before implementing anything, find the exact flow rules from the original project at ../shattered-pixel-dungeon and implement based on the original game rules logic and map building.

## Commands

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

## Debugging Tile Rendering / Map Analysis

Dev build exposes `window.__debug` (see `frontend/src/dev/useDebugApi.js`). When investigating rendering, vision, or map bugs, use `mcp__chrome-devtools` to navigate to `http://localhost:5173`, start a game, then `evaluate_script` against the page:

- `__debug.ascii()` — ASCII map with entities overlaid
- `__debug.at(x, y)` — tile id/name + entities at cell + visibility/door state
- `__debug.entities()` — players + mobs with positions
- `__debug.vision()`, `__debug.camera()`, `__debug.me()`, `__debug.depth()`, `__debug.bounds()`
- `__debug.help()` — list all

Prefer `evaluate_script` over `take_screenshot` — cheaper and gives structured data. Screenshot only when the data looks correct but visuals look wrong.

## Key Patterns

- Game state lives entirely on the server (`GameInstance`); frontend is a pure renderer
- WebSocket messages carry full game state snapshots (not deltas)
- Dungeon is 50 floors; floor gen is in `engine/dungeon/sewers_generation.py`
- Bosses spawn every 5 floors
- Vision uses line-of-sight; factions determine friendly-fire behavior