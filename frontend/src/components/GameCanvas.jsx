import React, { useRef, useState } from 'react';
import { useGameLoop } from '../hooks/useGameLoop';

const TILE_SIZE = 32;

const GameCanvas = ({
    grid,
    gridRef,
    entitiesRef,
    projectilesRef,
    visionRef,
    myPlayerId,
    myPlayerIdRef,
    assetImages,
    viewport,
    dimensions,
    onCanvasClick,
    targetingMode,
    playersState // Just to force re-render if needed or pass to sub-components
}) => {
    const canvasRef = useRef(null);
    const [camera, setCamera] = useState({ x: 0, y: 0 });

    useGameLoop(
        canvasRef,
        grid,
        gridRef,
        entitiesRef,
        projectilesRef,
        visionRef,
        myPlayerId,
        myPlayerIdRef,
        assetImages,
        setCamera
    );

    return (
        <div className="canvas-wrapper">
            <canvas
                ref={canvasRef}
                width={viewport.width}
                height={viewport.height}
                className={`game-canvas ${targetingMode ? 'cursor-crosshair' : ''}`}
                onClick={(e) => onCanvasClick(e, canvasRef, camera)}
            />
            <div
                className="player-container" // Overlay for names/DOM elements if any
                style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: dimensions.width,
                    height: dimensions.height,
                    transform: `translate(${-camera.x}px, ${-camera.y}px)`,
                    pointerEvents: 'none' // Let clicks pass through
                }}
            >
                {/* Render player nameplates/healthbars as DOM elements */}
                {Object.values(playersState).map(player => (
                    <PlayerDOM key={player.id} player={player} myPlayerId={myPlayerId} />
                ))}
            </div>
        </div>
    );
};

// Extracted PlayerDOM component
const PlayerDOM = ({ player, myPlayerId }) => {
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
                transition: 'none',
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
};

export default GameCanvas;
