import os
import sys
import pygame
from globals import *


class Display:
    """The game always draws to an 800x600 canvas, which is scaled to fit the window."""
    def __init__(self, mode):
        self.window = None
        self.canvas = None
        self.setMode(mode)
        self.canvas = pygame.Surface((screen_width, screen_height)).convert()

    def setMode(self, mode):
        self.mode = mode
        self.changedAt = pygame.time.get_ticks()
        (dw, dh) = self.desktopSize()
        if mode == "fullscreen":
            self.window = pygame.display.set_mode(self.fullscreenSize(), pygame.FULLSCREEN)
        elif mode == "borderless":
            os.environ["SDL_VIDEO_WINDOW_POS"] = "0,0"
            self.window = pygame.display.set_mode((dw, dh), pygame.NOFRAME)
            self.moveWindow(0, 0)
        else:
            x = (dw - screen_width) // 2
            y = (dh - screen_height) // 2
            os.environ["SDL_VIDEO_WINDOW_POS"] = "%d,%d" % (x, y)
            self.window = pygame.display.set_mode((screen_width, screen_height))
            self.moveWindow(x, y)
        pygame.display.set_caption("Farm Bandit")
        self.updateScale()

    def desktopSize(self):
        try:
            return pygame.display.get_desktop_sizes()[0]
        except (AttributeError, IndexError, pygame.error):
            return (screen_width, screen_height)

    def fullscreenSize(self):
        # The monitor's real top resolution. With Windows display scaling the desktop size
        # isn't a real monitor mode, and asking for it picks an odd fallback resolution.
        try:
            modes = pygame.display.list_modes()
            if modes and modes != -1: return modes[0]
        except pygame.error:
            pass
        return self.desktopSize()

    def recentlyChanged(self):
        # The mouse lands somewhere new when the window changes size
        return pygame.time.get_ticks() - self.changedAt < 500

    def moveWindow(self, x, y):
        # pygame keeps the same window when the mode changes, so move it ourselves.
        # (pygame._sdl2's Window.from_display_module() crashes the game later, so don't use it.)
        if sys.platform != "win32": return
        try:
            import ctypes
            hwnd = pygame.display.get_wm_info()["window"]
            no_size, no_zorder = 0x0001, 0x0004
            ctypes.windll.user32.SetWindowPos(hwnd, 0, x, y, 0, 0, no_size | no_zorder)
        except Exception:
            pass  # Moving the window is only a nicety

    def updateScale(self):
        # Largest 4:3 area that fits, with black bars on the sides
        (ww, wh) = self.window.get_size()
        scale = min(ww / screen_width, wh / screen_height)
        w = int(screen_width * scale)
        h = int(screen_height * scale)
        self.rect = pygame.Rect((ww - w) // 2, (wh - h) // 2, w, h)

    def toCanvas(self, pos):
        # Window position (like the mouse) to canvas position
        x = (pos[0] - self.rect.x) * screen_width / self.rect.width
        y = (pos[1] - self.rect.y) * screen_height / self.rect.height
        return (int(x), int(y))

    def present(self):
        if self.rect.size == (screen_width, screen_height) and self.rect.topleft == (0, 0):
            self.window.blit(self.canvas, (0, 0))
        else:
            self.window.fill(black)
            pygame.transform.scale(self.canvas, self.rect.size, self.window.subsurface(self.rect))
        pygame.display.flip()
