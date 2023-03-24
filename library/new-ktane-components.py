import RPi.GPIO as GPIO
import asyncio


GPIO.setmode(GPIO.BOARD)


# IN/OUT PIN OBJECT
class IO:

    def __init__(self, pin, io, pud=None):
        self.pin = pin
        self.io = (GPIO.IN, GPIO.OUT)[io]
        
        settings = [self.pin, self.io]

        # APPEND PULL_UP_DOWN RESISTOR STATE TO GPIO.IN
        if self.io == GPIO.IN:
            if pud is None: pud = False

            self.pud = (GPIO.PUD_DOWN, GPIO.PUD_UP)[pud]
            settings.append(self.pud)
        
        GPIO.setup(*settings)

    def value(self, state=None):
        if state is None:
            if self.io == GPIO.IN:
                return GPIO.input(self.pin)
            else:
                return GPIO
        
        GPIO.output(self.pin)