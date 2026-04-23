class TileType:
    VOID = 0
    WALL = 1
    FLOOR = 2
    DOOR = 3
    STAIRS_UP = 4
    STAIRS_DOWN = 5
    FLOOR_WOOD = 6
    FLOOR_WATER = 7
    FLOOR_COBBLE = 8
    FLOOR_GRASS = 9
    LOCKED_DOOR = 10
    WALL_DECO = 17
    EMPTY_DECO = 18
    HIGH_GRASS = 19
    SECRET_DOOR = 20


class RoomKind:
    STANDARD = "standard"
    SPECIAL = "special"
    HIDDEN = "hidden"


class TrapType:
    WORN_DART = "worn_dart"
