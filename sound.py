import os
import random
import pygame

# Sound name -> (files, loudness 0-1). A random file plays when there are several.
sound_list = {
    "hop":          (["hop1.ogg", "hop2.ogg", "hop3.ogg", "hop4.ogg"], 0.25),
    "pick":         (["pick.wav"], 0.6),
    "munch":        (["munch.wav"], 0.7),
    "store":        (["store.ogg"], 0.7),
    "deliver":      (["deliver.ogg"], 0.6),
    "order_filled": (["order_filled.ogg"], 0.8),
    "level_start":  (["level_start.ogg"], 0.6),
    "caught":       (["caught.ogg"], 0.8),
    "dawn":         (["dawn.ogg"], 0.8),
    "game_over":    (["game_over.ogg"], 0.8),
    "victory":      (["victory.ogg"], 0.8),
    "bark":         (["bark1.wav", "bark2.wav", "bark3.wav"], 0.6),
    "whistle":      (["whistle.wav"], 0.6),
    "cluck":        (["cluck.wav"], 0.6),
    "squawk":       (["squawk.wav"], 0.8),
    "squeak":       (["squeak.wav"], 0.5),
    "menu_move":    (["menu_move.wav"], 0.5),
    "menu_select":  (["menu_select.wav"], 0.6),
}

music_list = {
    "title": "title.mp3",
    "night": "night.ogg",
}


class SoundManager:
    def __init__(self, soundLevel, musicLevel):
        self.enabled = True
        self.sounds = {}
        self.currentMusic = None
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(44100, -16, 2, 512)
        except pygame.error:
            # No audio device: play silently
            self.enabled = False
            return
        for name, (files, loudness) in sound_list.items():
            loaded = []
            for filename in files:
                try:
                    loaded.append(pygame.mixer.Sound(os.path.join("sounds", filename)))
                except (pygame.error, FileNotFoundError):
                    print("Missing sound: %s" % filename)
            self.sounds[name] = (loaded, loudness)
        self.setVolumes(soundLevel, musicLevel)

    def setVolumes(self, soundLevel, musicLevel):
        # Levels are 0 to 5
        self.soundVolume = soundLevel / 5
        self.musicVolume = musicLevel / 5
        if not self.enabled: return
        pygame.mixer.music.set_volume(self.musicVolume * 0.7)
        if self.musicVolume == 0:
            pygame.mixer.music.stop()
        elif self.currentMusic and not pygame.mixer.music.get_busy():
            track = self.currentMusic
            self.currentMusic = None
            self.playMusic(track)

    def play(self, name):
        if not self.enabled or self.soundVolume == 0: return
        if name not in self.sounds or not self.sounds[name][0]: return
        (loaded, loudness) = self.sounds[name]
        sound = random.choice(loaded)
        sound.set_volume(self.soundVolume * loudness)
        sound.play()

    def playMusic(self, track):
        if not self.enabled or track == self.currentMusic: return
        self.currentMusic = track
        if self.musicVolume == 0: return
        try:
            pygame.mixer.music.load(os.path.join("music", music_list[track]))
            pygame.mixer.music.set_volume(self.musicVolume * 0.7)
            pygame.mixer.music.play(-1, fade_ms=800)
        except pygame.error:
            print("Could not play music: %s" % track)
