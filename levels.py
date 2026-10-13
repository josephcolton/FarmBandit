##########################################################
# Farm Levels                                            #
#                                                        #
# Each map is 20 columns by 15 rows. Map legend:         #
#   .  grass               :  empty garden soil          #
#   T  cliff top (blocked) C  cliff face (blocked)       #
#   H  burrow in the cliff face (one per farm)           #
#   =  fence (blocked)     ^  rocks (blocked)            #
#   B  hay bale (blocked, blocks the farmer's view)      #
#   ,  tall grass (the bunny can hide in it)             #
#   D  dog starts here (on grass)                        #
#   F  farmer starts here (on grass, optional)           #
#   R  rooster's home (on grass, optional)               #
#   Crop letters (planted in soil), see crops.py:        #
#   c carrot   s sweet potato  r radish   b beet         #
#   t turnip   l lettuce       g cabbage  f cauliflower  #
#   e pepper   w watermelon    p pumpkin  u potato       #
#   o onion    k broccoli      a eggplant y strawberry   #
#   v blueberry  m tomato      n corn     i pineapple    #
#                                                        #
# Run "python tools/check_levels.py" after editing maps. #
##########################################################

class Level:
    def __init__(self, name, layout, order, intro="",
                 dog_step=450, dog_sight=6, dog_chase=0.7,
                 farmer_step=650, farmer_sight=6,
                 rooster_step=320, rat_step=160, rat_interval=0,
                 hunger_rate=1.0, regrow_time=15000, night_length=180,
                 scarce=()):
        self.name = name
        self.layout = layout
        self.order = order              # {crop name: count} to deliver
        self.intro = intro
        self.dog_step = dog_step        # ms for a dog to cross one tile
        self.dog_sight = dog_sight      # tiles away a dog notices the bunny
        self.dog_chase = dog_chase      # chance a dog chases instead of wandering
        self.farmer_step = farmer_step  # ms for the farmer to cross one tile
        self.farmer_sight = farmer_sight  # tiles the farmer can see ahead
        self.rooster_step = rooster_step  # ms for the rooster to cross one tile
        self.rat_step = rat_step        # ms for a rat to cross one tile
        self.rat_interval = rat_interval  # average ms between rats (0 = no rats)
        self.hunger_rate = hunger_rate  # hunger lost per second
        self.regrow_time = regrow_time  # ms before a picked spot is replanted
        self.night_length = night_length  # seconds until dawn
        self.scarce = scarce            # crops with fewer spots than the order needs (on purpose)


levels = []

##########################################
# Farms 1-3: roosters, then a sleepy dog #
##########################################
levels.append(Level(
    "Henhouse Garden",
    [
        "TTTTTTTTTTTTTTTTTTTT",
        "CCCCCHCCCCCCCCCCCCCC",
        "....................",
        "..^.................",
        "...::::::::::.......",
        "...:cccccccc:.......",
        "...:cccccccc:..R....",
        "...:cccccccc:.......",
        "...::::::::::.......",
        "..............^.....",
        "....................",
        "....::::::::::......",
        "....:cccccccc:......",
        "....::::::::::......",
        "....................",
    ],
    {"carrot": 4},
    intro="Pick ripe carrots and carry them home. The rooster pecks!",
    hunger_rate=0.8, night_length=150,
))

levels.append(Level(
    "Two Hens",
    [
        "....................",
        "TTTTTTTTTTTTTTTTTTTT",
        "CCCCCCCCCCCCCCHCCCCC",
        "....................",
        ".::::::::::::::::...",
        ".:cccccccccccccc:...",
        ".:rrrrrrrrrrrrrr:...",
        ".:cccccccccccccc:.R.",
        ".:rrrrrrrrrrrrrr:...",
        ".::::::::::::::::...",
        "....................",
        "........R...........",
        "...^................",
        "..............^.....",
        "....................",
    ],
    {"carrot": 4, "radish": 3},
    intro="Mixed rows! Fill the order with carrots and radishes.",
    hunger_rate=0.9, night_length=160,
))

levels.append(Level(
    "Sleepy Pup",
    [
        "TTTTTTTTTTTTTTTTTTTT",
        "CCCHCCCCCCCCCCCCCCCC",
        "....................",
        "...........D........",
        "..::::::::::::::....",
        "..:llllllllllll:....",
        "..:cccccccccccc:....",
        "..:llllllllllll:....",
        "..::::::::::::::....",
        "....................",
        "..^..........^......",
        "......R.............",
        "...:::::::::::......",
        "...:ccccccccc:......",
        "...:::::::::::......",
    ],
    {"lettuce": 3, "carrot": 3},
    intro="A dog! This one is sleepy. Dogs can't follow you into the burrow.",
    dog_step=620, dog_sight=4, dog_chase=0.5,
    hunger_rate=1.0, night_length=170,
))

#############################################
# Farms 4-7: more dogs, the farmer, hiding  #
#############################################
levels.append(Level(
    "Carrot Patch",
    [
        "....................",
        "TTTTTTTTTTTTTTTTTTTT",
        "CCHCCCCCCCCCCCCCCCCC",
        "....................",
        ".........D..........",
        "...::::::::::::.....",
        "...:cccccccccc:.....",
        "...:cccccccccc:.....",
        "...:cccccccccc:..D..",
        "...:cccccccccc:.....",
        "...:cccccccccc:.R...",
        "...:cccccccccc:.....",
        "...::::::::::::.....",
        "....................",
        "....................",
    ],
    {"carrot": 6},
    intro="Two wide-awake dogs. Every crop you carry slows you down.",
    dog_step=520, dog_sight=5, dog_chase=0.65,
    hunger_rate=1.0, night_length=160,
))

levels.append(Level(
    "Farmer Bill",
    [
        "....................",
        "TTTTTTTTTTTTTTTTTTTT",
        "CCCCCCCCCHCCCCCCCCCC",
        "....................",
        ".::::::::....::::::.",
        ".:uuuuuu:....:oooo:.",
        ".:uuuuuu:....:oooo:.",
        ".:uuuuuu:..D.:oooo:.",
        ".::::::::....::::::.",
        "....................",
        "....^.........^.....",
        "....................",
        "..R.................",
        "..........F.........",
        "....................",
    ],
    {"potato": 4, "onion": 3},
    intro="Farmer Bill sees what's in front of him. If he spots you, he whistles for the dogs!",
    dog_step=520, dog_sight=5, dog_chase=0.65,
    farmer_step=720, farmer_sight=5,
    hunger_rate=1.0, night_length=180,
))

levels.append(Level(
    "Tall Grass Meadow",
    [
        "TTTTTTTTTTTTTTTTTTTT",
        "CCCCCCHCCCCCCCCCCCCC",
        "....................",
        ",,,,..........,,,,,,",
        ",,,,..........,,,,,,",
        "..::::::..::::::....",
        "..:bbbb:..:tttt:....",
        "..:bbbb:..:tttt:..D.",
        "..::::::..::::::....",
        "....,,,,,,,,,,......",
        "....,,,,,,,,,,......",
        "...D................",
        "..:::::::::::::::...",
        "..:ccccccccccccc:.F.",
        "..:::::::::::::::...",
    ],
    {"beet": 3, "turnip": 3, "carrot": 2},
    intro="Hide in tall grass. The farmer can't see you, and dogs must be right beside you.",
    dog_step=500, dog_sight=5, dog_chase=0.65,
    farmer_step=680, farmer_sight=6,
    hunger_rate=1.1, night_length=190,
))

levels.append(Level(
    "Root Cellar Farm",
    [
        "TTTTTTTTTTTTTTTTTTTT",
        "CCCCCCCCCHCCCCCCCCCC",
        "....................",
        ".=======....=======.",
        ".=rrrrr:....:bbbbb=.",
        ".:rrrrr=....=bbbbb=.",
        ".=======....=======.",
        "...^...........D^.R.",
        ".=======....=======.",
        ".=ttttt:....:ccccc=.",
        ".:ttttt=....=ccccc=.",
        ".=ttttt=....=ccccc=.",
        ".=======..D.=======.",
        "....................",
        "..........F.........",
    ],
    {"radish": 4, "beet": 3, "turnip": 3},
    intro="Watch the garden gates. The farmer checks on missing crops.",
    dog_step=500, dog_sight=5, dog_chase=0.65,
    farmer_step=650, farmer_sight=6,
    hunger_rate=1.3, night_length=200,
))

################################################
# Farms 8-10: scarce crops, then rats          #
################################################
levels.append(Level(
    "Two Pumpkin Patch",
    [
        "TTTTTTTTTTTTTTTTTTTT",
        "CCCCCCCCCCCCCHCCCCCC",
        "....................",
        ".:::::::.....::::::.",
        ".:sssss:..D..:pp:::.",
        ".:sssss:.....::::::.",
        ".:::::::............",
        "......,,,,,,........",
        "......,,,,,,....^...",
        "..^.................",
        ".:::::::::::::::::..",
        ".:ggggggggggggggg:..",
        ".:::::::::::::::::..",
        "....D..........R....",
        ".........F..........",
    ],
    {"pumpkin": 3, "sweet potato": 3, "cabbage": 2},
    intro="Only two pumpkin vines, but you need three. Wait for one to grow back!",
    dog_step=480, dog_sight=5, dog_chase=0.65,
    farmer_step=650, farmer_sight=6,
    hunger_rate=1.1, regrow_time=6000, night_length=260,
    scarce=("pumpkin",),
))

levels.append(Level(
    "Rat Run",
    [
        "TTTTTTTTTTTTTTTTTTTT",
        "CCHCCCCCCCCCCCCCCCCC",
        "....................",
        "..:::::::::::::::...",
        "..:ggggggggggggg:...",
        "..:fffffffffffff:...",
        "..:ggggggggggggg:.D.",
        "..:::::::::::::::...",
        "....................",
        ",,,,,....^.....,,,,,",
        ",,,,,..........,,,,,",
        "....:::::::::::.....",
        "....:fffffffff:..R..",
        "....:::::::::::.....",
        ".D........F.........",
    ],
    {"cabbage": 4, "cauliflower": 4},
    intro="Rats! They nibble ripe crops back to sprouts. Nobody chases them.",
    dog_step=460, dog_sight=6, dog_chase=0.7,
    farmer_step=650, farmer_sight=6,
    rat_interval=15000,
    hunger_rate=1.3, night_length=210,
))

levels.append(Level(
    "Pumpkin Hollow",
    [
        "TTTTTTTTTTTTTTTTTTTT",
        "CCCCCCCCCHCCCCCCCCCC",
        "....................",
        ".::::::.^..^.::::::R",
        ".:pppp:......:wwww:.",
        ".:pppp:..D...:wwww:.",
        ".::::::......::::::.",
        "...^.....^^.....^...",
        ".::::::......::::::.",
        ".:llll:...D..:gggg:.",
        ".:llll:......:gggg:.",
        ".::::::..^...::::::.",
        "..^.......D...F..^..",
        "....:eeeeeeeeee:....",
        "....::::::::::::....",
    ],
    {"pumpkin": 2, "watermelon": 2, "lettuce": 3, "cabbage": 3},
    intro="Three dogs, the farmer, a rooster, and rats. Pumpkins are heavy!",
    dog_step=490, dog_sight=6, dog_chase=0.7,
    farmer_step=600, farmer_sight=7,
    rat_interval=22000,
    hunger_rate=1.5, night_length=220,
))

###########################################################
# Farms 11-15: hay bales, berries, corn, and new crops    #
###########################################################
levels.append(Level(
    "Haystack Hideout",
    [
        "....................",
        "TTTTTTTTTTTTTTTTTTTT",
        "CCCCCCCCHCCCCCCCCCCC",
        "....................",
        "..B.....B.....B.....",
        ".::::::::::::::::::.",
        ".:kkkkkkkkkkkkkkkk:.",
        ".:oooooooooooooooo:.",
        ".:kkkkkkkkkkkkkkkk:.",
        ".::::::::::::::::::.",
        "...B....D.....B.....",
        "......B......B......",
        "..::::::.....D...R..",
        "..:aa:::...B........",
        "..::::::......F.....",
    ],
    {"broccoli": 4, "onion": 3, "eggplant": 3},
    intro="Duck behind hay bales: the farmer can't see through them.",
    dog_step=470, dog_sight=6, dog_chase=0.7,
    farmer_step=620, farmer_sight=7,
    hunger_rate=1.3, regrow_time=6000, night_length=250,
    scarce=("eggplant",),
))

levels.append(Level(
    "Berry Bramble",
    [
        "TTTTTTTTTTTTTTTTTTTT",
        "CCCCCCCCCCCCCCCCCHCC",
        "....................",
        ".::::::::::::::.....",
        ".:yyyyyyyyyyyy:.,,,,",
        ".:vvvvvvvvvvvv:.,,,,",
        ".:yyyyyyyyyyyy:.,,,,",
        ".::::::::::::::.....",
        "......D.......B.....",
        ",,,,.......R....,,,,",
        ",,,,..:::::::::.,,,,",
        "......:vvvvvvv:.....",
        "..D...:yyyyyyy:.....",
        "......:::::::::..F..",
        "..........D.........",
    ],
    {"strawberry": 6, "blueberry": 6},
    intro="Sweet berries! Lots to carry, and the rats love them too.",
    dog_step=440, dog_sight=7, dog_chase=0.7,
    farmer_step=620, farmer_sight=7,
    rat_interval=16000,
    hunger_rate=1.4, night_length=240,
))

levels.append(Level(
    "Corn Maze",
    [
        "TTTTTTTTTTTTTTTTTTTT",
        "CHCCCCCCCCCCCCCCCCCC",
        "....................",
        ".::::::::::::::::::.",
        ".:nnnnnnnn:nnnnnnn:.",
        ".::::::::::::::::::.",
        ".:nnnn:nnnnnnnn:nn:.",
        ".::::::::::::::::::.",
        ".:mmmmmmmmmmmmmmmm:.",
        ".::::::::::::::::::.",
        ".:nnnnnnn:nnnnnnnn:.",
        ".::::::::::::::::::.",
        "....D.......R.......",
        ".........D.....D....",
        "...F................",
    ],
    {"corn": 5, "tomato": 6},
    intro="Tall corn hides you and blocks the farmer's view, but these dogs are quick.",
    dog_step=420, dog_sight=6, dog_chase=0.75,
    farmer_step=560, farmer_sight=9,
    rat_interval=20000,
    hunger_rate=1.4, night_length=240,
))

levels.append(Level(
    "Market Garden",
    [
        "....................",
        "TTTTTTTTTTTTTTTTTTTT",
        "CCCCCCCCCCHCCCCCCCCC",
        "....................",
        ".:::::::::..:::::::.",
        ".:mmmmmmm:..:eeeee:.",
        ".:aaaaaaa:..:kkkkk:.",
        ".:ooooooo:..:eeeee:.",
        ".:::::::::..:::::::.",
        "..,,,,..D.....,,,,..",
        "..,,,,........,,,,..",
        "..::::......B.......",
        "..:ww:...R.....D....",
        "..::::..............",
        "..........F.........",
    ],
    {"tomato": 3, "eggplant": 3, "broccoli": 2, "watermelon": 3},
    intro="A market order! Only two watermelon vines for three melons.",
    dog_step=470, dog_sight=6, dog_chase=0.7,
    farmer_step=600, farmer_sight=7,
    rat_interval=26000,
    hunger_rate=1.4, regrow_time=6000, night_length=300,
    scarce=("watermelon",),
))

levels.append(Level(
    "Farmer Bill's Prize Farm",
    [
        "TTTTTTTTTTTTTTTTTTTT",
        "CCCCCCCCCHCCCCCCCCCC",
        "....................",
        ".::::::.B..B.::::::.",
        ".:iipp:......:nnnn:.",
        ".::::::..D...:nnnn:.",
        "..,,,,.......::::::.",
        "..,,,,...^^.........",
        ".::::::::...::::::::",
        ".:yyyyyy:...:vvvvvv:",
        ".::::::::...::::::::",
        "....B.....D.....B...",
        "..R.....,,,,,,......",
        "........,,,,,,..D...",
        "...F..........R.....",
    ],
    {"pineapple": 3, "pumpkin": 2, "corn": 3, "strawberry": 3, "blueberry": 3},
    intro="The grand prize: pineapples! Two plants, three needed. Everyone is guarding them.",
    dog_step=460, dog_sight=6, dog_chase=0.7,
    farmer_step=580, farmer_sight=7,
    rat_interval=26000,
    hunger_rate=1.5, regrow_time=6000, night_length=320,
    scarce=("pineapple",),
))
