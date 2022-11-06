import ktanepico as ktane
import uasyncio
import random
import time

V_NO_STRIKE = [2,3,0,1]
V_ONE_STRIKE = [3,2,1,0]
V_TWO_STRIKE = [1,3,0,2]
VOWEL_CYPHERS = [V_NO_STRIKE, V_ONE_STRIKE, V_TWO_STRIKE]
NV_NO_STRIKE = [2,1,3,0]
NV_ONE_STRIKE = [0,3,2,1]
NV_TWO_STRIKE = [3,2,1,0]
NO_VOWEL_CYPHERS = [NV_NO_STRIKE, NV_ONE_STRIKE, NV_TWO_STRIKE]

module = ktane.Module(identifier="SS")
module.status_led = ktane.LED(16,17,18)
module.r_led = ktane.LED(6)
module.g_led = ktane.LED(7)
module.b_led = ktane.LED(9)
module.y_led = ktane.LED(8)
module.r_btn = ktane.Button(10)
module.g_btn = ktane.Button(12)
module.b_btn = ktane.Button(11)
module.y_btn = ktane.Button(13)
module.leds = [module.r_led, module.g_led, module.b_led, module.y_led]

module.game_state = -1
module.stage = 0
module.current_stage = 0
module.stages = []
module.stage_time = 0
module.correct_stages = []
module.strikes = 0
module.prev_strikes = None

@module.event
async def on_ready():
    print("-"*20)

    setup()
    module.init(module.r_btn)
    module.init(module.g_btn)
    module.init(module.b_btn)
    module.init(module.y_btn)

    print("READY!")

@module.event
async def on_message_received(auth, msg):
    if msg.startswith("@~STATE"):
        state = msg.split("#")[1]
        module.game_state = int(state)
    
    if msg.startswith("@~STRIKES"):
        strikes = msg.split("#")[1]
        module.strikes = int(strikes)

@module.event
async def on_second_passed(t):
    if module.game_state != 0: return

    if (time.time() - module.stage_time) >= 5:
        await show_lights()

@module.r_btn.handler("pressed", False)
async def r_press():
    if module.game_state != 0: return
    module.stage_time = time.time()
    module.r_led.value(1)

@module.r_btn.handler("unpressed", False)
async def r_press():
    if module.game_state != 0: return
    module.stage_time = time.time()
    module.r_led.value(0)
    await check(0)

@module.g_btn.handler("pressed", False)
async def g_press():
    if module.game_state != 0: return
    module.stage_time = time.time()
    module.g_led.value(1)

@module.g_btn.handler("unpressed", False)
async def g_press():
    if module.game_state != 0: return
    module.stage_time = time.time()
    module.g_led.value(0)
    await check(1)

@module.b_btn.handler("pressed", False)
async def b_press():
    if module.game_state != 0: return
    module.stage_time = time.time()
    module.b_led.value(1)

@module.b_btn.handler("unpressed", False)
async def b_press():
    if module.game_state != 0: return
    module.stage_time = time.time()
    module.b_led.value(0)
    await check(2)

@module.y_btn.handler("pressed", False)
async def y_press():
    if module.game_state != 0: return
    module.stage_time = time.time()
    module.y_led.value(1)

@module.y_btn.handler("unpressed", False)
async def y_press():
    if module.game_state != 0: return
    module.stage_time = time.time()
    module.y_led.value(0)
    await check(3)

@module.task
async def update_correct_stages():
    if module.game_state not in (0, -2): return
    if module.strikes == module.prev_strikes: return

    module.prev_strikes = module.strikes
    strikes = max(min(module.strikes, 2), 0)

    if any([x in module.bomb_data["serial"] for x in "AEIOU"]):
        module.correct_stages = [VOWEL_CYPHERS[strikes][v] for v in module.stages]
    else:
        module.correct_stages = [NO_VOWEL_CYPHERS[strikes][v] for v in module.stages]

@module.event
async def on_turn_on(): setup()

@module.event
async def on_turn_off():
    module.r_led.value(0)
    module.g_led.value(0)
    module.b_led.value(0)
    module.y_led.value(0)

async def show_lights():
    module.game_state = -2
    module.r_led.value(0)
    module.g_led.value(0)
    module.b_led.value(0)
    module.y_led.value(0)
    for i,v in zip(range(module.stage+1), module.stages):
        module.leds[v].value(1)
        await uasyncio.sleep(0.5)
        module.leds[v].value(0)
        await uasyncio.sleep(0.5) if i != module.stage else await uasyncio.sleep(0)
    module.game_state = 0 if module.game_state == -2 else module.game_state
    module.stage_time = time.time()

async def check(col_id):
    if module.correct_stages[module.current_stage] == col_id:
        if module.current_stage < module.stage: 
            module.current_stage += 1
            return
        
        print("CORRECT!")
        module.stage += 1
        module.current_stage = 0
        module.stage_time = (time.time() - 4)
        if module.stage >= len(module.stages):
            print("DEFUSED")
            module.send(0, "@~DEFUSED")
            module.game_state = 1
            module.led_state = 1
            module.r_led.value(0)
            module.g_led.value(0)
            module.b_led.value(0)
            module.y_led.value(0)
        return
    
    print("WRONG")
    module.current_stage = 0
    module.send(0, "@~STRIKE")
    await show_lights()


def setup():
    module.r_led.value(0)
    module.g_led.value(0)
    module.b_led.value(0)
    module.y_led.value(0)

    module.stage = 0
    module.stage_time = (time.time()-3)
    module.current_stage = 0
    module.strikes = 0
    module.prev_strikes = None
    module.stages = [random.randint(0,3) for i in range(random.randint(3,5))]
    module.correct_stages = []

module.run()