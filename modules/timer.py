"""
RED = FAILED TO SETUP
FLASHING YELLOW = SETTING UP
GREEN = ON
NONE = OFF
PURPLE = DISABLED
"""

import ktane
import asyncio
import random
import json

MAX_STRIKES = 3
ALLOWED_CHARS = ["A","B","C","D","E","F","G","H","I","J","K","L","M","N","P","Q","R","S","T","U","V","W","X","Z","0","1","2","3","4","5","6","7","8","9"]
LABELS = ["SND","CLR","CAR","IND","FRQ","SIG","NSA","MSA","TRN","BOB","FRK"]

module = ktane.Module(identifier="T")
module.strike_leds = ktane.LED(11, 13, 15)
module.power_switch = ktane.Button(18)
module.buzzer = ktane.IO(16, 1)
module.status_led = ktane.LED(36, 38, 40)

module.previous_strikes = None
module.game_state = -1
module.strikes = 0
module.serial_number = None
module.battery_count = None
module.labels = None

@module.event
async def on_ready():
    module.init(module.power_switch)

    setup()
    module.led_state = 0

    print("-"*20)
    print("STARTED!")

@module.event
async def on_second_passed(t):
    if module.game_state != 0: return

    print(f"{t['h']}:{t['m']}:{t['s']}")
    
    for id,mod in module.modules.items():
        if mod["type"] == "BTN":
            module.send(id, f"@~T#{json.dumps(t)}")
            
    await buzz(0.1)

@module.event
async def on_message_received(auth, msg):
    if module.game_state != 0: return

    if msg == "@~DEFUSED":
        module.modules[auth[1]]["defused"] = True
        print("RECEIVED")
        print(module.modules)

    if msg == "@~STRIKE":
        module.strikes+=1

@module.power_switch.handler("pressed", False)
async def turn_on():
    print("\n... TURNED ON!")
    module.send(-1, "@~TURN_ON")

    setup()
    module.game_state = 0
    module.send(-1, "@~STATE#0")
    module.led_state = 0

    print("READY!")

@module.power_switch.handler("unpressed", False)
async def turn_off():
    print("... TURNED OFF!")
    module.send(-1, "@~TURN_OFF")

    module.game_state = -1
    module.send(-1, "@~STATE#-1")
    module.led_state = -1

@module.task
async def strikes_manager():
    if module.previous_strikes == module.strikes: return
    if module.game_state != 0: return

    if module.strikes >= MAX_STRIKES:
        module.game_state = -1
        module.send(-1, "@~BOOM")
        module.send(-1, "@~STATE#-1")
        module.led_state = -3
        return

    result = [False, False, False]
    for i in range(module.strikes):
        result[i] = True
    module.strike_leds.value(*result)
    
    module.previous_strikes = module.strikes

async def buzz(delay):
    module.buzzer.value(1)
    await asyncio.sleep(delay)
    module.buzzer.value(0)

def setup():
    module.strikes = 0
    module.previous_strikes = None
    module.time = 0
    module.serial_number = ("".join([ALLOWED_CHARS[random.randint(0,len(ALLOWED_CHARS)-1)] for i in range(5)])) + str(random.randint(0,9))
    module.battery_count = random.randint(1,4)
    module.labels = [None]
    if not random.randint(0,2):
        module.labels = []
        allowed = LABELS[:]
        for i in range(1,3):
            label = allowed.pop(random.randint(0,len(allowed)-1))
            module.labels += [label]

    data = {
        "batteries": module.battery_count,
        "serial": module.serial_number,
        "labels": module.labels
    }
    print(data)
    module.send(-1, f"@~BOMB_DETAILS#{json.dumps(data, separators=(',',':'))}")

    module.buzzer.value(0)

module.run()