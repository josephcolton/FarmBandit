import random
from globals import *

##############
# Crop Types #
##############
class CropType:
    def __init__(self, name, letter, spriteList, value, food, growTime, tall=False):
        self.name = name              # Display name (also the dictionary key)
        self.letter = letter          # Letter used in level maps
        self.spriteSheet = "crops"
        self.spriteList = spriteList  # One sprite per growth stage
        self.value = value            # Points when delivered to the burrow
        self.food = food              # Hunger restored when eaten ripe
        self.growTime = growTime      # Average ms per growth stage
        self.tall = tall              # Two tiles tall: hides the bunny and blocks the farmer's view

    def getIcon(self):
        # The ripe sprite doubles as the icon for the HUD
        return self.spriteList[-1]

cropTypes = {}
cropLetters = {}

def addCropType(name, letter, spriteBase, value, food, growTime=8000, tall=False):
    spriteList = ["%s%d" % (spriteBase, i) for i in range(1, 5)]
    cropType = CropType(name, letter, spriteList, value, food, growTime, tall)
    cropTypes[name] = cropType
    cropLetters[letter] = name

#           name            map  sprite         value food  ms/stage
addCropType("carrot",       "c", "carrot",       10,  30,   7000)
addCropType("sweet potato", "s", "sweetpotato",  15,  40,   9000)
addCropType("radish",       "r", "radish",       10,  25,   6000)
addCropType("beet",         "b", "beet",         15,  30,   8000)
addCropType("turnip",       "t", "turnip",       15,  30,   8000)
addCropType("lettuce",      "l", "lettuce",      20,  35,   8000)
addCropType("cabbage",      "g", "cabbage",      25,  45,  10000)
addCropType("cauliflower",  "f", "cauliflower",  25,  40,  10000)
addCropType("pepper",       "e", "pepper",       20,  20,   9000)
addCropType("watermelon",   "w", "watermelon",   40,  60,  12000)
addCropType("pumpkin",      "p", "pumpkin",      50,  60,  13000)
addCropType("potato",       "u", "potato",       15,  40,   8000)
addCropType("onion",        "o", "onion",        15,  20,   7000)
addCropType("broccoli",     "k", "broccoli",     25,  35,  10000)
addCropType("eggplant",     "a", "eggplant",     25,  30,  10000)
addCropType("strawberry",   "y", "strawberry",   20,  25,   8000)
addCropType("blueberry",    "v", "blueberry",    20,  25,   8000)
addCropType("tomato",       "m", "tomato",       25,  30,  10000)
addCropType("corn",         "n", "corn",         30,  40,  11000, tall=True)
addCropType("pineapple",    "i", "pineapple",    60,  50,  14000)


##############
# Crop Plant #
##############
class Crop:
    def __init__(self, kind, stage=0):
        self.kind = kind
        self.type = cropTypes[kind]
        self.maxStage = len(self.type.spriteList) - 1
        self.stage = min(stage, self.maxStage)
        self.growTimer = self.nextGrowTime()

    def nextGrowTime(self):
        # Every plant grows at a slightly different pace
        return self.type.growTime * random.uniform(0.6, 1.4)

    def hidesBunny(self):
        # Tall crops hide the bunny once they've grown up a bit
        return self.type.tall and self.stage >= 2

    def isRipe(self):
        return self.stage == self.maxStage

    def getValue(self):
        return self.type.value

    def getFood(self):
        # Unripe crops are less filling
        return int(self.type.food * (self.stage + 1) / (self.maxStage + 1))

    def getSheetName(self):
        return self.type.spriteSheet

    def getSpriteName(self):
        return self.type.spriteList[self.stage]

    def update(self, time):
        if self.isRipe(): return
        self.growTimer -= time
        if self.growTimer <= 0:
            self.stage += 1
            self.growTimer = self.nextGrowTime()
