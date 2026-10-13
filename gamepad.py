import pygame

##############################################################
# Gamepad support                                            #
#                                                            #
# Buttons use the Xbox layout, which is also what Steam      #
# Input presents for other controllers and the Steam Deck.   #
# Controller presses become ordinary key presses, so every   #
# screen that works with a keyboard works with a gamepad.    #
#   D-pad / left stick: arrows   A: Space (pick / select)    #
#   B: Esc (back)   X: E (eat)   Y: R (retry)                #
#   Start: Esc (pause)   Back: Esc                           #
##############################################################

button_keys = {
    0: pygame.K_SPACE,    # A
    1: pygame.K_ESCAPE,   # B
    2: pygame.K_e,        # X
    3: pygame.K_r,        # Y
    6: pygame.K_ESCAPE,   # Back / View
    7: pygame.K_ESCAPE,   # Start / Menu
}
direction_keys = {"north": pygame.K_UP, "south": pygame.K_DOWN, "west": pygame.K_LEFT, "east": pygame.K_RIGHT}
stick_deadzone = 0.5
repeat_delay = 400      # ms before a held direction repeats in menus
repeat_rate = 150       # ms between repeats


class Gamepad:
    def __init__(self):
        self.joysticks = {}
        self.direction = None
        self.heldTime = 0
        self.repeatTime = 0
        try:
            pygame.joystick.init()
            for i in range(pygame.joystick.get_count()):
                self.add(i)
        except pygame.error:
            pass

    def connected(self):
        return len(self.joysticks) > 0

    def add(self, index):
        try:
            joystick = pygame.joystick.Joystick(index)
            self.joysticks[joystick.get_instance_id()] = joystick
        except pygame.error:
            pass

    def handleEvent(self, event):
        # Returns a key event to use instead, or None if the event was handled here
        if event.type == pygame.JOYDEVICEADDED:
            self.add(event.device_index)
            return None
        if event.type == pygame.JOYDEVICEREMOVED:
            self.joysticks.pop(event.instance_id, None)
            return None
        if event.type == pygame.JOYBUTTONDOWN and event.button in button_keys:
            return self.keyEvent(button_keys[event.button])
        return None

    def keyEvent(self, key):
        return pygame.event.Event(pygame.KEYDOWN, key=key, mod=0, unicode="", scancode=0, gamepad=True)

    def heldDirection(self):
        # D-pad first, then the left stick
        for joystick in self.joysticks.values():
            try:
                if joystick.get_numhats() > 0:
                    (hx, hy) = joystick.get_hat(0)
                    if hx < 0: return "west"
                    if hx > 0: return "east"
                    if hy > 0: return "north"
                    if hy < 0: return "south"
                if joystick.get_numaxes() >= 2:
                    x = joystick.get_axis(0)
                    y = joystick.get_axis(1)
                    if max(abs(x), abs(y)) > stick_deadzone:
                        if abs(x) > abs(y): return "east" if x > 0 else "west"
                        return "south" if y > 0 else "north"
            except pygame.error:
                pass
        return None

    def update(self, time):
        # Returns arrow key events for a newly pressed or held direction (menus need these)
        events = []
        direction = self.heldDirection()
        if direction != self.direction:
            self.direction = direction
            self.heldTime = 0
            self.repeatTime = 0
            if direction: events.append(self.keyEvent(direction_keys[direction]))
        elif direction:
            self.heldTime += time
            if self.heldTime >= repeat_delay:
                self.repeatTime += time
                if self.repeatTime >= repeat_rate:
                    self.repeatTime = 0
                    events.append(self.keyEvent(direction_keys[direction]))
        return events
