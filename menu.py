import random
import pygame
import fonts
from globals import *
import animals
import levels
import settings
import world

farm_rows = 8   # farms per column on the farm select page

about_lines = [
    ("Farm Bandit", "title"),
    ("A hungry bunny raids the farm by night, carrying crops", ""),
    ("back to its burrow to fill an order before dawn.", ""),
    ("", ""),
    ("How to Play", "head"),
    ("Arrows / WASD: hop     Space: pick a ripe crop", ""),
    ("E: eat a crop (ground, basket, or burrow pantry)", ""),
    ("Gamepad: D-pad or stick to hop, A pick, X eat, Start pause", ""),
    ("Bring crops home to fill the order before the sun comes up.", ""),
    ("Dogs and the farmer cost you a life. The farmer whistles", ""),
    ("for the dogs when he sees you. The rooster pecks you until", ""),
    ("you drop your basket, and rats nibble the ripe crops.", ""),
    ("Hide in tall grass and corn, or behind hay bales.", ""),
    ("", ""),
    ("Art", "head"),
    ("Bunny: Stephen \"Redshrike\" Challener, for PixelFarm (Tebruno99)", ""),
    ("Crops: bluecarrot16, Daniel Eddeland, Joshua Taylor, Jetrel", ""),
    ("Fences, tall grass, hay, chicken: Daniel Eddeland", ""),
    ("Shiba dog: Sevarihk, adapted by tapatilorenzo", ""),
    ("Rat: tapatilorenzo", ""),
    ("Farmer: Universal LPC Character Generator artists (bluecarrot16,", ""),
    ("  JaidynReiman, ElizaWy, wulax, Redshrike, and more)", ""),
    ("Floors: bluecarrot16, Sharm, and the LPC floors contributors", ""),
    ("Cliffs: Lanea \"Sharm\" Zimmerman, arranged by Evert", ""),
    ("Font: Atkinson Hyperlegible, Braille Institute (SIL OFL)", ""),
    ("", ""),
    ("Sound and Music", "head"),
    ("Sound effects and jingles: Kenney (kenney.nl)", ""),
    ("Dog barks: pauliuw", ""),
    ("\"Quaint Town\": neonarkade     \"Crouch jumping in your walls\": Fupi", ""),
    ("", ""),
    ("Art and sounds from OpenGameArt.org. Full credits and", ""),
    ("licenses are in the sprites, sounds, and music folders.", ""),
]


class TitleScreen:
    def __init__(self, app):
        self.app = app
        self.sm = app.sm
        self.sound = app.sound
        self.screen = self.sm.screen
        self.titleFont = fonts.getFont(72, bold=True)
        self.font = fonts.getFont(26, bold=True)
        self.smallFont = fonts.getFont(17)
        self.headFont = fonts.getFont(19, bold=True)
        # The farm behind the menu is drawn at farm size, then stretched to fill the screen
        self.farmSurface = pygame.Surface((tile_width * map_width + farm_offset_x * 2,
                                           tile_height * map_height + farm_offset_y * 2)).convert()
        self.levelIndex = random.randrange(len(levels.levels))
        self.itemRects = []
        self.open("main")

    ##############
    # Background #
    ##############
    def makeFarm(self):
        # A live farm: the bunny hides in its burrow while everyone else goes about their night
        self.levelIndex = (self.levelIndex + 1) % len(levels.levels)
        level = levels.levels[self.levelIndex]
        self.fm = world.FarmMap(self.sm, level)
        self.rabbit = animals.Rabbit(self.sm, self.fm)
        self.animals = [animals.Dog(self.sm, self.fm, x, y, self.rabbit) for (x, y) in self.fm.dogSpawns]
        self.animals += [animals.Rooster(self.sm, self.fm, x, y, self.rabbit) for (x, y) in self.fm.roosterSpawns]
        if self.fm.farmerSpawn:
            (x, y) = self.fm.farmerSpawn
            self.animals.append(animals.Farmer(self.sm, self.fm, x, y, self.rabbit, []))

    def drawFarm(self):
        self.sm.screen = self.farmSurface
        self.fm.draw()
        for animal in sorted(self.animals, key=lambda a: a.getPosition()[1]):
            animal.draw()
        self.sm.screen = self.screen
        farm = self.farmSurface.subsurface((farm_offset_x, farm_offset_y,
                                            tile_width * map_width, tile_height * map_height))
        pygame.transform.scale(farm, (screen_width, screen_height), self.screen)
        # Dusk tint so the menu stands out
        shade = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        shade.fill((15, 25, 70, 90))
        self.screen.blit(shade, (0, 0))

    #########
    # Pages #
    #########
    def open(self, page, highlight=None):
        if page == "main" or not hasattr(self, "fm"): self.makeFarm()
        self.page = page
        self.selected = 0
        self.highlight = highlight
        self.scroll = 0

    def items(self):
        s = self.app.settings
        if self.page == "main":
            return ["Start Game", "Options", "High Scores", "About", "Quit"]
        if self.page == "farms":
            names = [level.name for level in levels.levels[:self.unlocked()]]
            return ["%d. %s" % (i + 1, name) for i, name in enumerate(names)] + ["Back"]
        if self.page == "options":
            return ["Sound: %s" % self.volumeBar(s["sound"]),
                    "Music: %s" % self.volumeBar(s["music"]),
                    "Display: %s" % settings.display_labels[s["display"]],
                    "Difficulty: %s" % settings.difficulty_settings[s["difficulty"]]["label"],
                    "Back"]
        return ["Back"]

    def unlocked(self):
        return max(1, min(self.app.settings["unlocked"], len(levels.levels)))

    def volumeBar(self, level):
        return "|" * level + "." * (5 - level) + "  %d" % level

    def choose(self, direction=1):
        # Enter, click, or left/right on the selected item
        self.sound.play("menu_select")
        item = self.items()[self.selected]
        if self.page == "main":
            if item == "Start Game":
                if self.unlocked() > 1:
                    self.open("farms")
                    self.selected = self.unlocked() - 1
                else:
                    self.app.startGame()
            elif item == "Quit": self.app.quit()
            else: self.open(item.lower().replace(" ", ""))
        elif self.page == "farms":
            if item == "Back": self.open("main")
            else: self.app.startGame(self.selected)
        elif self.page == "options":
            if item == "Back":
                self.open("main")
                self.selected = 1
            else:
                self.changeOption(self.selected, direction)
        else:
            self.open("main")
            self.selected = {"highscores": 2, "about": 3}.get(self.page, 0)

    def changeOption(self, index, direction):
        s = self.app.settings
        if index == 0: s["sound"] = max(0, min(5, s["sound"] + direction))
        if index == 1: s["music"] = max(0, min(5, s["music"] + direction))
        if index == 2:
            modes = settings.display_modes
            s["display"] = modes[(modes.index(s["display"]) + direction) % len(modes)]
        if index == 3:
            options = settings.difficulties
            s["difficulty"] = options[(options.index(s["difficulty"]) + direction) % len(options)]
        self.app.applySettings()

    ##########
    # Events #
    ##########
    def handleEvent(self, event):
        count = len(self.items())
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                if self.page == "about": self.scroll = max(0, self.scroll - 1)
                else: self.moveSelection(-1, count)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                if self.page == "about": self.scroll = min(len(about_lines) - 14, self.scroll + 1)
                else: self.moveSelection(1, count)
            elif event.key in (pygame.K_LEFT, pygame.K_a) and self.page == "options" and self.selected < 4:
                self.changeOption(self.selected, -1)
                self.sound.play("menu_move")
            elif event.key in (pygame.K_RIGHT, pygame.K_d) and self.page == "options" and self.selected < 4:
                self.changeOption(self.selected, 1)
                self.sound.play("menu_move")
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.choose()
            elif event.key in (pygame.K_LEFT, pygame.K_a) and self.page == "farms":
                self.moveSelection(-farm_rows, count, wrap=False)
            elif event.key in (pygame.K_RIGHT, pygame.K_d) and self.page == "farms":
                self.moveSelection(farm_rows, count, wrap=False)
            elif event.key == pygame.K_ESCAPE:
                # Esc (or the gamepad's B / Start) goes back; on the main menu it moves to Quit
                if self.page == "main":
                    self.selected = len(self.items()) - 1
                    self.sound.play("menu_move")
                else:
                    self.open("main")
        elif event.type == pygame.MOUSEMOTION:
            # After the window changes size the pointer lands on a new spot without the
            # player moving it. Only hover-select once the mouse really moves.
            changedAt = self.app.display.changedAt
            if self.app.display.recentlyChanged() or getattr(self, "seenChange", None) != changedAt:
                self.seenChange = changedAt
                self.lastMouse = event.pos
                return
            if event.pos == getattr(self, "lastMouse", None): return
            self.lastMouse = event.pos
            for i, rect in enumerate(self.itemRects):
                if rect.collidepoint(event.pos) and i != self.selected:
                    self.selected = i
                    self.sound.play("menu_move")
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4 and self.page == "about": self.scroll = max(0, self.scroll - 1)
            if event.button == 5 and self.page == "about": self.scroll = min(len(about_lines) - 14, self.scroll + 1)
            if event.button not in (1, 3): return
            for i, rect in enumerate(self.itemRects):
                if rect.collidepoint(event.pos):
                    self.selected = i
                    # Clicking the left half of an option turns it down
                    left = event.pos[0] < rect.centerx or event.button == 3
                    self.choose(-1 if left else 1)
                    return

    def moveSelection(self, step, count, wrap=True):
        if wrap: self.selected = (self.selected + step) % count
        else: self.selected = max(0, min(count - 1, self.selected + step))
        self.sound.play("menu_move")

    def update(self, time):
        for animal in self.animals:
            animal.update(time)
            animal.sounds = []   # The background farm stays quiet
            if hasattr(animal, "messages"): animal.messages = []
        self.fm.update(time)

    ###########
    # Drawing #
    ###########
    def text(self, message, x, y, font, color=hud_text, center=True):
        image = font.render(message, True, color)
        rect = image.get_rect(center=(x, y)) if center else image.get_rect(topleft=(x, y))
        shadow = font.render(message, True, black)
        for (ox, oy) in ((-2, 0), (2, 0), (0, -2), (0, 2), (2, 2)):
            self.screen.blit(shadow, rect.move(ox, oy))
        self.screen.blit(image, rect)
        return rect

    def panel(self, rect):
        surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        surface.fill(hud_background + (225,))
        self.screen.blit(surface, rect)
        pygame.draw.rect(self.screen, yellow, rect, 2, border_radius=10)

    def draw(self):
        self.drawFarm()
        cx = screen_width // 2
        self.text("Farm Bandit", cx, 90, self.titleFont, yellow)
        if self.page == "main":
            self.text("A bunny's night out", cx, 150, self.headFont)
            self.drawItems(cx, 220, 300)
            self.text("Arrows and Enter, the mouse, or a gamepad", cx, 560, self.smallFont)
            self.text("v%s" % self.app.version, screen_width - 30, screen_height - 16, self.smallFont)
        elif self.page == "farms":
            self.text("Choose a Farm", cx, 160, self.font)
            self.drawFarms(cx)
        elif self.page == "options":
            self.text("Options", cx, 160, self.font)
            self.drawItems(cx, 210, 420)
            self.text("Left / Right to change, Enter on Back to return", cx, 560, self.smallFont)
        elif self.page == "highscores":
            self.drawHighScores(cx)
        elif self.page == "about":
            self.drawAbout(cx)

    def drawItems(self, cx, top, width):
        items = self.items()
        rowHeight = 50
        self.panel(pygame.Rect(cx - width // 2, top - 20, width, rowHeight * len(items) + 20))
        self.itemRects = []
        for i, item in enumerate(items):
            y = top + i * rowHeight + 20
            rect = pygame.Rect(cx - width // 2 + 10, y - 20, width - 20, 40)
            if i == self.selected:
                pygame.draw.rect(self.screen, (95, 82, 110), rect, border_radius=6)
                label = "<  %s  >" % item if self.page == "options" and item != "Back" else item
                self.text(label, cx, y, self.font, yellow)
            else:
                self.text(item, cx, y, self.font)
            self.itemRects.append(rect)

    def drawFarms(self, cx):
        items = self.items()
        box = pygame.Rect(cx - 360, 190, 720, farm_rows * 38 + 20)
        self.panel(box)
        self.itemRects = []
        for i, item in enumerate(items[:-1]):
            column = i // farm_rows
            row = i % farm_rows
            rect = pygame.Rect(box.x + 10 + column * 350, box.y + 10 + row * 38, 340, 34)
            if i == self.selected:
                pygame.draw.rect(self.screen, (95, 82, 110), rect, border_radius=6)
            self.text(item, rect.x + 12, rect.y + 5, self.headFont, yellow if i == self.selected else hud_text, center=False)
            self.itemRects.append(rect)
        # Back button
        rect = pygame.Rect(cx - 80, 545, 160, 40)
        selected = self.selected == len(items) - 1
        pygame.draw.rect(self.screen, (95, 82, 110), rect, border_radius=6)
        self.text("Back", cx, rect.centery, self.font, yellow if selected else hud_text)
        self.itemRects.append(rect)
        locked = len(levels.levels) - self.unlocked()
        if locked: self.text("%d more farm%s to discover" % (locked, "s" if locked > 1 else ""), cx, 525, self.smallFont)

    def drawHighScores(self, cx):
        self.text("High Scores", cx, 160, self.font)
        box = pygame.Rect(cx - 330, 190, 660, 330)
        self.panel(box)
        scores = settings.loadHighScores()
        columns = [(box.x + 30, "#"), (box.x + 70, "Name"), (box.x + 270, "Score"),
                   (box.x + 380, "Farm Reached"), (box.x + 560, "Level")]
        for (x, label) in columns:
            self.text(label, x, box.y + 15, self.headFont, yellow, center=False)
        if not scores:
            self.text("No scores yet. Go raid a farm!", cx, box.centery, self.font)
        for i, entry in enumerate(scores):
            y = box.y + 50 + i * 27
            color = yellow if i == self.highlight else hud_text
            difficulty = settings.difficulty_settings.get(entry.get("difficulty"), {}).get("label", "")
            values = ["%d" % (i + 1), entry["name"], "%d" % entry["score"], entry.get("farm", ""), difficulty]
            for (x, _), value in zip(columns, values):
                self.text(value, x, y, self.smallFont, color, center=False)
        self.drawBack(cx)

    def drawAbout(self, cx):
        box = pygame.Rect(cx - 340, 140, 680, 390)
        self.panel(box)
        visible = about_lines[self.scroll:self.scroll + 14]
        y = box.y + 18
        for (line, style) in visible:
            if style == "title": self.text(line, cx, y + 8, self.font, yellow); y += 34
            elif style == "head": self.text(line, cx, y + 6, self.headFont, yellow); y += 28
            else: self.text(line, cx, y + 6, self.smallFont); y += 24
        if self.scroll + 14 < len(about_lines):
            self.text("More below: Down arrow or mouse wheel", cx, box.bottom - 14, self.smallFont, yellow)
        self.drawBack(cx)

    def drawBack(self, cx):
        rect = pygame.Rect(cx - 80, 545, 160, 40)
        pygame.draw.rect(self.screen, (95, 82, 110), rect, border_radius=6)
        self.text("Back", cx, rect.centery, self.font, yellow)
        self.itemRects = [rect]
