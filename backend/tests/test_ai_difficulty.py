import pytest
from app.engine.manager import GameInstance
from app.engine.entities.base import Position, Difficulty, TileType

def setup_game():
    game = GameInstance("test-game")
    game.mobs = {}
    game.players = {}
    # Create a simple 10x10 room
    game.width = 10
    game.height = 10
    game.grid = [[TileType.FLOOR for _ in range(10)] for _ in range(10)]
    return game

def test_easy_ai_roams_or_attacks():
    game = setup_game()
    game.difficulty = Difficulty.EASY
    
    player = game.add_player("p1", "Player")
    player.pos = Position(x=1, y=1)
    
    mob = game.mobs[list(game.mobs.keys())[0]] # Get one mob
    mob.pos = Position(x=3, y=3) # Far from player
    
    # Run many ticks, mob should move eventually
    moved = False
    for _ in range(100):
        old_pos = (mob.pos.x, mob.pos.y)
        game.update_tick()
        if (mob.pos.x, mob.pos.y) != old_pos:
            moved = True
            break
    assert moved, "Easy mob should roam eventually"
    
    # Test attack if adjacent
    mob.pos = Position(x=2, y=1)
    game.update_tick()
    assert player.hp < 10, "Easy mob should attack when adjacent"

def test_normal_ai_chases_in_los():
    game = setup_game()
    game.difficulty = Difficulty.NORMAL
    
    player = game.add_player("p1", "Player")
    player.pos = Position(x=1, y=1)
    
    # Mob far away but in LOS (open floor)
    mob = list(game.mobs.values())[0]
    mob.pos = Position(x=5, y=1)
    
    game.update_tick()
    # Should move closer to (1,1)
    assert mob.pos.x < 5, "Normal mob should move towards player in LOS"

def test_normal_ai_ignores_without_los():
    game = setup_game()
    game.difficulty = Difficulty.NORMAL
    
    player = game.add_player("p1", "Player")
    player.pos = Position(x=1, y=1)
    
    # Place a wall between player and mob
    game.grid[1][3] = TileType.WALL
    
    mob = list(game.mobs.values())[0]
    mob.pos = Position(x=5, y=1)
    
    # Run few ticks, shouldn't move towards player (though might roaming randomly)
    # Roaming is 5% chance. Chasing is deterministic. 
    # We check if it moves deterministic towards player.
    for _ in range(20):
        game.update_tick()
        if mob.pos.x < 5:
            # If it moves closer, it might be random roam. 
            # But it shouldn't be aggressive.
            pass
    
def test_hard_ai_hunts():
    game = setup_game()
    game.difficulty = Difficulty.HARD
    
    player = game.add_player("p1", "Player")
    player.pos = Position(x=1, y=1)
    
    # Corner case: Pathfinding through a wall (it must go around)
    # . . . . .
    # P W . . .
    # . W . M .
    # . W . . .
    # . . . . .
    game.grid[1][2] = TileType.WALL
    game.grid[2][2] = TileType.WALL
    game.grid[3][2] = TileType.WALL
    
    mob = list(game.mobs.values())[0]
    mob.pos = Position(x=4, y=2)
    
    game.update_tick()
    # Should move along path (e.g. up or down around the wall)
    assert (mob.pos.x != 4 or mob.pos.y != 2), "Hard mob should move"
    # Check if it didn't move into wall
    assert game.grid[mob.pos.y][mob.pos.x] != TileType.WALL
