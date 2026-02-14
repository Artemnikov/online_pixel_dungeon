import uuid
import random
from typing import Dict, List, Optional, Tuple
from app.engine.dungeon.generator import DungeonGenerator, TileType
from app.engine.entities.base import Player, Mob, Position, EntityType, Mob as MobEntity, Item, Weapon, Wearable, Faction, Difficulty, HealthPotion, RevivingPotion

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
        self.events = []
        self.difficulty = Difficulty.NORMAL
        
        self.generate_floor(1)

    def add_event(self, event_type: str, data: dict = None):
        self.events.append({
            "type": event_type,
            "data": data or {}
        })

    def flush_events(self):
        events = self.events
        self.events = []
        return events

    def generate_floor(self, depth: int):
        self.depth = depth
        self.generator = DungeonGenerator(self.width, self.height)
        self.grid, self.rooms = self.generator.generate(10 + depth, 4, 8 + (depth // 10))
        self.mobs = {}
        self.items = {}
        self._spawn_content()


    def _is_in_safe_room(self, x: int, y: int) -> bool:
        """
        Check if a coordinate is within the start (entry) or end (exit) rooms.
        Monsters should not spawn here or enter these rooms.
        """
        # We need to find which room contains (x, y)
        # However, checking every room might be overkill if we just want Start/End
        # Start Room is rooms[0], End Room is rooms[-1]
        
        if not self.rooms:
            return False

        start_room = self.rooms[0]
        end_room = self.rooms[-1]
        
        # Check if in start room
        if (start_room.x <= x < start_room.x + start_room.width and
            start_room.y <= y < start_room.y + start_room.height):
            return True
        
        # Check if in end room
        if (end_room.x <= x < end_room.x + end_room.width and
            end_room.y <= y < end_room.y + end_room.height):
            return True
            
        return False

    def _spawn_content(self):
        floor_tiles = [(x, y) for y in range(self.height) for x in range(self.width) 
                       if self.grid[y][x] == TileType.FLOOR]
        
        # Filter out safe rooms for mobs
        unsafe_floor_tiles = [pos for pos in floor_tiles if not self._is_in_safe_room(pos[0], pos[1])]
        
        # Spawn Boss every 5 floors - Bosses might need a special room, but for now use unsafe tiles
        if self.depth % 5 == 0:
            self._spawn_boss(unsafe_floor_tiles) # Use unsafe tiles for boss too? Or maybe boss has its own room logic?
            # Existing logic just picks a random floor tile. Let's stick to unsafe for now.
        
        # Spawn Mobs
        num_mobs = 5 + (self.depth * 2)
        for _ in range(num_mobs):
            if not unsafe_floor_tiles: break
            # Use unsafe_floor_tiles for mobs
            x, y = unsafe_floor_tiles.pop(random.randint(0, len(unsafe_floor_tiles) - 1))
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

        # Spawn Items - Items can be anywhere, including safe rooms
        num_items = 4 + random.randint(0, 3)
        for _ in range(num_items):
            if not floor_tiles: break
            x, y = floor_tiles.pop(random.randint(0, len(floor_tiles) - 1))
            item_id = str(uuid.uuid4())
            
            rand = random.random()
            if rand < 0.3:
                # Weapon
                self.items[item_id] = Weapon(
                    id=item_id,
                    name=random.choice(["Rusty Sword", "Wooden Club", "Dagger"]),
                    pos=Position(x=x, y=y),
                    damage=2 + random.randint(0, 2),
                    range=1,
                    strength_requirement=10 + random.randint(-2, 2)
                )
            elif rand < 0.6:
                # Wearable
                self.items[item_id] = Wearable(
                    id=item_id,
                    name=random.choice(["Cloth Armor", "Leather Vest", "Broken Shield"]),
                    pos=Position(x=x, y=y),
                    strength_requirement=10 + random.randint(-2, 2),
                    health_boost=5 + random.randint(0, 5)
                )
            elif rand < 0.8:
                # Health Potion
                self.items[item_id] = HealthPotion(
                    id=item_id,
                    pos=Position(x=x, y=y)
                )
            else:
                # Reviving Potion
                self.items[item_id] = RevivingPotion(
                    id=item_id,
                    pos=Position(x=x, y=y)
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
        
        # Downed players can't move
        if isinstance(entity, Player) and entity.is_downed:
            return
        
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
                # Teammate revive check
                if (isinstance(entity, Player) and isinstance(target_entity, Player) and 
                    target_entity.is_downed and entity.faction == target_entity.faction):
                    # Check for Reviving Potion in inventory
                    revive_potion_idx = next((i for i, item in enumerate(entity.inventory) if isinstance(item, RevivingPotion)), -1)
                    if revive_potion_idx != -1:
                        entity.inventory.pop(revive_potion_idx)
                        target_entity.is_downed = False
                        target_entity.hp = target_entity.get_total_max_hp() // 2
                        self.add_event("REVIVE", {"target": target_entity.id, "source": entity.id})
                        return

                # Combat! Only if different factions
                if entity.faction != target_entity.faction:
                    if isinstance(entity, Player) and entity.is_downed:
                        return # Downed players can't attack

                    attack_power = entity.attack
                    if isinstance(entity, Player):
                        attack_power = entity.get_total_attack()
                    
                    
                    dmg = target_entity.take_damage(attack_power)
                    self.add_event("ATTACK", {"source": entity.id, "target": target_entity.id, "damage": dmg})
                    if dmg > 0:
                        self.add_event("DAMAGE", {"target": target_entity.id, "amount": dmg})
                        if not target_entity.is_alive:
                            self.add_event("DEATH", {"target": target_entity.id})
                return
            
            tile = self.grid[new_y][new_x]
            if tile in [TileType.FLOOR, TileType.DOOR, TileType.STAIRS_UP, TileType.STAIRS_DOWN]:
                # Monster safe room restriction
                if not isinstance(entity, Player) and self._is_in_safe_room(new_x, new_y):
                    return

                entity.move(dx, dy)
                if isinstance(entity, Player):
                    self.add_event("MOVE", {"entity": entity_id, "x": entity.pos.x, "y": entity.pos.y})

                # Player item pickup
                if isinstance(entity, Player):
                    items_to_pickup = [i_id for i_id, i in self.items.items() if i.pos.x == entity.pos.x and i.pos.y == entity.pos.y]
                    for i_id in items_to_pickup:
                        item = self.items[i_id]
                        if entity.add_to_inventory(item):
                            del self.items[i_id]
                            self.add_event("PICKUP", {"player": entity.id, "item": item.id})
                
                # If player moves onto STAIRS_DOWN, go to next floor
                if entity_id in self.players and tile == TileType.STAIRS_DOWN:
                    self.add_event("STAIRS_DOWN", {"player": entity_id})
                    self.next_floor()

                # If player moves onto STAIRS_UP, go to prev floor
                if entity_id in self.players and tile == TileType.STAIRS_UP:
                    if self.depth > 1:
                        self.add_event("STAIRS_UP", {"player": entity_id})
                        self.prev_floor()

    def next_floor(self):
        if self.depth < 50:
            self.generate_floor(self.depth + 1)
            # Reset player positions to STAIRS_UP
            spawn_pos = self._get_stairs_pos(TileType.STAIRS_UP)
            for p in self.players.values():
                p.pos = spawn_pos

    def prev_floor(self):
        if self.depth > 1:
            self.generate_floor(self.depth - 1)
            # Reset player positions to STAIRS_DOWN (since we came from UP)
            spawn_pos = self._get_stairs_pos(TileType.STAIRS_DOWN)
            for p in self.players.values():
                p.pos = spawn_pos

    def update_tick(self):
        # Update Players (Regen)
        for player in self.players.values():
            if player.is_downed or not player.is_alive:
                continue
            
            if player.regen_ticks > 0:
                player.regen_ticks -= 1
                # 50% max HP over 50 ticks? (approx 2.5 seconds at 20 ticks/sec or 5 seconds at 10 ticks/sec)
                # sleep is 0.05, so approx 20 ticks per second. 50 ticks = 2.5 seconds.
                regen_amount = (player.get_total_max_hp() * 0.5) / 50
                player.hp = min(player.get_total_max_hp(), player.hp + regen_amount)

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
