import os
import sys
import math
import pygame
from enum import Enum

TILE_SIZE = 80
G_RESOLUTION = (TILE_SIZE * 9, TILE_SIZE * 9)
TARGET_FPS = 15

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class MouseAction(Enum):
    NONE   = 0,
    PLACE  = 1,
    REMOVE = 2,
    MARK   = 3

class Board:
    def __init__(self, screen):
        self.board_layout = [
            [0, 0, 0, 0, 0, 1, 1, 1],
            [0, 1, 0, 1, 0, 0, 0, 2],
            [0, 1, 2, 1, 0, 1, 1, 1],
            [0, 1, 1, 1, 0, 0, 0, 2],
            [0, 0, 0, 1, 0, 1, 1, 1],
            [0, 3, 0, 1, 0, 0, 0, 2],
            [0, 0, 0, 1, 0, 1, 1, 1],
            [1, 1, 1, 1, 0, 0, 0, 2],
        ]
        self.hint_x = [0] * 8
        self.hint_y = [0] * 8
        self.mouse_action = MouseAction.NONE
        self.screen = screen
        self.check_win_state = False
        self.game_won = False

        # load sprites
        self.sprite_wall  = self._load_sprite(resource_path('sprite/wall.png'))
        self.sprite_floor = self._load_sprite(resource_path('sprite/floor.png'))
        self.sprite_enemy = self._load_sprite(resource_path('sprite/enemy.png'))
        self.sprite_chest = self._load_sprite(resource_path('sprite/chest.png'))
        self.sprite_frame = self._load_sprite(resource_path('sprite/frame.png'))
        self.sprite_win   = self._load_sprite(resource_path('sprite/win.png'), 500, 500)
        self.sprite_number = []
        for i in range(0, 9):
            self.sprite_number.append(self._load_sprite(resource_path(f'sprite/{i}.png')))

        # calculate hints for border
        self._calc_hints()
        self.placed_walls = self._strip_walls()

    def load_map(self):
        pass

    def draw_debug_board(self):
        self._draw_frame()
        for y in range(1, 9):
            for x in range(1, 9):
                self.screen.blit(self.sprite_floor, (x * TILE_SIZE, y * TILE_SIZE))
        self._draw_map_objects(show_wall=False)
        self._draw_placed_walls()
        if self.game_won:
            self.screen.blit(self.sprite_win, (128, 128))
    
    def handle_mouse(self):
        mx, my = self._get_mouse_to_grid()
        cell_state = self.placed_walls[my][mx]
        map_obj    = self.board_layout[my][mx]
        mouse_press = pygame.mouse.get_pressed()
        if not mouse_press[0] and self.mouse_action != MouseAction.NONE:
            self.mouse_action = MouseAction.NONE
        if mouse_press[0] and not self.game_won:
            if self.mouse_action == MouseAction.NONE:
                if cell_state:
                    self.mouse_action = MouseAction.REMOVE
                else:
                    self.mouse_action = MouseAction.PLACE
            if self.mouse_action == MouseAction.PLACE:
                if map_obj == 0 or map_obj == 1:
                    if cell_state == 0:
                        self.placed_walls[my][mx] = 1
                        self.check_win_state = True
            elif self.mouse_action == MouseAction.REMOVE:
                if map_obj == 0 or map_obj == 1:
                    if cell_state == 1:
                        self.placed_walls[my][mx] = 0
                        self.check_win_state = True
        if self.check_win_state:
            self._check_win()
    
    def _check_win(self):
        if self.board_layout == self.placed_walls:
            self.game_won = True
            print("Win")
        self.check_win_state = False

    def _strip_walls(self) -> list:
        out = []
        for row in self.board_layout:
            out.append([v if v != 1 else 0 for v in row])
        return out

    def _calc_hints(self):
        for i, v in enumerate(self.board_layout):
            self.hint_y[i] = v.count(1)
        for x in range(8):
            sum_y = 0
            for y in range(8):
                if self.board_layout[y][x] == 1:
                    sum_y = sum_y + 1
            self.hint_x[x] = sum_y

    def _draw_sprite(self, sprite: pygame.image, grid_pos: tuple):
        pos_x = (grid_pos[0] + 1) * TILE_SIZE
        pos_y = (grid_pos[1] + 1) * TILE_SIZE
        self.screen.blit(sprite, (pos_x, pos_y))

    def _draw_placed_walls(self):
        for y, row in enumerate(self.placed_walls):
            for x, obj in enumerate(row):
                if obj == 1:
                    self._draw_sprite(self.sprite_wall, (x, y))  

    def _draw_map_objects(self, show_wall: bool = False):
        for y, row in enumerate(self.board_layout):
            for x, obj in enumerate(row):
                if  show_wall and obj == 1:
                    self._draw_sprite(self.sprite_wall, (x, y))
                elif obj == 2:
                    self._draw_sprite(self.sprite_enemy, (x, y))
                elif obj == 3:
                    self._draw_sprite(self.sprite_chest, (x, y))

    def _load_sprite(self, path: str, size_x: int = TILE_SIZE, size_y: int = TILE_SIZE) -> pygame.image:
        image = pygame.image.load(resource_path(path))
        return pygame.transform.scale(image, (size_x, size_x))

    def _get_mouse_to_grid(self) -> tuple:
        pos_x, pos_y = pygame.mouse.get_pos()
        pos_x = math.floor((pos_x / TILE_SIZE) - 1)
        pos_y = math.floor((pos_y / TILE_SIZE) - 1)
        pos_x = max(min(8, pos_x), 0)
        pos_y = max(min(8, pos_y), 0)
        return(pos_x, pos_y)

    def _draw_frame(self):
        for i in range(1, 9):
            hint_x = self.sprite_number[self.hint_x[i - 1]]
            hint_y = self.sprite_number[self.hint_y[i - 1]]
            self.screen.blit(hint_x, (i * TILE_SIZE, 0))
            self.screen.blit(hint_y, (0, i * TILE_SIZE))
        self.screen.blit(self.sprite_frame, (0, 0))


def main():
    pygame.init()
    screen = pygame.display.set_mode(G_RESOLUTION)
    clock = pygame.time.Clock()
    pygame.display.set_caption("Dungeon Cross")
    game = Board(screen)
    game_run = True

    while game_run:

        # clear screen
        screen.fill(pygame.color.Color(0, 0, 0))

        # handle quit events
        events = pygame.event.get()
        game.handle_mouse()
        for event in events:
            if event.type == pygame.QUIT:
                game_run = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game_run = False
        
        # update game
        game.draw_debug_board()
        #game.update()

        # update screen
        pygame.display.update()
        clock.tick(TARGET_FPS)

if __name__ == '__main__':
    main()
