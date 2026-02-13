from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List, Dict
import asyncio
import json
import uuid
from app.engine.manager import GameInstance
from app.engine.entities.base import Player, Position

app = FastAPI(title="Online Pixel Dungeon API")

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.game_instances: Dict[str, GameInstance] = {}

    async def connect(self, game_id: str, websocket: WebSocket, player_id: str):
        await websocket.accept()
        if game_id not in self.active_connections:
            self.active_connections[game_id] = []
            self.game_instances[game_id] = GameInstance(game_id)
        
        self.active_connections[game_id].append(websocket)
        
        game = self.game_instances[game_id]
        await websocket.send_json({
            "type": "INIT",
            "player_id": player_id,
            "grid": game.grid,
            "width": game.width,
            "height": game.height
        })


    def disconnect(self, game_id: str, websocket: WebSocket):
        if game_id in self.active_connections:
            self.active_connections[game_id].remove(websocket)
            if not self.active_connections[game_id]:
                del self.active_connections[game_id]

    async def broadcast_state(self, game_id: str):
        if game_id in self.active_connections and game_id in self.game_instances:
            game = self.game_instances[game_id]
            
            old_depth = getattr(game, "_last_broadcast_depth", 0)
            game.update_tick()
            state = game.get_state()
            
            new_depth = state["depth"]
            game._last_broadcast_depth = new_depth
            
            for connection in self.active_connections[game_id]:
                try:
                    # If depth changed, send INIT-like update with grid
                    if new_depth != old_depth:
                        await connection.send_json({
                            "type": "INIT",
                            "depth": new_depth,
                            "grid": state["grid"],
                            "width": game.width,
                            "height": game.height
                        })
                    
                    await connection.send_json({
                        "type": "STATE_UPDATE",
                        "depth": new_depth,
                        "players": state["players"],
                        "mobs": state["mobs"]
                    })
                except:
                    pass

manager = ConnectionManager()

@app.get("/")
async def root():
    return {"message": "Online Pixel Dungeon Server is running"}

@app.websocket("/ws/game/{game_id}")
async def game_websocket(websocket: WebSocket, game_id: str):
    player_id = str(uuid.uuid4())
    await manager.connect(game_id, websocket, player_id)
    
    game = manager.game_instances[game_id]
    player = game.add_player(player_id, f"Player_{player_id[:4]}")
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "MOVE":
                direction = message["direction"]
                dx, dy = 0, 0
                if direction == "UP": dy = -1
                elif direction == "DOWN": dy = 1
                elif direction == "LEFT": dx = -1
                elif direction == "RIGHT": dx = 1
                
                game.move_entity(player_id, dx, dy)
            
            elif message["type"] == "EQUIP_ITEM":
                item_id = message["item_id"]
                if player_id in game.players:
                    game.players[player_id].equip_item(item_id)
            
            elif message["type"] == "DROP_ITEM":
                item_id = message["item_id"]
                if player_id in game.players:
                    player = game.players[player_id]
                    item_idx = next((i for i, item in enumerate(player.inventory) if item.id == item_id), -1)
                    if item_idx != -1:
                        item = player.inventory.pop(item_idx)
                        item.pos = Position(x=player.pos.x, y=player.pos.y)
                        game.items[item.id] = item
                        if player.equipped_weapon and player.equipped_weapon.id == item_id:
                            player.equipped_weapon = None
                        if player.equipped_wearable and player.equipped_wearable.id == item_id:
                            player.equipped_wearable = None
    except WebSocketDisconnect:
        manager.disconnect(game_id, websocket)
        if player_id in game.players:
            del game.players[player_id]

async def global_game_loop():
    while True:
        for game_id in list(manager.active_connections.keys()):
            await manager.broadcast_state(game_id)
        await asyncio.sleep(0.05)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(global_game_loop())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
