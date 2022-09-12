import ktanepico as ktane

module = ktane.Module(identifier="BTN")
send_button = ktane.Button(15)
led = ktane.IO(25,1)

@module.event
async def on_ready():
    led.value(0)
    
    module.init(send_button)

    print("-"*10)
    print("READY!")

@send_button.handler("pressed")
async def send_msg():
    module.send("hi!")
    print("SENT!")

@module.event
async def on_message_received(auth, msg):
    print(f"{auth} >> {msg}")

module.run()