import random
import pygame
import fonts
from globals import *
from crops import cropTypes

directions = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}


class Mover:
    """Something that hops from tile to tile on the farm grid."""
    def __init__(self, sm, fm, map_x, map_y):
        self.sm = sm
        self.fm = fm
        self.sounds = []     # sound names for the game to play
        self.placeAt(map_x, map_y)

    def setFacing(self, dx, dy):
        for name in directions:
            if directions[name] == (dx, dy): self.facing = name

    def placeAt(self, map_x, map_y):
        self.map_x = map_x
        self.map_y = map_y
        self.new_map_x = map_x
        self.new_map_y = map_y
        self.moving = False
        self.moveTime = 0
        self.moveDuration = 1

    def startMove(self, dx, dy, duration):
        self.new_map_x = self.map_x + dx
        self.new_map_y = self.map_y + dy
        self.moving = True
        self.moveTime = 0
        self.moveDuration = duration

    def moveProgress(self):
        # 0.0 at the start of a move, 1.0 at the end
        if not self.moving: return 0.0
        return min(self.moveTime / self.moveDuration, 1.0)

    def updateMove(self, time):
        # Returns True on the frame the move finishes
        if not self.moving: return False
        self.moveTime += time
        if self.moveTime >= self.moveDuration:
            self.map_x = self.new_map_x
            self.map_y = self.new_map_y
            self.moving = False
            return True
        return False

    def getPosition(self):
        # Screen pixel position, part way between tiles while moving
        t = self.moveProgress()
        x = (self.map_x + (self.new_map_x - self.map_x) * t) * tile_width + farm_offset_x
        y = (self.map_y + (self.new_map_y - self.map_y) * t) * tile_height + farm_offset_y
        return (x, y)

    def nearestTile(self):
        if self.moveProgress() >= 0.5: return (self.new_map_x, self.new_map_y)
        return (self.map_x, self.map_y)


class Dog(Mover):
    def __init__(self, sm, fm, map_x, map_y, target):
        super().__init__(sm, fm, map_x, map_y)
        self.target = target
        self.home = (map_x, map_y)
        level = fm.level
        self.stepTime = level.dog_step
        self.sight = level.dog_sight
        self.chase = level.dog_chase
        # Animal Sprite (48x48, drawn centered on the tile with feet at the bottom)
        self.spriteName = "s_walk1"
        self.animTime = 0
        self.reset()

    def reset(self):
        self.placeAt(*self.home)
        self.lastStep = (0, 0)
        self.facing = "south"
        self.waitTime = random.randint(500, 1500)
        self.alertTime = 0
        self.chasing = False
        self.barkTime = 0

    def bark(self):
        if self.barkTime > 0: return
        self.sounds.append("bark")
        self.barkTime = random.randint(3000, 6000)

    def alert(self, duration):
        # The farmer whistled: run straight for the bunny for a while
        self.alertTime = duration
        self.waitTime = min(self.waitTime, 100)
        self.bark()

    def canSeeTarget(self):
        (tx, ty) = self.target.nearestTile()
        if self.fm.isBurrow(tx, ty): return False
        distance = abs(tx - self.map_x) + abs(ty - self.map_y)
        # A hidden bunny can only be sniffed out from right next to it
        if self.target.isHidden(): return distance <= 1
        if self.alertTime > 0: return True
        return distance <= self.sight

    def chooseStep(self):
        # Returns (dx, dy, wait ms after the step)
        chase = 1.0 if self.alertTime > 0 else self.chase
        if self.canSeeTarget() and random.random() < chase:
            goal = (self.target.new_map_x, self.target.new_map_y)
            step = self.fm.nextStepToward((self.map_x, self.map_y), goal)
            if step:
                if not self.chasing: self.bark()
                self.chasing = True
                return step + (random.randint(0, 80),)
        self.chasing = False
        return self.wander() + (random.randint(200, 900),)

    def wander(self):
        options = []
        for (dx, dy) in directions.values():
            if self.fm.isWalkable(self.map_x + dx, self.map_y + dy, dog=True):
                options.append((dx, dy))
        if not options: return (0, 0)
        # Prefer to keep walking the same way
        if self.lastStep in options and random.random() < 0.6:
            return self.lastStep
        return random.choice(options)

    def update(self, time):
        self.animTime += time
        if self.alertTime > 0: self.alertTime -= time
        if self.barkTime > 0: self.barkTime -= time
        if self.moving:
            self.updateMove(time)
        else:
            self.waitTime -= time
            if self.waitTime <= 0:
                (dx, dy, wait) = self.chooseStep()
                self.waitTime = wait
                if (dx, dy) != (0, 0):
                    self.lastStep = (dx, dy)
                    self.setFacing(dx, dy)
                    self.startMove(dx, dy, self.stepTime)
        # Walk while moving, sniff the ground while waiting
        prefix = self.facing[0]
        if self.moving:
            frame = int(self.moveProgress() * 4) % 4 + 1
            self.spriteName = "%s_walk%d" % (prefix, frame)
        else:
            frame = int(self.animTime / 250) % 4 + 1
            self.spriteName = "%s_sniff%d" % (prefix, frame) if self.waitTime > 400 else "%s_walk1" % prefix

    def draw(self):
        (x, y) = self.getPosition()
        self.sm.drawSprite("dog", self.spriteName, x - 8, y - 14)


class Farmer(Mover):
    """Patrols the fields, replants picked spots, and whistles for the dogs."""
    def __init__(self, sm, fm, map_x, map_y, target, dogs):
        super().__init__(sm, fm, map_x, map_y)
        self.target = target
        self.dogs = dogs
        self.home = (map_x, map_y)
        level = fm.level
        self.stepTime = level.farmer_step
        self.sight = level.farmer_sight
        self.messages = []   # popup text for the game to show
        self.font = fonts.getFont(20, bold=True)
        self.reset()

    def reset(self):
        self.placeAt(*self.home)
        self.facing = "south"
        self.goal = None
        self.chasing = False
        self.chaseTime = 0       # ms left to chase after losing sight of the bunny
        self.whistleTime = 0     # ms until he can whistle again
        self.alarmTime = 0       # ms to show the "!" over his head
        self.waitTime = random.randint(1000, 2000)
        self.animTime = 0

    ##########
    # Seeing #
    ##########
    def canSeeTarget(self):
        (tx, ty) = self.target.nearestTile()
        if self.fm.isBurrow(tx, ty): return False
        dx = tx - self.map_x
        dy = ty - self.map_y
        distance = abs(dx) + abs(dy)
        if distance > self.sight: return False
        # He hears the bunny right next to him
        if distance <= 1: return True
        if self.target.isHidden(): return False
        # Otherwise the bunny has to be in front of him
        (fx, fy) = directions[self.facing]
        forward = dx * fx + dy * fy
        sideways = abs(dx * fy - dy * fx)
        if forward <= 0 or sideways > forward: return False
        return self.fm.hasLineOfSight((self.map_x, self.map_y), (tx, ty))

    def whistle(self):
        self.alarmTime = 1200
        if self.whistleTime > 0: return
        self.whistleTime = farmer_whistle_cooldown
        self.messages.append("Fweeet! Get that rabbit!")
        self.sounds.append("whistle")
        for dog in self.dogs:
            dog.alert(farmer_alert_time)

    ##############
    # Moving     #
    ##############
    def pickPatrolGoal(self):
        # Check on picked spots first, otherwise walk the rows
        holes = list(self.fm.regrowMap)
        if holes and random.random() < 0.4: return random.choice(holes)
        spots = list(self.fm.cropMap)
        if spots: return random.choice(spots)
        return self.home

    def chooseStep(self):
        # Returns (dx, dy, wait ms after the step)
        if self.chasing:
            goal = (self.target.new_map_x, self.target.new_map_y)
            step = self.fm.nextStepToward((self.map_x, self.map_y), goal)
            if step: return step + (0,)
            return (0, 0, 300)
        here = (self.map_x, self.map_y)
        if self.goal is None or self.goal == here:
            if self.goal == here and self.fm.replant(*here):
                self.messages.append("Replanted")
                self.goal = None
                return (0, 0, 1200)
            self.goal = self.pickPatrolGoal()
            # Stop and look around now and then
            self.facing = random.choice(list(directions))
            return (0, 0, random.randint(800, 1800))
        step = self.fm.nextStepToward(here, self.goal)
        if step is None:
            self.goal = None
            return (0, 0, 500)
        return step + (random.randint(0, 200),)

    def update(self, time):
        self.animTime += time
        if self.whistleTime > 0: self.whistleTime -= time
        if self.alarmTime > 0: self.alarmTime -= time
        # Look for the bunny
        if self.canSeeTarget():
            if not self.chasing: self.waitTime = min(self.waitTime, 200)
            self.chasing = True
            self.chaseTime = farmer_chase_time
            self.whistle()
        elif self.chasing:
            self.chaseTime -= time
            if self.chaseTime <= 0 or self.target.isSafe():
                self.chasing = False
                self.goal = None
        # Walk
        if self.moving:
            self.updateMove(time)
        else:
            self.waitTime -= time
            if self.waitTime <= 0:
                (dx, dy, wait) = self.chooseStep()
                self.waitTime = wait
                if (dx, dy) != (0, 0):
                    self.setFacing(dx, dy)
                    self.startMove(dx, dy, self.stepTime)

    def draw(self):
        (x, y) = self.getPosition()
        prefix = self.facing[0]
        frame = int(self.animTime / 90) % 8 + 1 if self.moving else 0
        # 64x64 frame, centered on the tile with his feet at the bottom
        self.sm.drawSprite("farmer", "%s_walk%d" % (prefix, frame), x - 16, y - 30)
        if self.alarmTime > 0:
            center = (x + tile_width // 2, y - 42)
            pygame.draw.circle(self.sm.screen, white, center, 11)
            pygame.draw.circle(self.sm.screen, red, center, 11, 2)
            text = self.font.render("!", True, red)
            self.sm.screen.blit(text, text.get_rect(center=center))


class Rooster(Mover):
    """Guards its patch. Chases a nearby bunny and pecks it until it drops its basket."""
    def __init__(self, sm, fm, map_x, map_y, target):
        super().__init__(sm, fm, map_x, map_y)
        self.target = target
        self.home = (map_x, map_y)
        self.stepTime = fm.level.rooster_step
        self.reset()

    def reset(self):
        self.placeAt(*self.home)
        self.facing = "south"
        self.chasing = False
        self.calmTime = 0      # ms before it will chase again after a peck
        self.waitTime = random.randint(500, 1500)
        self.animTime = 0

    def distanceToTarget(self):
        (tx, ty) = self.target.nearestTile()
        return abs(tx - self.map_x) + abs(ty - self.map_y)

    def canPeck(self):
        return self.chasing and self.calmTime <= 0

    def peck(self):
        # Caught the bunny: squawk, then calm down for a while
        self.sounds.append("squawk")
        self.chasing = False
        self.calmTime = rooster_calm_time
        self.waitTime = 600

    def chooseStep(self):
        # Returns (dx, dy, wait ms after the step)
        here = (self.map_x, self.map_y)
        if self.chasing:
            step = self.fm.nextStepToward(here, (self.target.new_map_x, self.target.new_map_y))
            if step: return step + (0,)
        # Strut around near home, pecking at the ground
        if abs(self.map_x - self.home[0]) + abs(self.map_y - self.home[1]) >= rooster_range:
            step = self.fm.nextStepToward(here, self.home)
            if step: return step + (random.randint(300, 900),)
        options = [d for d in directions.values() if self.fm.isWalkable(self.map_x + d[0], self.map_y + d[1], dog=True)]
        if options and random.random() < 0.6:
            return random.choice(options) + (random.randint(600, 1800),)
        return (0, 0, random.randint(600, 1500))

    def update(self, time):
        self.animTime += time
        if self.calmTime > 0: self.calmTime -= time
        # Notice a bunny within two tiles, give up when it gets away
        distance = self.distanceToTarget()
        if not self.chasing and self.calmTime <= 0 and not self.target.isSafe() and distance <= rooster_notice:
            self.chasing = True
            self.sounds.append("cluck")
            self.waitTime = min(self.waitTime, 50)
        elif self.chasing and (distance > rooster_notice + 1 or self.target.isSafe()):
            self.chasing = False
        if self.moving:
            self.updateMove(time)
        else:
            self.waitTime -= time
            if self.waitTime <= 0:
                (dx, dy, wait) = self.chooseStep()
                self.waitTime = wait
                if (dx, dy) != (0, 0):
                    self.setFacing(dx, dy)
                    self.startMove(dx, dy, self.stepTime)

    def draw(self):
        (x, y) = self.getPosition()
        prefix = self.facing[0]
        if self.moving:
            frame = int(self.moveProgress() * 4) % 4 + 1
            self.sm.drawSprite("rooster_walk", "%s_walk%d" % (prefix, frame), x, y - 6)
        elif self.waitTime > 300:
            frame = int(self.animTime / 180) % 4 + 1
            self.sm.drawSprite("rooster_eat", "%s_eat%d" % (prefix, frame), x, y - 6)
        else:
            self.sm.drawSprite("rooster_walk", "%s_walk1" % prefix, x, y - 6)


class Rat(Mover):
    """Sneaks in from the edge of the farm, nibbles a crop back to a sprout, and runs off.
    The farmer and dogs never notice rats."""
    def __init__(self, sm, fm, map_x, map_y):
        super().__init__(sm, fm, map_x, map_y)
        self.exit = (map_x, map_y)
        self.stepTime = fm.level.rat_step
        self.state = "seek"       # seek, eat, flee, then gone
        self.goal = self.pickCrop()
        self.facing = "south"
        self.eatTime = 0
        self.searchTime = 20000   # ms before it gives up and goes home
        self.animTime = 0
        self.gone = False
        self.messages = []

    def pickCrop(self):
        # Head for one of the closest ripe crops
        crops = [i for i, c in self.fm.cropMap.items() if c.isRipe()]
        if not crops: crops = [i for i, c in self.fm.cropMap.items() if c.stage > 0]
        if not crops: return None
        crops.sort(key=lambda i: abs(i[0] - self.map_x) + abs(i[1] - self.map_y))
        return random.choice(crops[:3])

    def update(self, time):
        self.animTime += time
        self.searchTime -= time
        if self.moving:
            self.updateMove(time)
            return
        here = (self.map_x, self.map_y)
        if self.state == "seek":
            if self.searchTime <= 0: self.goal = None
            elif self.goal not in self.fm.cropMap: self.goal = self.pickCrop()
            if self.goal is None:
                self.state = "flee"
            elif here == self.goal:
                self.state = "eat"
                self.eatTime = rat_eat_time
                self.sounds.append("squeak")
            else:
                self.stepToward(self.goal)
        elif self.state == "eat":
            self.eatTime -= time
            if self.eatTime <= 0:
                if self.fm.nibble(*here): self.messages.append("Nibbled!")
                self.state = "flee"
        elif self.state == "flee":
            if here == self.exit: self.gone = True
            else: self.stepToward(self.exit)

    def stepToward(self, goal):
        step = self.fm.nextStepToward((self.map_x, self.map_y), goal)
        if step is None:
            # Can't get there; give up
            if self.state == "flee": self.gone = True
            else: self.goal = None
            return
        self.setFacing(*step)
        self.startMove(step[0], step[1], self.stepTime)

    def draw(self):
        (x, y) = self.getPosition()
        prefix = self.facing[0]
        if self.state == "eat":
            frame = int(self.animTime / 150) % 2 + 1
            side = "w" if prefix == "w" else "e"
            self.sm.drawSprite("rat", "%s_eat%d" % (side, frame), x, y - 4)
        else:
            frames = 3 if prefix in "ew" else 4
            frame = int(self.animTime / 70) % frames + 1
            self.sm.drawSprite("rat", "%s_run%d" % (prefix, frame), x, y - 4)


class Rabbit(Mover):
    def __init__(self, sm, fm):
        (home_x, home_y) = fm.burrow
        super().__init__(sm, fm, home_x, home_y)
        # Action sprites
        self.actionSprite = {}
        self.actionSprite["s_eat"] = ["s_eat1", "s_eat2", "s_eat4", "s_eat3", "s_eat4", "s_eat3", "s_eat4", "s_eat3", "s_eat2", "s_eat1"]
        self.actionSprite["s_hop"] = ["s_hopa1", "s_hopa2", "s_hopa3", "s_hopb2", "s_hopb3", "s_hopa1", "s_hopa2", "s_hopa3", "s_hopb2", "s_hopb3"]
        self.actionSprite["n_eat"] = ["n_eat1", "n_eat2", "n_eat4", "n_eat3", "n_eat4", "n_eat3", "n_eat4", "n_eat3", "n_eat2", "n_eat1"]
        self.actionSprite["n_hop"] = ["n_hopa1", "n_hopa2", "n_hopa3", "n_hopb2", "n_hopb3", "n_hopa1", "n_hopa2", "n_hopa3", "n_hopb2", "n_hopb3"]
        self.actionSprite["e_eat"] = ["e_eat1", "e_eat2", "e_eat4", "e_eat3", "e_eat4", "e_eat3", "e_eat4", "e_eat3", "e_eat2", "e_eat1"]
        self.actionSprite["e_hop"] = ["e_hopa1", "e_hopa2", "e_hopa3", "e_hopb2", "e_hopb3", "e_hopa1", "e_hopa2", "e_hopa3", "e_hopb2", "e_hopb3"]
        self.actionSprite["w_eat"] = ["w_eat1", "w_eat2", "w_eat4", "w_eat3", "w_eat4", "w_eat3", "w_eat4", "w_eat3", "w_eat2", "w_eat1"]
        self.actionSprite["w_hop"] = ["w_hopa1", "w_hopa2", "w_hopa3", "w_hopb2", "w_hopb3", "w_hopa1", "w_hopa2", "w_hopa3", "w_hopb2", "w_hopb3"]
        self.playerSpriteName = "s_hopa1"
        self.facing = "south"
        # Carrying and eating
        self.basket = []   # crop names being carried
        self.pantry = []   # extra crops stored in the burrow
        self.hunger = max_hunger
        # Actions
        self.currentAction = None   # "hop", "eat" or "grab"
        self.actionTime = 0
        self.actionDuration = 1
        self.nextAction = None
        self.invulnerable = 0
        self.messages = []          # popup text for the game to show

    def respawn(self):
        self.placeAt(*self.fm.burrow)
        self.basket = []
        self.currentAction = None
        self.nextAction = None
        self.facing = "south"
        self.hunger = max(self.hunger, max_hunger // 2)
        self.invulnerable = invulnerable_time

    def isSafe(self):
        # Dogs can't reach the bunny in its burrow
        return self.fm.isBurrow(*self.nearestTile())

    def isHidden(self):
        # In tall grass or corn, and not hopping out of it
        return self.fm.hidesBunny(*self.nearestTile())

    def isStarving(self):
        return self.hunger <= 0

    def hopTime(self):
        time = hop_time + carry_hop_time * len(self.basket)
        if self.isStarving(): time *= starving_slowdown
        return time

    def action(self, move):
        # Queue an action; it starts as soon as the current one finishes
        self.nextAction = move

    def startAction(self, move):
        if move in directions: self.hop(move)
        if move == "grab": self.grab()
        if move == "eat": self.eat()

    def hop(self, move):
        self.facing = move
        (dx, dy) = directions[move]
        if self.fm.isWalkable(self.map_x + dx, self.map_y + dy):
            self.currentAction = "hop"
            self.startMove(dx, dy, self.hopTime())
            self.sounds.append("hop")

    def startTimedAction(self, name, duration):
        self.currentAction = name
        self.actionTime = 0
        self.actionDuration = duration

    def grab(self):
        crop = self.fm.cropAt(self.map_x, self.map_y)
        if crop is None:
            self.messages.append("Nothing to pick here")
            return
        if not crop.isRipe():
            self.messages.append("Not ripe yet")
            return
        if len(self.basket) >= basket_size:
            self.messages.append("Basket full!")
            return
        self.fm.harvest(self.map_x, self.map_y)
        self.basket.append(crop.kind)
        self.messages.append("Picked a %s" % crop.kind)
        self.sounds.append("pick")
        self.startTimedAction("grab", grab_time)

    def eat(self):
        # Eat what's in the ground first, then the basket, then the pantry
        crop = self.fm.cropAt(self.map_x, self.map_y)
        if crop:
            self.fm.harvest(self.map_x, self.map_y)
            food = crop.getFood()
            kind = crop.kind
        elif self.basket:
            kind = self.basket.pop()
            food = cropTypes[kind].food
        elif self.isSafe() and self.pantry:
            kind = self.pantry.pop()
            food = cropTypes[kind].food
        else:
            self.messages.append("Nothing to eat")
            return
        self.hunger = min(max_hunger, self.hunger + food)
        self.messages.append("Ate a %s" % kind)
        self.sounds.append("munch")
        self.startTimedAction("eat", eat_time)

    def update(self, time, heldMove=None):
        # Time is ms since the last frame. Returns True when a hop lands.
        landed = False
        self.hunger = max(0, self.hunger - self.fm.level.hunger_rate * time / 1000)
        if self.invulnerable > 0: self.invulnerable -= time
        # Process the current action
        if self.currentAction == "hop":
            if self.updateMove(time):
                self.currentAction = None
                landed = True
        elif self.currentAction in ["eat", "grab"]:
            self.actionTime += time
            if self.actionTime >= self.actionDuration:
                self.currentAction = None
        # Start the next action, or keep hopping while a key is held
        if self.currentAction is None:
            move = self.nextAction or heldMove
            self.nextAction = None
            if move: self.startAction(move)
        self.updateSprite()
        return landed

    def updateSprite(self):
        prefix = self.facing[0]
        if self.currentAction == "hop":
            frames = self.actionSprite[prefix + "_hop"]
            progress = self.moveProgress()
        elif self.currentAction in ["eat", "grab"]:
            frames = self.actionSprite[prefix + "_eat"]
            progress = self.actionTime / self.actionDuration
        else:
            frames = self.actionSprite[prefix + "_hop"]
            progress = 0
        index = min(int(progress * len(frames)), len(frames) - 1)
        self.playerSpriteName = frames[index]

    def draw(self):
        # Blink while invulnerable
        if self.invulnerable > 0 and int(self.invulnerable / 120) % 2 == 0: return
        (x, y) = self.getPosition()
        if self.isHidden():
            # See-through while hidden
            sprite = self.sm.getSprite("rabbit", self.playerSpriteName).copy()
            sprite.set_alpha(120)
            self.sm.screen.blit(sprite, (x, y))
        else:
            self.sm.drawSprite("rabbit", self.playerSpriteName, x, y)
