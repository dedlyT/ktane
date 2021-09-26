import ktane_lib as ktane
import asyncio

core = ktane.Module(2)

wires = [11,13,15,16,18]
for i in range(len(wires)):
    exec(f"wire{i} = ktane.IO({wires[i]}, 'in', 'down')")

@core.event
async def on_ready():
    print("ready!")
    core.init(wire0)
    core.init(wire1)
    core.init(wire2)
    core.init(wire3)
    core.init(wire4)

@core.event
async def on_io_rise(io):
    print(f"{io.pin} rise!")

@core.event
async def on_io_fall(io):
    print(f"{io.pin} fall!")
    
core.run()