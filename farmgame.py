import pygame
import os
import sys
import copy
import random

##############################
# Import Farm Bandit Modules #
##############################
from globals import *
from crops import cropTypes
import sprites
import world
import animals
import levels
import hud
import menu
import settings
import sound
import display
import gamepad

version = "1.0"

# Keys for moving the bunny
move_keys = {
    pygame.K_UP: "north", pygame.K_w: "north",
    pygame.K_DOWN: "south", pygame.K_s: "south",
    pygame.K_LEFT: "west", pygame.K_a: "west",
    pygame.K_RIGHT: "east", pygame.K_d: "east",
}


class Game:
    def __init__(self, app):
        self.app = app
        self.sm = app.sm
        self.sound = app.sound
        self.screen = self.sm.screen
        self.wm = app.wm
        self.hud = app.hud
        self.difficulty = app.settings["difficulty"]
        self.newGame(app.startFarm)

    def newGame(self, levelIndex=0):
        self.levelIndex = levelIndex
        self.score = 0
        self.lives = settings.difficulty_settings[self.difficulty]["lives"]
        self.startLevel()

    def makeLevel(self, index):
        # A copy of the level adjusted for the chosen difficulty
        level = copy.copy(levels.levels[index])
        d = settings.difficulty_settings[self.difficulty]
        level.dog_step = int(level.dog_step * d["step"])
        level.farmer_step = int(level.farmer_step * d["step"])
        level.rooster_step = int(level.rooster_step * d["step"])
        level.dog_sight = max(2, level.dog_sight + d["sight"])
        level.farmer_sight = max(2, level.farmer_sight + d["sight"])
        level.hunger_rate *= d["hunger"]
        level.night_length = int(level.night_length * d["night"])
        return level

    def startLevel(self):
        self.level = self.makeLevel(self.levelIndex)
        self.fm = world.FarmMap(self.sm, self.level)
        self.rabbit = animals.Rabbit(self.sm, self.fm)
        self.dogs = [animals.Dog(self.sm, self.fm, x, y, self.rabbit) for (x, y) in self.fm.dogSpawns]
        self.farmer = None
        if self.fm.farmerSpawn:
            (x, y) = self.fm.farmerSpawn
            self.farmer = animals.Farmer(self.sm, self.fm, x, y, self.rabbit, self.dogs)
        self.roosters = [animals.Rooster(self.sm, self.fm, x, y, self.rabbit) for (x, y) in self.fm.roosterSpawns]
        self.rats = []
        self.ratTimer = self.level.rat_interval * 0.5
        self.delivered = {kind: 0 for kind in self.level.order}
        self.levelStartScore = self.score
        self.nightLeft = self.level.night_length * 1000   # ms until dawn
        self.warnedDawn = False
        self.timeBonus = 0
        self.popups = []
        self.setState("intro")

    def setState(self, state):
        self.state = state
        self.stateTime = 0

    def movers(self):
        return [self.rabbit] + self.dogs + self.roosters + self.rats + ([self.farmer] if self.farmer else [])

    ##########
    # Popups #
    ##########
    def popup(self, message, color=hud_text, who=None):
        (x, y) = (who or self.rabbit).getPosition()
        self.popups.append([message, x + tile_width // 2, y, 1200, color])

    def updatePopups(self, time):
        for popup in self.popups:
            popup[2] -= time * 0.03   # Float upward
            popup[3] -= time
        self.popups = [p for p in self.popups if p[3] > 0]

    ###############
    # Burrow Logic #
    ###############
    def deposit(self):
        # Store the basket in the burrow
        delivered = False
        for kind in self.rabbit.basket:
            self.score += cropTypes[kind].value
            if kind in self.delivered and self.delivered[kind] < self.level.order[kind]:
                self.delivered[kind] += 1
                delivered = True
                self.popup("%s %d/%d" % (kind, self.delivered[kind], self.level.order[kind]), yellow)
            else:
                self.rabbit.pantry.append(kind)
                self.popup("%s to the pantry" % kind)
        self.rabbit.basket = []
        if self.orderComplete():
            # Bonus points for every second left before dawn
            self.timeBonus = int(self.nightLeft / 1000) * 2
            self.score += self.timeBonus
            self.sound.play("order_filled")
            self.setState("complete")
        else:
            self.sound.play("deliver" if delivered else "store")

    def orderComplete(self):
        for kind in self.level.order:
            if self.delivered[kind] < self.level.order[kind]: return False
        return True

    def caught(self, catcher):
        self.lives -= 1
        lost = len(self.rabbit.basket)
        self.rabbit.basket = []
        self.caughtMessage = "The %s caught you!" % catcher
        if lost: self.caughtMessage += " You dropped %d crop%s." % (lost, "s" if lost > 1 else "")
        self.sound.play("caught")
        self.setState("caught")

    def pecked(self, rooster):
        # The rooster doesn't cost a life, but the bunny drops its basket
        rooster.peck()
        basket = self.rabbit.basket
        self.rabbit.basket = []
        if basket:
            landed = self.fm.dropCrops(basket, self.rabbit.nearestTile())
            self.popup("Peck! Dropped %d crop%s" % (len(basket), "s" if len(basket) > 1 else ""), alert_red, rooster)
            if landed < len(basket): self.popup("Some were trampled", hud_text)
        else:
            self.popup("Peck!", alert_red, rooster)

    def dawn(self):
        self.lives -= 1
        self.rabbit.basket = []
        self.sound.play("dawn")
        self.setState("dawn")

    def respawn(self):
        self.rabbit.respawn()
        for dog in self.dogs:
            dog.reset()
        for rooster in self.roosters:
            rooster.reset()
        if self.farmer: self.farmer.reset()

    def retryLevel(self):
        self.score = self.levelStartScore
        self.startLevel()

    def finish(self):
        # The run is over: record a high score or go back to the title
        if settings.isHighScore(self.score):
            self.playerName = self.app.settings.get("name", "Bunny")
            self.setState("entername")
        else:
            self.app.toTitle()

    ###########
    # Updates #
    ###########
    def handleEvent(self, event):
        if event.type != pygame.KEYDOWN: return
        key = event.key
        button = getattr(event, "button", None)   # set for gamepad presses
        if self.state == "playing":
            if key in move_keys: self.rabbit.action(move_keys[key])
            if key == pygame.K_SPACE: self.rabbit.action("grab")
            if key == pygame.K_e or button == "east": self.rabbit.action("eat")
            elif key in (pygame.K_p, pygame.K_ESCAPE) or button == "start": self.setState("paused")
        elif self.state == "paused":
            if key == pygame.K_q or button == "back": self.app.toTitle()
            elif key in (pygame.K_p, pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE): self.setState("playing")
        elif self.state == "intro":
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self.sound.play("level_start")
                self.setState("playing")
            if key == pygame.K_ESCAPE: self.app.toTitle()
        elif self.state == "complete":
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.levelIndex + 1 < len(levels.levels):
                    self.levelIndex += 1
                    self.app.unlockFarm(self.levelIndex + 1)
                    self.startLevel()
                else:
                    self.sound.play("victory")
                    self.setState("victory")
        elif self.state == "dawn":
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.lives > 0: self.retryLevel()
                else: self.gameOver()
        elif self.state == "gameover":
            if key == pygame.K_r:
                self.lives = settings.difficulty_settings[self.difficulty]["lives"]
                self.retryLevel()
            if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE): self.finish()
        elif self.state == "victory":
            if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE): self.finish()
        elif self.state == "entername":
            self.typeName(event)

    def typeName(self, event):
        fromPad = getattr(event, "gamepad", False)
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
        if event.key in (pygame.K_UP, pygame.K_DOWN):
            # Gamepad (or arrows): change the last letter
            if not self.playerName: self.playerName = "A"
            last = self.playerName[-1].upper()
            index = letters.index(last) if last in letters else 0
            index = (index + (1 if event.key == pygame.K_UP else -1)) % len(letters)
            self.playerName = self.playerName[:-1] + letters[index]
        elif event.key == pygame.K_RIGHT:
            if len(self.playerName) < 12: self.playerName += "A"
        elif event.key == pygame.K_LEFT:
            self.playerName = self.playerName[:-1]
        elif event.key == pygame.K_RETURN or (fromPad and event.key == pygame.K_SPACE):
            name = self.playerName.strip() or "Bunny"
            self.app.settings["name"] = name
            settings.saveSettings(self.app.settings)
            rank = settings.addHighScore(name, self.score, self.level.name, self.difficulty)
            self.sound.play("menu_select")
            self.app.toTitle("highscores", highlight=rank)
        elif event.key == pygame.K_BACKSPACE:
            self.playerName = self.playerName[:-1]
        elif event.key == pygame.K_ESCAPE and not fromPad:
            self.app.toTitle()
        elif event.unicode and event.unicode.isprintable() and len(self.playerName) < 12:
            self.playerName += event.unicode

    def gameOver(self):
        self.sound.play("game_over")
        self.setState("gameover")

    def heldMove(self):
        pressed = pygame.key.get_pressed()
        for key in move_keys:
            if pressed[key]: return move_keys[key]
        return self.app.gamepad.heldDirection()

    def playSounds(self):
        for mover in self.movers():
            for name in mover.sounds:
                self.sound.play(name)
            mover.sounds = []

    def update(self, time):
        self.stateTime += time
        self.updatePopups(time)
        if self.state == "caught":
            if self.stateTime >= caught_pause:
                if self.lives <= 0: self.gameOver()
                else:
                    self.respawn()
                    self.setState("playing")
            return
        if self.state != "playing": return

        # The night
        self.nightLeft -= time
        if not self.warnedDawn and self.nightLeft < 30000:
            self.warnedDawn = True
            self.popup("The sky is getting light!", yellow)
        if self.nightLeft <= 0:
            self.nightLeft = 0
            self.dawn()
            return

        self.fm.update(time)
        landed = self.rabbit.update(time, self.heldMove())
        for message in self.rabbit.messages:
            self.popup(message)
        self.rabbit.messages = []
        if landed and self.rabbit.isSafe() and self.rabbit.basket:
            self.deposit()
            if self.state != "playing":
                self.playSounds()
                return
        for dog in self.dogs:
            dog.update(time)
        for rooster in self.roosters:
            rooster.update(time)
        self.updateRats(time)
        if self.farmer:
            self.farmer.update(time)
            for message in self.farmer.messages:
                self.popup(message, yellow if message.startswith("Fweeet") else hud_text, self.farmer)
            self.farmer.messages = []
        self.checkCatches()
        self.playSounds()

    def updateRats(self, time):
        if self.level.rat_interval:
            self.ratTimer -= time
            if self.ratTimer <= 0:
                self.ratTimer = self.level.rat_interval * random.uniform(0.6, 1.4)
                start = self.fm.randomEdgeTile()
                if start and len(self.rats) < max_rats:
                    self.rats.append(animals.Rat(self.sm, self.fm, *start))
        for rat in self.rats:
            rat.update(time)
            for message in rat.messages:
                self.popup(message, alert_red, rat)
            rat.messages = []
        self.rats = [rat for rat in self.rats if not rat.gone]

    def touching(self, a, b):
        (ax, ay) = a.getPosition()
        (bx, by) = b.getPosition()
        return abs(ax - bx) < catch_distance and abs(ay - by) < catch_distance

    def checkCatches(self):
        if self.rabbit.isSafe(): return
        for rooster in self.roosters:
            if rooster.canPeck() and self.touching(rooster, self.rabbit):
                self.pecked(rooster)
        if self.rabbit.invulnerable > 0: return
        chasers = [(dog, "dog") for dog in self.dogs]
        if self.farmer: chasers.append((self.farmer, "farmer"))
        for (chaser, name) in chasers:
            if self.touching(chaser, self.rabbit):
                self.caught(name)
                break

    ###########
    # Drawing #
    ###########
    def draw(self):
        self.wm.draw()
        self.fm.draw()
        # Night falls on the farm, but the animals stay easy to see
        self.hud.drawNight(self.nightLeft, self.level.night_length * 1000)
        # Draw animals top to bottom so the closer one overlaps
        for animal in sorted(self.movers(), key=lambda a: a.getPosition()[1]):
            animal.draw()
        for (message, x, y, timeLeft, color) in self.popups:
            self.hud.text(message, x, y, self.hud.smallFont, color, center=True, outline=True)
        self.hud.draw(self)
        self.drawStateOverlay()

    def drawStateOverlay(self):
        if self.state == "intro":
            order = ", ".join("%d %s" % (n, kind) for (kind, n) in self.level.order.items())
            minutes = self.level.night_length // 60
            seconds = self.level.night_length % 60
            self.hud.drawOverlay([
                "Level %d: %s" % (self.levelIndex + 1, self.level.name),
                self.level.intro,
                "Order: %s" % order,
                "Dawn comes in %d:%02d" % (minutes, seconds),
                "",
                "Arrows / WASD: hop     Space: pick a ripe crop",
                "E: eat (ground, basket, or pantry in the burrow)",
                "Stay out of the farmer's sight, he whistles for the dogs!" if self.farmer else "Hop home to the burrow to store what you carry.",
                "",
                "Press Enter to start",
            ])
        if self.state == "paused":
            self.hud.drawOverlay(["Paused", "P, Esc, Enter, B, Start, L or R: keep playing", "Q or Select: quit to the title screen"])
        if self.state == "caught":
            self.hud.drawOverlay(["Caught!", self.caughtMessage,
                                  "Lives left: %d" % self.lives])
        if self.state == "dawn":
            lines = ["Dawn!", "The sun is up and the farm is waking.",
                     "The order wasn't filled in time.", "Lives left: %d" % self.lives, ""]
            lines.append("Press Enter to try the night again" if self.lives > 0 else "Press Enter")
            self.hud.drawOverlay(lines)
        if self.state == "complete":
            self.hud.drawOverlay(["Order Filled!",
                                  "%s is a little emptier now." % self.level.name,
                                  "Time bonus: +%d" % self.timeBonus,
                                  "Score: %d" % self.score, "",
                                  "Press Enter for the next farm"])
        if self.state == "gameover":
            self.hud.drawOverlay(["Game Over", "The farm was too much for one bunny.",
                                  "Score: %d" % self.score, "",
                                  "R or Y: try this farm again",
                                  "Enter or A: finish"])
        if self.state == "victory":
            self.hud.drawOverlay(["You Win!", "Every order filled. The burrow is full!",
                                  "Final score: %d" % self.score, "",
                                  "Press Enter"])
        if self.state == "entername":
            cursor = "_" if int(self.stateTime / 400) % 2 == 0 else " "
            self.hud.drawOverlay(["New High Score!", "Score: %d" % self.score, "",
                                  "Type your name:", self.playerName + cursor, "",
                                  "Enter to save",
                                  "Gamepad: Up/Down letter, Right add, Left erase, A save"])


class App:
    """Owns the window, sound, and settings, and switches between the title and the game."""
    def __init__(self):
        settings.migrateOldSaves()
        self.settings = settings.loadSettings()
        self.startFarm = 0
        self.display = display.Display(self.settings["display"])
        try:
            pygame.display.set_icon(pygame.image.load("sprites/icon.png"))
        except (pygame.error, FileNotFoundError):
            pass
        self.gamepad = gamepad.Gamepad()
        self.version = version
        self.sm = sprites.SpriteManager(self.display.canvas)
        self.sm.loadData("sprites.data")
        self.wm = world.WorldMap(self.sm)
        self.hud = hud.Hud(self.sm)
        self.sound = sound.SoundManager(self.settings["sound"], self.settings["music"])
        self.title = menu.TitleScreen(self)
        self.game = None
        self.running = True
        self.toTitle()

    def startGame(self, farm=0):
        self.startFarm = farm
        self.game = Game(self)
        self.scene = self.game
        self.sound.playMusic("night")

    def toTitle(self, page="main", highlight=None):
        self.game = None
        self.title.open(page, highlight)
        self.scene = self.title
        self.sound.playMusic("title")

    def applySettings(self):
        self.sound.setVolumes(self.settings["sound"], self.settings["music"])
        if self.settings["display"] != self.display.mode:
            self.display.setMode(self.settings["display"])
        settings.saveSettings(self.settings)

    def unlockFarm(self, count):
        if count > self.settings["unlocked"]:
            self.settings["unlocked"] = min(count, len(levels.levels))
            settings.saveSettings(self.settings)

    def quit(self):
        self.running = False

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            time = clock.tick(max_fps)  # ms since the last frame
            time = min(time, 100)       # Don't jump ahead after a stall
            events = pygame.event.get()
            events += self.gamepad.update(time)
            for event in events:
                if event.type in gamepad.events:
                    event = self.gamepad.handleEvent(event)
                    if event is None: continue
                if event.type == pygame.QUIT:
                    self.running = False
                elif hasattr(event, "pos"):
                    # Mouse positions are in window pixels; the scenes want canvas pixels
                    pos = self.display.toCanvas(event.pos)
                    self.scene.handleEvent(pygame.event.Event(event.type, {**event.__dict__, "pos": pos}))
                else:
                    self.scene.handleEvent(event)
            self.scene.update(time)
            self.scene.draw()
            self.display.present()


def resourceDir():
    # Where the art, sound, and data files are: next to this file, or inside the PyInstaller build
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def main():
    # Run from the resource folder so sprites load from anywhere
    os.chdir(resourceDir())
    pygame.init()
    App().run()
    # Quit Pygame
    pygame.quit()


if __name__ == "__main__":
    main()
