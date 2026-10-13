import pygame

# Atkinson Hyperlegible, SIL Open Font License (see fonts/OFL.txt)
font_files = {
    False: "fonts/AtkinsonHyperlegible-Regular.ttf",
    True: "fonts/AtkinsonHyperlegible-Bold.ttf",
}
cache = {}


def getFont(size, bold=False):
    key = (size, bold)
    if key not in cache:
        try:
            cache[key] = pygame.font.Font(font_files[bold], size)
        except (OSError, pygame.error):
            cache[key] = pygame.font.SysFont("Arial", size, bold=bold)
    return cache[key]
