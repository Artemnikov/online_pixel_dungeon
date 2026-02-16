import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.engine.manager import GameInstance, MONSTER_TABLE
from app.engine.dungeon.generator import TileType

def test_floor_spawning():
    # Test Floor 1
    game = GameInstance("test-game-1")
    game.generate_floor(1)
    
    mobs_floor_1 = [m.name for m in game.mobs.values()]
    print(f"Floor 1 mobs: {set(mobs_floor_1)}")
    # Should only contain Marsupial Rat or Sewer Snake
    allowed_1 = ["Marsupial Rat", "Sewer Snake"]
    for m in mobs_floor_1:
        assert m in allowed_1, f"Unexpected monster {m} on floor 1"

    # Test Floor 3
    game.generate_floor(3)
    mobs_floor_3 = [m.name for m in game.mobs.values()]
    print(f"Floor 3 mobs: {set(mobs_floor_3)}")
    # Should contain more variety
    allowed_3 = list(MONSTER_TABLE.keys())
    for m in mobs_floor_3:
        assert m in allowed_3
    
    # Check if Sewer Crab spawned (it's eligible on floor 3)
    # Since it's random, we might need a few tries or just check eligibility
    assert any(m in ["Gnoll Scout", "Sewer Crab", "Albino Rat"] for m in mobs_floor_3)

    # Test Floor 5 (Boss)
    game.generate_floor(5)
    mobs_floor_5 = [m.name for m in game.mobs.values()]
    print(f"Floor 5 mobs: {set(mobs_floor_5)}")
    assert "Goo" in mobs_floor_5
    assert len(game.mobs) == 1 # Only boss on boss floor usually in this impl

    print("All spawning tests passed!")

if __name__ == "__main__":
    try:
        test_floor_spawning()
    except AssertionError as e:
        print(f"Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
