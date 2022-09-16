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

import math
import gzip
import json
import time
import pygame
import random
import logging
import hashlib
import pygame_menu
import pygame_menu.locals
import pygame_menu.events
from enum import Enum
from collections import namedtuple

# local includes
import log_system
import sound_handler
from map_object_enum import MapObject
from resource_path import resource_path
from save_game import SaveFile
from debug_timer import debug_timer

VERSION = "v1.0.0"
G_LOG_LEVEL = logging.DEBUG
TILE_SIZE = 90
G_RESOLUTION = (TILE_SIZE * 9, TILE_SIZE * 9)
TARGET_FPS = 60
THEME_COLOR = (100, 70, 0)

# Used to store a single user action for undo/redo functions
HistoryAction = namedtuple("HistoryAction", ['x', 'y', 'old_state', 'new_state'])

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
        self._save_file = SaveFile("dungeon_cross.sav")

        # Create Menus 
        self._menu_theme = self._menu_build_theme()
        self._menu_tutorial = self._menu_build_tutorial()
        self._menu_about = self._menu_build_about()
        self._menu = self._menu_build_main()
        self._menu_pid: int = 0
        self._menu_backdrop = pygame.Surface(self._screen.get_size())
        self._menu_backdrop.fill((50, 50, 50))
        self._menu_backdrop.set_alpha(150)

        # System settings
        self._power_save = False

        # Game variables
        self.game_won = False
        self.last_puzzle_id = -1
        self._action_history = []
        self._action_history_idx = 0
        self._action_history_idx_top = 0
        self._board_layout = []
        self._puzzle_book  = []
        self._placed_walls = []
        self._hint_x = [0] * 8
        self._hint_y = [0] * 8
        self._x_err  = []
        self._y_err  = []
        self._x_lim  = []
        self._y_lim  = []
        self._map_hash: str = ""
        self._mouse_action: MouseAction = MouseAction.NONE.value
        self._check_board_state = False
        self._player_wins = 0

        # UI variables
        self.needs_display_update = True
        self._font_offset = 32
        self._font_pos_offset = self._font_offset / 2
        self._menu_is_open = False
        self._cb_mode = False

        # error overlay
        self._err_overlay_og = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self._err_overlay_og.fill((255, 0, 0))
        self._err_overlay_og.set_alpha(120)

        # colorblind error overlay
        self._err_overlay_cb = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self._err_overlay_cb.fill((0, 100, 200))
        self._err_overlay_cb.set_alpha(180)
        _err_overlay_sprite = self._load_sprite('sprite/error.png')
        _err_overlay_sprite.set_alpha(120)
        self._err_overlay_cb.blit(_err_overlay_sprite, (0, 0))

        # set default error overlay to "normal" (not colorblind) mode
        self._err_overlay = self._err_overlay_og

        # limit overlay, used to show when a row/column has the needed number of walls
        self._limit_overlay = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self._limit_overlay.fill((0, 0, 0))
        self._limit_overlay.set_alpha(120)

        # load sprites for both normal and colorblind modes
        self._sprite_enemy_cb = self._load_sprite('sprite/cb_enemy.png')
        self._sprite_enemy_og = self._load_sprite('sprite/enemy.png')
        self._sprite_wall_cb  = self._load_sprite('sprite/cb_wall.png')
        self._sprite_wall_og  = self._load_sprite('sprite/wall3.png')
        self._sprite_mark_cb  = self._load_sprite('sprite/cb_mark.png')
        self._sprite_mark_og  = self._load_sprite('sprite/mark4.png')
        self._sprite_floor_og = self._load_sprite('sprite/floor4.png')
        self._sprite_floor_cb = self._load_sprite('sprite/cb_floor2.png')
        self._sprite_wall  = self._sprite_wall_og
        self._sprite_mark  = self._sprite_mark_og
        self._sprite_enemy = self._sprite_enemy_og
        self._sprite_floor = self._sprite_floor_og
        self._sprite_chest = self._load_sprite('sprite/chest.png')
        self._sprite_frame = self._load_sprite('sprite/frame3.png')
        self._sprite_book  = self._load_sprite('sprite/book.png')
        self._sprite_win   = self._load_sprite('sprite/win.png', G_RESOLUTION[0], G_RESOLUTION[1])
        self._sprite_number = []
        for i in range(0, 9):
            self._sprite_number.append(self._load_sprite(f"sprite/{i}.png", TILE_SIZE - self._font_offset, TILE_SIZE - self._font_offset))
        pygame.display.set_icon(self._sprite_book)

        # load sound effects
        self._sound_win = self._sound.load_sfx('audio/sfx/level_win.mp3')
        self._sound_wall = self._sound.load_sfx('audio/sfx/place_wall.mp3')
        self._sound_mark = self._sound.load_sfx('audio/sfx/place_mark.mp3')
        self._sound_open = self._sound.load_sfx('audio/sfx/level_open.mp3')

    def update(self):
        """Main game update function. Should be called in main loop once per frame."""
        if not self._menu_is_open:
            self._game_handle_mouse()
            if not self._power_save or self.needs_display_update:
                self._draw_game()
                self.needs_display_update = False
        else:
            self._menu.enable()
            self._menu.mainloop(self._screen, bgfun=self._draw_game)

    @debug_timer
    def load_puzzle_book(self, file_name: str = "puzzles.json.gz"):
        """Loads a gzipped JSON file containing the puzzle data. Puzzles are stored as a list of lists."""
        logging.info(f"Opening puzzle book: {file_name}.")
        try:
            with gzip.open(resource_path(file_name), 'r') as f:
                self._puzzle_book = json.load(f)
                f.close()
            logging.info(f"{len(self._puzzle_book)} puzzles loaded.")
        except FileNotFoundError:
            logging.warning(f"Couldn't open file: {file_name}")
            raise
        except json.JSONDecodeError:
            logging.warning(f"Error reading file: {file_name}")
            raise
    
    def open_puzzle(self, num: int = 0) -> None:
        """
        Opens a puzzle by ID. Whatever method you use to select a puzzle number
        by should end with calling this method. Invalid puzzle IDs will default
        to puzzle #0.
        """

        logging.info(f"Opening puzzle #{num:05d}.")

        # reset board data
        self._hint_x = [0] * 8
        self._hint_y = [0] * 8
        self._x_err  = []
        self._y_err  = []

        # reset user history
        self._action_history = []
        self._action_history_idx = 0
        self._action_history_idx_top = 0

        # if we attempt to load an invalid puzzle, default to puzzle 0
        if num not in range(0, self.get_number_of_puzzles() + 1):
            logging.error(f"Attempted to load invalid puzzle ID {num}")
            num = 0

        # load and setup game board
        self.game_won = False
        self.last_puzzle_id = num
        self._board_layout = self._puzzle_book[num]
        self._calc_hints()
        self._placed_walls = self._strip_walls()
        self._check_board_state = False
        self._sound.play_sfx(self._sound_open)
        self._check_for_errors()
        self._map_hash = hashlib.sha256(repr(self._board_layout).encode()).hexdigest()
        self._menu.get_widget("PUZZLE_ID").set_value(f"{num:05d}")
        self._menu_pid = num
        logging.debug(f"Map hash: {self._map_hash}")
        pygame.display.set_caption(f"Dungeon Cross - {VERSION} - Puzzle #{num:05d} - Wins: {self._player_wins}")
        self.needs_display_update = True
    
    def open_random_puzzle(self):
        """Opens a random puzzle. Will not select the same puzzle twice in a row."""
        pid = random.choice(range(0, len(self._puzzle_book)))
        if pid == self.last_puzzle_id:
            pid = (pid + 1) % len(self._puzzle_book)
        self.open_puzzle(pid)

    def handle_io_event(self, event: pygame.event.Event) -> bool:
        """Pass pygame events to this function. Returns false if ESCAPE key was pressed."""
        if not self._menu_is_open:
            if event.type == pygame.KEYDOWN:
                self.needs_display_update = True
                mods = pygame.key.get_mods()
                shift_pressed = bool(mods & 0x1)
                ctrl_pressed  = bool(mods & 0x40)
                if event.key == pygame.K_ESCAPE:
                    return False
                if not self._menu_is_open:
                    if event.key == pygame.K_SPACE:
                        self.open_random_puzzle()
                    elif event.key == pygame.K_r:
                        self.open_puzzle(self.get_puzzle_id()) 
                    elif event.key == pygame.K_z:
                        if ctrl_pressed:
                            if not shift_pressed:
                                self._undo_action()
                                self._check_for_errors()
                            else:
                                self._redo_action()
                                self._check_for_errors()
                    elif event.key == pygame.K_y and ctrl_pressed:
                        self._redo_action()
                        self._check_for_errors()                        
            elif event.type == pygame.MOUSEBUTTONDOWN:
                lm = event.button == 1
                rm = event.button == 3
                self._game_handle_mouse(lm_event=lm, rm_event=rm)
        return True

    def get_number_of_puzzles(self):
        """Returns total number of puzzles loaded."""
        return len(self._puzzle_book)
    
    def get_puzzle_id(self) -> int:
        """Returns the ID of the currently open puzzle."""
        return self.last_puzzle_id
        
    ### Save game methods
    def load_save(self):
        try:
            data = self._save_file.get_save_data()
            self._player_wins = data["WINS"]

            # if version matches, load settings
            if data["VERSION"] == VERSION:

                # sound settings
                self._sound.enabled = data["SOUND"]
                if not self._sound.enabled:
                    self._sound.stop_music()
                    self._sound.enabled = False
                    self._menu.get_widget("SOUND").set_value(False)

                # colorblind mode settings
                self._cb_mode = data["CB_MODE"]
                if self._cb_mode:
                    w = self._menu.get_widget("CB_MODE")
                    w.set_value(True)
                    w._onchange(True)
                
                # power save settings
                self._power_save = data["PW_SAVE"]
                if self._power_save:
                    w = self._menu.get_widget("PW_SAVE")
                    w.set_value(True)
                    w._onchange(True)

                # open the last puzzle and reload user progress
                self.open_puzzle(data["LEVEL"])
                if data["MAPHASH"] == self._map_hash:
                    self._placed_walls = data["PROGRESS"]
                    self._check_for_errors()
                else:
                    logging.warning("Map hash invalid for puzzle ID.")
                    self.open_random_puzzle()
            else:
                self.open_random_puzzle()
        except Exception as e:
            logging.error(f"Exception opening/reading save file {self._save_file.get_save_path()}\n{e}")
            self.open_random_puzzle()
    
    def save_game(self):
        try:
            save_data = {}
            save_data['VERSION'] = VERSION
            save_data['WINS'] = self._player_wins
            save_data['SOUND'] = self._sound.enabled
            save_data['CB_MODE'] = self._cb_mode
            save_data['PW_SAVE'] = self._power_save
            save_data["LEVEL"] = self.get_puzzle_id()
            save_data["PROGRESS"] = self._placed_walls
            save_data["MAPHASH"] = self._map_hash
            self._save_file.store_save_data(save_data)
        except Exception as e:  # temporary catchall
            logging.error(f"Could not save to save file. \n{e}")


    ### Menu callback methods. These are called directly by the pygame_menu widgets.
    # I'd want to move these out of this file
    def _menu_open_map(self, val = None):
        self.open_puzzle(self._menu_pid)
        self._menu_close()
    def _menu_random_map(self):
        self.open_random_puzzle()
        self._menu_close()
    def _menu_reset(self):
        self.open_puzzle(self.get_puzzle_id())
        self._menu_close()
    def _menu_update_pid(self, value):
        try:
            self._menu_pid = int(value)
        except:
            self._menu_pid = 0
    def _menu_close(self):
        self._menu_is_open = False
        self._menu.disable()
        self.needs_display_update = True
    def _menu_set_mute(self, val: bool) -> None:
        self._sound.enabled = val
        if not self._sound.enabled:
            self._sound.stop_music()
        else:
            self._sound.play_next_background_song()
    def _menu_quit(self):
        pygame.event.post(pygame.event.Event(pygame.QUIT))
        self._menu_is_open = False
        self._menu.disable()
    def _menu_power_save(self, val: bool) -> None:
        self._power_save = val
    def _menu_change_cb_mode(self, val: bool) -> None:
        try:
            if val:
                self._sprite_wall  = self._sprite_wall_cb
                self._sprite_mark  = self._sprite_mark_cb
                self._sprite_enemy = self._sprite_enemy_cb
                self._sprite_floor = self._sprite_floor_cb
                self._err_overlay = self._err_overlay_cb
                self._cb_mode = True
            else:
                self._sprite_wall  = self._sprite_wall_og
                self._sprite_mark  = self._sprite_mark_og
                self._sprite_enemy = self._sprite_enemy_og
                self._sprite_floor = self._sprite_floor_og
                self._err_overlay = self._err_overlay_og
                self._cb_mode = False
        except AttributeError as e:
            logging.debug(f"Error switching color modes: {e}")

    ### Internal game methods
    def _undo_action(self):
        """Undo a move from the user. Retains history for Redo function."""
        if self._action_history_idx > 0:
            self._action_history_idx -= 1
            action: HistoryAction = self._action_history[self._action_history_idx]
            self._placed_walls[action.y][action.x] = action.old_state

    def _redo_action(self):
        """Redo an action after an undo was made."""
        if self._action_history_idx < self._action_history_idx_top:
            action: HistoryAction = self._action_history[self._action_history_idx]
            self._action_history_idx += 1
            self._placed_walls[action.y][action.x] = action.new_state

    def _draw_game(self):
        """
        Redraws the entire game board. This should be called by the engine and not by
        the user. This function should only run when there has been a change to the 
        game board itself, or if the window has changed focus states.
        """
        
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
        if self._menu_is_open:
            self._screen.blit(self._menu_backdrop, (0, 0))

    def _game_handle_mouse(self, lm_event: bool = False, rm_event: bool = False):
        """
        Handles all mouse input/actions. If a user-placed wall is changed, it will automatically
        call the routines to check for a win condition or if an error is made.

        Modifies: 
            self._placed_walls
        """

        mx, my      = self._get_mouse_to_grid()
        user_tile   = self._placed_walls[my][mx]
        map_tile    = self._board_layout[my][mx]
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
                        update_history = False
                        old_state = self._placed_walls[my][mx]
                        if self._mouse_action == MouseAction.PLACE_WALL.value:
                            if user_tile == MapObject.EMPTY.value:
                                self._placed_walls[my][mx] = MapObject.WALL.value
                                self._check_board_state = True
                                self._sound.play_sfx(self._sound_wall)
                                update_history = True
                                self.needs_display_update = True
                        elif self._mouse_action == MouseAction.REMOVE_WALL.value:
                            if user_tile == MapObject.WALL.value:
                                self._placed_walls[my][mx] = MapObject.EMPTY.value
                                self._check_board_state = True
                                self._sound.play_sfx(self._sound_wall)
                                update_history = True
                                self.needs_display_update = True
                        elif self._mouse_action == MouseAction.PLACE_MARK.value:
                            if user_tile == MapObject.EMPTY.value:
                                self._placed_walls[my][mx] = MapObject.MARK.value
                                self._sound.play_sfx(self._sound_mark)
                                update_history = True
                                self.needs_display_update = True
                        elif self._mouse_action == MouseAction.REMOVE_MARK.value:
                            if user_tile == MapObject.MARK.value:
                                self._placed_walls[my][mx] = MapObject.EMPTY.value                   
                                self._sound.play_sfx(self._sound_mark) 
                                update_history = True
                                self.needs_display_update = True
                        if update_history:

                            # update history with this move. If we've done an undo in
                            # the past, reset the 'top' pointer to start overwriting 
                            # old actions
                            this_action = HistoryAction(mx, my, old_state, self._placed_walls[my][mx])
                            try:
                                self._action_history[self._action_history_idx] = this_action
                            except IndexError:
                                self._action_history.append(this_action)
                            self._action_history_idx += 1
                            self._action_history_idx_top = self._action_history_idx

            # if a user wall has changed, check for errors/win condition
            if self._check_board_state:
                self._check_for_errors()
                self._check_win()
                self._check_board_state = False
        elif mx == -1 and my == -1:      # if user has clicked on book icon
            if click_lmb and not self._mouse_action:
                self._mouse_action = MouseAction.MENU_ACTION.value
                self._menu_is_open = True
                logging.debug("MENU OPEN")
    
    def _check_win(self):
        """Checks to see if the user-modified board matches the puzzle book board."""
        user_board = self._strip_marks()
        if self._board_layout == user_board:
            self._sound.play_sfx(self._sound_win)
            self.game_won = True
            self._player_wins += 1
    
    def _check_for_errors(self):
        """
        Generates the sum of user-placed walls by row and column. Checks to see 
        if any of those user values exceed the generated hints from the puzzle.
        Updates the error arrays x_err and y_err with the indexes of the errors.
        """

        x_sum = []
        y_sum = []

        # calculate sums of placed walls row/columns
        for i, v in enumerate(self._placed_walls):
            y_sum.append(v.count(MapObject.WALL.value))
        for x in range(8):
            e_sum = 0
            for y in range(8):
                if self._placed_walls[y][x] == MapObject.WALL.value:
                    e_sum = e_sum + 1
            x_sum.append(e_sum)
        
        # get indexes of errors when compared to the hint frame
        self._x_err = [i for i, v in enumerate(x_sum) if v > self._hint_x[i]]
        self._y_err = [i for i, v in enumerate(y_sum) if v > self._hint_y[i]]

        # get indexes of limits against hint frame
        self._x_lim = [i for i, v in enumerate(x_sum) if v == self._hint_x[i]]
        self._y_lim = [i for i, v in enumerate(y_sum) if v == self._hint_y[i]]

    def _draw_errors(self):
        """Draws a red overlay over the hint numbers based on the values in _x_err and _y_err."""
        for i in self._x_err:
            self._screen.blit(self._err_overlay, ((i + 1) * TILE_SIZE, 0))
        for i in self._y_err:
            self._screen.blit(self._err_overlay, (0, (i + 1) * TILE_SIZE))

    def _draw_limit(self):
        """Draws a grey overlay over the hint numbers based on the values in _x_lim and _y_lim."""
        for i in self._x_lim:
            self._screen.blit(self._limit_overlay, ((i + 1) * TILE_SIZE, 0))
        for i in self._y_lim:
            self._screen.blit(self._limit_overlay, (0, (i + 1) * TILE_SIZE))

    def _strip_walls(self) -> list:
        """Removes walls from loaded puzzle. Used to generate the 'user board'."""
        out = []
        for row in self._board_layout:
            out.append([v if v != MapObject.WALL.value else MapObject.EMPTY.value for v in row])
        return out

    def _strip_marks(self) -> list:
        """Returns a list of the board with all user-placed marks removed. Used by _check_win"""
        out = []
        for row in self._placed_walls:
            out.append([v if v != MapObject.MARK.value else MapObject.EMPTY.value for v in row])
        return out        

    def _calc_hints(self) -> None:
        """Calculates the hint numbers for the border. Updates _hint_x and _hint_y"""
        for i, v in enumerate(self._board_layout):
            self._hint_y[i] = v.count(MapObject.WALL.value)
        for x in range(8):
            sum_y = 0
            for y in range(8):
                if self._board_layout[y][x] == MapObject.WALL.value:
                    sum_y = sum_y + 1
            self._hint_x[x] = sum_y

    def _draw_sprite(self, sprite: pygame.image, grid_pos: tuple):
        """
        Draws a grid-oriented sprite to an (x, y) position. 
        x and y are GRID positions, not pixel coordiantes. 
        """

        pos_x = (grid_pos[0] + 1) * TILE_SIZE
        pos_y = (grid_pos[1] + 1) * TILE_SIZE
        self._screen.blit(sprite, (pos_x, pos_y))

    def _draw_placed_objects(self):
        """Draws all user-placed objects on board. Should be called after _draw_map_tiles"""
        for y, row in enumerate(self._placed_walls):
            for x, obj in enumerate(row):
                if obj == MapObject.WALL.value:
                    self._draw_sprite(self._sprite_wall, (x, y))
                elif obj == MapObject.MARK.value:
                    self._draw_sprite(self._sprite_mark, (x, y))

    def _draw_map_tiles(self, show_wall: bool = False):
        """
        Draws the map to the board including enemies and chests.
        If show_wall is True, it also draws the walls for the map.
        """

        for y, row in enumerate(self._board_layout):
            for x, obj in enumerate(row):
                if show_wall and obj == MapObject.WALL.value:
                    self._draw_sprite(self._sprite_wall, (x, y))
                elif obj == MapObject.ENEMY.value:
                    self._draw_sprite(self._sprite_enemy, (x, y))
                elif obj == MapObject.CHEST.value:
                    self._draw_sprite(self._sprite_chest, (x, y))

    def _load_sprite(self, path: str, size_x: int = TILE_SIZE, size_y: int = TILE_SIZE) -> pygame.image:
        """
        Load a sprite of a given size (size_x, size_y), returns the pygame image.
        This should be called rather than directly calling pygame.image.load because
        it automatically detects the correct path of the asset, whether the program 
        is running from the main directory or if it's compiled as a standalone executable.
        """

        logging.debug(f"Loading sprite: {path}. Size ({size_x}, {size_y})")
        try:
            image = pygame.image.load(resource_path(path))
            return pygame.transform.scale(image, (size_x, size_x))
        except FileNotFoundError:
            logging.critical(f"Could not open sprite: {path}")
            raise

    def _get_mouse_to_grid(self) -> tuple:
        """"Snaps" the mouse position to the board grid. Returns mouse's position on grid."""
        pos_x, pos_y = pygame.mouse.get_pos()
        pos_x = math.floor((pos_x / TILE_SIZE) - 1)
        pos_y = math.floor((pos_y / TILE_SIZE) - 1)
        pos_x = max(min(8, pos_x), -1)
        pos_y = max(min(8, pos_y), -1)
        return(pos_x, pos_y)

    def _draw_frame(self):
        """Draws the outer frame of the board along with the wall hints."""
        for i in range(1, 9):
            hint_x = self._sprite_number[self._hint_x[i - 1]]
            hint_y = self._sprite_number[self._hint_y[i - 1]]
            self._screen.blit(self._sprite_frame, (i * TILE_SIZE, 0))
            self._screen.blit(self._sprite_frame, (0, i * TILE_SIZE))
            self._screen.blit(hint_x, (i * TILE_SIZE + self._font_pos_offset, self._font_pos_offset))
            self._screen.blit(hint_y, (self._font_pos_offset, i * TILE_SIZE + self._font_pos_offset))
        self._screen.blit(self._sprite_frame, (0, 0))
        self._screen.blit(self._sprite_book, (0, 0))
    
    # Methods for building the menus. I'd love to move these methods out of this file because they look dumb.
    def _menu_build_theme(self) -> pygame_menu.Theme:
        pygame_menu.widgets.MENUBAR_STYLE_UNDERLINE_TITLE
        theme: pygame_menu.Theme = pygame_menu.themes.THEME_DARK.copy()
        theme.background_color = THEME_COLOR
        theme.widget_font_shadow = True
        theme.widget_font_size = 20
        return theme
    
    def _menu_build_main(self) -> pygame_menu.Menu:
        menu: pygame_menu.Menu = pygame_menu.Menu(
            "Dungeon Cross", 
            400, 
            600,
            theme = self._menu_theme
        )
        menu.set_onclose(self._menu_close)
        menu.add.button('Resume', action=self._menu_close)
        menu.add.button('Reset', action=self._menu_reset)
        menu.add.button("Random Puzzle", action=self._menu_random_map)
        menu.add.vertical_fill(2)
        menu.add.text_input(
            'Puzzle ID: ',
            default='00000',
            maxchar=5,
            valid_chars=[*'0123456789'],
            onchange=self._menu_update_pid,
            onreturn=self._menu_open_map,
            background_color = (70, 50, 0),
            textinput_id="PUZZLE_ID"
        )
        menu.add.button("Load Puzzle", action=self._menu_open_map)
        menu.add.vertical_fill(2)
        self._menu_sound_selector = menu.add.toggle_switch(
            "Sound: ",
            onchange=self._menu_set_mute, 
            default=True,
            width=90,
            toggleswitch_id="SOUND"
        )
        self._menu_colorblind_selector = menu.add.toggle_switch(
            "Colorblind Mode: ",
            onchange=self._menu_change_cb_mode,
            default=False,
            width=90,
            toggleswitch_id="CB_MODE"
        )
        menu.add.toggle_switch(
            title="Power Saver: ",
            default=False,
            width=90,
            onchange=self._menu_power_save,
            toggleswitch_id="PW_SAVE"
        )
        menu.add.vertical_fill(2)
        menu.add.button("How to Play", action=self._menu_tutorial)
        menu.add.button("About", self._menu_about)
        menu.add.button('Quit', self._menu_quit)
        return menu

    def _menu_build_about(self):
        menu: pygame_menu.Menu = pygame_menu.Menu(
            "About", 
            700, 
            600,
            theme = self._menu_theme
        )
        with open(resource_path("about.txt")) as f:
            lines = f.readlines()
        f.close()
        menu.add.image(resource_path("sprite/hydra3.png"))
        for line in lines:
            menu.add.label(line.splitlines()[0], align=pygame_menu.locals.ALIGN_LEFT)
        menu.add.image(resource_path("sprite/hydra3.png"))
        return menu
    
    def _menu_build_tutorial(self):
        menu: pygame_menu.Menu = pygame_menu.Menu(
            "Tutorial", 
            700, 
            600,
            theme = self._menu_theme
        )
        with open(resource_path("tutorial.txt")) as f:
            lines = f.readlines()
        f.close()
        menu.add.image(resource_path("sprite/hydra3.png"))
        for line in lines:
            if line.strip() == '':
                continue
            if line.strip()[0] == '#':
                file_str = line.strip('#')
                try:
                    menu.add.image(resource_path(file_str.strip()))
                except AssertionError as e:
                    print(e)
            else:
                menu.add.label(line.splitlines()[0], align=pygame_menu.locals.ALIGN_LEFT)
        menu.add.image(resource_path("sprite/hydra3.png"))
        return menu


def show_splash(screen: pygame.Surface):
    """
    Shows splash screen while loading. 
    Automatically calls pygame.display.update. 
    Only needs be called once.
    """

    image = pygame.image.load(resource_path('sprite/splash.png'))
    sxm = round(image.get_width() / 2)
    sym = round(image.get_height() / 2)
    pos_x = (G_RESOLUTION[0] / 2) - sxm
    pos_y = (G_RESOLUTION[1] / 2) - sym
    screen.fill(pygame.color.Color(THEME_COLOR))
    screen.blit(image, (pos_x, pos_y))
    pygame.display.update()


def main():

    # init logging
    log_system.init_logging(G_LOG_LEVEL)

    # init pygame
    pygame.init()

    # create music handler object, load music, and start playback
    sound = sound_handler.SoundHandler(resource_path('audio/music/'))
    sound.load_music_all()
    sound.shuffle()
    sound.set_volume(35)
    sound.play_next_background_song()

    # create display window
    screen = pygame.display.set_mode(G_RESOLUTION)
    show_splash(screen)

    # internal timer for FPS regulation
    clock = pygame.time.Clock()

    # create game and load levels
    game = DungeonCross(screen, sound)
    game.load_puzzle_book()
    game.load_save()
    game_run = True

    # main loop
    logging.info("GAME START")
    while game_run:
        while game_run and not game.game_won:

            # handle events
            events = pygame.event.get()
            for event in events:

                # handle window quit event
                if event.type == pygame.QUIT:
                    logging.info("GAME EXITING")
                    game.save_game()
                    game_run = False
                
                # handle song-end event
                elif event.type == pygame.USEREVENT:
                    sound.play_next_background_song()

                # handle window focus change event
                elif event.type == pygame.ACTIVEEVENT:
                    game.needs_display_update = True

                # otherwise, pass event to game object
                else:
                    game_run = game.handle_io_event(event)

            # draw game assets
            game.update()

            # update screen
            pygame.display.update()
            clock.tick(TARGET_FPS)
        if game.game_won:
            time.sleep(2)
            game.open_random_puzzle()

if __name__ == '__main__':
    main()
