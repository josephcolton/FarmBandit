import pygame

try:
    from pygame._sdl2 import controller
except ImportError:
    controller = None

##############################################################
# Gamepad support                                            #
#                                                            #
# Buttons are read by position through SDL's controller      #
# database, so the bottom face button is the same on Xbox,   #
# PlayStation, SNES-style and Steam Deck pads. Controller    #
# presses become ordinary key presses, so every screen that  #
# works with a keyboard works with a gamepad. Each press     #
# also carries the button's name for the few places that     #
# treat a button differently from its key.                   #
#   D-pad / left stick: arrows                               #
#   Bottom (Xbox A, SNES B): Space (pick / select / resume)  #
#   Right (Xbox B, SNES A): Esc (back), eat while playing    #
#   Left (Xbox X, SNES Y): E (eat)   Top: R (retry)          #
#   Start: Enter, pause while playing                        #
#   Back / Select: Esc, quit to the title while paused       #
#   Shoulders and triggers: P (pause / resume)               #
##############################################################

button_keys = {
    "south": pygame.K_SPACE,
    "east": pygame.K_ESCAPE,
    "west": pygame.K_e,
    "north": pygame.K_r,
    "start": pygame.K_RETURN,
    "back": pygame.K_ESCAPE,
    "shoulder": pygame.K_p,
}
# Positions of SDL's named controller buttons
controller_buttons = {
    pygame.CONTROLLER_BUTTON_A: "south",
    pygame.CONTROLLER_BUTTON_B: "east",
    pygame.CONTROLLER_BUTTON_X: "west",
    pygame.CONTROLLER_BUTTON_Y: "north",
    pygame.CONTROLLER_BUTTON_START: "start",
    pygame.CONTROLLER_BUTTON_BACK: "back",
    pygame.CONTROLLER_BUTTON_LEFTSHOULDER: "shoulder",
    pygame.CONTROLLER_BUTTON_RIGHTSHOULDER: "shoulder",
}
controller_triggers = (pygame.CONTROLLER_AXIS_TRIGGERLEFT, pygame.CONTROLLER_AXIS_TRIGGERRIGHT)
# Events the gamepad turns into key presses (or swallows)
events = (pygame.JOYDEVICEADDED, pygame.JOYDEVICEREMOVED, pygame.JOYBUTTONDOWN,
          pygame.CONTROLLERBUTTONDOWN, pygame.CONTROLLERAXISMOTION)
# Pads SDL doesn't know: guess the Xbox numbering
raw_buttons = {0: "south", 1: "east", 2: "west", 3: "north", 4: "shoulder", 5: "shoulder", 6: "back", 7: "start"}
direction_keys = {"north": pygame.K_UP, "south": pygame.K_DOWN, "west": pygame.K_LEFT, "east": pygame.K_RIGHT}
stick_deadzone = 0.5
trigger_threshold = 16000   # trigger axes run 0 to 32767
repeat_delay = 400      # ms before a held direction repeats in menus
repeat_rate = 150       # ms between repeats


class Gamepad:
    def __init__(self):
        self.joysticks = {}
        self.controllers = {}   # instance id -> SDL controller, for pads SDL recognizes
        self.triggers = set()   # triggers currently held down
        self.direction = None
        self.heldTime = 0
        self.repeatTime = 0
        try:
            pygame.joystick.init()
            if controller: controller.init()
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
            if controller and controller.is_controller(index):
                self.controllers[joystick.get_instance_id()] = controller.Controller(index)
        except pygame.error:
            pass

    def remove(self, instance):
        self.joysticks.pop(instance, None)
        self.controllers.pop(instance, None)
        self.triggers = {t for t in self.triggers if t[0] != instance}

    def handleEvent(self, event):
        # Returns a key event to use instead, or None if the event was handled here
        if event.type == pygame.JOYDEVICEADDED:
            self.add(event.device_index)
            return None
        if event.type == pygame.JOYDEVICEREMOVED:
            self.remove(event.instance_id)
            return None
        if event.type == pygame.CONTROLLERBUTTONDOWN and event.instance_id in self.controllers:
            return self.buttonEvent(controller_buttons.get(event.button))
        if event.type == pygame.CONTROLLERAXISMOTION and event.axis in controller_triggers:
            trigger = (event.instance_id, event.axis)
            if event.value > trigger_threshold and trigger not in self.triggers:
                self.triggers.add(trigger)
                return self.buttonEvent("shoulder")
            if event.value < trigger_threshold // 2: self.triggers.discard(trigger)
            return None
        if event.type == pygame.JOYBUTTONDOWN and event.instance_id not in self.controllers:
            return self.buttonEvent(raw_buttons.get(event.button))
        return None

    def buttonEvent(self, button):
        if button is None: return None
        return self.keyEvent(button_keys[button], button)

    def keyEvent(self, key, button=None):
        return pygame.event.Event(pygame.KEYDOWN, key=key, mod=0, unicode="", scancode=0, gamepad=True, button=button)

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
