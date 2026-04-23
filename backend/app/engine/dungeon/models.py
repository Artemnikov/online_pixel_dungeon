from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from app.engine.dungeon.constants import RoomKind, TrapType


@dataclass
class SewersProfile:
    STANDARD_ROOMS_MIN: int = 4
    STANDARD_ROOMS_MAX: int = 6
    SPECIAL_ROOMS_MIN: int = 1
    SPECIAL_ROOMS_MAX: int = 2
    HIDDEN_ROOMS_COUNT: int = 2

    depth: int = 1
    BASE_HIDDEN_DOOR_CHANCE: float = 0.1
    WATER_RATIO: float = 0.30
    GRASS_RATIO: float = 0.20

    TRAPS_MIN: int = 1
    TRAPS_MAX: int = 3
    TRAP_TYPES: Tuple[str, ...] = (TrapType.WORN_DART,)


@dataclass
class Room:
    x: int
    y: int
    width: int
    height: int
    kind: str = RoomKind.STANDARD
    template: str = "standard"
    tags: Set[str] = field(default_factory=set)
    room_id: int = -1

    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)

    def intersects(self, other: Room, padding: int = 1) -> bool:
        return (
            self.x - padding <= other.x + other.width
            and self.x + self.width + padding >= other.x
            and self.y - padding <= other.y + other.height
            and self.y + self.height + padding >= other.y
        )

    def contains(self, x: int, y: int) -> bool:
        return self.x <= x < self.x + self.width and self.y <= y < self.y + self.height

    def is_perimeter(self, x: int, y: int) -> bool:
        on_lr = x in (self.x - 1, self.x + self.width)
        on_tb = y in (self.y - 1, self.y + self.height)
        if on_lr and not on_tb:
            return self.y <= y < self.y + self.height
        if on_tb and not on_lr:
            return self.x <= x < self.x + self.width
        return False


@dataclass
class TrapInfo:
    x: int
    y: int
    trap_type: str
    hidden: bool = True
    active: bool = True


@dataclass
class Edge:
    a: int
    b: int
    secret: bool = False
    locked_room_id: Optional[int] = None


@dataclass
class DoorInfo:
    x: int
    y: int
    room_id: int
    actual_tile: int
    can_hide: bool
    force_hidden: bool
    hidden: bool = False


@dataclass
class SewersGenerationMetadata:
    region: str
    layout_kind: str
    room_ids_by_kind: Dict[str, List[int]]
    room_connections: List[Tuple[int, int]]
    hidden_doors: Dict[Tuple[int, int], int]
    locked_doors: Dict[Tuple[int, int], str]
    key_spawns: Dict[str, Tuple[int, int]]
    traps: Dict[Tuple[int, int], TrapInfo]
    start_room_id: int
    end_room_id: int
    seed: int = 0


@dataclass
class SewersGenerationResult:
    grid: List[List[int]]
    rooms: List[Room]
    metadata: SewersGenerationMetadata
