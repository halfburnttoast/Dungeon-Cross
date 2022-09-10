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