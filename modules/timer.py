"""
RED = FAILED TO SETUP
FLASHING YELLOW = SETTING UP
GREEN = ON
NONE = OFF
PURPLE = DISABLED
"""

import ktane
import asyncio

module = ktane.Module(identifier="T")
module.strike_leds = ktane.LED(11, 13, 15)
module.power_switch = ktane.Button(18)
module.buzzer = ktane.IO(16, 1)
module.status_led = ktane.LED(36, 38, 40)

module.MAX_STRIKES = 3
module.previous_strikes = None
module.game_state = 0
module.strikes = 0

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
    await buzz(0.1)

@module.event
async def on_message_received(auth, msg):
    if module.game_state != 0: return

    if msg == "@~STRIKE":
        module.strikes+=1

@module.power_switch.handler("pressed")
async def turn_on():
    print("\n... TURNED ON!")

    setup()
    module.game_state = 0
    module.led_state = 0

    print("READY!")

@module.power_switch.handler("unpressed")
async def turn_off():
    print("... TURNED OFF!")

    module.game_state = -1 
    module.led_state = -1

@module.task
async def strikes_manager():
    if module.previous_strikes == module.strikes: return
    if module.strikes >= module.MAX_STRIKES:
        module.game_state = -1
        module.send(-1, "@~BOOM")
        module.led_state = -3

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
    module.MAX_STRIKES = 3
    module.strikes = 0
    module.previous_strikes = None
    module.time = 0

    module.buzzer.value(0)

module.run()