import uuid
import time
import random
from typing import Dict, List, Optional, Tuple
from app.engine.dungeon.generator import DungeonGenerator, TileType
from app.engine.entities.base import Player, Mob, Position, EntityType, Mob as MobEntity, Item, Weapon, Wearable, Faction, Difficulty, HealthPotion, RevivingPotion, CharacterClass, Bow, Staff, Throwable, Stone, Boomerang, ThrowableDagger

MONSTER_TABLE = {
    "Marsupial Rat": {"hp": 8, "attack": 2, "defense": 0, "evasion": 0.05, "speed": 1.0, "attack_cooldown": 5.0, "min_floor": 1, "max_floor": 4, "weight": 10},
    "Sewer Snake": {"hp": 5, "attack": 2, "defense": 0, "evasion": 0.50, "speed": 1.0, "attack_cooldown": 4.0, "min_floor": 1, "max_floor": 4, "weight": 8},
    "Gnoll Scout": {"hp": 15, "attack": 3, "defense": 1, "evasion": 0.10, "speed": 1.0, "attack_cooldown": 4.0, "min_floor": 2, "max_floor": 4, "weight": 7},
    "Sewer Crab": {"hp": 12, "attack": 4, "defense": 2, "evasion": 0.10, "speed": 2.2, "attack_cooldown": 3.0, "min_floor": 3, "max_floor": 4, "weight": 5},
    "Albino Rat": {"hp": 20, "attack": 4, "defense": 1, "evasion": 0.20, "speed": 1.2, "attack_cooldown": 4.0, "min_floor": 2, "max_floor": 4, "weight": 1},
    "Fetid Rat": {"hp": 25, "attack": 5, "defense": 2, "evasion": 0.00, "speed": 0.8, "attack_cooldown": 6.0, "min_floor": 2, "max_floor": 4, "weight": 1},
}

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
        self.player_count = 0 
        
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
        if not self.rooms:
            return False

        start_room = self.rooms[0]
        end_room = self.rooms[-1]
        
        if (start_room.x <= x < start_room.x + start_room.width and
            start_room.y <= y < start_room.y + start_room.height):
            return True
        
        if (end_room.x <= x < end_room.x + end_room.width and
            end_room.y <= y < end_room.y + end_room.height):
            return True
            
        return False

    def _spawn_content(self):
        floor_tiles = [(x, y) for y in range(self.height) for x in range(self.width) 
                       if self.grid[y][x] in [TileType.FLOOR, TileType.FLOOR_WOOD, TileType.FLOOR_WATER, TileType.FLOOR_COBBLE]]
        
        unsafe_floor_tiles = [pos for pos in floor_tiles if not self._is_in_safe_room(pos[0], pos[1])]
        
        if self.depth % 5 == 0:
            self._spawn_boss(unsafe_floor_tiles)
        else:
            available_monsters = [
                name for name, stats in MONSTER_TABLE.items()
                if stats["min_floor"] <= self.depth <= stats["max_floor"]
            ]
            
            if available_monsters:
                weights = [MONSTER_TABLE[name]["weight"] for name in available_monsters]
                num_mobs = 5 + (self.depth * 2)
                for _ in range(num_mobs):
                    if not unsafe_floor_tiles: break
                    x, y = unsafe_floor_tiles.pop(random.randint(0, len(unsafe_floor_tiles) - 1))
                    
                    monster_name = random.choices(available_monsters, weights=weights)[0]
                    stats = MONSTER_TABLE[monster_name]
                    
                    mob_id = str(uuid.uuid4())
                    self.mobs[mob_id] = MobEntity(
                        id=mob_id,
                        name=monster_name,
                        pos=Position(x=x, y=y),
                        hp=stats["hp"],
                        max_hp=stats["hp"],
                        attack=stats["attack"],
                        defense=stats["defense"],
                        evasion=stats["evasion"],
                        speed=stats["speed"],
                        attack_cooldown=stats["attack_cooldown"],
                        faction=Faction.DUNGEON
                    )

        num_items = 4 + random.randint(0, 3)
        for _ in range(num_items):
            if not floor_tiles: break
            x, y = floor_tiles.pop(random.randint(0, len(floor_tiles) - 1))
            item_id = str(uuid.uuid4())
            
            rand = random.random()
            if rand < 0.2:
                # Weapon
                self.items[item_id] = Weapon(
                    id=item_id,
                    name=random.choice(["Rusty Sword", "Wooden Club", "Dagger"]),
                    pos=Position(x=x, y=y),
                    damage=2 + random.randint(0, 2),
                    range=1,
                    strength_requirement=10 + random.randint(-2, 2),
                    attack_cooldown=3.0 if "Dagger" not in "Rusty Sword, Wooden Club" else 1.5
                )
            elif rand < 0.3: 
                # Bow
                self.items[item_id] = Bow(
                    id=item_id,
                    name="Old Bow",
                    pos=Position(x=x, y=y),
                    damage=2 + random.randint(0, 2),
                    strength_requirement=10,
                    attack_cooldown=3.5 # Bow: 1 attack / 3.5 seconds
                )
            elif rand < 0.4:
                # Staff
                self.items[item_id] = Staff(
                    id=item_id,
                    name="Magic Staff",
                    pos=Position(x=x, y=y),
                    damage=1 + random.randint(0, 2),
                    magic_damage=2 + random.randint(0, 2),
                    strength_requirement=10
                )
            elif rand < 0.7:
                # Wearable
                self.items[item_id] = Wearable(
                    id=item_id,
                    name=random.choice(["Cloth Armor", "Leather Vest", "Broken Shield"]),
                    pos=Position(x=x, y=y),
                    strength_requirement=10 + random.randint(-2, 2),
                    health_boost=5 + random.randint(0, 5)
                )
            elif rand < 0.8:
                # Throwables
                t_rand = random.random()
                if t_rand < 0.5:
                    self.items[item_id] = Stone(id=item_id, pos=Position(x=x, y=y), damage=1, range=5)
                elif t_rand < 0.8:
                    self.items[item_id] = ThrowableDagger(id=item_id, pos=Position(x=x, y=y), damage=4, range=4)
                else:
                    self.items[item_id] = Boomerang(id=item_id, pos=Position(x=x, y=y), damage=3, range=6)
            elif rand < 0.9:
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
        
        name = f"Floor {self.depth} Boss"
        hp = 100 + (self.depth * 20)
        attack = 10 + self.depth
        defense = 5 + self.depth
        evasion = 0.05
        
        if self.depth == 5:
            name = "Goo"
            hp = 150
            attack = 12
            defense = 8
            evasion = 0.1

        self.mobs[boss_id] = MobEntity(
            id=boss_id,
            type=EntityType.BOSS,
            name=name,
            pos=Position(x=x, y=y),
            hp=hp,
            max_hp=hp,
            attack=attack,
            defense=defense,
            evasion=evasion,
            faction=Faction.DUNGEON
        )

    def add_player(self, player_id: str, name: str, class_type: str = CharacterClass.WARRIOR) -> Player:
        spawn_pos = self._get_stairs_pos(TileType.STAIRS_UP)
        
        self.player_count += 1
        
        inventory = []
        equipped_weapon = None
        equipped_wearable = None
        
        if class_type == CharacterClass.WARRIOR:
            w = Weapon(id=str(uuid.uuid4()), name="Shortsword", damage=3, range=1, strength_requirement=10, attack_cooldown=3.0)
            inventory.append(w)
            equipped_weapon = w
            a = Wearable(id=str(uuid.uuid4()), name="Cloth Armor", strength_requirement=10, health_boost=5)
            inventory.append(a)
            equipped_wearable = a
            
        elif class_type == CharacterClass.MAGE:
            w = Staff(id=str(uuid.uuid4()), name="Mage's Staff", damage=2, magic_damage=3, strength_requirement=10, charges=4, attack_cooldown=3.0)
            inventory.append(w)
            equipped_weapon = w
            
        elif class_type == CharacterClass.ROGUE:
            w = Weapon(id=str(uuid.uuid4()), name="Dagger", damage=2, range=1, strength_requirement=9, attack_cooldown=1.5)
            inventory.append(w)
            equipped_weapon = w
            a = Wearable(id=str(uuid.uuid4()), name="Rogue's Cloak", strength_requirement=9, health_boost=2)
            inventory.append(a)
            equipped_wearable = a

        elif class_type == CharacterClass.HUNTRESS:
            w = Bow(id=str(uuid.uuid4()), name="Spirit Bow", damage=2, strength_requirement=10, attack_cooldown=3.5)
            inventory.append(w)
            equipped_weapon = w
        
        
        player = Player(
            id=player_id,
            name=name,
            pos=spawn_pos,
            hp=10,
            max_hp=10,
            attack=3,
            defense=1,
            faction=Faction.PLAYER,
            class_type=class_type,
            inventory=inventory,
            equipped_weapon=equipped_weapon,
            equipped_wearable=equipped_wearable
        )
        
        # Adjust HP based on wearable
        player.hp = player.get_total_max_hp()
        
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

                    # Check cooldown
                    current_time = time.time()
                    cooldown = entity.attack_cooldown
                    if isinstance(entity, Player) and entity.equipped_weapon:
                        cooldown = entity.equipped_weapon.attack_cooldown
                    
                    if current_time - entity.last_attack_time < cooldown:
                        return # Attack is on cooldown

                    entity.last_attack_time = current_time

                    attack_power = entity.attack
                    if isinstance(entity, Player):
                        attack_power = entity.get_total_attack()
                    
                    # Evasion Check
                    if random.random() < target_entity.evasion:
                        self.add_event("MISS", {"source": entity.id, "target": target_entity.id})
                        return # Missed!
                    
                    dmg = target_entity.take_damage(attack_power)
                    self.add_event("ATTACK", {"source": entity.id, "target": target_entity.id, "damage": dmg})
                    if dmg > 0:
                        self.add_event("DAMAGE", {"target": target_entity.id, "amount": dmg})
                        
                        # Sound Effects for Melee
                        if isinstance(entity, Player):
                            # Player hitting Monster
                            # Default to slash for melee weapons
                             self.add_event("PLAY_SOUND", {"sound": "HIT_SLASH"})
                        
                        if isinstance(target_entity, Player):
                            # Player getting hit
                            self.add_event("PLAY_SOUND", {"sound": "HIT_BODY"})
                            # Low health warning
                            if target_entity.hp / target_entity.get_total_max_hp() <= 0.3:
                                 self.add_event("PLAY_SOUND", {"sound": "HEALTH_WARN"})

                        if not target_entity.is_alive:
                            self.add_event("DEATH", {"target": target_entity.id})
                return
            
            tile = self.grid[new_y][new_x]
            if tile in [TileType.FLOOR, TileType.DOOR, TileType.STAIRS_UP, TileType.STAIRS_DOWN, 
                        TileType.FLOOR_WOOD, TileType.FLOOR_WATER, TileType.FLOOR_COBBLE]:
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
                        
    def perform_ranged_attack(self, player_id: str, item_id: str, target_x: int, target_y: int) -> Optional[int]:
        player = self.players.get(player_id)
        if not player or player.is_downed:
            return None

        # Find item: could be equipped weapon OR a throwable in inventory
        item = None
        if player.equipped_weapon and player.equipped_weapon.id == item_id:
            item = player.equipped_weapon
        else:
            item = next((i for i in player.inventory if i.id == item_id), None)

        if not item:
            return None

        # Determine properties
        is_throwable = isinstance(item, Throwable)
        is_weapon = isinstance(item, Weapon)
        
        if not (is_throwable or (is_weapon and getattr(item, 'projectile_type', None))):
             return None

        # Check cooldown (Global attack cooldown for now, or per-item?)
        # Base entity has last_attack_time.
        current_time = time.time()
        cooldown = 1.0
        if is_weapon:
            cooldown = item.attack_cooldown
        # Throwables might not have explicit cooldown in class def yet, using default 1.0 or fast?
        # Let's say throwables are fast or standard. Base Entity has 1.0. 
        # For throwables, let's use a standard 1.0s for now or 0.5s.
        
        if (current_time - player.last_attack_time) < cooldown:
            return None

        # Check range
        dist = abs(player.pos.x - target_x) + abs(player.pos.y - target_y)
        max_range = item.range if hasattr(item, 'range') else 1
        if dist > max_range:
            return None

        # Check LoS
        if not self._is_in_los(player.pos, Position(x=target_x, y=target_y)):
             return None

        # Consume cooldown
        player.last_attack_time = current_time

        # Logic for projectile
        projectile_type = getattr(item, 'projectile_type', 'arrow')

        # Find target at location
        target_entity = None
        for p in self.players.values():
            if p.id != player_id and p.pos.x == target_x and p.pos.y == target_y:
                target_entity = p
                break
        
        if not target_entity:
            for m in self.mobs.values():
                if m.is_alive and m.pos.x == target_x and m.pos.y == target_y:
                    target_entity = m
                    break
        
        # Identify projectile endpoint (if no target, it still flies to x,y)
        self.add_event("RANGED_ATTACK", {
            "source": player_id,
            "x": player.pos.x,
            "y": player.pos.y,
            "target_x": target_x,
            "target_y": target_y,
            "projectile": projectile_type
        })

        damage_dealt = 0
        if target_entity:
            # Check Faction
             if player.faction == target_entity.faction:
                 pass # Friendly fire ignored
             else:
                 attack_power = 0
                 if is_weapon:
                     attack_power = player.get_total_attack() # Includes strength + weapon damage? 
                     # Wait, get_total_attack uses equipped_weapon. 
                     # If we are throwing a rock, we shouldn't use equipped sword's damage.
                     # We should use item damage + maybe strength bonus?
                     if item == player.equipped_weapon:
                         attack_power = player.get_total_attack()
                     else:
                         # It's a throwable from inventory
                         attack_power = item.damage + (player.strength // 2) # Simple strength scaling
                 elif is_throwable:
                     attack_power = item.damage + (player.strength // 2)

                 damage_dealt = target_entity.take_damage(attack_power)
                 self.add_event("DAMAGE", {"target": target_entity.id, "amount": damage_dealt})
                 
                 # Sound Effects for Ranged Hit
                 if damage_dealt > 0:
                     if projectile_type == 'magic_bolt':
                         self.add_event("PLAY_SOUND", {"sound": "HIT_MAGIC"})
                     else:
                         self.add_event("PLAY_SOUND", {"sound": "HIT_ARROW"})

                     if isinstance(target_entity, Player):
                            self.add_event("PLAY_SOUND", {"sound": "HIT_BODY"})
                            if target_entity.hp / target_entity.get_total_max_hp() <= 0.3:
                                 self.add_event("PLAY_SOUND", {"sound": "HEALTH_WARN"})

                 if not target_entity.is_alive:
                     self.add_event("DEATH", {"target": target_entity.id})
        
        # Handle Consumption
        if is_throwable and item.consumable:
            if item in player.inventory:
                player.inventory.remove(item)
                # If it was equipped (unlikely for throwable in this logic but possible if we allowed equipping):
                if player.equipped_weapon == item:
                    player.equipped_weapon = None

        return damage_dealt


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
            
            # Use speed for movement frequency
            current_time = time.time()
            base_cooldown = 1.0 # Base action once a second
            if self.difficulty == Difficulty.HARD: base_cooldown = 0.8
            elif self.difficulty == Difficulty.EASY: base_cooldown = 1.5

            action_cooldown = base_cooldown / mob.speed
            
            if current_time - mob.last_move_time < action_cooldown:
                # Still allow attack if adjacent! 
                # PD usually takes a turn for both, but for real-time we want them to feel distinct.
                # If they are already in range, they use attack_cooldown which is separate.
                if dist > 1:
                    continue
            
            # Only update move time if they actually MOVE or attempt to.
            # But if they are attacking, we should still respect action cooldown?
            # Let's say speed affects how often they "step". 
            
            # Difficulty-specific behavior
            moved = False
            
            if self.difficulty == Difficulty.EASY:
                # Roam randomly, attack if adjacent
                if target_player and dist <= 1:
                    dx, dy = target_player.pos.x - mob.pos.x, target_player.pos.y - mob.pos.y
                    self.move_entity(mob.id, dx, dy)
                    mob.last_move_time = current_time
                    moved = True
                elif random.random() < 0.2: # Probability reduced because it runs every tick if not on cooldown
                    dx, dy = random.choice([(0,1), (0,-1), (1,0), (-1,0)])
                    self.move_entity(mob.id, dx, dy)
                    mob.last_move_time = current_time
                    moved = True

            elif self.difficulty == Difficulty.NORMAL:
                # Chase if in LOS, move towards player
                if target_player and dist <= 1:
                    dx, dy = target_player.pos.x - mob.pos.x, target_player.pos.y - mob.pos.y
                    self.move_entity(mob.id, dx, dy)
                    mob.last_move_time = current_time
                    moved = True
                elif target_player and self._is_in_los(mob.pos, target_player.pos):
                    # Move towards player if in LOS
                    step = self._get_next_step_to(mob.pos, target_player.pos)
                    if step:
                        self.move_entity(mob.id, step[0], step[1])
                        mob.last_move_time = current_time
                        moved = True
                elif random.random() < 0.2:
                    dx, dy = random.choice([(0,1), (0,-1), (1,0), (-1,0)])
                    self.move_entity(mob.id, dx, dy)
                    mob.last_move_time = current_time
                    moved = True

            elif self.difficulty == Difficulty.HARD:
                # Hunt across room (dist < 20), pathfinding
                if target_player and dist <= 1:
                    dx, dy = target_player.pos.x - mob.pos.x, target_player.pos.y - mob.pos.y
                    self.move_entity(mob.id, dx, dy)
                    mob.last_move_time = current_time
                    moved = True
                elif target_player and dist < 20:
                    # Pathfind to player
                    step = self._get_next_step_to(mob.pos, target_player.pos)
                    if step:
                        self.move_entity(mob.id, step[0], step[1])
                        mob.last_move_time = current_time
                        moved = True
                elif random.random() < 0.2:
                    dx, dy = random.choice([(0,1), (0,-1), (1,0), (-1,0)])
                    self.move_entity(mob.id, dx, dy)
                    mob.last_move_time = current_time
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
                    self.grid[ny][nx] in [TileType.FLOOR, TileType.DOOR, TileType.STAIRS_UP, TileType.STAIRS_DOWN,
                                          TileType.FLOOR_WOOD, TileType.FLOOR_WATER, TileType.FLOOR_COBBLE] and 
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
