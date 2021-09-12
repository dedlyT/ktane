import ktane_lib as ktane
import asyncio
import random
import time

core = ktane.Module("timer")
lcd = ktane.LCD(0x27)
btn = ktane.Button(16, "down")
bzrLow = ktane.Buzzer(18)
bzrMid = ktane.Buzzer(13)
bzrHgh = ktane.Buzzer(15)

core.new_time = core.default_time
core.on = False

@core.task
async def test():
    pass

@core.event
async def on_ready():
    print("loop on")
    core.init(btn)

@core.event
async def on_timer_update(current_time):
    if not core.on:
        return
    
    calc_time = current_time[0] + (current_time[1] * 60) + (current_time[2] * 3600)
    core.new_time = core.default_time - calc_time
    sec_time = core.new_time
    hr_time, sec_time = divmod(sec_time, 3600)
    min_time, sec_time = divmod(sec_time, 60)

    if sec_time <= 9:
        sec_time = f"0{sec_time}"
    if min_time <= 9:
        min_time = f"0{min_time}"
    cock = hr_time
    if hr_time <= 9:
        hr_time = f"0{hr_time}"

    pass_time = f"{min_time}:{sec_time}"
    if cock >= 1:
        pass_time = f"{hr_time}:{min_time}:{sec_time}"

    if core._x == 3:
        await die()
        return

    text = ""
    for i in range(core._x):
        text += "X"
    rangeNum = 3 - core._x
    for i in range(rangeNum):
        text += "-"

    lcd.text(text, 1, align="center")
    lcd.text(pass_time, 2, align="center")
    
    clc_time = core.default_time - calc_time

    await core.send(f"{clc_time}\n")

    if clc_time > 180:
        await bzrLow.buzz(1, 0.1)    
    elif clc_time == 180:
        await level_up(1)
    elif clc_time > 120 and clc_time < 180:
        await bzrLow.buzz(1, 0.1)
    elif clc_time == 120:
        await level_up(1)
    elif clc_time > 60 and clc_time < 120:
        await bzrMid.buzz(1, 0.1)
    elif clc_time == 60:
        await level_up(2)
    elif clc_time > 30 and clc_time < 60:
        await bzrMid.buzz(1, 0.1)
    elif clc_time == 30:
        await level_up(3)
    elif clc_time > 0 and clc_time < 30:
        await bzrHgh.buzz(1, 0.1)
    elif clc_time == 0:
        await die()
        return


@core.event
async def on_message_recieved(msg):
    if msg == "module X":
        print("WRONG!")
        core._x += 1
        await bzrHgh.buzz(1)
        await bzrLow.buzz(1)
        await asyncio.sleep(0.1)
        await bzrHgh.buzz(0)
        await bzrLow.buzz(0)
    if msg == "module Y":
        print("CORRECT!")
    if msg in ("module X", "module Y"):
        text = ""
        for i in range(core._x):
            text += "X"
        rangeNum = 3 - core._x
        for i in range(rangeNum):
            text += "-"
        lcd.text(text, 1, align="center")
        

@core.event
async def on_button_pressed(button):
    thing = not core.on
    
    if thing:
        await turnOn()
    
    if not thing:
        await turnOff()


async def turnOff():
    lcd.text("TURNING OFF", 1, align="center")
    lcd.text("", 2, align="center")
    await asyncio.sleep(1)
    core.on = False
    print(core.on)
    lcd.text("", 1)
    lcd.text("", 2)


async def turnOn():
    core._sec = 0
    core._min = 0
    core._hour = 0
    core._day = 0
    core._old_sec = 0
    core._x = 0
    lcd.text("TURNING ON", 1, align="center")
    lcd.text("", 2, align="center")
    await asyncio.sleep(1)
    core.on = True
    print(core.on)
    lcd.text("", 1)
    lcd.text("", 2)


async def die():
    await bzrHgh.buzz(1)
    await bzrMid.buzz(1)
    await bzrLow.buzz(1)
    await asyncio.sleep(1)
    await bzrHgh.buzz(0)
    await bzrMid.buzz(0)
    await bzrLow.buzz(0)
    lcd.text("",1)
    lcd.text("",2)
    await asyncio.sleep(1)
    await turnOff()
    return


async def level_up(num):
    ecc = {
           1:0.1,
           2:0.09,
           3:0.08
          }
    for i in range(3):
        await bzrLow.buzz(1, 0.1)
        await asyncio.sleep(ecc[num])

core.run()