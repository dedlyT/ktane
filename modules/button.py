import ktane
import random
import time
import json

BUTTON_COLOURS = [
    (0,0,1), # BLUE
    (1,0,0), # RED
    (1,1,1), # WHITE
    (1,1,0), # YELLOW
    (0,1,0) # GREEN
]
STRIP_COLOURS = [
    (0,0,1), # BLUE
    (1,0,0), # RED
    (1,1,1), # WHITE
    (1,1,0), # YELLOW
    (0,1,0) # GREEN
]
BUTTON_TEXTS = [
    "Abort",
    "Detonate",
    "Hold",
    "Press"
]

module = ktane.Module(identifier="BTN")
module.status_led = ktane.LED(36, 38, 40)
module.button_colour_led = ktane.LED(11, 13, 15)
module.strip_led = ktane.LED(3,5,7)
module.main_button = ktane.Button(19)
module.game_state = -1
module.strip_colour = None
module.colour = None
module.text = None
module.button_held_time = 0
module.timer_time = {"h":0,"m":0,"s":0}

@module.event
async def on_ready():
    module.status_led.value(0)
    module.init(module.main_button)
    module.button_colour_led.value(0,0,0)

    print("-"*20)
    print("READY!")

@module.event
async def on_message_received(auth, msg):
    if msg.startswith("@~T"):
        t = msg.split("#")[1]
        module.timer_time = json.loads(t)

    if msg.startswith("@~STATE"):
        state = msg.split("#")[1]
        module.game_state = int(state)

@module.main_button.handler("pressed")
async def button_pressed():
    if module.game_state != 0: return

    module.button_held_time = time.time()
    module.strip_colour = STRIP_COLOURS[random.randint(0,len(STRIP_COLOURS)-1)]
    module.strip_led.value(*module.strip_colour)

@module.main_button.handler("unpressed")
async def button_unpressed():
    if module.game_state != 0: return

    if module.colour == (0,0,1) and module.text == "Abort": releasing_held()
    elif module.bomb_data["batteries"] > 1 and module.text == "Detonate": press_release()
    elif module.colour == (1,1,1) and "CAR" in module.bomb_data["labels"]: releasing_held()
    elif module.bomb_data["batteries"] > 2 and "FRK" in module.bomb_data["labels"]: press_release()
    elif module.colour == (1,1,0): press_release()
    elif module.colour == (1,0,0) and module.text == "Hold": press_release()
    else: releasing_held()

@module.event
async def on_turn_on():
    setup()

@module.event
async def on_turn_off():
    module.button_colour_led.value(0,0,0)
    module.strip_led.value(0,0,0)

def setup():
    module.colour = BUTTON_COLOURS[random.randint(0,len(BUTTON_COLOURS)-1)]
    module.text = BUTTON_TEXTS[random.randint(0,len(BUTTON_TEXTS)-1)]

    module.button_colour_led.value(module.colour)
    print(module.text)

def releasing_held():
    compare = "".join([str(x) for x in module.timer_time.values()])

    if module.strip_colour == (0,0,1):
        if "4" in compare: defused()
        else: module.send(0, "@~STRIKE")
        return
    
    if module.strip_colour == (1,1,0):
        if "5" in compare: defused()
        else: module.send(0, "@~STRIKE")
        return
    
    if "1" in compare: defused()
    else: module.send(0, "@~STRIKE")

def press_release():
    if (time.time() - module.button_held_time) > 0.5:
        return module.send(0, "@~STRIKE")
    
    defused()

def defused():
    print("DEFUSED!")
    module.send(0, "@~DEFUSED")
    module.button_colour_led.value(0,0,0)
    module.strip_led.value(0,0,0)
    module.game_state = 1
    module.led_state = 1

module.run()