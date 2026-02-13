from pydantic import BaseModel
from typing import Optional, List, Dict

class EntityType:
    PLAYER = "player"
    MOB = "mob"
    BOSS = "boss"
    ITEM = "item"

class Position(BaseModel):
    x: int
    y: int

class Entity(BaseModel):
    id: str
    type: str
    name: str
    pos: Position
    hp: int
    max_hp: int
    attack: int
    defense: int
    speed: float = 1.0
    is_alive: bool = True

    def move(self, dx: int, dy: int):
        self.pos.x += dx
        self.pos.y += dy

    def take_damage(self, amount: int):
        dmg = max(0, amount - self.defense)
        self.hp -= dmg
        if self.hp <= 0:
            self.hp = 0
            self.is_alive = False
        return dmg

class Item(BaseModel):
    id: str
    name: str
    type: str # "weapon" or "wearable"
    pos: Optional[Position] = None

class Weapon(Item):
    type: str = "weapon"
    damage: int
    range: int
    enchantment: Optional[str] = None
    strength_requirement: int

class Wearable(Item):
    type: str = "wearable"
    strength_requirement: int
    health_boost: int
    enchantment: Optional[str] = None

class Mob(Entity):
    type: str = EntityType.MOB
    ai_state: str = "idle"
    target_id: Optional[str] = None

class Player(Entity):
    type: str = EntityType.PLAYER
    experience: int = 0
    level: int = 1
    strength: int = 10
    inventory: List[Item] = []
    equipped_weapon: Optional[Weapon] = None
    equipped_wearable: Optional[Wearable] = None
    websocket_id: Optional[str] = None

    def get_total_attack(self) -> int:
        bonus = 0
        if self.equipped_weapon:
            bonus = self.equipped_weapon.damage
        return self.attack + bonus

    def get_total_defense(self) -> int:
        # Wearables can provide defense in the future, for now they boost health
        return self.defense

    def get_total_max_hp(self) -> int:
        bonus = 0
        if self.equipped_wearable:
            bonus = self.equipped_wearable.health_boost
        return self.max_hp + bonus

    def add_to_inventory(self, item: Item) -> bool:
        if len(self.inventory) < 20:
            self.inventory.append(item)
            return True
        return False

    def equip_item(self, item_id: str) -> bool:
        item = next((i for i in self.inventory if i.id == item_id), None)
        if not item:
            return False

        if isinstance(item, Weapon):
            if self.strength >= item.strength_requirement:
                self.equipped_weapon = item
                return True
        elif isinstance(item, Wearable):
            if self.strength >= item.strength_requirement:
                self.equipped_wearable = item
                # Recalculate health if needed
                if self.hp > self.get_total_max_hp():
                    self.hp = self.get_total_max_hp()
                return True
        return False
