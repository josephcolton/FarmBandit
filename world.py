import random
from collections import deque
import pygame
from globals import *
from crops import *

# Ground tiles nothing can walk through (they also block the farmer's view)
blocked_tiles = "TC=^B"
burrow_tiles = "H"
hiding_tiles = ","    # tall grass


class WorldMap:
    def __init__(self, sm):
        self.sm = sm
        self.worldmap = pygame.Surface((screen_width, screen_height))
        self.createMap()

    def createMap(self):
        self.worldmap.fill(hud_background)
        self.sm.drawSprite("floors", "nwfloor", 0, 0, surface=self.worldmap)
        # Draw border
        for i in range(map_width):
            self.sm.drawSprite("floors", "nfloor", i*tile_width+farm_offset_x, 0, surface=self.worldmap)
            self.sm.drawSprite("floors", "sfloor", i*tile_width+farm_offset_x, tile_height*map_height+farm_offset_y, surface=self.worldmap)
        self.sm.drawSprite("floors", "nefloor", tile_width*map_width+farm_offset_x, 0, surface=self.worldmap)
        self.sm.drawSprite("floors", "swfloor", 0, tile_height*map_height+farm_offset_y, surface=self.worldmap)
        for i in range(map_height):
            self.sm.drawSprite("floors", "wfloor", 0, i*tile_height+farm_offset_y, surface=self.worldmap)
            self.sm.drawSprite("floors", "efloor", tile_width*map_width+farm_offset_x, i*tile_height+farm_offset_y, surface=self.worldmap)
        self.sm.drawSprite("floors", "sefloor", tile_width*map_width+farm_offset_x, tile_height*map_height+farm_offset_y, surface=self.worldmap)

    def draw(self):
        pos = self.worldmap.get_rect()
        self.sm.screen.blit(self.worldmap, pos)


class FarmMap:
    def __init__(self, sm, level):
        self.sm = sm
        self.level = level
        self.offset_x = farm_offset_x
        self.offset_y = farm_offset_y
        self.farm_width = tile_width * map_width
        self.farm_height = tile_height * map_height
        # Crops to harvest
        self.cropMap = {}
        self.regrowMap = {}  # (x, y) -> [crop name, ms until replanted]
        self.burrow = None
        self.dogSpawns = []
        self.farmerSpawn = None
        self.roosterSpawns = []
        self.loadLevel()
        self.farmmap = pygame.Surface((self.farm_width, self.farm_height))
        self.createMap()

    def loadLevel(self):
        layout = self.level.layout
        if len(layout) != map_height:
            raise ValueError("Level '%s' has %d rows, expected %d" % (self.level.name, len(layout), map_height))
        self.ground = []
        for y, row in enumerate(layout):
            if len(row) != map_width:
                raise ValueError("Level '%s' row %d is %d wide, expected %d" % (self.level.name, y, len(row), map_width))
            groundRow = []
            for x, char in enumerate(row):
                if char in cropLetters:
                    self.cropMap[(x, y)] = Crop(cropLetters[char], self.randomStartStage())
                    char = ":"
                elif char == "D":
                    self.dogSpawns.append((x, y))
                    char = "."
                elif char == "F":
                    self.farmerSpawn = (x, y)
                    char = "."
                elif char == "R":
                    self.roosterSpawns.append((x, y))
                    char = "."
                elif char in burrow_tiles:
                    self.burrow = (x, y)
                groundRow.append(char)
            self.ground.append(groundRow)
        if self.burrow is None:
            raise ValueError("Level '%s' has no burrow (H)" % self.level.name)

    def randomStartStage(self):
        # Start the farm with a mix of sprouts and ripe crops
        return random.choice([0, 1, 1, 2, 2, 3, 3, 3])

    ###############
    # Map Queries #
    ###############
    def getGround(self, map_x, map_y):
        if 0 <= map_x < map_width and 0 <= map_y < map_height:
            return self.ground[map_y][map_x]
        return None

    def hidesBunny(self, map_x, map_y):
        # Tall grass and grown corn hide the bunny from the farmer and dogs
        if self.getGround(map_x, map_y) in hiding_tiles: return True
        crop = self.cropAt(map_x, map_y)
        return crop is not None and crop.hidesBunny()

    def isBurrow(self, map_x, map_y):
        return (map_x, map_y) == self.burrow

    def isWalkable(self, map_x, map_y, dog=False):
        tile = self.getGround(map_x, map_y)
        if tile is None or tile in blocked_tiles: return False
        # Dogs are too big to fit in the burrow
        if dog and tile in burrow_tiles: return False
        return True

    def hasLineOfSight(self, start, goal):
        # Walk a straight line between tiles; fences, rocks, cliffs, hay, and corn block the view
        (x0, y0) = start
        (x1, y1) = goal
        steps = max(abs(x1 - x0), abs(y1 - y0))
        for i in range(1, steps):
            x = round(x0 + (x1 - x0) * i / steps)
            y = round(y0 + (y1 - y0) * i / steps)
            if self.getGround(x, y) in blocked_tiles: return False
            crop = self.cropAt(x, y)
            if crop is not None and crop.hidesBunny(): return False
        return True

    def nextStepToward(self, start, goal):
        # Breadth first search for a dog, returns the first (dx, dy) step or None
        if start == goal: return None
        cameFrom = {start: None}
        queue = deque([start])
        while queue:
            current = queue.popleft()
            if current == goal: break
            (cx, cy) = current
            for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nxt = (cx + dx, cy + dy)
                if nxt in cameFrom: continue
                if not self.isWalkable(nxt[0], nxt[1], dog=True): continue
                cameFrom[nxt] = current
                queue.append(nxt)
        if goal not in cameFrom: return None
        # Walk back to find the first step
        step = goal
        while cameFrom[step] != start:
            step = cameFrom[step]
        return (step[0] - start[0], step[1] - start[1])

    #########
    # Crops #
    #########
    def cropAt(self, map_x, map_y):
        return self.cropMap.get((map_x, map_y))

    def harvest(self, map_x, map_y):
        # Remove the crop; the farmer replants the spot later
        index = (map_x, map_y)
        crop = self.cropMap.pop(index, None)
        if crop:
            self.regrowMap[index] = [crop.kind, self.level.regrow_time]
        return crop

    #################
    # Drawing Setup #
    #################
    def createMap(self):
        self.farmmap.fill(green)
        for y in range(map_height):
            for x in range(map_width):
                self.drawGround(x, y)

    def drawGround(self, x, y):
        tile = self.ground[y][x]
        px = x * tile_width
        py = y * tile_height
        draw = lambda sheet, sprite: self.sm.drawSprite(sheet, sprite, px, py, surface=self.farmmap)
        if tile == ":": draw("cliffs", "dirt")
        if tile == "T": draw("cliffs", "clifftop")
        if tile == "C": draw("cliffs", "dirt")
        if tile == "H":
            draw("cliffs", "dirt")
            draw("cliffs", "cave")
        if tile == "^": draw("cliffs", "rocks")
        if tile == "=": draw("fence", self.fenceSprite(x, y))
        if tile == ",": draw("tallgrass", self.tallGrassSprite(x, y))
        if tile == "B":
            # Hay bales are two tiles tall and lean up over the tile above
            self.sm.drawSprite("wheat", "haybale", px, py - tile_height, surface=self.farmmap)

    def tallGrassSprite(self, x, y):
        # Pick the edge or middle piece of a tall grass patch
        def grass(gx, gy): return self.getGround(gx, gy) == ","
        row = "n" if not grass(x, y - 1) else "s" if not grass(x, y + 1) else ""
        column = "w" if not grass(x - 1, y) else "e" if not grass(x + 1, y) else ""
        return (row + column) or "c"
    def fenceSprite(self, x, y):
        # Pick a fence piece based on the neighboring fences
        left = self.getGround(x - 1, y) == "="
        right = self.getGround(x + 1, y) == "="
        if left and right: return "fence_h"
        if right: return "fence_left"
        if left: return "fence_right"
        return "fence_v"

    def replant(self, map_x, map_y):
        # The farmer plants a fresh sprout in a picked spot
        index = (map_x, map_y)
        if index not in self.regrowMap: return False
        kind = self.regrowMap.pop(index)[0]
        self.cropMap[index] = Crop(kind, 0)
        return True

    def nibble(self, map_x, map_y):
        # A rat eats a crop back down to a sprout
        crop = self.cropAt(map_x, map_y)
        if crop is None or crop.stage == 0: return False
        crop.stage = 0
        crop.growTimer = crop.nextGrowTime()
        return True

    def dropCrops(self, kinds, near):
        # Spill crops into the nearest empty spots; returns how many landed
        (nx, ny) = near
        spots = [i for i in self.regrowMap if abs(i[0] - nx) + abs(i[1] - ny) <= 4]
        spots.sort(key=lambda i: abs(i[0] - nx) + abs(i[1] - ny))
        landed = 0
        for kind in kinds:
            if not spots: break
            index = spots.pop(0)
            del self.regrowMap[index]
            crop = Crop(kind)
            crop.stage = crop.maxStage
            self.cropMap[index] = crop
            landed += 1
        return landed

    def randomEdgeTile(self):
        # A walkable spot on the edge of the farm for a rat to sneak in from
        edges = []
        for x in range(map_width):
            edges += [(x, 0), (x, map_height - 1)]
        for y in range(1, map_height - 1):
            edges += [(0, y), (map_width - 1, y)]
        edges = [e for e in edges if self.isWalkable(e[0], e[1], dog=True)]
        return random.choice(edges) if edges else None

    def drawCrops(self):
        for index in self.regrowMap:
            (crop_x, crop_y) = index
            x = (crop_x * tile_width) + farm_offset_x
            y = (crop_y * tile_height) + farm_offset_y
            self.sm.drawSprite("crops", "hole", x, y)
        # Top to bottom, so tall crops overlap the row behind them
        for index in sorted(self.cropMap, key=lambda i: i[1]):
            (crop_x, crop_y) = index
            sheetName = self.cropMap[index].getSheetName()
            spriteName = self.cropMap[index].getSpriteName()
            height = self.sm.getSprite(sheetName, spriteName).get_height()
            x = (crop_x * tile_width) + farm_offset_x
            y = (crop_y * tile_height) + farm_offset_y - (height - tile_height)
            self.sm.drawSprite(sheetName, spriteName, x, y)

    def update(self, time):
        # Grow the crops
        for index in self.cropMap:
            self.cropMap[index].update(time)
        # Replant picked spots
        for index in list(self.regrowMap):
            self.regrowMap[index][1] -= time
            if self.regrowMap[index][1] <= 0:
                self.replant(*index)

    def draw(self):
        # Draw Farm Map
        pos = self.farmmap.get_rect()
        pos.x = self.offset_x
        pos.y = self.offset_y
        self.sm.screen.blit(self.farmmap, pos)
        # Draw Crops
        self.drawCrops()
