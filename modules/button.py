import ktane

module = ktane.Module(identifier="B")
module.status_led = ktane.LED(36, 38, 40)
module.game_state = -1

@module.event
async def on_ready():
    module.status_led.value(0)

    setup()
    module.status_led.value(0,1,0)

    print("-"*20)
    print("READY!")

@module.event
async def on_message_received(auth, msg):
    if msg == "@~":
        return

    if msg.startswith("@~STATE"):
        state = msg.split(" ")[1]
        module.game_state = int(state)
        return

def setup():
    pass

module.run()