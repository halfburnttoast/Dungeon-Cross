from enum import Enum

class MapObject(Enum):
    EMPTY = 0
    WALL  = 1
    ENEMY = 2
    CHEST = 3
    MARK  = 4