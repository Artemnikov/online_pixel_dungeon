import uuid
import random
from typing import Dict, List, Optional, Tuple
from app.engine.dungeon.generator import DungeonGenerator, TileType
from app.engine.entities.base import Player, Mob, Position, EntityType, Mob as MobEntity, Item, Weapon, Wearable, Faction, Difficulty

class GameInstance:
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.depth = 1
        self.width = 60
        self.height = 40
        self.players: Dict[str, Player] = {}
        self.mobs: Dict[str, MobEntity] = {}
        self.items: Dict[str, Item] = {}
        self.grid = []
        self.rooms = []
        self.difficulty = Difficulty.NORMAL
        
        self.generate_floor(1)

    def generate_floor(self, depth: int):
        self.depth = depth
        self.generator = DungeonGenerator(self.width, self.height)
        self.grid, self.rooms = self.generator.generate(10 + depth, 4, 8 + (depth // 10))
        self.mobs = {}
        self.items = {}
        self._spawn_content()

    def _spawn_content(self):
        floor_tiles = [(x, y) for y in range(self.height) for x in range(self.width) 
                       if self.grid[y][x] == TileType.FLOOR]
        
        # Spawn Boss every 5 floors
        if self.depth % 5 == 0:
            self._spawn_boss(floor_tiles)
        
        # Spawn Mobs
        num_mobs = 5 + (self.depth * 2)
        for _ in range(num_mobs):
            if not floor_tiles: break
            x, y = floor_tiles.pop(random.randint(0, len(floor_tiles) - 1))
            mob_id = str(uuid.uuid4())
            self.mobs[mob_id] = MobEntity(
                id=mob_id,
                name=f"Rat",
                pos=Position(x=x, y=y),
                hp=10,
                max_hp=10,
                attack=2,
                defense=0,
                faction=Faction.DUNGEON
            )

        # Spawn Items
        num_items = 3 + random.randint(0, 2)
        for _ in range(num_items):
            if not floor_tiles: break
            x, y = floor_tiles.pop(random.randint(0, len(floor_tiles) - 1))
            item_id = str(uuid.uuid4())
            
            if random.random() < 0.5:
                # Weapon
                self.items[item_id] = Weapon(
                    id=item_id,
                    name=random.choice(["Rusty Sword", "Wooden Club", "Dagger"]),
                    pos=Position(x=x, y=y),
                    damage=2 + random.randint(0, 2),
                    range=1,
                    strength_requirement=10 + random.randint(-2, 2)
                )
            else:
                # Wearable
                self.items[item_id] = Wearable(
                    id=item_id,
                    name=random.choice(["Cloth Armor", "Leather Vest", "Broken Shield"]),
                    pos=Position(x=x, y=y),
                    strength_requirement=10 + random.randint(-2, 2),
                    health_boost=5 + random.randint(0, 5)
                )

    def _spawn_boss(self, floor_tiles):
        if not floor_tiles: return
        x, y = floor_tiles.pop(random.randint(0, len(floor_tiles) - 1))
        boss_id = str(uuid.uuid4())
        self.mobs[boss_id] = MobEntity(
            id=boss_id,
            type=EntityType.BOSS,
            name=f"Floor {self.depth} Boss",
            pos=Position(x=x, y=y),
            hp=100 + (self.depth * 20),
            max_hp=100 + (self.depth * 20),
            attack=10 + self.depth,
            defense=5 + self.depth,
            faction=Faction.DUNGEON
        )

    def add_player(self, player_id: str, name: str) -> Player:
        spawn_pos = self._get_stairs_pos(TileType.STAIRS_UP)
        player = Player(
            id=player_id,
            name=name,
            pos=spawn_pos,
            hp=10,
            max_hp=10,
            attack=3,
            defense=1,
            faction=Faction.PLAYER
        )
        self.players[player_id] = player
        return player

    def _get_stairs_pos(self, tile_type) -> Position:
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] == tile_type:
                    return Position(x=x, y=y)
        return Position(x=0, y=0)

    def move_entity(self, entity_id: str, dx: int, dy: int):
        entity = self.players.get(entity_id) or self.mobs.get(entity_id)
        if not entity: return
        
        new_x = entity.pos.x + dx
        new_y = entity.pos.y + dy
        
        if 0 <= new_x < self.width and 0 <= new_y < self.height:
            # Check for other entities in the target tile
            target_entity = None
            for p in self.players.values():
                if p.id != entity_id and p.pos.x == new_x and p.pos.y == new_y:
                    target_entity = p
                    break
            
            if not target_entity:
                for m in self.mobs.values():
                    if m.id != entity_id and m.pos.x == new_x and m.pos.y == new_y and m.is_alive:
                        target_entity = m
                        break
            
            if target_entity:
                # Combat! Only if different factions
                if entity.faction != target_entity.faction:
                    attack_power = entity.attack
                    if isinstance(entity, Player):
                        attack_power = entity.get_total_attack()
                    
                    dmg = target_entity.take_damage(attack_power)
                return
            
            tile = self.grid[new_y][new_x]
            if tile in [TileType.FLOOR, TileType.DOOR, TileType.STAIRS_UP, TileType.STAIRS_DOWN]:
                entity.move(dx, dy)

                # Player item pickup
                if isinstance(entity, Player):
                    items_to_pickup = [i_id for i_id, i in self.items.items() if i.pos.x == entity.pos.x and i.pos.y == entity.pos.y]
                    for i_id in items_to_pickup:
                        item = self.items[i_id]
                        if entity.add_to_inventory(item):
                            del self.items[i_id]
                
                # If player moves onto STAIRS_DOWN, go to next floor
                if entity_id in self.players and tile == TileType.STAIRS_DOWN:
                    self.next_floor()

    def next_floor(self):
        if self.depth < 50:
            self.generate_floor(self.depth + 1)
            # Reset player positions to STAIRS_UP
            spawn_pos = self._get_stairs_pos(TileType.STAIRS_UP)
            for p in self.players.values():
                p.pos = spawn_pos
            
            # We would need to notify clients that the map changed
            # This will be handled by the next broadcast which should include INIT if needed
            # Or we can send a special event. For now, we'll assume the client detects INIT or map change.

    def update_tick(self):
        for mob in self.mobs.values():
            if not mob.is_alive: continue
            
            # Simple AI logic based on difficulty
            target_player = self._find_nearest_player(mob.pos)
            dist = self._get_distance(mob.pos, target_player.pos) if target_player else float('inf')
            
            # Difficulty-specific behavior
            moved = False
            
            if self.difficulty == Difficulty.EASY:
                # Roam randomly, attack if adjacent
                if target_player and dist <= 1:
                    dx, dy = target_player.pos.x - mob.pos.x, target_player.pos.y - mob.pos.y
                    self.move_entity(mob.id, dx, dy)
                    moved = True
                elif random.random() < 0.05:
                    dx, dy = random.choice([(0,1), (0,-1), (1,0), (-1,0)])
                    self.move_entity(mob.id, dx, dy)
                    moved = True

            elif self.difficulty == Difficulty.NORMAL:
                # Chase if in LOS, move towards player
                if target_player and dist <= 1:
                    dx, dy = target_player.pos.x - mob.pos.x, target_player.pos.y - mob.pos.y
                    self.move_entity(mob.id, dx, dy)
                    moved = True
                elif target_player and self._is_in_los(mob.pos, target_player.pos):
                    # Move towards player if in LOS
                    step = self._get_next_step_to(mob.pos, target_player.pos)
                    if step:
                        self.move_entity(mob.id, step[0], step[1])
                        moved = True
                elif random.random() < 0.05:
                    dx, dy = random.choice([(0,1), (0,-1), (1,0), (-1,0)])
                    self.move_entity(mob.id, dx, dy)
                    moved = True

            elif self.difficulty == Difficulty.HARD:
                # Hunt across room (dist < 20), pathfinding
                if target_player and dist <= 1:
                    dx, dy = target_player.pos.x - mob.pos.x, target_player.pos.y - mob.pos.y
                    self.move_entity(mob.id, dx, dy)
                    moved = True
                elif target_player and dist < 20:
                    # Pathfind to player
                    step = self._get_next_step_to(mob.pos, target_player.pos)
                    if step:
                        self.move_entity(mob.id, step[0], step[1])
                        moved = True
                elif random.random() < 0.05:
                    dx, dy = random.choice([(0,1), (0,-1), (1,0), (-1,0)])
                    self.move_entity(mob.id, dx, dy)
                    moved = True

    def _find_nearest_player(self, pos: Position) -> Optional[Player]:
        if not self.players: return None
        nearest = None
        min_dist = float('inf')
        for p in self.players.values():
            d = self._get_distance(pos, p.pos)
            if d < min_dist:
                min_dist = d
                nearest = p
        return nearest

    def _get_distance(self, p1: Position, p2: Position) -> int:
        return abs(p1.x - p2.x) + abs(p1.y - p2.y)

    def _is_in_los(self, p1: Position, p2: Position) -> bool:
        # Bresenham's line algorithm to check LOS
        x1, y1 = p1.x, p1.y
        x2, y2 = p2.x, p2.y
        dx = abs(x2 - x1)
        dy = -abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx + dy
        
        curr_x, curr_y = x1, y1
        while True:
            if curr_x == x2 and curr_y == y2:
                return True
            
            # Check for WALL
            if 0 <= curr_x < self.width and 0 <= curr_y < self.height:
                if self.grid[curr_y][curr_x] == TileType.WALL:
                    return False
            
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                curr_x += sx
            if e2 <= dx:
                err += dx
                curr_y += sy

    def _get_next_step_to(self, start: Position, target: Position) -> Optional[tuple]:
        # Simple BFS for pathfinding
        queue = [(start.x, start.y, [])]
        visited = set([(start.x, start.y)])
        
        while queue:
            x, y, path = queue.pop(0)
            
            if x == target.x and y == target.y:
                if path:
                    return path[0]
                return None
            
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.width and 0 <= ny < self.height and 
                    self.grid[ny][nx] in [TileType.FLOOR, TileType.DOOR, TileType.STAIRS_UP, TileType.STAIRS_DOWN] and 
                    (nx, ny) not in visited):
                    
                    # Check if another mob is there (friendly fire/blocking)
                    blocked = False
                    for m in self.mobs.values():
                        if m.is_alive and m.pos.x == nx and m.pos.y == ny:
                            blocked = True
                            break
                    
                    if not blocked:
                        visited.add((nx, ny))
                        queue.append((nx, ny, path + [(dx, dy)]))
                        
            # Limit search depth for performance
            if len(visited) > 400:
                break
        return None

    def change_difficulty(self, new_level: str):
        if new_level in [Difficulty.EASY, Difficulty.NORMAL, Difficulty.HARD]:
            self.difficulty = new_level

    def get_visible_tiles(self, pos: Position, radius: int = 8) -> List[Tuple[int, int]]:
        visible = []
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                tx, ty = pos.x + dx, pos.y + dy
                if 0 <= tx < self.width and 0 <= ty < self.height:
                    dist_sq = dx*dx + dy*dy
                    if dist_sq <= radius*radius:
                        if self._is_in_los(pos, Position(x=tx, y=ty)):
                            visible.append((tx, ty))
        return visible

    def get_state(self, player_id: Optional[str] = None):
        if player_id and player_id in self.players:
            player = self.players[player_id]
            visible_tiles = self.get_visible_tiles(player.pos)
            visible_set = set(visible_tiles)
            
            return {
                "depth": self.depth,
                "players": [p.dict() for p in self.players.values()], # Players always visible for now? Or maybe only if in LOS?
                # For multiplayer, usually you see all players on the current screen/map, 
                # but Pixel Dungeon style might be only in LOS. Let's stick to LOS for Mobs/Items.
                "mobs": [m.dict() for m in self.mobs.values() if m.is_alive and (m.pos.x, m.pos.y) in visible_set],
                "items": [i.dict() for i in self.items.values() if (i.pos.x, i.pos.y) in visible_set],
                "visible_tiles": visible_tiles,
                "grid": self.grid # Still sending full grid for now, rendering handles discovery
            }

        return {
            "depth": self.depth,
            "players": [p.dict() for p in self.players.values()],
            "mobs": [m.dict() for m in self.mobs.values() if m.is_alive],
            "items": [i.dict() for i in self.items.values()],
            "grid": self.grid
        }
