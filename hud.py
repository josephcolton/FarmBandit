import pygame
import fonts
from globals import *
from crops import cropTypes
import settings

panel_x = tile_width * map_width + farm_offset_x * 2   # Right side panel
strip_y = tile_height * map_height + farm_offset_y * 2 # Bottom strip
overlay_width = 600                                    # Message panels over the farm


class Hud:
    def __init__(self, sm):
        self.sm = sm
        self.screen = sm.screen
        self.font = fonts.getFont(18)
        self.smallFont = fonts.getFont(14)
        self.bigFont = fonts.getFont(40, bold=True)
        self.titleFont = fonts.getFont(30, bold=True)
        self.nightShade = pygame.Surface((tile_width * map_width, tile_height * map_height), pygame.SRCALPHA)

    def text(self, message, x, y, font=None, color=hud_text, center=False, outline=False):
        font = font or self.font
        image = font.render(message, True, color)
        rect = image.get_rect()
        if center: rect.center = (x, y)
        else: rect.topleft = (x, y)
        if outline:
            # Dark edge so the text reads on top of the farm
            shadow = font.render(message, True, black)
            for (ox, oy) in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                self.screen.blit(shadow, rect.move(ox, oy))
        self.screen.blit(image, rect)
        return rect

    def drawIcon(self, kind, x, y):
        crop = cropTypes[kind]
        sprite = self.sm.getSprite(crop.spriteSheet, crop.getIcon())
        if sprite.get_height() > tile_height:
            # Tall crops are shrunk to fit the icon space
            (w, h) = sprite.get_size()
            sprite = pygame.transform.smoothscale(sprite, (w * tile_height // h, tile_height))
            x += (tile_width - sprite.get_width()) // 2
        self.screen.blit(sprite, (x, y))

    def draw(self, game):
        rabbit = game.rabbit
        y = strip_y + 4
        # Lives
        self.text("Lives", 16, y, self.smallFont)
        for i in range(game.lives):
            self.sm.drawSprite("rabbit", "s_hopa1", 12 + i * 26, y + 16)
        # Hunger
        self.text("Hunger", 120, y, self.smallFont)
        bar = pygame.Rect(120, y + 22, 150, 16)
        fill = bar.copy()
        fill.width = int(bar.width * rabbit.hunger / max_hunger)
        color = green if rabbit.hunger > 30 else yellow if rabbit.hunger > 0 else red
        pygame.draw.rect(self.screen, black, bar)
        pygame.draw.rect(self.screen, color, fill)
        pygame.draw.rect(self.screen, hud_text, bar, 1)
        if rabbit.isStarving():
            self.text("Starving!", 280, y + 21, self.smallFont, red)
        # Basket
        self.text("Basket", 360, y, self.smallFont)
        for i in range(basket_size):
            slot = pygame.Rect(360 + i * 36, y + 16, 34, 34)
            pygame.draw.rect(self.screen, black, slot)
            pygame.draw.rect(self.screen, hud_text, slot, 1)
            if i < len(rabbit.basket):
                self.drawIcon(rabbit.basket[i], slot.x + 1, slot.y + 1)
        # Score
        self.text("Score", 520, y, self.smallFont)
        self.text("%d" % game.score, 520, y + 18)
        self.text("P pause", 620, y + 20, self.smallFont)

        # Order panel
        self.text("Level %d" % (game.levelIndex + 1), panel_x + 6, 12)
        self.text("Order", panel_x + 6, 44, self.smallFont, yellow)
        oy = 64
        for kind in game.level.order:
            self.drawIcon(kind, panel_x + 4, oy)
            done = game.delivered[kind]
            need = game.level.order[kind]
            color = green if done >= need else hud_text
            self.text("%d/%d" % (done, need), panel_x + 42, oy + 7, color=color)
            oy += 36
        # Pantry of extra crops
        oy += 10
        self.text("Pantry", panel_x + 6, oy, self.smallFont, yellow)
        self.text("%d stored" % len(rabbit.pantry), panel_x + 6, oy + 18, self.smallFont)
        # Time until dawn
        oy += 52
        seconds = int(game.nightLeft / 1000)
        late = seconds < 30
        self.text("Dawn in", panel_x + 6, oy, self.smallFont, yellow)
        self.text("%d:%02d" % (seconds // 60, seconds % 60), panel_x + 6, oy + 18,
                  color=red if late and int(game.stateTime / 300) % 2 else hud_text)
        bar = pygame.Rect(panel_x + 6, oy + 42, 80, 8)
        fill = bar.copy()
        fill.width = int(bar.width * (1 - game.nightLeft / (game.level.night_length * 1000)))
        pygame.draw.rect(self.screen, (30, 30, 70), bar)
        pygame.draw.rect(self.screen, (255, 170, 90), fill)
        pygame.draw.rect(self.screen, hud_text, bar, 1)
        # Difficulty
        label = settings.difficulty_settings[game.difficulty]["label"]
        self.text(label, panel_x + 6, strip_y - 24, self.smallFont)

    def drawNight(self, nightLeft, nightLength):
        # Dark blue night that turns to a warm sunrise in the last quarter
        progress = 1 - nightLeft / nightLength
        night = (15, 25, 70, 110)
        sunrise = (255, 150, 80, 45)
        t = max(0.0, (progress - 0.75) / 0.25)
        color = tuple(int(n + (s - n) * t) for (n, s) in zip(night, sunrise))
        self.nightShade.fill(color)
        self.screen.blit(self.nightShade, (farm_offset_x, farm_offset_y))

    def drawOverlay(self, lines):
        # Dark box over the farm with centered text, first line is the title
        shade = pygame.Surface((tile_width * map_width, tile_height * map_height), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 120))
        self.screen.blit(shade, (farm_offset_x, farm_offset_y))
        cx = farm_offset_x + tile_width * map_width // 2
        cy = farm_offset_y + tile_height * map_height // 2
        # Long titles get a smaller font; long lines wrap to fit the panel
        textWidth = overlay_width - 40
        titleFont = self.bigFont
        if titleFont.size(lines[0])[0] > textWidth: titleFont = self.titleFont
        body = []
        for line in lines[1:]:
            body += self.wrap(line, self.font, textWidth)
        # Solid panel behind the text
        height = 60 + 28 * len(body) + 30
        panel = pygame.Rect(0, 0, overlay_width, height)
        panel.center = (cx, cy)
        pygame.draw.rect(self.screen, hud_background, panel, border_radius=10)
        pygame.draw.rect(self.screen, yellow, panel, 2, border_radius=10)
        y = panel.y + 40
        self.text(lines[0], cx, y, titleFont, yellow, center=True)
        y += 60
        for line in body:
            self.text(line, cx, y, center=True)
            y += 28

    def wrap(self, line, font, width):
        # Split a line into pieces that fit the width, breaking between words
        if font.size(line)[0] <= width: return [line]
        pieces = []
        current = ""
        for word in line.split(" "):
            attempt = (current + " " + word).strip()
            if current and font.size(attempt)[0] > width:
                pieces.append(current)
                current = word
            else:
                current = attempt
        pieces.append(current)
        return pieces
