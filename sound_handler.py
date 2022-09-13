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
import random
import logging
from pygame import mixer, USEREVENT
from pygame import error as pygame_error
from resource_path import resource_path

class SoundHandler:
    def __init__(self, music_path: str):
        self._mixer_running = False
        if mixer.get_init() != None:
            self._mixer_running = True
        else:
            logging.warn("Failed to open mixer.")
        self._playlist: list = []
        self._volume: float = 0.5
        self._music_path = music_path
        self.muted = False
        self.song_idx = 0

    def load_music_all(self):
        try:
            files = os.listdir(self._music_path)
            self._playlist = [x for x in files if '.mp3' in x]
        except PermissionError as e:
            logging.warn(f"Failed to open music directory {self._music_path}")
            raise

    def shuffle(self) -> None:
        random.shuffle(self._playlist)

    def play_next_background_song(self):
        """
        Plays the next background song in list. Sends pygame.USEREVENT + 0 when 
        song has finsihed. Auto-increments to next song when called, so you can
        call this function again to start the next song.
        """
        
        if self._mixer_running and not mixer.get_init() is None:
            song = self._playlist[self.song_idx]
            logging.debug(f"Playing background song: {song}")
            mixer.music.unload()
            mixer.music.load(os.path.join(self._music_path, song))
            self.song_idx = (self.song_idx + 1) % len(self._playlist)
            mixer.music.play(fade_ms=5000)
            mixer.music.set_endevent(USEREVENT)

    def set_volume(self, volume: int = 100):
        if self._mixer_running:
            vol = min(100, max(0, volume))
            mixer.music.set_volume(vol / 100)

    def stop_music(self):
        if self._mixer_running:
            mixer.music.stop()

    def load_sfx(self, sound_effect_path: str, volume: float = 0.6) -> mixer.Sound:
        if not self.muted and self._mixer_running:        
            try:
                snd = mixer.Sound(resource_path(sound_effect_path))
                snd.set_volume(0.6)
                return snd
            except pygame_error as e:
                logging.warn(f"Failed to open: {sound_effect_path}")
                raise

    def play_sfx(self, sound_effect: mixer.Sound) -> None:
        """Wrap sfx calls in a try/except block."""
        if not self.muted and self._mixer_running:
            try:
                sound_effect.play()
            except pygame_error as e:
                logging.warn(f"Could not play sound: {sound_effect}")
                raise