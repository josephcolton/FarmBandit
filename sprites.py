import os
import pygame
from globals import *

class SpriteManager:
    def __init__(self, screen):
        self.screen = screen
        self.sheets = {}
        self.sprites = {}

    def loadSheet(self, name, filename):
        fullname = os.path.join("sprites", filename)
        sheet = pygame.image.load(fullname).convert_alpha()
        self.sheets[name] = sheet

    def setSprite(self, sheetName, spriteName, x, y, width, height):
        # Make sure we have the sheet sprite dictionary
        if not sheetName in self.sprites:
            self.sprites[sheetName] = {}
        # Create sprite object
        rect = pygame.Rect(x, y, width, height)
        sheet = self.sheets[sheetName]
        sprite = sheet.subsurface(rect)
        # Save the sprite object
        self.sprites[sheetName][spriteName] = sprite

    def mirrorSprite(self, sheetName, spriteName, newName):
        # Left-right flipped copy, for animals drawn facing only one way
        sprite = self.sprites[sheetName][spriteName]
        self.sprites[sheetName][newName] = pygame.transform.flip(sprite, True, False)

    def createColorSprite(self, spriteName, color):
        sheetName = "color"
        # Make sure we have the sheet sprite dictionary
        if not sheetName in self.sprites:
            self.sprites[sheetName] = {}
        # Create sprite
        sprite = pygame.Surface((tile_width, tile_height))
        sprite.fill(color)
        self.sprites[sheetName][spriteName] = sprite

    def getSprite(self, sheetName, spriteName):
        sprite = self.sprites[sheetName][spriteName]
        return sprite

    def getSpriteList(self, sheetName):
        spriteList = list(self.sprites[sheetName].keys())
        return spriteList

    def loadData(self, filename):
        fh = open(filename, "r")
        for line in fh:
            if not line: break
            if line[0] == '#': continue
            line = line.strip()
            parts = line.split(":")
            if len(parts) < 3: continue
            # Handle sheet data
            if (parts[0] == "sheet"):
                sheetName = parts[1]
                sheetFile = parts[2]
                self.loadSheet(sheetName, sheetFile)
            # Handle sheet sprites
            if (parts[0] == "sprite"):
                sheetName = parts[1]
                spriteName = parts[2]
                x = int(parts[3])
                y = int(parts[4])
                width = int(parts[5])
                height = int(parts[6])
                self.setSprite(sheetName, spriteName, x, y, width, height)
            # Handle mirrored sprites
            if (parts[0] == "mirror"):
                self.mirrorSprite(parts[1], parts[2], parts[3])
            # Handle color tiles
            if (parts[0] == "color"):
                sheetName = "color"
                spriteName = parts[1]
                color = (int(parts[2]), int(parts[3]), int(parts[4]))
                self.createColorSprite(spriteName, color)
        fh.close()

    #####################
    # Drawing Functions #
    #####################
    def drawSheet(self, name, x=0, y=0):
        image = self.sprites[name]
        pos = image.get_rect()
        pos.x = x
        pos.y = y
        self.screen.blit(image, pos)

    def drawSprite(self, sheetName, spriteName, x, y, surface=None):
        image = self.getSprite(sheetName, spriteName)
        pos = image.get_rect()
        pos.x = x
        pos.y = y
        if surface: surface.blit(image, pos)
        else: self.screen.blit(image, pos)

