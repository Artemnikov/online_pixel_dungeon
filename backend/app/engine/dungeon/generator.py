import random
from typing import List, Tuple

class TileType:
    VOID = 0
    WALL = 1
    FLOOR = 2
    DOOR = 3
    STAIRS_UP = 4
    STAIRS_DOWN = 5

class Room:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.center = (x + width // 2, y + height // 2)

    def intersects(self, other):
        return (self.x <= other.x + other.width and
                self.x + self.width >= other.x and
                self.y <= other.y + other.height and
                self.y + self.height >= other.y)

class DungeonGenerator:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid = [[TileType.VOID for _ in range(width)] for _ in range(height)]
        self.rooms: List[Room] = []

    def generate(self, max_rooms: int, min_room_size: int, max_room_size: int) -> Tuple[List[List[int]], List[Room]]:
        self.rooms = []
        
        for _ in range(max_rooms):
            w = random.randint(min_room_size, max_room_size)
            h = random.randint(min_room_size, max_room_size)
            x = random.randint(1, self.width - w - 1)
            y = random.randint(1, self.height - h - 1)

            new_room = Room(x, y, w, h)
            
            # Check for intersections
            if any(new_room.intersects(other) for other in self.rooms):
                continue
            
            self._create_room(new_room)
            
            if self.rooms:
                # Connect to previous room
                prev_center = self.rooms[-1].center
                new_center = new_room.center
                self._create_tunnel(prev_center, new_center)
            
            self.rooms.append(new_room)
        
        # Add stairs
        if self.rooms:
            up_x, up_y = self.rooms[0].center
            down_x, down_y = self.rooms[-1].center
            self.grid[up_y][up_x] = TileType.STAIRS_UP
            self.grid[down_y][down_x] = TileType.STAIRS_DOWN

        return self.grid, self.rooms

    def _create_room(self, room: Room):
        for y in range(room.y, room.y + room.height):
            for x in range(room.x, room.x + room.width):
                # Inside floor
                self.grid[y][x] = TileType.FLOOR
        
        # Add borders (Walls) - simpler logic for now: just surround floor with walls if void
        for y in range(room.y - 1, room.y + room.height + 1):
            for x in range(room.x - 1, room.x + room.width + 1):
                if self.grid[y][x] == TileType.VOID:
                    self.grid[y][x] = TileType.WALL

    def _create_tunnel(self, start: Tuple[int, int], end: Tuple[int, int]):
        x1, y1 = start
        x2, y2 = end
        
        # Horizontal then Vertical or vice-versa
        if random.random() < 0.5:
            self._h_tunnel(x1, x2, y1)
            self._v_tunnel(y1, y2, x2)
        else:
            self._v_tunnel(y1, y2, x1)
            self._h_tunnel(x1, x2, y2)

    def _h_tunnel(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.grid[y][x] = TileType.FLOOR
            # Surround with walls if void
            if y > 0 and self.grid[y-1][x] == TileType.VOID: self.grid[y-1][x] = TileType.WALL
            if y < self.height - 1 and self.grid[y+1][x] == TileType.VOID: self.grid[y+1][x] = TileType.WALL

    def _v_tunnel(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.grid[y][x] = TileType.FLOOR
            # Surround with walls if void
            if x > 0 and self.grid[y][x-1] == TileType.VOID: self.grid[y][x-1] = TileType.WALL
            if x < self.width - 1 and self.grid[y][x+1] == TileType.VOID: self.grid[y][x+1] = TileType.WALL

if __name__ == "__main__":
    gen = DungeonGenerator(40, 30)
    level = gen.generate(10, 4, 8)
    for row in level:
        print("".join(['#' if t == TileType.WALL else '.' if t == TileType.FLOOR else 'U' if t == TileType.STAIRS_UP else 'D' if t == TileType.STAIRS_DOWN else ' ' for t in row]))
