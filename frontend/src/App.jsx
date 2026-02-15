import { useEffect, useRef, useState } from 'react'
import './App.css'

import sewerTiles from './assets/pixel-dungeon/environment/tiles_sewers.png';
import warriorSprite from './assets/pixel-dungeon/sprites/warrior.png';
import mageSprite from './assets/pixel-dungeon/sprites/mage.png';
import rogueSprite from './assets/pixel-dungeon/sprites/rogue.png';
import huntressSprite from './assets/pixel-dungeon/sprites/huntress.png';
import itemsSprite from './assets/pixel-dungeon/sprites/items.png';

import ratSprite from './assets/pixel-dungeon/sprites/rat.png';
import batSprite from './assets/pixel-dungeon/sprites/bat.png';
import AudioManager from './audio/AudioManager';
import CharacterSelection from './CharacterSelection';


const TILE_SIZE = 32
const TILE_SCALE = 2; // scale factor to draw 16x16 assets at 32x32
const INTERPOLATION_SPEED = 0.2 // Speed of moving towards server position
const PROJECTILE_SPEED = 0.5; // Tiles per frame? No, that's slow. 15px/frame?

// Item Sprite Mapping (Simplified based on ItemSpriteSheet.java)
// Format: { name_keyword: [col, row] }
const ITEM_SPRITES = {
  // Weapon Tier 1
  "Shortsword": [13, 13],
  "Mage's Staff": [15, 16],
  "Dagger": [12, 13],
  "Spirit Bow": [0, 10], // Assuming MISSILE_WEP starts at row 10, col 0? No, col 16/16. Let's approximate.

  // Weapon Tier 2
  "Wooden Club": [15, 15], // Cudgel
  "Spear": [0, 7],

  // Wearable
  "Cloth Armor": [15, 12],
  "Leather Vest": [14, 13],
  "Rogue's Cloak": [9, 15], // Cloak artifact maybe?
  "Broken Shield": [12, 16], // Buckler?

  // Potions
  "Potion": [12, 14],

  // Default
  "default": [8, 13],

  // Throwables (Approximated)
  "Stone": [10, 10],
  "Boomerang": [11, 10],
  "Throwable Dagger": [12, 13] // Same as Dagger
};

// Helper to get sprite coords
const getItemSpriteCoords = (itemName, itemType) => {
  for (const key in ITEM_SPRITES) {
    if (itemName && itemName.includes(key)) {
      return ITEM_SPRITES[key];
    }
  }
  if (itemType === 'potion') return [12, 14];
  if (itemType === 'weapon') return [14, 14];
  if (itemType === 'wearable') return [14, 12];

  if (itemType === 'throwable') return [11, 10]; // Fallback for throwables
  return ITEM_SPRITES["default"];
}

function App() {
  const canvasRef = useRef(null)
  const [grid, setGrid] = useState([])
  const gridRef = useRef([]);
  const socketRef = useRef(null)

  // Using refs for mutable state that doesn't trigger re-renders
  // This is better for the high-frequency animation loop
  const entitiesRef = useRef({ players: {}, mobs: {} })
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 })
  const [messages, setMessages] = useState([])
  const [gameId] = useState("default-lobby")
  const [myPlayerId, setMyPlayerId] = useState(null)
  const myPlayerIdRef = useRef(null) // Ref for stable access inside the effect
  const [viewport, setViewport] = useState({ width: 800, height: 600 })
  const [showInventory, setShowInventory] = useState(false)
  const [inventory, setInventory] = useState([])
  const [equippedItems, setEquippedItems] = useState({ weapon: null, wearable: null })
  const [targetingMode, setTargetingMode] = useState(false)

  const projectilesRef = useRef([])
  const lastKeyRef = useRef({ key: null, time: 0 }) // For double-tap detection

  const [gameState, setGameState] = useState('SELECT'); // 'SELECT', 'PLAYING'
  const [selectedClass, setSelectedClass] = useState('warrior');

  useEffect(() => {
    const enableAudio = () => {
      AudioManager.play('SILENCE'); // Just to resume context if needed
      window.removeEventListener('click', enableAudio);
      window.removeEventListener('keydown', enableAudio);
    };
    window.addEventListener('click', enableAudio);
    window.addEventListener('keydown', enableAudio);
    return () => {
      window.removeEventListener('click', enableAudio);
      window.removeEventListener('keydown', enableAudio);
    };
  }, []);

  const [myStats, setMyStats] = useState({ hp: 0, maxHp: 10, name: "" })
  const [difficulty, setDifficulty] = useState("normal")
  const visionRef = useRef({ visible: new Set(), discovered: new Set() })
  const [camera, setCamera] = useState({ x: 0, y: 0 })
  const [playersState, setPlayersState] = useState({})
  const [assetImages, setAssetImages] = useState({
    tiles: null,
    warrior: null,
    mage: null,
    rogue: null,
    huntress: null,
    items: null,
    rat: null,
    bat: null,
  });

  useEffect(() => {
    const loadImage = (src, key) => {
      const img = new Image();
      img.src = src;
      img.onload = () => {
        setAssetImages(prev => ({ ...prev, [key]: img }));
      };
    }

    loadImage(sewerTiles, 'tiles');
    loadImage(warriorSprite, 'warrior');
    loadImage(mageSprite, 'mage');
    loadImage(rogueSprite, 'rogue');
    loadImage(huntressSprite, 'huntress');
    loadImage(itemsSprite, 'items');
    loadImage(ratSprite, 'rat');
    loadImage(batSprite, 'bat');
  }, []);

  const equipItem = (itemId) => {
    socketRef.current.send(JSON.stringify({ type: 'EQUIP_ITEM', item_id: itemId }))
  }

  const dropItem = (itemId) => {
    socketRef.current.send(JSON.stringify({ type: 'DROP_ITEM', item_id: itemId }))
  }

  const changeDifficulty = (level) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type: 'CHANGE_DIFFICULTY', difficulty: level }))
    }
  }

  const useItem = (itemId) => {
    socketRef.current.send(JSON.stringify({ type: 'USE_ITEM', item_id: itemId }))
  }

  const handleCanvasClick = (e) => {
    if (!targetingMode) return;
    if (!canvasRef.current) return;

    const rect = canvasRef.current.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;

    // Adjust for camera
    const worldX = clickX + camera.x;
    const worldY = clickY + camera.y;

    const tileX = Math.floor(worldX / TILE_SIZE);
    const tileY = Math.floor(worldY / TILE_SIZE);

    // Fire!
    // Use optimistic item ID if set (string), otherwise currently equipped
    const weaponId = typeof targetingMode === 'string' ? targetingMode : equippedItems.weapon?.id;

    if (weaponId) {
      socketRef.current.send(JSON.stringify({
        type: 'RANGED_ATTACK',
        item_id: weaponId,
        target_x: tileX,
        target_y: tileY
      }));
      setTargetingMode(true); // Keep targeting on (reverting to boolean)
    }
  };

  const handleToolbarClick = (item) => {
    if (!item) {
      setShowInventory(true);
      return;
    }
    if (item.type === 'potion') {
      useItem(item.id);
    } else {
      // If it's a weapon
      if (item.type === 'weapon') {
        const isEquipped = equippedItems.weapon && equippedItems.weapon.id === item.id;

        if (!isEquipped) {
          equipItem(item.id);
          // If ranged, optimistically enter targeting mode using the item's ID
          if (item.range && item.range > 1) {
            setTargetingMode(item.id);
          } else {
            setTargetingMode(false);
          }
        } else {
          // Already equipped. Toggle targeting if ranged.
          if (item.range && item.range > 1) {
            setTargetingMode(prev => !prev);
          }
        }
      } else if (item.type === 'wearable') {
        equipItem(item.id);
      } else if (item.type === 'throwable') {
        // Throwable items: toggle targeting mode specifically for this item
        if (targetingMode === item.id) {
          setTargetingMode(false);
        } else {
          setTargetingMode(item.id);
        }
      }
    }
  };

  const handleToolbarDoubleClick = (item) => {
    const isRangedWeapon = item && item.type === 'weapon' && item.range && item.range > 1;
    const isThrowable = item && item.type === 'throwable';

    if (isRangedWeapon || isThrowable) {
      // Auto-target nearest
      const myPlayer = entitiesRef.current.players[myPlayerIdRef.current];
      if (!myPlayer) return;

      let nearestMob = null;
      let minDist = item.range + 1;

      Object.values(entitiesRef.current.mobs).forEach(mob => {
        if (!visionRef.current.visible.has(`${Math.round(mob.renderPos.x)},${Math.round(mob.renderPos.y)}`)) return;

        // Use renderPos for both player and mob to get accurate visual distance
        // myPlayer.pos is not constantly updated in the ref (only initial), so it becomes stale.
        const dx = mob.renderPos.x - myPlayer.renderPos.x;
        const dy = mob.renderPos.y - myPlayer.renderPos.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist <= item.range && dist < minDist) {
          minDist = dist;
          nearestMob = mob;
        }
      });

      if (nearestMob) {
        const targetX = Math.round(nearestMob.renderPos.x);
        const targetY = Math.round(nearestMob.renderPos.y);
        socketRef.current.send(JSON.stringify({
          type: 'RANGED_ATTACK',
          item_id: item.id,
          target_x: targetX,
          target_y: targetY
        }));
      }
    }
  };


  useEffect(() => {
    if (gameState !== 'PLAYING') return;

    const ws = new WebSocket(`ws://${window.location.hostname}:8000/ws/game/${gameId}?class_type=${selectedClass}&difficulty=${difficulty}`)
    socketRef.current = ws

    ws.onopen = () => setMessages(prev => [...prev, "Connected to server"])
    ws.onerror = () => setMessages(prev => [...prev, "Connection error!"])

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'INIT') {
        setGrid(data.grid)
        gridRef.current = data.grid;
        visionRef.current.discovered = new Set()
        setDimensions({ width: data.width * TILE_SIZE, height: data.height * TILE_SIZE })
        if (data.player_id) {
          setMyPlayerId(data.player_id)
          myPlayerIdRef.current = data.player_id
        }
      } else if (data.type === 'STATE_UPDATE') {
        if (data.difficulty) setDifficulty(data.difficulty)
        // Sync players
        const currentServerPlayerIds = new Set(data.players.map(p => p.id))
        Object.keys(entitiesRef.current.players).forEach(id => {
          if (!currentServerPlayerIds.has(id)) {
            delete entitiesRef.current.players[id]
          }
        })

        data.players.forEach(p => {
          if (p.id === myPlayerIdRef.current) {
            setInventory(p.inventory || [])
            setEquippedItems({
              weapon: p.equipped_weapon,
              wearable: p.equipped_wearable
            })
            // Calculate total max hp for display
            const healthBoost = p.equipped_wearable ? p.equipped_wearable.health_boost : 0
            setMyStats({
              hp: p.hp,
              maxHp: p.max_hp + healthBoost,
              name: p.name,
              isDowned: p.is_downed,
              isRegen: (p.regen_ticks || 0) > 0
            })
          }

          if (!entitiesRef.current.players[p.id]) {
            entitiesRef.current.players[p.id] = { ...p, renderPos: { x: p.pos.x, y: p.pos.y }, facing: 'RIGHT' }
          } else {
            const currentTarget = entitiesRef.current.players[p.id].targetPos || entitiesRef.current.players[p.id].renderPos;
            const dx = p.pos.x - currentTarget.x;
            const dy = p.pos.y - currentTarget.y;

            if (Math.abs(dx) > Math.abs(dy)) {
              if (dx > 0) entitiesRef.current.players[p.id].facing = 'RIGHT';
              else if (dx < 0) entitiesRef.current.players[p.id].facing = 'LEFT';
            } else {
              if (dy > 0) entitiesRef.current.players[p.id].facing = 'DOWN';
              else if (dy < 0) entitiesRef.current.players[p.id].facing = 'UP';
            }

            entitiesRef.current.players[p.id].targetPos = p.pos
            entitiesRef.current.players[p.id].name = p.name
            entitiesRef.current.players[p.id].hp = p.hp
            entitiesRef.current.players[p.id].max_hp = p.max_hp
            entitiesRef.current.players[p.id].equipped_wearable = p.equipped_wearable
            entitiesRef.current.players[p.id].is_downed = p.is_downed
            entitiesRef.current.players[p.id].regen_ticks = p.regen_ticks
            entitiesRef.current.players[p.id].class_type = p.class_type
          }
        })

        // Trigger re-render for DOM-based players
        setPlayersState({ ...entitiesRef.current.players })

        // Sync mobs
        const currentServerMobIds = new Set(data.mobs.map(m => m.id))
        Object.keys(entitiesRef.current.mobs).forEach(id => {
          if (!currentServerMobIds.has(id)) {
            delete entitiesRef.current.mobs[id]
          }
        })

        data.mobs.forEach(m => {
          if (!entitiesRef.current.mobs[m.id]) {
            entitiesRef.current.mobs[m.id] = { ...m, renderPos: { x: m.pos.x, y: m.pos.y }, facing: 'RIGHT' }
          } else {
            const currentTarget = entitiesRef.current.mobs[m.id].targetPos || entitiesRef.current.mobs[m.id].renderPos;
            if (m.pos.x > currentTarget.x) entitiesRef.current.mobs[m.id].facing = 'RIGHT';
            else if (m.pos.x < currentTarget.x) entitiesRef.current.mobs[m.id].facing = 'LEFT';

            entitiesRef.current.mobs[m.id].targetPos = m.pos
            entitiesRef.current.mobs[m.id].hp = m.hp
          }
        })

        // Sync items (for rendering on floor)
        entitiesRef.current.items = data.items || []

        if (data.visible_tiles) {
          const newVisible = new Set(data.visible_tiles.map(t => `${t[0]},${t[1]}`))
          visionRef.current.visible = newVisible
          newVisible.forEach(t => visionRef.current.discovered.add(t))
        }

        if (data.events) {
          data.events.forEach(event => {
            if (event.type === 'MOVE') {
              // console.log('[App] MOVE event:', event.data, 'MyID:', myPlayerIdRef.current);
              if (event.data.entity === myPlayerIdRef.current) {
                // Check tile type for audio
                const tileX = event.data.x;
                const tileY = event.data.y;

                if (gridRef.current[tileY] && gridRef.current[tileY][tileX]) {
                  const tileType = gridRef.current[tileY][tileX];
                  console.log('[App] Calling playStep with tileType:', tileType);
                  AudioManager.playStep(tileType);
                } else {
                  console.warn('[App] Grid lookup failed for audio:', tileX, tileY);
                  AudioManager.play('MOVE');
                }
              } else {
                // Only play MOVE for others if we want to hear them? 
                // Original code played MOVE for everyone at line 394 unconditionally.
                // But wait, line 394 is OUTSIDE the player check.
              }

              // Original logic played MOVE for everyone including self.
              // IF we want to replace the sound for self, we should probably NOT play 'MOVE' again if we played 'playStep'.
              if (event.data.entity !== myPlayerIdRef.current) {
                AudioManager.play(event.type);
              }
            }
            if (event.type === 'RANGED_ATTACK') {
              // Add projectile
              const startX = event.data.x * TILE_SIZE + TILE_SIZE / 2;
              const startY = event.data.y * TILE_SIZE + TILE_SIZE / 2;
              const targetX = event.data.target_x * TILE_SIZE + TILE_SIZE / 2;
              const targetY = event.data.target_y * TILE_SIZE + TILE_SIZE / 2;

              projectilesRef.current.push({
                x: startX,
                y: startY,
                startX: startX,
                startY: startY,
                targetX: targetX,
                targetY: targetY,
                type: event.data.projectile || 'arrow',
                progress: 0,
                finished: false
              });
              AudioManager.play('ATTACK_BOW'); // Or distinguish based on type
            }
          });
        }
      }
    }

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    }
  }, [gameId, gameState])

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'f') {
        setShowInventory(prev => !prev)
        return
      }

      let direction = null
      if (e.key === 'ArrowUp' || e.key === 'w') direction = 'UP'
      if (e.key === 'ArrowDown' || e.key === 's') direction = 'DOWN'
      if (e.key === 'ArrowLeft' || e.key === 'a') direction = 'LEFT'
      if (e.key === 'ArrowRight' || e.key === 'd') direction = 'RIGHT'

      // Toolbar hotkeys 1-5
      if (['1', '2', '3', '4', '5'].includes(e.key)) {
        const index = parseInt(e.key) - 1;
        const item = inventory[index];
        if (item) {
          const now = Date.now();
          const isDoubleTap = lastKeyRef.current.key === e.key && (now - lastKeyRef.current.time) < 300;

          if (isDoubleTap) {
            handleToolbarDoubleClick(item);
            lastKeyRef.current = { key: null, time: 0 }; // Reset
          } else {
            handleToolbarClick(item);
            lastKeyRef.current = { key: e.key, time: now };
          }
        }
      }

      if (direction && socketRef.current?.readyState === WebSocket.OPEN) {
        socketRef.current.send(JSON.stringify({ type: 'MOVE', direction }))
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [inventory, handleToolbarClick, handleToolbarDoubleClick, socketRef, setShowInventory]) // Added dependencies

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animationFrameId;

    const tileMap = {
      1: { x: 0, y: 3 }, // Wall
      2: { x: 0, y: 0 }, // Floor
    };

    const drawGrid = () => {
      for (let y = 0; y < grid.length; y++) {
        for (let x = 0; x < grid[y].length; x++) {
          const tile = grid[y][x];
          if (tile === 0) continue;

          const key = `${x},${y}`;
          const isVisible = visionRef.current.visible.has(key);
          const isDiscovered = visionRef.current.discovered.has(key);

          if (!isDiscovered) {
            ctx.fillStyle = 'black';
            ctx.fillRect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
          } else {
            const tileCoords = tileMap[tile];
            if (tileCoords && assetImages.tiles) {
              ctx.drawImage(
                assetImages.tiles,
                tileCoords.x * (TILE_SIZE / TILE_SCALE),
                tileCoords.y * (TILE_SIZE / TILE_SCALE),
                TILE_SIZE / TILE_SCALE,
                TILE_SIZE / TILE_SCALE,
                x * TILE_SIZE,
                y * TILE_SIZE,
                TILE_SIZE,
                TILE_SIZE
              );
            } else {
              if (tile === 3) ctx.fillStyle = '#855'; // DOOR
              else if (tile === 4) ctx.fillStyle = '#aa4'; // STAIRS_UP
              else if (tile === 5) ctx.fillStyle = '#4aa'; // STAIRS_DOWN
              ctx.fillRect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
            }

            if (!isVisible) {
              ctx.fillStyle = 'rgba(0, 0, 0, 0.6)';
              ctx.fillRect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
            }
          }
        }
      }
    };

    const drawItems = () => {
      if (entitiesRef.current.items) {
        entitiesRef.current.items.forEach(item => {
          if (!visionRef.current.visible.has(`${item.pos.x},${item.pos.y}`)) return;

          if (assetImages.items) {
            const coords = getItemSpriteCoords(item.name, item.type);
            ctx.drawImage(
              assetImages.items,
              coords[0] * (TILE_SIZE / TILE_SCALE), // sx
              coords[1] * (TILE_SIZE / TILE_SCALE), // sy
              TILE_SIZE / TILE_SCALE, // sWidth
              TILE_SIZE / TILE_SCALE, // sHeight
              item.pos.x * TILE_SIZE,
              item.pos.y * TILE_SIZE,
              TILE_SIZE,
              TILE_SIZE
            );
          } else {
            ctx.fillStyle = item.type === 'weapon' ? '#f1c40f' : '#9b59b6';
            ctx.beginPath();
            ctx.arc(item.pos.x * TILE_SIZE + TILE_SIZE / 2, item.pos.y * TILE_SIZE + TILE_SIZE / 2, 6, 0, Math.PI * 2);
            ctx.fill();
          }
        });
      }
    };

    const drawMobs = () => {
      Object.values(entitiesRef.current.mobs).forEach(mob => {
        if (!visionRef.current.visible.has(`${Math.round(mob.renderPos.x)},${Math.round(mob.renderPos.y)}`)) return;

        if (mob.targetPos) {
          mob.renderPos.x += (mob.targetPos.x - mob.renderPos.x) * INTERPOLATION_SPEED;
          mob.renderPos.y += (mob.targetPos.y - mob.renderPos.y) * INTERPOLATION_SPEED;
        }

        let mobSprite = assetImages.rat;
        if (mob.name === 'Bat') {
          mobSprite = assetImages.bat;
        }

        const x = mob.renderPos.x * TILE_SIZE;
        const y = mob.renderPos.y * TILE_SIZE;

        if (mobSprite) {
          ctx.save();
          if (mob.facing === 'LEFT') {
            ctx.translate(x + TILE_SIZE, y);
            ctx.scale(-1, 1);
            ctx.drawImage(
              mobSprite,
              0, // sx
              0, // sy
              TILE_SIZE / TILE_SCALE, // sWidth
              TILE_SIZE / TILE_SCALE, // sHeight
              0, // dx (relative to translated origin)
              0, // dy
              TILE_SIZE,
              TILE_SIZE
            );
          } else {
            ctx.drawImage(
              mobSprite,
              0, // sx
              0, // sy
              TILE_SIZE / TILE_SCALE, // sWidth
              TILE_SIZE / TILE_SCALE, // sHeight
              x,
              y,
              TILE_SIZE,
              TILE_SIZE
            );
          }
          ctx.restore();
        } else {
          ctx.fillStyle = '#e74c3c';
          ctx.fillRect(x + 4, y + 4, TILE_SIZE - 8, TILE_SIZE - 8);
        }

        const mobHpBarWidth = TILE_SIZE - 8;
        const mobHpPercent = (mob.hp || 0) / (mob.max_hp || 1);
        ctx.fillStyle = '#111';
        ctx.fillRect(x + 4, y - 4, mobHpBarWidth, 3);
        ctx.fillStyle = '#e74c3c';
        ctx.fillRect(x + 4, y - 4, mobHpBarWidth * mobHpPercent, 3);
      });
    };

    const drawPlayers = () => {
      Object.values(entitiesRef.current.players).forEach(player => {
        if (player.targetPos) {
          player.renderPos.x += (player.targetPos.x - player.renderPos.x) * INTERPOLATION_SPEED;
          player.renderPos.y += (player.targetPos.y - player.renderPos.y) * INTERPOLATION_SPEED;
        }

        const isPlayerVisible = visionRef.current.visible.has(`${Math.round(player.renderPos.x)},${Math.round(player.renderPos.y)}`) || player.id === myPlayerId;
        if (!isPlayerVisible) return;

        const x = player.renderPos.x * TILE_SIZE;
        const y = player.renderPos.y * TILE_SIZE;

        // Select sprite based on class
        let playerSprite = assetImages.warrior;
        if (player.class_type === 'mage' && assetImages.mage) playerSprite = assetImages.mage;
        else if (player.class_type === 'rogue' && assetImages.rogue) playerSprite = assetImages.rogue;
        else if (player.class_type === 'huntress' && assetImages.huntress) playerSprite = assetImages.huntress;

        if (playerSprite) {
          ctx.save();

          // Adjusted source width to 12px to avoid artifacts from adjacent sprites
          const sWidth = 12;
          const dWidth = sWidth * TILE_SCALE;
          const xOffset = (TILE_SIZE - dWidth) / 2;

          if (player.facing === 'LEFT') {
            ctx.translate(x + TILE_SIZE - xOffset, y);
            ctx.scale(-1, 1);
            ctx.drawImage(
              playerSprite,
              0, // Source x
              0, // Source y
              sWidth, // Source width
              TILE_SIZE / TILE_SCALE, // Source height
              0, // dx (relative to translated origin)
              0, // dy
              dWidth,
              TILE_SIZE
            );
          } else {
            // RIGHT, UP, DOWN
            ctx.drawImage(
              playerSprite,
              0, // Source x
              0, // Source y
              sWidth, // Source width
              TILE_SIZE / TILE_SCALE, // Source height
              x + xOffset,
              y,
              dWidth,
              TILE_SIZE
            );
          }
          ctx.restore();
        }

        const hpBarWidth = TILE_SIZE - 4;
        const healthBoost = player.equipped_wearable ? player.equipped_wearable.health_boost : 0;
        const playerHpPercent = player.hp / (player.max_hp + healthBoost);
        ctx.fillStyle = '#111';
        ctx.fillRect(x + 2, y - 12, hpBarWidth, 4);
        ctx.fillStyle = player.is_downed ? '#e74c3c' : (player.regen_ticks > 0 ? '#f1c40f' : '#2ecc71');
        ctx.fillRect(x + 2, y - 12, hpBarWidth * playerHpPercent, 4);

        if (player.is_downed) {
          ctx.fillStyle = '#e74c3c';
          ctx.textAlign = 'center';
          ctx.font = '24px Arial';
          ctx.fillText("☠️", x + TILE_SIZE / 2, y - 25);
        }

        ctx.fillStyle = 'white';
        ctx.font = '10px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(player.name, x + TILE_SIZE / 2, y - 15);
      });
    };

    const drawProjectiles = () => {
      const finishedIndices = [];
      projectilesRef.current.forEach((proj, index) => {
        // Move projectile
        const dx = proj.targetX - proj.startX;
        const dy = proj.targetY - proj.startY;
        const dist = Math.sqrt(dx * dx + dy * dy);

        proj.progress += PROJECTILE_SPEED * 15; // Speed adjustment

        const ratio = dist > 0 ? Math.min(1, proj.progress / dist) : 1;
        proj.x = proj.startX + dx * ratio;
        proj.y = proj.startY + dy * ratio;

        if (ratio >= 1) {
          proj.finished = true;
          finishedIndices.push(index);
        }

        // Draw
        ctx.fillStyle = proj.type === 'magic_bolt' ? '#3498db' : '#ecf0f1';
        ctx.beginPath();
        ctx.arc(proj.x, proj.y, 4, 0, Math.PI * 2);
        ctx.fill();
      });

      // Remove finished
      for (let i = finishedIndices.length - 1; i >= 0; i--) {
        projectilesRef.current.splice(finishedIndices[i], 1);
      }
    };


    const render = () => {
      if (grid.length === 0) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      let cameraX = 0;
      let cameraY = 0;
      const myPlayer = entitiesRef.current.players[myPlayerIdRef.current];

      if (myPlayer) {
        if (myPlayer.targetPos) {
          myPlayer.renderPos.x += (myPlayer.targetPos.x - myPlayer.renderPos.x) * INTERPOLATION_SPEED;
          myPlayer.renderPos.y += (myPlayer.targetPos.y - myPlayer.renderPos.y) * INTERPOLATION_SPEED;
        }
        cameraX = myPlayer.renderPos.x * TILE_SIZE - canvas.width / 2 + TILE_SIZE / 2;
        cameraY = myPlayer.renderPos.y * TILE_SIZE - canvas.height / 2 + TILE_SIZE / 2;
      }

      // Smoothly update camera state without causing infinite re-renders
      // Using simple approach: only update if changed significantly or just use a ref if performance is an issue
      // But for now, let's keep it simple. To avoid React state updates in requestAnimationFrame, 
      // we should ideally use a ref for the camera too if it's just for the transform.
      // However, the component expects 'camera.x' in JSX.
      setCamera({ x: cameraX, y: cameraY });


      ctx.save();
      ctx.translate(-cameraX, -cameraY);

      drawGrid();
      drawItems();
      drawMobs();
      drawPlayers();
      drawProjectiles();
      drawProjectiles();

      ctx.restore();

      animationFrameId = requestAnimationFrame(render);
    };

    render();
    return () => cancelAnimationFrame(animationFrameId);
  }, [grid, myPlayerId, assetImages]);

  // Calculate toolbar items (first 5 items)
  const toolbarItems = Array.from({ length: 5 }).map((_, i) => inventory[i] || null);

  if (gameState === 'SELECT') {
    return <CharacterSelection onSelect={(c, d) => {
      setSelectedClass(c);
      setDifficulty(d);
      setGameState('PLAYING');
    }} />;
  }

  return (
    <div className="game-container">
      {grid.length === 0 && (
        <div className="loading-screen">
          <div className="loading-spinner"></div>
          <div className="loading-text">Loading Dungeon...</div>
        </div>
      )}

      {/* Top Left HUD: Health & Player Info */}
      <div className="top-left-hud">
        <div className="player-status-card">
          <div className="player-portrait">
            {/* Simple placeholder or could be class sprite */}
            <div className="portrait-inner">👤</div>
          </div>
          <div className="player-details">
            <div className="player-name">{myStats.name}</div>
            <div className="health-bar-container-large">
              <div
                className={`health-bar-fill-large ${myStats.isDowned ? 'downed' : myStats.isRegen ? 'regen' : ''}`}
                style={{ width: `${(myStats.hp / myStats.maxHp) * 100}%` }}
              ></div>
              <div className="health-text-large">{Math.ceil(myStats.hp)} / {myStats.maxHp} HP</div>
            </div>
          </div>
        </div>
      </div>

      <div className="canvas-wrapper">
        <canvas
          ref={canvasRef}
          width={viewport.width}
          height={viewport.height}
          className={`game-canvas ${targetingMode ? 'cursor-crosshair' : ''}`}
          onClick={handleCanvasClick}
        />
        <div
          className="player-container"
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: dimensions.width,
            height: dimensions.height,
            transform: `translate(${-camera.x}px, ${-camera.y}px)`,
          }}
        >
          {Object.values(playersState).map(player => (
            <Player key={player.id} player={player} myPlayerId={myPlayerId} />
          ))}
        </div>
      </div>

      {showInventory && (
        <div className="inventory-overlay">
          <div className="inventory-modal">
            <div className="inventory-header">
              <h2>Inventory (20 slots)</h2>
              <button className="close-btn" onClick={() => setShowInventory(false)}>×</button>
            </div>
            <div className="inventory-grid">
              {inventory.map((item, i) => (
                <div key={item.id || i} className="inventory-slot">
                  <div className="item-name">{item.name}</div>
                  <div className="item-type">{item.type}</div>
                  <div className="item-stats">
                    {item.type === 'weapon' ? `Dmg: ${item.damage}` : (item.health_boost ? `HP+: ${item.health_boost}` : '')}
                    {item.type === 'potion' && item.effect === 'regen' && 'Regen 50% HP'}
                    {item.type === 'potion' && item.effect === 'revive' && 'Revives DBNO Ally'}
                  </div>
                  <div className="item-actions">
                    {item.type === 'potion' && (
                      <button className="use-btn" onClick={() => useItem(item.id)}>Drink</button>
                    )}
                    {item.type !== 'potion' && (
                      <button onClick={() => equipItem(item.id)}>Equip</button>
                    )}
                    <button onClick={() => dropItem(item.id)}>Drop</button>
                  </div>
                </div>
              ))}
              {Array.from({ length: 20 - inventory.length }).map((_, i) => (
                <div key={`empty-${i}`} className="inventory-slot empty"></div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Bottom HUD: Toolbar & Status */}
      <div className="game-hud-bottom">

        <div className="toolbar-container">
          <div className="toolbar">
            {toolbarItems.map((item, i) => {
              const spriteCoords = item ? getItemSpriteCoords(item.name, item.type) : null;
              return (
                <div
                  key={i}
                  className={`toolbar-slot ${targetingMode && equippedItems.weapon?.id === item?.id ? 'targeting-active' : ''}`}
                  onClick={() => handleToolbarClick(item)}
                  onDoubleClick={() => handleToolbarDoubleClick(item)}
                >
                  {item ? (
                    <>
                      <div
                        className="toolbar-item-sprite"
                      >
                        <div style={{
                          width: '16px',
                          height: '16px',
                          backgroundImage: `url(${itemsSprite})`,
                          backgroundPosition: `-${spriteCoords[0] * 16}px -${spriteCoords[1] * 16}px`,
                          transform: 'scale(2)',
                          transformOrigin: 'top left',
                          imageRendering: 'pixelated'
                        }}></div>
                      </div>
                      <div className="toolbar-item-name">{item.name.substring(0, 8)}..</div>
                    </>
                  ) : <span className="slot-number">{i + 1}</span>}
                </div>
              );
            })}
          </div>

          <button className="inventory-toggle-btn-bottom" onClick={() => setShowInventory(true)}>
            🎒
          </button>
        </div>

        <div className="connection-log">
          {messages.slice(-3).map((msg, i) => (
            <div key={i} className="log-entry">{msg}</div>
          ))}
        </div>
      </div>

    </div>
  )
}

function Player({ player, myPlayerId }) {
  const isMe = player.id === myPlayerId;
  const healthBoost = player.equipped_wearable ? player.equipped_wearable.health_boost : 0;
  const maxHp = (player.max_hp || 10) + healthBoost;
  const hpPercent = Math.max(0, (player.hp || 0) / maxHp);

  return (
    <div
      className={`player-sprite ${isMe ? 'is-me' : ''}`}
      style={{
        position: 'absolute',
        left: player.renderPos.x * TILE_SIZE,
        top: player.renderPos.y * TILE_SIZE,
        width: TILE_SIZE,
        height: TILE_SIZE,
        transition: 'none', // Managed by interpolation
        zIndex: isMe ? 2 : 1
      }}
    >
      <div className="player-name-plate">
        <div className="hp-bar-small">
          <div
            className={`hp-fill ${player.is_downed ? 'downed' : (player.regen_ticks > 0 ? 'regen' : '')}`}
            style={{ width: `${hpPercent * 100}%` }}
          ></div>
        </div>
        <div className="name-text">{player.name}</div>
        {player.is_downed && <div className="downed-tag">DOWNED</div>}
      </div>
    </div>
  );
}

export default App
