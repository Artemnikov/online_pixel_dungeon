import pytest
from app.engine.manager import GameInstance
from app.engine.entities.base import Position

def test_combat_logic():
    game = GameInstance("test-game")
    
    # Clear mobs for controlled test
    game.mobs = {}
    
    # Add a player
    player_id = "test-player"
    player = game.add_player(player_id, "Tester")
    player.pos = Position(x=1, y=1)
    player.hp = 10
    player.max_hp = 10
    player.attack = 5
    
    # Add a mob
    mob_id = "test-mob"
    from app.engine.entities.base import Mob as MobEntity
    mob = MobEntity(
        id=mob_id,
        name="Rat",
        pos=Position(x=2, y=1),
        hp=10,
        max_hp=10,
        attack=2,
        defense=0
    )
    game.mobs[mob_id] = mob
    
    # Attack the mob by moving into it
    game.move_entity(player_id, 1, 0)
    
    # Check if mob took damage
    assert mob.hp == 5
    assert mob.is_alive == True
    
    # Attack again to kill it
    game.move_entity(player_id, 1, 0)
    assert mob.hp == 0
    assert mob.is_alive == False

def test_player_takes_damage():
    game = GameInstance("test-game")
    game.mobs = {}
    
    # Add a player
    player_id = "test-player"
    player = game.add_player(player_id, "Tester")
    player.pos = Position(x=1, y=1)
    player.hp = 10
    player.max_hp = 10
    player.defense = 0
    
    # Add a mob
    mob_id = "test-mob"
    from app.engine.entities.base import Mob as MobEntity
    mob = MobEntity(
        id=mob_id,
        name="Rat",
        pos=Position(x=2, y=1),
        hp=10,
        max_hp=10,
        attack=2,
        defense=0
    )
    game.mobs[mob_id] = mob
    
    # Mob attacks player by moving into them
    game.move_entity(mob_id, -1, 0)
    
    # Check if player took damage
    assert player.hp == 8
