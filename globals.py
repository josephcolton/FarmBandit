##################
# Game Constants #
##################
screen_width = 800
screen_height = 600
max_fps = 60

###############
# Game Colors #
###############
white = (255, 255, 255)
green = (47, 129, 54)
black = (0, 0, 0)
red = (200, 50, 50)
alert_red = (255, 110, 90)
yellow = (240, 210, 60)
hud_background = (60, 52, 72)
hud_text = (240, 236, 220)

######################
# Farm Map Variables #
######################
tile_width = 32
tile_height = 32
map_width = 20  # Map Width Tiles
map_height = 15 # Map Height Tiles
farm_offset_x = 32
farm_offset_y = 32

###################
# Bunny Variables #
###################
hop_time = 260             # ms per hop with an empty basket
carry_hop_time = 60        # extra ms per hop for each crop carried
starving_slowdown = 1.8    # hops take this much longer when starving
basket_size = 3            # crops the bunny can carry at once
max_hunger = 100
eat_time = 800             # ms to eat a crop
grab_time = 300            # ms to pull up a crop
start_lives = 3
invulnerable_time = 2000   # ms of safety after being caught

#################
# Dog Variables #
#################
catch_distance = 20        # pixels between bunny and dog to count as caught
caught_pause = 1500        # ms the game pauses after a catch

####################
# Farmer Variables #
####################
farmer_alert_time = 4000         # ms the dogs chase after a whistle
farmer_whistle_cooldown = 6000   # ms before the farmer can whistle again
farmer_chase_time = 2500         # ms he keeps chasing after losing sight

#####################
# Rooster Variables #
#####################
rooster_notice = 2         # tiles away the rooster notices the bunny
rooster_range = 3          # tiles the rooster wanders from home
rooster_calm_time = 4000   # ms the rooster stays calm after a peck

#################
# Rat Variables #
#################
rat_eat_time = 1500        # ms a rat spends nibbling a crop
max_rats = 2               # rats on the farm at once


class Location:
    def __init__(self, map_x, map_y):
        self.map_x = map_x
        self.map_y = map_y

    def getXCoord(self):
        return self.map_x * tile_width

    def getYCoord(self):
        return self.map_y * tile_height
