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

import sys
import json
import logging

class SaveFile:
    def __init__(self, save_file_name: str):
        self._save_path: str = self._get_save_path(save_file_name)

    def get_save_data(self) -> dict:
        logging.info(f"Loading save file: {self._save_path}.")
        save_file = open(self._save_path, 'r')
        data = json.load(save_file)
        save_file.close()
        return data

    def store_save_data(self, data: dict):
        logging.info(f"Saving data to save file: {self._save_path}")
        save_file = open(self._save_path, 'w')
        json.dump(data, save_file)
        save_file.close()
    
    def get_save_path(self) -> str:
        return self._save_path

    def _get_save_path(self, file_name: str) -> str:
        """When compiled, MacOS needs to store the save file to a different location"""
        file_path = ''
        if sys.platform == 'darwin' and hasattr(sys, "_MEIPASS"):
            file_dir = os.path.expanduser('~/Library/Application Support/')
            file_path = log_dir + log_file_name
        elif sys.platform in ['linux', 'win32', 'darwin']:
            file_path = file_name
        else:
            raise OSError(f"Unsupported platform: {sys.platform}")
        return file_path