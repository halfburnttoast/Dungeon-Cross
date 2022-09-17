from enum import Enum

class MouseAction(Enum):
    """Mouse action ENUM"""
    NONE        = 0
    PLACE_WALL  = 1
    PLACE_MARK  = 2
    REMOVE_WALL = 3
    REMOVE_MARK = 4
    MARK        = 5
    MENU_ACTION = 6