#!/usr/bin/python3

import json
import random
from map_object_enum import MapObject

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
                break

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

def convert_map(map_list: list) -> list:
    _map = convert_str_to_map(map_list)
    _map = place_enemies(_map)
    _map = place_chest(_map)
    return _map

def main():
    with open("mapcodes.txt", 'r') as f:
        lines = f.read().splitlines()
    f.close()

    out_list = []
    for line in lines:
        out_list.append(convert_map(line))
    with open("out.json", "w") as f:
        json.dump(out_list, f)
    f.close()

if __name__ == '__main__':
    main()