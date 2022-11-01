import ktane

module = ktane.Module(identifier="BTN")
module.strike_button = ktane.Button(15)

@module.event
async def on_ready():
    module.init(module.strike_button)
    print("-"*20)
    print("READY!")

@module.strike_button.handler("pressed")
async def send_strike():
    module.send(0, "@~STRIKE")

module.run()