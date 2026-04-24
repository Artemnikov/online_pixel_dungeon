"""MazeConnectionRoom: connection corridor used in branches that lead to a
secret room.

Mirrors SPD `rooms/connection/MazeConnectionRoom.java`. Functionally the
same as a TunnelRoom for our purposes — draws an L-shaped tunnel through
the room interior. The semantic distinction is just the ABSENCE of an
implicit corridor floor inside the room (so the path between two doors
is the only walkable strip), giving the area a more confined "maze"
feel. We delegate to TunnelRoom's paint here; a future pass can
introduce a wider/randomized path pattern if SPD's variant proves
visually distinct enough to warrant the divergence.
"""

from app.engine.dungeon.rooms.connection.tunnel_room import TunnelRoom


class MazeConnectionRoom(TunnelRoom):
    pass
