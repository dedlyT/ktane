import ktanepico as ktane
import uasyncio
import time

# MAKE PRESSURE ALIGN WITH PERSONAL TIMER

module = ktane.Module(identifier="CD")
module.status_led = ktane.LED(15,14,13)
module.bars = [ktane.LED(pin, pwm=True) for pin in [28,27,26,22,21,20,19,18,17,16]]
module.relief_btn = ktane.Button(12)

module.game_state = -1
module.progress = 0
module.timer = 45
module.previous_pressure_time = 0
module.previous_pressure_timer_time = 0
module.previous_relief_time = 0
module.previous_relief_timer_time = 0

@module.event
async def on_ready():
    print("-"*20)

    module.init(module.relief_btn)
    setup()

    print("READY!")

@module.task
async def build_pressure():
    if module.game_state != 0: return

    if time.ticks_diff(time.ticks_ms(), module.previous_pressure_time) < 100: return
    module.previous_pressure_time = time.ticks_ms()
    module.progress += (1000/45)/10
    
    if time.ticks_diff(time.ticks_ms(), module.previous_pressure_timer_time) >= 1000:
        module.previous_pressure_timer_time = time.ticks_ms()
        module.timer -= 1
        print(module.timer)

    if module.progress >= 1000:
        module.progress = 0
        module.game_state = 1
        module.led_state = -1
        module.send(0, "@~STRIKE")

@module.task
async def relieve_pressure():
    if module.game_state != -2: return

    if time.ticks_diff(time.ticks_ms(), module.previous_relief_time) < 100: return
    module.previous_relief_time = time.ticks_ms()
    module.progress -= ((1000/45)/10)*5

    if time.ticks_diff(time.ticks_ms(), module.previous_relief_timer_time) >= 200:
        module.previous_relief_timer_time = time.ticks_ms()
        module.timer += 1
        print(module.timer)
    
    if module.progress <= 0:
        module.progress = 0
        module.game_state = -3

@module.task
async def update_bar():
    prog = module.progress
    for bar in module.bars:
        y = max(min((prog), 100), 0)
        bar.value(y)
        prog -= y
        await uasyncio.sleep(0)

@module.relief_btn.handler("pressed")
async def button_held():
    if module.game_state not in (0, -2): return
    print(f"CALC: {45 - module.timer} ::: {module.timer}")
    print(f"CALC: {1000 - module.progress} ::: {module.progress}")
    module.send(0, "@~RELIEVING")
    module.game_state = -2

@module.relief_btn.handler("unpressed")
async def button_released():
    if module.game_state not in (-2, -3): return
    module.send(0, "@~N_RELIEVING")
    module.game_state = 0

@module.event
async def on_message_received(auth, msg):
    if msg.startswith("@~STATE"):
        state = msg.split("#")[1]
        if int(state) == 2 and module.game_state == 1: return
        module.game_state = int(state)

@module.event
async def on_turn_on(): setup()

@module.event
async def on_turn_off():
    module.progress = 0

def setup():
    module.previous_pressure_time = 0
    module.previous_pressure_timer_time = 0
    module.previous_relief_time = 0
    module.previous_relief_timer_time = 0
    module.progress = 0
    module.timer = 45
    print(module.timer)

module.run()