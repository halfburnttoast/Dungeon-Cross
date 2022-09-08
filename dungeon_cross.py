#!/usr/bin/python3

#       Dungeon Cross
#  Written by HalfBurntToast
#  https://github.com/halfburnttoast/Dungeon-Cross
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.

import os
import sys
import math
import json
import time
import pygame
import random
from enum import Enum

# local includes
import music_handler
from map_object_enum import MapObject

VERSION = "v0.14.1"

TILE_SIZE = 90
G_RESOLUTION = (TILE_SIZE * 9, TILE_SIZE * 9)
TARGET_FPS = 30

def resource_path(relative_path):
    """Used for looking up assets inside of compiled binaries."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class MouseAction(Enum):
    NONE        = 0
    PLACE_WALL  = 1
    PLACE_MARK  = 2
    REMOVE_WALL = 3
    REMOVE_MARK = 4
    MARK        = 5
    MENU_ACTION = 6

class Board:
    def __init__(self, screen):
        self.board_layout = []
        self.puzzle_book = []
        self.placed_walls = []
        self.hint_x = [0] * 8
        self.hint_y = [0] * 8
        self.x_err  = []
        self.y_err  = []
        self.x_lim  = []
        self.y_lim  = []
        self.mouse_action = MouseAction.NONE.value
        self.screen = screen
        self.check_board_state = False
        self.game_won = False
        self.last_puzzle_id = -1
        self.font_offset = 32
        self.font_pos_offset = self.font_offset / 2

        # error overlay
        self._err_overlay = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self._err_overlay.fill((255, 0, 0))
        self._err_overlay.set_alpha(120)

        # limit overlay
        self._limit_overlay = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self._limit_overlay.fill((0, 0, 0))
        self._limit_overlay.set_alpha(120)

        # load sprites
        self.sprite_wall  = self._load_sprite(resource_path('sprite/wall3.png'))
        self.sprite_floor = self._load_sprite(resource_path('sprite/floor4.png'))
        self.sprite_enemy = self._load_sprite(resource_path('sprite/enemy.png'))
        self.sprite_chest = self._load_sprite(resource_path('sprite/chest.png'))
        self.sprite_frame = self._load_sprite(resource_path('sprite/frame3.png'))
        self.sprite_mark  = self._load_sprite(resource_path('sprite/mark4.png'))
        self.sprite_book  = self._load_sprite(resource_path('sprite/book.png'))
        self.sprite_win   = self._load_sprite(resource_path('sprite/win.png'), G_RESOLUTION[0], G_RESOLUTION[1])
        self.sprite_number = []
        for i in range(0, 9):
            self.sprite_number.append(self._load_sprite(resource_path(f'sprite/{i}.png'), 
                                                        TILE_SIZE - self.font_offset, 
                                                        TILE_SIZE - self.font_offset)
                                    )
        pygame.display.set_icon(self.sprite_book)

        # sound effects
        self.sound_win = pygame.mixer.Sound(resource_path('audio/sfx/level_win.mp3'))
        self.sound_wall = pygame.mixer.Sound(resource_path('audio/sfx/place_wall.mp3'))
        self.sound_mark = pygame.mixer.Sound(resource_path('audio/sfx/place_mark.mp3'))
        self.sound_open = pygame.mixer.Sound(resource_path('audio/sfx/level_open.mp3'))
        self.sound_win.set_volume(0.6)
        self.sound_wall.set_volume(0.6)
        self.sound_mark.set_volume(0.6)
        self.sound_open.set_volume(0.6)


    def load_puzzle_book(self, file_name: str = "puzzles.json"):
        """Loads a JSON file containing the puzzle data. Puzzles are stored as a list of lists."""
        try:
            with open(resource_path(file_name), 'r') as f:
                self.puzzle_book = json.load(f)
                f.close()
            print(f"{len(self.puzzle_book)} puzzles loaded.")
        except FileNotFoundError:
            print(f"Couldn't open file: {file_name}")
            sys.exit(1)
    
    def open_puzzle(self, num: int = 0):
        """Opens a puzzle by ID."""
        print(f"Opening puzzle #{num:05d}.")
        self.hint_x = [0] * 8
        self.hint_y = [0] * 8
        self.x_err  = []
        self.y_err  = []
        self.board_layout = self.puzzle_book[num]
        self._calc_hints()
        self.placed_walls = self._strip_walls()
        self.check_board_state = False
        self.game_won = False
        self.last_puzzle_id = num
        pygame.display.set_caption(f"Dungeon Cross - {VERSION} - PID #{num:05d}")
        self.sound_open.play()
        self._check_for_errors()
    
    def open_random_puzzle(self):
        """Opens a random puzzle. Will not select the same puzzle twice in a row."""
        pid = random.choice(range(0, len(self.puzzle_book)))
        if pid == self.last_puzzle_id:
            pid = (pid + 1) % len(self.puzzle_book)
        self.open_puzzle(pid)

    def draw_all(self):
        self._draw_frame()
        for y in range(1, 9):
            for x in range(1, 9):
                self.screen.blit(self.sprite_floor, (x * TILE_SIZE, y * TILE_SIZE))
        self._draw_map_tiles(show_wall=False)
        self._draw_placed_objects()
        self._draw_errors()
        self._draw_limit()
        if self.game_won:
            self.screen.blit(self.sprite_win, (0, 0))
    
    def handle_mouse(self):
        """
        Handles all mouse input/actions. If a user-placed wall is changed, it will automatically
        call the routines to check for a win condition or if an error is made. 
        """

        mx, my      = self._get_mouse_to_grid()
        user_tile   = self.placed_walls[my][mx]
        map_tile    = self.board_layout[my][mx]
        mouse_press = pygame.mouse.get_pressed()
        click_lmb   = mouse_press[0]
        click_rmb   = mouse_press[2]

        # reset mouse action if no buttons are being pressed
        if not True in [click_lmb, click_rmb] and self.mouse_action != MouseAction.NONE.value:
            self.mouse_action = MouseAction.NONE.value

        # update mouse action if not already set
        if mx >= 0 and my >= 0:
            if not self.game_won:
                if self.mouse_action == MouseAction.NONE.value:
                    if click_lmb:
                        if user_tile:
                            self.mouse_action = MouseAction.REMOVE_WALL.value
                        else:
                            self.mouse_action = MouseAction.PLACE_WALL.value
                    elif click_rmb:
                        if user_tile:
                            self.mouse_action = MouseAction.REMOVE_MARK.value
                        else:
                            self.mouse_action = MouseAction.PLACE_MARK.value                 

                # update user tiles based on mouse location and action
                if self.mouse_action:
                    if map_tile in [MapObject.EMPTY.value, MapObject.WALL.value]:
                        if self.mouse_action == MouseAction.PLACE_WALL.value:
                            if user_tile == MapObject.EMPTY.value:
                                self.placed_walls[my][mx] = MapObject.WALL.value
                                self.check_board_state = True
                                self.sound_wall.play()
                        elif self.mouse_action == MouseAction.REMOVE_WALL.value:
                            if user_tile == MapObject.WALL.value:
                                self.placed_walls[my][mx] = MapObject.EMPTY.value
                                self.check_board_state = True
                                self.sound_wall.play()
                        elif self.mouse_action == MouseAction.PLACE_MARK.value:
                            if user_tile == MapObject.EMPTY.value:
                                self.placed_walls[my][mx] = MapObject.MARK.value
                                self.sound_mark.play()   
                        elif self.mouse_action == MouseAction.REMOVE_MARK.value:
                            if user_tile == MapObject.MARK.value:
                                self.placed_walls[my][mx] = MapObject.EMPTY.value                   
                                self.sound_mark.play()  

            # if a user wall has changed, check for errors/win condition
            if self.check_board_state:
                self._check_for_errors()
                self._check_win()
                self.check_board_state = False
        elif mx == -1 and my == -1:      # if user has clicked on book icon
            if click_lmb and not self.mouse_action:
                self.mouse_action = MouseAction.MENU_ACTION.value
                print("TEST")

    def get_number_of_puzzles(self):
        """Returns total number of puzzles loaded."""
        return len(self.puzzle_book)
    
    def get_puzzle_id(self) -> int:
        """Returns the ID of the currently open puzzle."""
        return self.last_puzzle_id
    
    def _check_win(self):
        """Checks to see if the user-modified board matches the puzzle book board."""
        user_board = self._strip_marks()
        if self.board_layout == user_board:
            self.sound_win.play()
            self.game_won = True
    
    def _check_for_errors(self):
        """
        Generates the sum of user-placed walls by row and column. Checks to see 
        if any of those user values exceed the generated hints from the puzzle.
        Updates the error arrays x_err and y_err with the indexes of the errors.
        """

        x_sum = []
        y_sum = []

        # calculate sums of placed walls row/columns
        for i, v in enumerate(self.placed_walls):
            y_sum.append(v.count(MapObject.WALL.value))
        for x in range(8):
            sum = 0
            for y in range(8):
                if self.placed_walls[y][x] == MapObject.WALL.value:
                    sum = sum + 1
            x_sum.append(sum)
        
        # get indexes of errors when compared to the hint frame
        self.x_err = [i for i, v in enumerate(x_sum) if v > self.hint_x[i]]
        self.y_err = [i for i, v in enumerate(y_sum) if v > self.hint_y[i]]

        # get indexes of limits against hint frame
        self.x_lim = [i for i, v in enumerate(x_sum) if v == self.hint_x[i]]
        self.y_lim = [i for i, v in enumerate(y_sum) if v == self.hint_y[i]]

    def _draw_errors(self):
        """Draws a red overlay over the hint numbers based on the values in x_err and y_err"""
        for i in self.x_err:
            self.screen.blit(self._err_overlay, ((i + 1) * TILE_SIZE, 0))
        for i in self.y_err:
            self.screen.blit(self._err_overlay, (0, (i + 1) * TILE_SIZE))

    def _draw_limit(self):
        """Draws a red overlay over the hint numbers based on the values in x_err and y_err"""
        for i in self.x_lim:
            self.screen.blit(self._limit_overlay, ((i + 1) * TILE_SIZE, 0))
        for i in self.y_lim:
            self.screen.blit(self._limit_overlay, (0, (i + 1) * TILE_SIZE))

    def _strip_walls(self) -> list:
        """Removes walls from loaded puzzle. Used to generate the 'user board'."""
        out = []
        for row in self.board_layout:
            out.append([v if v != MapObject.WALL.value else MapObject.EMPTY.value for v in row])
        return out

    def _strip_marks(self) -> list:
        """Removes all user-placed marks. Used by _check_win"""
        out = []
        for row in self.placed_walls:
            out.append([v if v != MapObject.MARK.value else MapObject.EMPTY.value for v in row])
        return out        

    def _calc_hints(self):
        for i, v in enumerate(self.board_layout):
            self.hint_y[i] = v.count(MapObject.WALL.value)
        for x in range(8):
            sum_y = 0
            for y in range(8):
                if self.board_layout[y][x] == MapObject.WALL.value:
                    sum_y = sum_y + 1
            self.hint_x[x] = sum_y

    def _draw_sprite(self, sprite: pygame.image, grid_pos: tuple):
        pos_x = (grid_pos[0] + 1) * TILE_SIZE
        pos_y = (grid_pos[1] + 1) * TILE_SIZE
        self.screen.blit(sprite, (pos_x, pos_y))

    def _draw_placed_objects(self):
        for y, row in enumerate(self.placed_walls):
            for x, obj in enumerate(row):
                if obj == MapObject.WALL.value:
                    self._draw_sprite(self.sprite_wall, (x, y))
                elif obj == MapObject.MARK.value:
                    self._draw_sprite(self.sprite_mark, (x, y))

    def _draw_map_tiles(self, show_wall: bool = False):
        for y, row in enumerate(self.board_layout):
            for x, obj in enumerate(row):
                if show_wall and obj == MapObject.WALL.value:
                    self._draw_sprite(self.sprite_wall, (x, y))
                elif obj == MapObject.ENEMY.value:
                    self._draw_sprite(self.sprite_enemy, (x, y))
                elif obj == MapObject.CHEST.value:
                    self._draw_sprite(self.sprite_chest, (x, y))

    def _load_sprite(self, path: str, size_x: int = TILE_SIZE, size_y: int = TILE_SIZE) -> pygame.image:
        image = pygame.image.load(resource_path(path))
        return pygame.transform.scale(image, (size_x, size_x))

    def _get_mouse_to_grid(self) -> tuple:
        pos_x, pos_y = pygame.mouse.get_pos()
        pos_x = math.floor((pos_x / TILE_SIZE) - 1)
        pos_y = math.floor((pos_y / TILE_SIZE) - 1)
        pos_x = max(min(8, pos_x), -1)
        pos_y = max(min(8, pos_y), -1)
        return(pos_x, pos_y)

    def _draw_frame(self):
        for i in range(1, 9):
            hint_x = self.sprite_number[self.hint_x[i - 1]]
            hint_y = self.sprite_number[self.hint_y[i - 1]]
            self.screen.blit(self.sprite_frame, (i * TILE_SIZE, 0))
            self.screen.blit(self.sprite_frame, (0, i * TILE_SIZE))
            self.screen.blit(hint_x, (i * TILE_SIZE + self.font_pos_offset, self.font_pos_offset))
            self.screen.blit(hint_y, (self.font_pos_offset, i * TILE_SIZE + self.font_pos_offset))
        self.screen.blit(self.sprite_frame, (0, 0))
        self.screen.blit(self.sprite_book, (0, 0))


def main():
    pygame.init()
    music = music_handler.MusicHandler(resource_path('audio/music/'))
    music.load_music_all()
    music.shuffle()
    music.set_volume(35)
    music.play_music_all()
    screen = pygame.display.set_mode(G_RESOLUTION)
    clock = pygame.time.Clock()
    game = Board(screen)
    game.load_puzzle_book()
    game_run = True

    while game_run:
        game.open_random_puzzle()
        #game.open_puzzle(10)

        while game_run and not game.game_won:

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
                    elif event.key == pygame.K_SPACE:
                        game.open_random_puzzle()
                    elif event.key == pygame.K_r:
                        game.open_puzzle(game.get_puzzle_id())
                    elif event.key == pygame.K_m:
                        music.stop_music()
            
            # draw game assets
            game.draw_all()

            # update screen
            pygame.display.update()
            clock.tick(TARGET_FPS)
        if game.game_won:
            time.sleep(2)

if __name__ == '__main__':
    main()
