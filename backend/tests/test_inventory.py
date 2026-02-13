import pytest
from app.engine.entities.base import Player, Weapon, Wearable, Position
from app.engine.manager import GameInstance

def test_player_inventory_limit():
    player = Player(id="p1", name="Test", pos=Position(x=0,y=0), hp=10, max_hp=10, attack=1, defense=0)
    for i in range(20):
        assert player.add_to_inventory(Weapon(id=f"w{i}", name=f"Sword {i}", damage=1, range=1, strength_requirement=0)) is True
    
    # 21st item should fail
    assert player.add_to_inventory(Weapon(id="w21", name="Sword 21", damage=1, range=1, strength_requirement=0)) is False

def test_player_equip_weapon():
    player = Player(id="p1", name="Test", pos=Position(x=0,y=0), hp=10, max_hp=10, attack=5, defense=0, strength=10)
    weapon = Weapon(id="w1", name="Pro Sword", damage=10, range=1, strength_requirement=5)
    player.add_to_inventory(weapon)
    
    assert player.get_total_attack() == 5
    assert player.equip_item("w1") is True
    assert player.equipped_weapon.id == "w1"
    assert player.get_total_attack() == 15

def test_player_equip_strength_requirement():
    player = Player(id="p1", name="Test", pos=Position(x=0,y=0), hp=10, max_hp=10, attack=5, defense=0, strength=5)
    heavy_weapon = Weapon(id="w1", name="Heavy Axe", damage=10, range=1, strength_requirement=10)
    player.add_to_inventory(heavy_weapon)
    
    assert player.equip_item("w1") is False
    assert player.equipped_weapon is None

def test_player_wearable_hp_boost():
    player = Player(id="p1", name="Test", pos=Position(x=0,y=0), hp=10, max_hp=10, attack=5, defense=0, strength=10)
    armor = Wearable(id="a1", name="Plate Armor", health_boost=20, strength_requirement=0)
    player.add_to_inventory(armor)
    
    assert player.get_total_max_hp() == 10
    assert player.equip_item("a1") is True
    assert player.get_total_max_hp() == 30

def test_item_pickup_in_game():
    game = GameInstance("test-game")
    player_id = "test-player"
    player = game.add_player(player_id, "Tester")
    
    # Manually place an item
    item_id = "test-item"
    item_pos = Position(x=player.pos.x + 1, y=player.pos.y)
    item = Weapon(id=item_id, name="Test Sword", pos=item_pos, damage=5, range=1, strength_requirement=0)
    game.items[item_id] = item
    
    # Move player to item
    game.move_entity(player_id, 1, 0)
    
    assert player.pos.x == item_pos.x
    assert player.pos.y == item_pos.y
    assert len(player.inventory) == 1
    assert player.inventory[0].id == item_id
    assert item_id not in game.items
