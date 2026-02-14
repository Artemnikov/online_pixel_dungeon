import { useEffect, useRef, useState } from 'react'
import './App.css'

const TILE_SIZE = 32
const INTERPOLATION_SPEED = 0.2 // Speed of moving towards server position

function App() {
  const canvasRef = useRef(null)
  const [grid, setGrid] = useState([])
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
  const [myStats, setMyStats] = useState({ hp: 0, maxHp: 10, name: "" })
  const [difficulty, setDifficulty] = useState("normal")
  const visionRef = useRef({ visible: new Set(), discovered: new Set() })

  useEffect(() => {
    const ws = new WebSocket(`ws://${window.location.hostname}:8000/ws/game/${gameId}`)
    socketRef.current = ws

    ws.onopen = () => setMessages(prev => [...prev, "Connected to server"])
    ws.onerror = () => setMessages(prev => [...prev, "Connection error!"])

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'INIT') {
        setGrid(data.grid)
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
            entitiesRef.current.players[p.id] = { ...p, renderPos: { x: p.pos.x, y: p.pos.y } }
          } else {
            entitiesRef.current.players[p.id].targetPos = p.pos
            entitiesRef.current.players[p.id].name = p.name
            entitiesRef.current.players[p.id].hp = p.hp
            entitiesRef.current.players[p.id].max_hp = p.max_hp
            entitiesRef.current.players[p.id].equipped_wearable = p.equipped_wearable
          }
        })

        // Sync mobs
        const currentServerMobIds = new Set(data.mobs.map(m => m.id))
        Object.keys(entitiesRef.current.mobs).forEach(id => {
          if (!currentServerMobIds.has(id)) {
            delete entitiesRef.current.mobs[id]
          }
        })

        data.mobs.forEach(m => {
          if (!entitiesRef.current.mobs[m.id]) {
            entitiesRef.current.mobs[m.id] = { ...m, renderPos: { x: m.pos.x, y: m.pos.y } }
          } else {
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
      }
    }

    return () => ws.close()
  }, [gameId])

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

      if (direction && socketRef.current?.readyState === WebSocket.OPEN) {
        socketRef.current.send(JSON.stringify({ type: 'MOVE', direction }))
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    let animationFrameId

    const render = () => {
      if (grid.length === 0) return

      ctx.clearRect(0, 0, canvas.width, canvas.height)

      // Calculate camera position centered on player
      let cameraX = 0
      let cameraY = 0
      const myPlayer = entitiesRef.current.players[myPlayerId]

      if (myPlayer) {
        cameraX = myPlayer.renderPos.x * TILE_SIZE - canvas.width / 2 + TILE_SIZE / 2
        cameraY = myPlayer.renderPos.y * TILE_SIZE - canvas.height / 2 + TILE_SIZE / 2
      }

      ctx.save()
      ctx.translate(-cameraX, -cameraY)

      // Draw Grid
      for (let y = 0; y < grid.length; y++) {
        for (let x = 0; x < grid[y].length; x++) {
          const tile = grid[y][x]
          if (tile === 0) continue // Skip VOID

          const key = `${x},${y}`
          const isVisible = visionRef.current.visible.has(key)
          const isDiscovered = visionRef.current.discovered.has(key)

          if (!isDiscovered) {
            ctx.fillStyle = 'black'
          } else {
            if (tile === 1) ctx.fillStyle = '#444' // WALL
            else if (tile === 2) ctx.fillStyle = '#222' // FLOOR
            else if (tile === 3) ctx.fillStyle = '#855' // DOOR
            else if (tile === 4) ctx.fillStyle = '#aa4' // STAIRS_UP
            else if (tile === 5) ctx.fillStyle = '#4aa' // STAIRS_DOWN

            // If not visible but discovered, darken the tile (Fog of War)
            if (!isVisible) {
              // Draw the tile normally first, then overlay with semi-transparent black
              ctx.fillRect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
              ctx.fillStyle = 'rgba(0, 0, 0, 0.6)'
            }
          }

          ctx.fillRect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        }
      }

      // Draw Items on Floor
      if (entitiesRef.current.items) {
        entitiesRef.current.items.forEach(item => {
          // Only draw visible items
          if (!visionRef.current.visible.has(`${item.pos.x},${item.pos.y}`)) return

          ctx.fillStyle = item.type === 'weapon' ? '#f1c40f' : '#9b59b6'
          ctx.beginPath()
          ctx.arc(item.pos.x * TILE_SIZE + TILE_SIZE / 2, item.pos.y * TILE_SIZE + TILE_SIZE / 2, 6, 0, Math.PI * 2)
          ctx.fill()
        })
      }

      // Update and Draw Mobs
      Object.values(entitiesRef.current.mobs).forEach(mob => {
        // Only draw visible mobs
        if (!visionRef.current.visible.has(`${Math.round(mob.renderPos.x)},${Math.round(mob.renderPos.y)}`)) return

        // Interpolate position
        if (mob.targetPos) {
          mob.renderPos.x += (mob.targetPos.x - mob.renderPos.x) * INTERPOLATION_SPEED
          mob.renderPos.y += (mob.targetPos.y - mob.renderPos.y) * INTERPOLATION_SPEED
        }

        ctx.fillStyle = '#e74c3c'
        ctx.fillRect(mob.renderPos.x * TILE_SIZE + 4, mob.renderPos.y * TILE_SIZE + 4, TILE_SIZE - 8, TILE_SIZE - 8)

        // Draw Mob HP Bar
        const mobHpBarWidth = TILE_SIZE - 8
        const mobHpPercent = (mob.hp || 0) / (mob.max_hp || 1)
        ctx.fillStyle = '#111'
        ctx.fillRect(mob.renderPos.x * TILE_SIZE + 4, mob.renderPos.y * TILE_SIZE - 4, mobHpBarWidth, 3)
        ctx.fillStyle = '#e74c3c'
        ctx.fillRect(mob.renderPos.x * TILE_SIZE + 4, mob.renderPos.y * TILE_SIZE - 4, mobHpBarWidth * mobHpPercent, 3)
      })

      // Update and Draw Players
      Object.values(entitiesRef.current.players).forEach(player => {
        // Interpolate position
        if (player.targetPos) {
          player.renderPos.x += (player.targetPos.x - player.renderPos.x) * INTERPOLATION_SPEED
          player.renderPos.y += (player.targetPos.y - player.renderPos.y) * INTERPOLATION_SPEED
        }

        const isPlayerVisible = visionRef.current.visible.has(`${Math.round(player.renderPos.x)},${Math.round(player.renderPos.y)}`) || player.id === myPlayerId
        if (!isPlayerVisible) return

        if (player.is_downed) {
          ctx.fillStyle = '#7f8c8d' // Gray for downed
          ctx.fillRect(player.renderPos.x * TILE_SIZE + 2, player.renderPos.y * TILE_SIZE + 8, TILE_SIZE - 4, TILE_SIZE - 10)
        } else {
          ctx.fillStyle = player.id === myPlayerId ? '#2ecc71' : '#3498db'
          ctx.fillRect(player.renderPos.x * TILE_SIZE + 2, player.renderPos.y * TILE_SIZE + 2, TILE_SIZE - 4, TILE_SIZE - 4)
        }

        // Draw Player HP Bar
        const hpBarWidth = TILE_SIZE - 4
        const healthBoost = player.equipped_wearable ? player.equipped_wearable.health_boost : 0
        const playerHpPercent = player.hp / (player.max_hp + healthBoost)
        ctx.fillStyle = '#111'
        ctx.fillRect(player.renderPos.x * TILE_SIZE + 2, player.renderPos.y * TILE_SIZE - 12, hpBarWidth, 4)

        if (player.is_downed) {
          ctx.fillStyle = '#e74c3c' // Red for downed HP bar
        } else if (player.regen_ticks > 0) {
          ctx.fillStyle = '#f1c40f' // Yellow for regenerating
        } else {
          ctx.fillStyle = '#2ecc71'
        }

        ctx.fillRect(player.renderPos.x * TILE_SIZE + 2, player.renderPos.y * TILE_SIZE - 12, hpBarWidth * playerHpPercent, 4)

        // Show "DOWNED" text for teammates to see
        if (player.is_downed) {
          ctx.fillStyle = '#e74c3c'
          ctx.font = 'bold 10px Arial'
          ctx.fillText("DOWNED", player.renderPos.x * TILE_SIZE + TILE_SIZE / 2, player.renderPos.y * TILE_SIZE - 25)
        }

        ctx.fillStyle = 'white'
        ctx.font = '10px Arial'
        ctx.textAlign = 'center'
        ctx.fillText(player.name, player.renderPos.x * TILE_SIZE + TILE_SIZE / 2, player.renderPos.y * TILE_SIZE - 15)
      })

      ctx.restore()

      animationFrameId = requestAnimationFrame(render)
    }

    render()
    return () => cancelAnimationFrame(animationFrameId)
  }, [grid, myPlayerId])

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

  return (
    <div className="game-container">
      {grid.length === 0 && (
        <div className="loading-screen">
          <div className="loading-spinner"></div>
          <div className="loading-text">Loading Dungeon...</div>
        </div>
      )}

      <button className="inventory-toggle-btn" onClick={() => setShowInventory(true)}>
        🎒
      </button>

      <div className="canvas-wrapper">
        <canvas
          ref={canvasRef}
          width={viewport.width}
          height={viewport.height}
          className="game-canvas"
        />
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
                    {item.type === 'weapon' ? `Dmg: ${item.damage}` : `HP+: ${item.health_boost}`}
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

      <div className="game-hud">
        <div className="bottom-left-hud">
          <div className="health-bar-container">
            <div
              className={`health-bar-fill ${myStats.isDowned ? 'downed' : myStats.isRegen ? 'regen' : ''}`}
              style={{ width: `${(myStats.hp / myStats.maxHp) * 100}%` }}
            ></div>
            <div className="health-text">{Math.ceil(myStats.hp)} / {myStats.maxHp} HP</div>
          </div>
          <div className="player-info">{myStats.name}</div>
        </div>

        <div className="bottom-center-hud">
          <div className="equipped-items">
            <div className="equipped-slot">
              <span className="label">Weapon:</span>
              <span className="value">{equippedItems.weapon?.name || "None"}</span>
            </div>
            <div className="equipped-slot">
              <span className="label">Armor:</span>
              <span className="value">{equippedItems.wearable?.name || "None"}</span>
            </div>
          </div>
        </div>

        <div className="bottom-right-hud">
          <div className="difficulty-selector">
            <span className="label">Difficulty:</span>
            <select
              value={difficulty}
              onChange={(e) => changeDifficulty(e.target.value)}
              className="difficulty-select"
            >
              <option value="easy">Easy</option>
              <option value="normal">Normal</option>
              <option value="hard">Hard</option>
            </select>
          </div>
        </div>

        <div className="connection-log">
          {messages.slice(-3).map((msg, i) => (
            <div key={i} className="log-entry">{msg}</div>
          ))}
        </div>
        <div className="game-controls-hint">
          Arrows/WASD to move. 'F' for Inventory.
        </div>
      </div>

    </div>
  )
}

export default App
