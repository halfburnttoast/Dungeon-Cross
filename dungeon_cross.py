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
import logging
import log_system
from enum import Enum

# local includes
import sound_handler
from map_object_enum import MapObject
from resource_path import resource_path

VERSION = "v0.15.1"
TILE_SIZE = 90
G_RESOLUTION = (TILE_SIZE * 9, TILE_SIZE * 9)
TARGET_FPS = 30

class MouseAction(Enum):
    """Mouse action ENUM"""
    NONE        = 0
    PLACE_WALL  = 1
    PLACE_MARK  = 2
    REMOVE_WALL = 3
    REMOVE_MARK = 4
    MARK        = 5
    MENU_ACTION = 6

class DungeonCross:
    def __init__(self, screen, sound):

        # I/O Objects
        self._screen: pygame.Surface = screen
        self._sound: sound_handler.SoundHandler = sound

        # Game variables
        self.board_layout = []
        self.puzzle_book  = []
        self.placed_walls = []
        self.hint_x = [0] * 8
        self.hint_y = [0] * 8
        self.x_err  = []
        self.y_err  = []
        self.x_lim  = []
        self.y_lim  = []
        self.game_won = False
        self.last_puzzle_id = -1
        self._mouse_action: MouseAction = MouseAction.NONE.value
        self._check_board_state = False

        # UI variables
        self._font_offset = 32
        self._font_pos_offset = self._font_offset / 2
        self._menu_open = False

        # error overlay
        self._err_overlay = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self._err_overlay.fill((255, 0, 0))
        self._err_overlay.set_alpha(120)

        # limit overlay
        self._limit_overlay = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self._limit_overlay.fill((0, 0, 0))
        self._limit_overlay.set_alpha(120)

        # load sprites
        self._sprite_wall  = self._load_sprite('sprite/wall3.png')
        self._sprite_floor = self._load_sprite('sprite/floor4.png')
        self._sprite_enemy = self._load_sprite('sprite/enemy.png')
        self._sprite_chest = self._load_sprite('sprite/chest.png')
        self._sprite_frame = self._load_sprite('sprite/frame3.png')
        self._sprite_mark  = self._load_sprite('sprite/mark4.png')
        self._sprite_book  = self._load_sprite('sprite/book.png')
        self._sprite_win   = self._load_sprite('sprite/win.png', G_RESOLUTION[0], G_RESOLUTION[1])
        self._sprite_number = []
        for i in range(0, 9):
            self._sprite_number.append(self._load_sprite(f"sprite/{i}.png", TILE_SIZE - self._font_offset, TILE_SIZE - self._font_offset))
        pygame.display.set_icon(self._sprite_book)

        # sound effects
        self._sound_win = self._sound.load_sfx('audio/sfx/level_win.mp3')
        self._sound_wall = self._sound.load_sfx('audio/sfx/place_wall.mp3')
        self._sound_mark = self._sound.load_sfx('audio/sfx/place_mark.mp3')
        self._sound_open = self._sound.load_sfx('audio/sfx/level_open.mp3')


    def load_puzzle_book(self, file_name: str = "puzzles.json"):
        """Loads a JSON file containing the puzzle data. Puzzles are stored as a list of lists."""
        logging.info(f"Opening puzzle book: {file_name}.")
        try:
            with open(resource_path(file_name), 'r') as f:
                self.puzzle_book = json.load(f)
                f.close()
            logging.info(f"{len(self.puzzle_book)} puzzles loaded.")
        except FileNotFoundError:
            logging.warn(f"Couldn't open file: {file_name}")
            raise
        except json.JSONDecodeError:
            logging.warn(f"Error reading file: {file_name}")
            raise
    
    def open_puzzle(self, num: int = 0):
        """Opens a puzzle by ID."""
        logging.info(f"Opening puzzle #{num:05d}.")
        self.hint_x = [0] * 8
        self.hint_y = [0] * 8
        self.x_err  = []
        self.y_err  = []
        self.board_layout = self.puzzle_book[num]
        self._calc_hints()
        self.placed_walls = self._strip_walls()
        self._check_board_state = False
        self.game_won = False
        self.last_puzzle_id = num
        pygame.display.set_caption(f"Dungeon Cross - {VERSION} - PID #{num:05d}")
        self._sound.play_sfx(self._sound_open)
        self._check_for_errors()
    
    def open_random_puzzle(self):
        """Opens a random puzzle. Will not select the same puzzle twice in a row."""
        pid = random.choice(range(0, len(self.puzzle_book)))
        if pid == self.last_puzzle_id:
            pid = (pid + 1) % len(self.puzzle_book)
        self.open_puzzle(pid)

    def _draw_game(self):
        self._draw_frame()
        for y in range(1, 9):
            for x in range(1, 9):
                self._screen.blit(self._sprite_floor, (x * TILE_SIZE, y * TILE_SIZE))
        self._draw_map_tiles(show_wall=False)
        self._draw_placed_objects()
        self._draw_errors()
        self._draw_limit()
        if self.game_won:
            self._screen.blit(self._sprite_win, (0, 0))

    def update(self):
        if not self._menu_open:
            self._game_handle_mouse()
            self._draw_game()
        else:
            self._menu_handle_events()
            #self._draw_menu()

    def handle_io_event(self, event: pygame.event.Event) -> bool:
        """Returns false if ESCAPE key was pressed"""
        if not self._menu_open:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if not self._menu_open:
                    if event.key == pygame.K_SPACE:
                        self.open_random_puzzle()
                    elif event.key == pygame.K_r:
                        self.open_puzzle(self.get_puzzle_id())
                    elif event.key == pygame.K_m:
                        self._sound.stop_music()
                        self._sound.muted = True      
            elif event.type == pygame.MOUSEBUTTONDOWN:
                lm = event.button == 1
                rm = event.button == 3
                self._game_handle_mouse(lm_event=lm, rm_event=rm)
        else:
            # handle menu
            pass
        
        return True

    def _menu_handle_events(self):
        pass

    def _game_handle_mouse(self, lm_event: bool = False, rm_event: bool = False):
        """
        Handles all mouse input/actions. If a user-placed wall is changed, it will automatically
        call the routines to check for a win condition or if an error is made. 
        """

        mx, my      = self._get_mouse_to_grid()
        user_tile   = self.placed_walls[my][mx]
        map_tile    = self.board_layout[my][mx]
        mouse_press = pygame.mouse.get_pressed()
        click_lmb   = mouse_press[0] or lm_event
        click_rmb   = mouse_press[2] or rm_event

        # reset mouse action if no buttons are being pressed
        if not True in [click_lmb, click_rmb] and self._mouse_action != MouseAction.NONE.value:
            self._mouse_action = MouseAction.NONE.value

        # update mouse action if not already set
        if mx >= 0 and my >= 0:
            if not self.game_won:
                if self._mouse_action == MouseAction.NONE.value:
                    if click_lmb:
                        if user_tile:
                            self._mouse_action = MouseAction.REMOVE_WALL.value
                        else:
                            self._mouse_action = MouseAction.PLACE_WALL.value
                    elif click_rmb:
                        if user_tile:
                            self._mouse_action = MouseAction.REMOVE_MARK.value
                        else:
                            self._mouse_action = MouseAction.PLACE_MARK.value                 

                # update user tiles based on mouse location and action
                if self._mouse_action:
                    if map_tile in [MapObject.EMPTY.value, MapObject.WALL.value]:
                        if self._mouse_action == MouseAction.PLACE_WALL.value:
                            if user_tile == MapObject.EMPTY.value:
                                self.placed_walls[my][mx] = MapObject.WALL.value
                                self._check_board_state = True
                                self._sound.play_sfx(self._sound_wall)
                        elif self._mouse_action == MouseAction.REMOVE_WALL.value:
                            if user_tile == MapObject.WALL.value:
                                self.placed_walls[my][mx] = MapObject.EMPTY.value
                                self._check_board_state = True
                                self._sound.play_sfx(self._sound_wall)
                        elif self._mouse_action == MouseAction.PLACE_MARK.value:
                            if user_tile == MapObject.EMPTY.value:
                                self.placed_walls[my][mx] = MapObject.MARK.value
                                self._sound.play_sfx(self._sound_mark)
                        elif self._mouse_action == MouseAction.REMOVE_MARK.value:
                            if user_tile == MapObject.MARK.value:
                                self.placed_walls[my][mx] = MapObject.EMPTY.value                   
                                self._sound.play_sfx(self._sound_mark) 

            # if a user wall has changed, check for errors/win condition
            if self._check_board_state:
                self._check_for_errors()
                self._check_win()
                self._check_board_state = False
        elif mx == -1 and my == -1:      # if user has clicked on book icon
            if click_lmb and not self._mouse_action:
                self._mouse_action = MouseAction.MENU_ACTION.value
                #self._menu_open = True
                print("MENU OPEN")

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
            self._sound.play_sfx(self._sound_win)
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
            self._screen.blit(self._err_overlay, ((i + 1) * TILE_SIZE, 0))
        for i in self.y_err:
            self._screen.blit(self._err_overlay, (0, (i + 1) * TILE_SIZE))

    def _draw_limit(self):
        """Draws a red overlay over the hint numbers based on the values in x_err and y_err"""
        for i in self.x_lim:
            self._screen.blit(self._limit_overlay, ((i + 1) * TILE_SIZE, 0))
        for i in self.y_lim:
            self._screen.blit(self._limit_overlay, (0, (i + 1) * TILE_SIZE))

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
        self._screen.blit(sprite, (pos_x, pos_y))

    def _draw_placed_objects(self):
        for y, row in enumerate(self.placed_walls):
            for x, obj in enumerate(row):
                if obj == MapObject.WALL.value:
                    self._draw_sprite(self._sprite_wall, (x, y))
                elif obj == MapObject.MARK.value:
                    self._draw_sprite(self._sprite_mark, (x, y))

    def _draw_map_tiles(self, show_wall: bool = False):
        for y, row in enumerate(self.board_layout):
            for x, obj in enumerate(row):
                if show_wall and obj == MapObject.WALL.value:
                    self._draw_sprite(self._sprite_wall, (x, y))
                elif obj == MapObject.ENEMY.value:
                    self._draw_sprite(self._sprite_enemy, (x, y))
                elif obj == MapObject.CHEST.value:
                    self._draw_sprite(self._sprite_chest, (x, y))

    def _load_sprite(self, path: str, size_x: int = TILE_SIZE, size_y: int = TILE_SIZE) -> pygame.image:
        logging.debug(f"Loading sprite: {path}. Size ({size_x}, {size_y}")
        try:
            image = pygame.image.load(resource_path(path))
            return pygame.transform.scale(image, (size_x, size_x))
        except FileNotFoundError:
            logging.critical(f"Could not open sprite: {path}")
            raise

    def _get_mouse_to_grid(self) -> tuple:
        pos_x, pos_y = pygame.mouse.get_pos()
        pos_x = math.floor((pos_x / TILE_SIZE) - 1)
        pos_y = math.floor((pos_y / TILE_SIZE) - 1)
        pos_x = max(min(8, pos_x), -1)
        pos_y = max(min(8, pos_y), -1)
        return(pos_x, pos_y)

    def _draw_frame(self):
        for i in range(1, 9):
            hint_x = self._sprite_number[self.hint_x[i - 1]]
            hint_y = self._sprite_number[self.hint_y[i - 1]]
            self._screen.blit(self._sprite_frame, (i * TILE_SIZE, 0))
            self._screen.blit(self._sprite_frame, (0, i * TILE_SIZE))
            self._screen.blit(hint_x, (i * TILE_SIZE + self._font_pos_offset, self._font_pos_offset))
            self._screen.blit(hint_y, (self._font_pos_offset, i * TILE_SIZE + self._font_pos_offset))
        self._screen.blit(self._sprite_frame, (0, 0))
        self._screen.blit(self._sprite_book, (0, 0))


def show_splash(screen: pygame.Surface):
    """Shows splash/loading screen"""
    image = pygame.image.load(resource_path('sprite/splash.png'))
    sxm = round(image.get_width() / 2)
    sym = round(image.get_height() / 2)
    pos_x = (G_RESOLUTION[0] / 2) - sxm
    pos_y = (G_RESOLUTION[1] / 2) - sym
    screen.fill(pygame.color.Color(100, 70, 0))
    screen.blit(image, (pos_x, pos_y))
    pygame.display.update()


def main():

    # setup logging
    lfmt = "%(levelname)s [%(funcName)s]: %(message)s"
    log_file_name = 'dungeon_cross.log'
    try:
        # When compiled as .app file on Mac, sandboxing will have the logical working directory '/'
        # meaning creating logfiles in the same directory will fail. We'll need to redirect the 
        # log output to the standard logfile location for user apps.
        if sys.platform == 'darwin':
            log_dir = os.path.expanduser('~/Library/Logs/')
            log_path = log_dir + log_file_name
            logging.basicConfig(filename=log_path, level=logging.INFO, filemode='w', format=lfmt)
        else:
            logging.basicConfig(filename=log_file_name, level=logging.INFO, filemode='w', format=lfmt)
    except OSError as e:
        logging.basicConfig(level=logging.INFO, format=lfmt)
        logging.error(e)
    logging.info("PROGRAM START")
    log_system.log_sys_info()
    sys.excepthook = log_system.exception_handler_hook

    # init pygame
    pygame.init()

    # create music handler object, load music, and start playback
    sound = sound_handler.SoundHandler(resource_path('audio/music/'))
    sound.load_music_all()
    sound.shuffle()
    sound.set_volume(35)
    sound.play_music_all()

    # create display window
    screen = pygame.display.set_mode(G_RESOLUTION)
    show_splash(screen)

    # internal timer for FPS regulation
    clock = pygame.time.Clock()

    # create game and load levels
    game = DungeonCross(screen, sound)
    game.load_puzzle_book()
    game_run = True

    # main loop
    logging.info("GAME START")
    while game_run:
        game.open_random_puzzle()
        #game.open_puzzle(10)

        while game_run and not game.game_won:

            # clear screen
            screen.fill(pygame.color.Color(0, 0, 0))

            # handle quit events
            events = pygame.event.get()
            # game.handle_mouse()
            for event in events:
                if event.type == pygame.QUIT:
                    game_run = False
                else:
                    game_run = game.handle_io_event(event)

            # draw game assets
            game.update()

            # update screen
            pygame.display.update()
            clock.tick(TARGET_FPS)
        if game.game_won:
            time.sleep(2)

if __name__ == '__main__':
    main()
