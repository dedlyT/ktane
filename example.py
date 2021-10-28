import pktanelib as k
import uasyncio

kc = k.Module("test")
kc.init(k.Button(15))
kc.init(k.IO(14, "in"))
kc.thing = False # type: ignore
led = k.LED(25)

@kc.event
async def on_ready():
    print("hi!")
    
@kc.event
async def on_timer_update(time):
    print(time)

@kc.event
async def on_button_pressed(btn):
    print(f"{btn} pressed!")
    kc.thing = True # type: ignore

@kc.event
async def on_button_unpressed(btn):
    print(f"{btn} unpressed.")
    kc.thing = False # type: ignore

@kc.event
async def on_io_rise(io):
    print(f"{io} rise!")

@kc.event
async def on_io_fall(io):
    print(f"{io} fall.")

@kc.s_task
async def blink():
    if not kc.thing: # type: ignore
        led.toggle()

kc.run()