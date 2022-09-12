import asyncio
import random
import ktane

module = ktane.Module()

button = ktane.Button(8)
rgb = ktane.LED(3,5,7)
module.init(button)
module.pressed = False
module.colour = []

@module.event
async def on_ready():
    rgb.value(0,0,0)

@module.event
async def on_button_pressed(obj):
    module.pressed = True
    change_led_colour()

@module.event
async def on_button_unpressed(obj):
    module.pressed = False
    rgb.value(0,0,0)

@module.event
async def on_second_passed(t):
    if module.pressed:
        change_led_colour()

def change_led_colour():
    def __core():
        color = [random.randint(0,1),random.randint(0,1),random.randint(0,1)]
        if color == [0,0,0]: color = [1,1,1]
        if module.colour == color: color = __core()
        return color
    module.colour = __core()
    rgb.value(*module.colour)

module.run()