import ktane_lib as ktane
import asyncio
import random
import time

core = ktane.Module(1)
led = ktane.LED((11,13,15), "rgb")
btn = ktane.Button(16, "down")

LOGIC = {
	(0,0,1): "4",
	(1,1,0): "5"
}

core.timer = 300

@core.event
async def on_ready():
	core.init(btn)
	print("ready")

@core.event
async def on_message_recieved(msg):
	if msg.startswith("timer"):
		if msg != "timer fail":
			core.timer = int(msg[6:])

@core.event
async def on_button_pressed(button):
	tuple = (random.randint(0,1),random.randint(0,1),random.randint(0,1))
	
	if tuple == (0,0,0):
		things = [(1,0,0), (0,1,0), (0,0,1)]
		tuple = things[random.randint(0,2)]
	
	core.tuple = tuple
	led.state(core.tuple)

@core.event
async def on_button_unpressed(button):
	led.state((0,0,0))
	sec_time = core.timer
	hr_time, sec_time = divmod(sec_time, 3600)
	min_time, sec_time = divmod(sec_time, 60)
	
	if core.tuple in ((0,0,1), (1,1,0)):
		thing = LOGIC[core.tuple]
	else:
		thing = "1"

	cond1 = eval(f"'{thing}' in str(sec_time)")
	cond2 = eval(f"'{thing}' in str(min_time)")
	cond3 = eval(f"'{thing}' in str(hr_time)")
	
	if True in (cond1, cond2, cond3):
		print("yum :D")
		await core.send("Y")
	else:
		print("cum >:(")
		await core.send("X")
	

core.run()