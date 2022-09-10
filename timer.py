import asyncio
import ktane

module = ktane.Module(identifier="T")

power_switch = ktane.IO(11, 0)

@module.event
async def on_ready():
    print("penis!\n")

    power_switch.rise = power_on
    power_switch.fall = power_off

    module.init(power_switch)

async def power_on():
    print("pressed!")

async def power_off():
    print("unpressed!")

module.run()