from lib2to3 import pygram
import os
import random
from pygame import mixer
from pygame import error as pygame_error

class MusicHandler:
    def __init__(self, music_path: str):
        self._playlist: list = []
        self._volume: float = 0.5
        self._music_path = music_path
    def load_music_all(self):
        try:
            files = os.listdir(self._music_path)
            self._playlist = [x for x in files if '.mp3' in x]
        except PermissionError as e:
            print(f"Failed to open music directory {self._music_path}")
            print(e)
    def shuffle(self) -> None:
        random.shuffle(self._playlist)
    def play_music_all(self):
        if not mixer.get_init() is None:
            mixer.music.load(self._music_path + self._playlist[0])
            self._playlist.pop(0)
            for i in self._playlist:
                try:
                    mixer.music.queue(os.path.join(self._music_path + i))
                except pygame_error as e:
                    print("Couldn't open audio output device.")
                    print(e)
            mixer.music.play()
    def set_volume(self, volume: int = 100):
        vol = min(100, max(0, volume))
        mixer.music.set_volume(vol / 100)
    def stop_music(self):
        mixer.music.stop()