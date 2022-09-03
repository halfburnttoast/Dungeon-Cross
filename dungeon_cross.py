import enum
from http.client import NON_AUTHORITATIVE_INFORMATION
import os
from re import T
import sys
import math
from tkinter.messagebox import NO
import pygame
from enum import Enum

TILE_SIZE = 80
G_RESOLUTION = (TILE_SIZE * 9, TILE_SIZE * 9)
TARGET_FPS = 30

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

class Board:
    def __init__(self, screen):
        self.board_layout = (
            (0, 0, 0, 0, 0, 1, 1, 1),
            (0, 1, 0, 1, 0, 0, 0, 2),
            (0, 1, 2, 1, 0, 1, 1, 1),
            (0, 1, 1, 1, 0, 0, 0, 2),
            (0, 0, 0, 1, 0, 1, 1, 1),
            (0, 3, 0, 1, 0, 0, 0, 2),
            (0, 0, 0, 1, 0, 1, 1, 1),
            (1, 1, 1, 1, 0, 0, 0, 2),
        )
        self.hint_x = [0] * 8
        self.hint_y = [0] * 8
        self.mouse_action = MouseAction.NONE
        self.placed_walls = [[0] * 8 for _ in range(8)]
        self.screen = screen
        self.sprite_wall  = self._load_sprite(resource_path('sprite/wall.png'))
        self.sprite_floor = self._load_sprite(resource_path('sprite/floor.png'))
        self.sprite_enemy = self._load_sprite(resource_path('sprite/enemy.png'))
        self.sprite_chest = self._load_sprite(resource_path('sprite/chest.png'))
        self.sprite_frame = self._load_sprite(resource_path('sprite/frame.png'))
        self.sprite_number = []
        for i in range(0, 9):
            self.sprite_number.append(self._load_sprite(resource_path(f'sprite/{i}.png')))
        self._calc_hints()

    def draw_debug_board(self):
        self._draw_frame()
        for y in range(1, 9):
            for x in range(1, 9):
                self.screen.blit(self.sprite_floor, (x * TILE_SIZE, y * TILE_SIZE))
        self._draw_map_objects(True)
        self._draw_placed_walls()
    
    def handle_mouse(self):
        mx, my = self._get_mouse_to_grid()
        cell_state = self.placed_walls[my][mx]
        map_obj    = self.board_layout[my][mx]
        mouse_press = pygame.mouse.get_pressed()
        if not mouse_press[0] and self.mouse_action != MouseAction.NONE:
            self.mouse_action = MouseAction.NONE
        if mouse_press[0]:
            if self.mouse_action == MouseAction.NONE:
                if cell_state:
                    self.mouse_action = MouseAction.REMOVE
                else:
                    self.mouse_action = MouseAction.PLACE
            if self.mouse_action == MouseAction.PLACE:
                if map_obj == 0 or map_obj == 1:
                    self.placed_walls[my][mx] = 1
            elif self.mouse_action == MouseAction.REMOVE:
                if map_obj == 0 or map_obj == 1:
                    self.placed_walls[my][mx] = 0

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
                if obj:
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

    def _load_sprite(self, path: str) -> pygame.image:
        image = pygame.image.load(resource_path(path))
        return pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE))

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
