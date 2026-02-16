import { useEffect } from 'react';
import itemsSprite from '../assets/pixel-dungeon/sprites/items.png'; // Need raw path or just use what's passed?
// Actually the loop uses assetImages which are passed in.

const TILE_SIZE = 32;
const TILE_SCALE = 2;
const INTERPOLATION_SPEED = 0.2;
const PROJECTILE_SPEED = 0.5;

// Item Sprite Mapping (Moved here or duplicated, better needed in a constant file)
const ITEM_SPRITES = {
    "Shortsword": [13, 13],
    "Mage's Staff": [15, 16],
    "Dagger": [12, 13],
    "Spirit Bow": [0, 10],
    "Wooden Club": [15, 15],
    "Spear": [0, 7],
    "Cloth Armor": [15, 12],
    "Leather Vest": [14, 13],
    "Rogue's Cloak": [9, 15],
    "Broken Shield": [12, 16],
    "Potion": [12, 14],
    "default": [8, 13],
    "Stone": [10, 10],
    "Boomerang": [11, 10],
    "Throwable Dagger": [12, 13]
};

const getItemSpriteCoords = (itemName, itemType) => {
    for (const key in ITEM_SPRITES) {
        if (itemName && itemName.includes(key)) {
            return ITEM_SPRITES[key];
        }
    }
    if (itemType === 'potion') return [12, 14];
    if (itemType === 'weapon') return [14, 14];
    if (itemType === 'wearable') return [14, 12];
    if (itemType === 'throwable') return [11, 10];
    return ITEM_SPRITES["default"];
}

export const useGameLoop = (
    canvasRef,
    grid,
    gridRef, // Assuming we might need the ref for sync? App.jsx used grid state in dependency, but gridRef inside? 
    // App.jsx used: const gridRef = useRef([]); and updated it.
    // App.jsx effect: [grid, myPlayerId, assetImages]
    // render() used grid and myPlayerIdRef.
    entitiesRef,
    projectilesRef,
    visionRef,
    myPlayerId, // used for dependency
    myPlayerIdRef,
    assetImages,
    setCamera
) => {

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
            // Using gridRef might be safer if grid state is stale in closure?
            // Actually the effect depends on [grid], so it resets when grid changes. 
            // So using 'grid' from scope is fine.
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
                            coords[0] * (TILE_SIZE / TILE_SCALE),
                            coords[1] * (TILE_SIZE / TILE_SCALE),
                            TILE_SIZE / TILE_SCALE,
                            TILE_SIZE / TILE_SCALE,
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
                            0, 0,
                            TILE_SIZE / TILE_SCALE, TILE_SIZE / TILE_SCALE,
                            0, 0,
                            TILE_SIZE, TILE_SIZE
                        );
                    } else {
                        ctx.drawImage(
                            mobSprite,
                            0, 0,
                            TILE_SIZE / TILE_SCALE, TILE_SIZE / TILE_SCALE,
                            x, y,
                            TILE_SIZE, TILE_SIZE
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

                let playerSprite = assetImages.warrior;
                if (player.class_type === 'mage' && assetImages.mage) playerSprite = assetImages.mage;
                else if (player.class_type === 'rogue' && assetImages.rogue) playerSprite = assetImages.rogue;
                else if (player.class_type === 'huntress' && assetImages.huntress) playerSprite = assetImages.huntress;

                if (playerSprite) {
                    ctx.save();
                    const sWidth = 12;
                    const dWidth = sWidth * TILE_SCALE;
                    const xOffset = (TILE_SIZE - dWidth) / 2;

                    if (player.facing === 'LEFT') {
                        ctx.translate(x + TILE_SIZE - xOffset, y);
                        ctx.scale(-1, 1);
                        ctx.drawImage(playerSprite, 0, 0, sWidth, TILE_SIZE / TILE_SCALE, 0, 0, dWidth, TILE_SIZE);
                    } else {
                        ctx.drawImage(playerSprite, 0, 0, sWidth, TILE_SIZE / TILE_SCALE, x + xOffset, y, dWidth, TILE_SIZE);
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
                const dx = proj.targetX - proj.startX;
                const dy = proj.targetY - proj.startY;
                const dist = Math.sqrt(dx * dx + dy * dy);

                proj.progress += PROJECTILE_SPEED * 15;

                const ratio = dist > 0 ? Math.min(1, proj.progress / dist) : 1;
                proj.x = proj.startX + dx * ratio;
                proj.y = proj.startY + dy * ratio;

                if (ratio >= 1) {
                    proj.finished = true;
                    finishedIndices.push(index);
                }

                ctx.fillStyle = proj.type === 'magic_bolt' ? '#3498db' : '#ecf0f1';
                ctx.beginPath();
                ctx.arc(proj.x, proj.y, 4, 0, Math.PI * 2);
                ctx.fill();
            });

            for (let i = finishedIndices.length - 1; i >= 0; i--) {
                projectilesRef.current.splice(finishedIndices[i], 1);
            }
        };

        const render = () => {
            // Safe guard for empty grid
            if (!grid || grid.length === 0) return;

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

            // Update camera safely
            setCamera({ x: cameraX, y: cameraY });

            ctx.save();
            ctx.translate(-cameraX, -cameraY);

            drawGrid();
            drawItems();
            drawMobs();
            drawPlayers();
            drawProjectiles(); // Double call in original, keeping it
            drawProjectiles();

            ctx.restore();

            animationFrameId = requestAnimationFrame(render);
        };

        render();
        return () => cancelAnimationFrame(animationFrameId);
    }, [grid, myPlayerId, assetImages]); // Dependencies
};
