#!/usr/bin/python3

#     DC Map Converter
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

import json
import gzip
import numpy
import random
import argparse
from map_object_enum import MapObject

VERSION = "v1.1.0"

def to_bit_list(byte):
    out = []
    for i in range(8):
        out.append((byte >> i) & 1)
    return out

def get_walls(map_mask):
    out = []
    for i in range(8):
        out.append(to_bit_list(map_mask[i]))
    return out

def convert_str_to_map(map_str: str):
    map_bytes = int(map_str).to_bytes(8, 'big')
    return get_walls(map_bytes)

def place_enemies(map_list: list):
    """
    Locates any tile surrounded by three walls (including borders) and inserts
    the MapObject.ENEMY.value into that tile. 
    """

    for yi, yv in enumerate(map_list):
        for xi, xv in enumerate(yv):
            cell_score = 0

            # if cell contains a wall, move on to next cell
            if xv == MapObject.WALL.value:
                continue

            # if the cell exists next to a border, add 1 to score instead for
            # each border wall
            if xi == 0 or xi == 7:
                cell_score = cell_score + 1
            if yi == 0 or yi == 7:
                cell_score = cell_score + 1
            
            # check all non-border neighbor cells in a cross pattern,
            # add 1 to the score for each wall detected
            if yi > 0:      # upper
                if map_list[yi - 1][xi] == MapObject.WALL.value:
                    cell_score = cell_score + 1
            if yi < 7:      # lower
                if map_list[yi + 1][xi] == MapObject.WALL.value:
                    cell_score = cell_score + 1
            if xi > 0:      # left
                if map_list[yi][xi - 1] == MapObject.WALL.value:
                    cell_score = cell_score + 1
            if xi < 7:      # right
                if map_list[yi][xi + 1] == MapObject.WALL.value:
                    cell_score = cell_score + 1

            # if cell is surrounded by 3 walls, place enemy
            if cell_score == 3:
                map_list[yi][xi] = MapObject.ENEMY.value
    return map_list

def place_chest(map_list: list):
    """
    Locates an empty 3x3 grid and places a chest in a random position.
    This is currently done by a brute-force method.
    """

    for yi, yv in enumerate(map_list):

        # a treasure room cannot start below row 5
        if yi > 5:
            break

        for xi, xv in enumerate(yv):

            # treasure room cannot start past column 5
            if xi > 5:
                break

            # if starting cell is not empty, skip to next cell
            if xv != MapObject.EMPTY.value:
                continue
            
            # save current cell location
            cur_x = xi
            cur_y = yi

            # check if cell is inside of an empty 3x3 grid
            cell_check = True
            for y in range(0, 3):
                for x in range(0, 3):
                    try:
                        if map_list[cur_y + y][cur_x + x] != MapObject.EMPTY.value:
                            cell_check = False
                            break
                    except:
                        print(f"{cur_x} {x}")
                        print(f"{cur_y} {y}")
                        for i in map_list:
                            print(i)
                        exit(1)
                if cell_check == False:
                    break
            if cell_check == False:
                continue

            # place chest in a random position in the 3x3 grid
            cx = random.randint(0, 2)
            cy = random.randint(0, 2)
            try:
                map_list[cur_y + cy][cur_x + cx] = MapObject.CHEST.value
            except Exception as e:
                print(f"{cur_x} {cx}")
                print(f"{cur_y} {cy}")
                for i in map_list:
                    print(i)                
                exit(1)
    return map_list

def get_rot_maps(map_list: list) -> list:
    """
    Returns copies of the maps rotated by 90-degree intervals.
    Does not return original maps.
    """

    print("Generating rotated maps", end="")
    out_list = []
    for i, m in enumerate(map_list):
        mp: numpy.ndarray = numpy.array(m)
        for _ in range(0, 3):
            mp = numpy.rot90(mp)
            out_list.append(mp.tolist())
        if i % 1000 == 0:
            print(".", end="", flush=True)
    print("Done.")
    return out_list

def get_flip_maps(map_list: list) -> list:
    """
    Returns list of flippled maps
    Does not return original maps.
    """

    print("Generating flipped maps", end="")
    out_list = []
    for i, m in enumerate(map_list):
        mp: numpy.ndarray = numpy.array(m)
        mp = numpy.flip(mp)
        out_list.append(mp.tolist())
        if i % 1000 == 0:
            print(".", end="", flush=True)
    print("Done.")
    return out_list

def convert_map(map_list: list) -> list:
    _map = convert_str_to_map(map_list)
    _map = place_enemies(_map)
    _map = place_chest(_map)
    return _map

def main():
    print(f"Map Converter {VERSION}")

    # get command arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", action="store_true", help="Include rotated maps.")
    parser.add_argument("-f", action="store_true", help="Include flipped maps.")
    parser.add_argument("file", type=argparse.FileType('r'))
    args = parser.parse_args()

    # retrieve all the raw mask codes 
    print("Building maps", end='',flush=True)
    with args.file as f:
        lines = f.read().splitlines()
    f.close()

    # start building the maps (walls, monsters, chests)
    out_list = []
    for i, line in enumerate(lines):
        out_list.append(convert_map(line))
        if i % 1000 == 0:
            print('.', end='', flush=True)
    print("Done.")

    # if rotation option is selected, call the rotation function and merge the returned list
    if args.r:
        out_list = out_list + get_rot_maps(out_list)

    # if flip option is selected, call the flip function and merge the returned list
    if args.f:
        out_list = out_list + get_flip_maps(out_list)

    # finally, write output to a compressed file
    print(f"Writing {len(out_list)} maps to file, this might take a while...")
    with gzip.open("puzzles.json.gz", "w") as f:
        f.write(bytes(json.dumps(out_list, separators=(',', ':')), 'utf-8'))
    f.close()
    print("Done.")

if __name__ == '__main__':
    main()