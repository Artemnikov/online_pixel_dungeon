import { useEffect, useState } from 'react'
import './App.css'

import AudioManager from './audio/AudioManager';
import CharacterSelection from './CharacterSelection';

import { useGameAssets } from './hooks/useGameAssets';
import { useGameState } from './hooks/useGameState';
import { useGameInput } from './hooks/useGameInput';

import LoadingScreen from './components/LoadingScreen';
import GameHUD from './components/GameHUD';
import InventoryModal from './components/InventoryModal';
import GameToolbar from './components/GameToolbar';
import GameCanvas from './components/GameCanvas';

const TILE_SIZE = 32

function App() {
  const [gameState, setGameState] = useState('SELECT'); // 'SELECT', 'PLAYING'
  const [selectedClass, setSelectedClass] = useState('warrior');
  const [difficulty, setDifficulty] = useState("normal")
  const [gameId] = useState("default-lobby")

  const [viewport, setViewport] = useState({ width: 800, height: 600 })
  const [showInventory, setShowInventory] = useState(false)
  const [targetingMode, setTargetingMode] = useState(false) // boolean or itemId string

  const assetImages = useGameAssets();

  const {
    grid, gridRef, entitiesRef, projectilesRef, visionRef,
    myPlayerId, myPlayerIdRef, playersState,
    messages, dimensions, inventory, equippedItems, myStats,
    sendAction, socketRef
  } = useGameState(gameId, selectedClass, difficulty);

  // Audio Context Resume
  useEffect(() => {
    const enableAudio = () => {
      AudioManager.play('SILENCE');
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

  const equipItem = (itemId) => sendAction({ type: 'EQUIP_ITEM', item_id: itemId });
  const dropItem = (itemId) => sendAction({ type: 'DROP_ITEM', item_id: itemId });
  const useItem = (itemId) => sendAction({ type: 'USE_ITEM', item_id: itemId });

  const handleToolbarClick = (item) => {
    if (!item) {
      setShowInventory(true);
      return;
    }
    if (item.type === 'potion') {
      useItem(item.id);
    } else {
      if (item.type === 'weapon') {
        const isEquipped = equippedItems.weapon && equippedItems.weapon.id === item.id;

        if (!isEquipped) {
          equipItem(item.id);
          if (item.range && item.range > 1) {
            setTargetingMode(item.id);
          } else {
            setTargetingMode(false);
          }
        } else {
          if (item.range && item.range > 1) {
            setTargetingMode(prev => !prev);
          }
        }
      } else if (item.type === 'wearable') {
        equipItem(item.id);
      } else if (item.type === 'throwable') {
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
      const myPlayer = entitiesRef.current.players[myPlayerIdRef.current];
      if (!myPlayer) return;

      let nearestMob = null;
      let minDist = item.range + 1;

      Object.values(entitiesRef.current.mobs).forEach(mob => {
        if (!visionRef.current.visible.has(`${Math.round(mob.renderPos.x)},${Math.round(mob.renderPos.y)}`)) return;

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
        sendAction({
          type: 'RANGED_ATTACK',
          item_id: item.id,
          target_x: targetX,
          target_y: targetY
        });
      }
    }
  };

  useGameInput(
    sendAction,
    inventory,
    handleToolbarClick,
    handleToolbarDoubleClick,
    setShowInventory
  );

  const handleCanvasClick = (e, canvasRef, camera) => {
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

    const weaponId = typeof targetingMode === 'string' ? targetingMode : equippedItems.weapon?.id;

    if (weaponId) {
      sendAction({
        type: 'RANGED_ATTACK',
        item_id: weaponId,
        target_x: tileX,
        target_y: tileY
      });
      setTargetingMode(true);
    }
  };

  if (gameState === 'SELECT') {
    return <CharacterSelection onSelect={(c, d) => {
      setSelectedClass(c);
      setDifficulty(d);
      setGameState('PLAYING');
    }} />;
  }

  return (
    <div className="game-container">
      {(grid.length === 0) && <LoadingScreen />}

      <GameHUD myStats={myStats} />

      <GameCanvas
        grid={grid}
        gridRef={gridRef}
        entitiesRef={entitiesRef}
        projectilesRef={projectilesRef}
        visionRef={visionRef}
        myPlayerId={myPlayerId}
        myPlayerIdRef={myPlayerIdRef}
        assetImages={assetImages}
        viewport={viewport}
        dimensions={dimensions}
        onCanvasClick={handleCanvasClick}
        targetingMode={targetingMode}
        playersState={playersState}
      />

      {showInventory && (
        <InventoryModal
          inventory={inventory}
          onClose={() => setShowInventory(false)}
          onUse={useItem}
          onEquip={equipItem}
          onDrop={dropItem}
        />
      )}

      <GameToolbar
        inventory={inventory}
        equippedWeapon={equippedItems.weapon}
        targetingMode={targetingMode}
        onToggleInventory={() => setShowInventory(true)}
        onToolbarClick={handleToolbarClick}
        onToolbarDoubleClick={handleToolbarDoubleClick}
        messages={messages}
      />

    </div>
  )
}

export default App
