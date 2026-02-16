import { useState, useEffect, useRef } from 'react';
import AudioManager from '../audio/AudioManager';

const TILE_SIZE = 32;

export const useGameState = (gameId, selectedClass, difficulty) => {
    const [grid, setGrid] = useState([]);
    const gridRef = useRef([]);
    const socketRef = useRef(null);
    const entitiesRef = useRef({ players: {}, mobs: {}, items: [] });
    const projectilesRef = useRef([]);
    const visionRef = useRef({ visible: new Set(), discovered: new Set() });
    const myPlayerIdRef = useRef(null);
    const [myPlayerId, setMyPlayerId] = useState(null);
    const [messages, setMessages] = useState([]);
    const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
    const [inventory, setInventory] = useState([]);
    const [equippedItems, setEquippedItems] = useState({ weapon: null, wearable: null });
    const [myStats, setMyStats] = useState({ hp: 0, maxHp: 10, name: "", isDowned: false, isRegen: false });
    const [playersState, setPlayersState] = useState({}); // For forcing re-renders of UI

    useEffect(() => {
        const ws = new WebSocket(`ws://${window.location.hostname}:8000/ws/game/${gameId}?class_type=${selectedClass}&difficulty=${difficulty}`);
        socketRef.current = ws;

        ws.onopen = () => setMessages(prev => [...prev, "Connected to server"]);
        ws.onerror = () => setMessages(prev => [...prev, "Connection error!"]);

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'INIT') {
                setGrid(data.grid);
                gridRef.current = data.grid;
                visionRef.current.discovered = new Set();
                setDimensions({ width: data.width * TILE_SIZE, height: data.height * TILE_SIZE });
                if (data.player_id) {
                    setMyPlayerId(data.player_id);
                    myPlayerIdRef.current = data.player_id;
                }
            } else if (data.type === 'STATE_UPDATE') {
                // Sync players
                const currentServerPlayerIds = new Set(data.players.map(p => p.id));
                Object.keys(entitiesRef.current.players).forEach(id => {
                    if (!currentServerPlayerIds.has(id)) {
                        delete entitiesRef.current.players[id];
                    }
                });

                data.players.forEach(p => {
                    if (p.id === myPlayerIdRef.current) {
                        setInventory(p.inventory || []);
                        setEquippedItems({
                            weapon: p.equipped_weapon,
                            wearable: p.equipped_wearable
                        });
                        const healthBoost = p.equipped_wearable ? p.equipped_wearable.health_boost : 0;
                        setMyStats({
                            hp: p.hp,
                            maxHp: p.max_hp + healthBoost,
                            name: p.name,
                            isDowned: p.is_downed,
                            isRegen: (p.regen_ticks || 0) > 0
                        });
                    }

                    if (!entitiesRef.current.players[p.id]) {
                        entitiesRef.current.players[p.id] = { ...p, renderPos: { x: p.pos.x, y: p.pos.y }, facing: 'RIGHT' };
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

                        entitiesRef.current.players[p.id].targetPos = p.pos;
                        entitiesRef.current.players[p.id].name = p.name;
                        entitiesRef.current.players[p.id].hp = p.hp;
                        entitiesRef.current.players[p.id].max_hp = p.max_hp;
                        entitiesRef.current.players[p.id].equipped_wearable = p.equipped_wearable;
                        entitiesRef.current.players[p.id].is_downed = p.is_downed;
                        entitiesRef.current.players[p.id].regen_ticks = p.regen_ticks;
                        entitiesRef.current.players[p.id].class_type = p.class_type;
                    }
                });

                setPlayersState({ ...entitiesRef.current.players });

                // Sync mobs
                const currentServerMobIds = new Set(data.mobs.map(m => m.id));
                Object.keys(entitiesRef.current.mobs).forEach(id => {
                    if (!currentServerMobIds.has(id)) {
                        delete entitiesRef.current.mobs[id];
                    }
                });

                data.mobs.forEach(m => {
                    if (!entitiesRef.current.mobs[m.id]) {
                        entitiesRef.current.mobs[m.id] = { ...m, renderPos: { x: m.pos.x, y: m.pos.y }, facing: 'RIGHT' };
                    } else {
                        const currentTarget = entitiesRef.current.mobs[m.id].targetPos || entitiesRef.current.mobs[m.id].renderPos;
                        if (m.pos.x > currentTarget.x) entitiesRef.current.mobs[m.id].facing = 'RIGHT';
                        else if (m.pos.x < currentTarget.x) entitiesRef.current.mobs[m.id].facing = 'LEFT';

                        entitiesRef.current.mobs[m.id].targetPos = m.pos;
                        entitiesRef.current.mobs[m.id].hp = m.hp;
                    }
                });

                entitiesRef.current.items = data.items || [];

                if (data.visible_tiles) {
                    const newVisible = new Set(data.visible_tiles.map(t => `${t[0]},${t[1]}`));
                    visionRef.current.visible = newVisible;
                    newVisible.forEach(t => visionRef.current.discovered.add(t));
                }

                if (data.events) {
                    data.events.forEach(event => {
                        if (event.type === 'PLAY_SOUND') {
                            AudioManager.play(event.data.sound);
                        }
                        if (event.type === 'MOVE') {
                            if (event.data.entity === myPlayerIdRef.current) {
                                const tileX = event.data.x;
                                const tileY = event.data.y;
                                if (gridRef.current[tileY] && gridRef.current[tileY][tileX]) {
                                    AudioManager.playStep(gridRef.current[tileY][tileX]);
                                } else {
                                    AudioManager.play('MOVE');
                                }
                            } else {
                                AudioManager.play(event.type);
                            }
                        }
                        if (event.type === 'RANGED_ATTACK') {
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

                            if (event.data.projectile === 'magic_bolt') {
                                AudioManager.play('ATTACK_MAGIC');
                            } else {
                                AudioManager.play('ATTACK_BOW');
                            }
                        }
                    });
                }
            }
        };

        return () => {
            if (ws.readyState === WebSocket.OPEN) {
                ws.close();
            }
        };
    }, [gameId, selectedClass, difficulty]);

    const sendAction = (action) => {
        if (socketRef.current?.readyState === WebSocket.OPEN) {
            socketRef.current.send(JSON.stringify(action));
        }
    };

    return {
        grid, gridRef, entitiesRef, projectilesRef, visionRef,
        myPlayerId, myPlayerIdRef, playersState,
        messages, dimensions, inventory, equippedItems, myStats,
        sendAction,
        socketRef // Exposed for specialized calls if needed, but sendAction is preferred
    };
};
