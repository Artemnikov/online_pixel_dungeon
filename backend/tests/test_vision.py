import pytest
from app.engine.manager import GameInstance
from app.engine.entities.base import Position, TileType

def test_los_blocked_by_wall():
    game = GameInstance("test-game")
    # Manual grid setup for predictable test
    game.width = 10
    game.height = 10
    game.grid = [[TileType.FLOOR for _ in range(10)] for _ in range(10)]
    game.grid[1][1] = TileType.WALL
    
    # P1 is at (0, 1), P2 at (2, 1). Wall is at (1, 1).
    p1 = Position(x=0, y=1)
    p2 = Position(x=2, y=1)
    
    assert game._is_in_los(p1, p2) == False
    
    # Clear wall
    game.grid[1][1] = TileType.FLOOR
    assert game._is_in_los(p1, p2) == True

def test_get_visible_tiles():
    game = GameInstance("test-game")
    game.width = 20
    game.height = 20
    game.grid = [[TileType.FLOOR for _ in range(20)] for _ in range(20)]
    
    pos = Position(x=10, y=10)
    visible = game.get_visible_tiles(pos, radius=2)
    
    # (10,10) plus neighbors within radius 2
    # Simple check: (10,12) should be in, (10,13) should not.
    visible_coords = set(visible)
    assert (10, 12) in visible_coords
    assert (10, 13) not in visible_coords

def test_get_state_filters_mobs():
    game = GameInstance("test-game")
    game.width = 20
    game.height = 20
    game.grid = [[TileType.FLOOR for _ in range(20)] for _ in range(20)]
    
    player_id = "p1"
    game.add_player(player_id, "Tester")
    game.players[player_id].pos = Position(x=10, y=10)
    
    # Mob 1: Near player
    mob1_id = "m1"
    from app.engine.entities.base import Mob
    game.mobs[mob1_id] = Mob(id=mob1_id, name="Rat1", pos=Position(x=11, y=11), hp=10, max_hp=10, attack=1, defense=0, faction="dungeon")
    
    # Mob 2: Far from player
    mob2_id = "m2"
    game.mobs[mob2_id] = Mob(id=mob2_id, name="Rat2", pos=Position(x=0, y=0), hp=10, max_hp=10, attack=1, defense=0, faction="dungeon")
    
    state = game.get_state(player_id)
    mob_ids = [m["id"] for m in state["mobs"]]
    
    assert mob1_id in mob_ids
    assert mob2_id not in mob_ids
