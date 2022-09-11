import asyncio
import random
import ktane

module = ktane.Module(identifier="T")
module.state = 0
module.prev_s = 0
module.strikes = 0

power_switch = ktane.IO(11, 0)
button = ktane.Button(8)
led1 = ktane.IO(3,1)
led2 = ktane.IO(5,1)
led3 = ktane.IO(7,1)

@module.event
async def on_ready():
    print("penis!\n")

    module.paused = power_switch.value()
    module.init(power_switch)
    module.init(button)

@module.event
async def on_second_passed(t):
    print(f"{t['h']}:{t['m']}:{t['s']}")

@module.task
async def fail_vfx():
    if module.state != -1: return

    seconds = module.time["s"] + module.time["m"]*60 + module.time["h"]*3600
    if seconds - module.prev_s >= 1:
        module.prev_s = seconds
        for led in (led1,led2,led3): led.switch()

@module.task
async def strike_manager():
    if module.state == -1: return

    if module.strikes>=3:
        print("BOOOOOOOOOOOOOOOM!")
        module.paused = True
        module.state = -1
        module.strikes = 0
        module.prev_s = -1
    
    vals = [0,0,0]
    for i in range(module.strikes): vals[i] = 1

    for led,val in zip((led1,led2,led3),vals):
        led.value(val)

@power_switch.handler("rise")
async def power_on():
    print("POWERING ON!")
    module.state = 1

    module.strikes = 0
    module.time = 0
    module.paused = False

@power_switch.handler("fall")
async def power_off():
    module.paused = True
    module.strikes = 0

    print("POWERING OFF!")
    module.state = 0

@button.handler("pressed", False)
async def add_strike():
    if module.state>0:
        module.strikes+=1

module.run()