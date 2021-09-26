from RPi import GPIO as GPIO
from smbus import SMBus
import asyncio
import serial
import time

SEND_UART = serial.Serial("/dev/serial0", 9600)
RECIEVE_UART = serial.Serial("/dev/serial0", 9600, timeout=1)
FUNCS = [
    "on_ready",
    "on_timer_update",
    "on_button_pressed",
    "on_button_unpressed",
    "on_message_recieved",
    "on_io_rise",
    "on_io_fall"]
TIME_INCS = [
    "sec",
    "min",
    "hour",
    "day"]
ALIGN_FUNC = {
    'left': 'ljust',
    'right': 'rjust',
    'center': 'center'}
CLEAR_DISPLAY = 0x01
ENABLE_BIT = 0b00000100
LINES = {
    1: 0x80,
    2: 0xC0,
    3: 0x94,
    4: 0xD4}

GPIO.setmode(GPIO.BOARD)

class Module(object):

    def __init__(self, name, *args):
        for func in FUNCS:
            exec(f"self._{func} = self._empty")

        self.__tasks = [self._empty]
        self.__name = name
        self._buttons = []
        self._io = []
        self.default_time = 300

        for inc in TIME_INCS:
            exec(f"self._{inc} = 0")

    #Empty method
    async def _empty(self, *args, **kwargs):
        pass

    #@EVENT decorator
    def event(self, func):
        name = func.__name__
        if name in FUNCS:
            exec(f"self._{name} = func")

    #@TASK decorator
    def task(self, func):
        r = self.__tasks+[func]
        self.__tasks = [func] if self._empty in self.__tasks else r

    #Register certain parts (e.g. Buttons) that can trigger certain events
    #(e.g. on_button_pressed())
    def init(self, item):
        if isinstance(item, Button):
            self._buttons = self._buttons+[[item, False]]
        if isinstance(item, IO):
            if item.io == GPIO.IN:
                self._io = self._io+[[item, False]]
            else:
                raise TypeError("IO obj must be of type 'GPIO.IN'")

    #Send UART
    async def send(self, txt: str):
        SEND_UART.write(bytes(f"{self.__name} {txt}\n", encoding="utf8"))

    #Main loop
    async def __loop(self):
        await self._on_ready()
        self._old_sec = 0
        old_time = time.time()
        while True:
            #events
            #on_timer_update()
            if bool(self._old_sec):
                self._old_sec = 0
                await self._on_timer_update((self._sec, self._min, self._hour, self._day))

            #on_button_pressed() /// on_button_unpressed()
            for btn in self._buttons:
                btn_button = btn[0]
                btn_state = btn[1]
                if btn_button.input() and not btn_state:
                    btn[1] = True
                    await self._on_button_pressed(btn_button)
                elif not btn_button.input() and btn_state:
                    await asyncio.sleep(0.05)
                    if not btn_button.input() and btn_state:
                        btn[1] = False
                        await self._on_button_unpressed(btn_button)

            #on_io_rise() /// on_io_fall()
            for io in self._io:
                io_io = io[0]
                io_state = io[1]
                if io_io.state() and not io_state:
                    io[1] = True
                    await self._on_io_rise(io_io)
                elif not io_io.state() and io_state:
                    await asyncio.sleep(0.05)
                    if not io_io.state() and io_state:
                        io[1] = False
                        await self._on_io_fall(io_io)

            #on_message_recieved()
            if RECIEVE_UART.in_waiting > 0:
                message = RECIEVE_UART.readline().decode("utf-8").rstrip()
                await self._on_message_recieved(message)

            #tasks
            for task in self.__tasks:
                await task()

            #timer
            current_time = time.time()
            calc_time = current_time - old_time
            if calc_time >= 1:
                old_time = current_time
                self._sec += 1
                self._old_sec = 1
                if self._sec == 60:
                    self._sec = 0
                    self._min += 1
                    if self._min == 60:
                        self._min = 0
                        self._hour += 1
                        if self._hour == 60:
                            self._hour = 0
                            self._day += 1
    
    def __loop_exception(self, loop, ctx):
        loop.default_exception_handler(ctx)
        exception = ctx.get('exception')
        if isinstance(exception, KeyboardInterrupt):
            print("\n\nFINISHING...\n\n")
            loop.stop()

    def run(self):
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(self.__loop_exception)
        loop.create_task(self.__loop())
        loop.run_forever()


class LCD(object):

    def __init__(self, address=0x27, bus=1, width=20, rows=4):
        self.address = address
        self.bus = SMBus(bus)
        self.delay = 0.0005
        self.rows = rows
        self.width = width

        self.write(0x33)
        self.write(0x32)
        self.write(0x06)
        self.write(0x0C)
        self.write(0x28)
        self.write(CLEAR_DISPLAY)
        time.sleep(self.delay)

    def _write_byte(self, byte):
        self.bus.write_byte(self.address, byte)
        self.bus.write_byte(self.address, (byte | ENABLE_BIT))
        time.sleep(self.delay)
        self.bus.write_byte(self.address,(byte & ~ENABLE_BIT))
        time.sleep(self.delay)

    def write(self, byte, mode=0):
        self._write_byte(mode | (byte & 0xF0) | 0x08)
        self._write_byte(mode | ((byte << 4) & 0xF0) | 0x08)

    def text(self, text, line, align='left'):
        self.write(LINES.get(line, LINES[1]))
        text, other_lines = self.get_text_line(text)
        text = getattr(text, ALIGN_FUNC.get(align, 'ljust'))(self.width)
        for char in text:
            self.write(ord(char), mode=1)
        if other_lines and line <= self.rows - 1:
            self.text(other_lines, line + 1, align=align)

    def get_text_line(self, text):
        line_break = self.width
        if len(text) > self.width:
            line_break = text[:self.width + 1].rfind(' ')
        if line_break < 0:
            line_break = self.width
        return text[:line_break], text[line_break:].strip()

    def clear(self):
        self.write(CLEAR_DISPLAY)


class Button(object):
    
    def __init__(self, pin, pud="DEFAULT"):
        self.pin = pin
        self._pud = pud
        if self._pud == "DEFAULT":
            self._pud = GPIO.PUD_DOWN
        if self._pud is None:
            GPIO.setup(self.pin, GPIO.IN)
        elif self._pud in ("up", GPIO.PUD_UP, 1):
            GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        elif self._pud in ("down", GPIO.PUD_DOWN, 0):
            GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        else:
            raise ValueError("'pud' must be either 'up' or 'down'")
        
    #Button state GETTER
    def input(self):
        return GPIO.input(self.pin)


class LED(object):

    def __init__(self, pin, type="single"):
        self.type = type
        if self.type == "single":
            self.pin = pin
            GPIO.setup(self.pin, GPIO.OUT)
        elif self.type == "rgb":
            self.pinr = pin[0]
            self.ping = pin[1]
            self.pinb = pin[2]
            GPIO.setup(self.pinr, GPIO.OUT)
            GPIO.setup(self.ping, GPIO.OUT)
            GPIO.setup(self.pinb, GPIO.OUT)
        else:
            raise ValueError("'type' must be either 'single' or 'rgb'")

    def state(self, power=None):
        if power is None:
            if self.type == "single":
                return GPIO.input(self.pin)
            elif self.type == "rgb":
                rin = GPIO.input(self.pinr)
                gin = GPIO.input(self.ping)
                bin = GPIO.input(self.pinb)
                return (rin, gin, bin)
        elif self.type == "single":
            if power in (1, GPIO.HIGH, True, 0, GPIO.LOW, False):
                GPIO.output(self.pin, power)
            else:
                raise ValueError("'power' must be either 'GPIO.HIGH' or 'GPIO.LOW'")
        elif self.type == "rgb":
            thing = ["r", "g", "b"]
            for i in range(0,3):
                if power[i] in (0, 1, False, True, GPIO.LOW, GPIO.HIGH):
                    exec(f"GPIO.output(self.pin{thing[i]}, power[i])")
                else:
                    raise ValueError(f"'power' value '{i}' must be either 'GPIO.HIGH' or 'GPIO.LOW'")


class Buzzer(object):

    def __init__(self, pin):
        self.pin = pin
        self.__async_state = False
        self.__async_time = None
        GPIO.setup(self.pin, GPIO.OUT, initial=GPIO.LOW)

    async def buzz(self, state: (int, float, bool), time: (int, float, None)=None):
        if state in ("on", 1, True, GPIO.HIGH):
            state = True
        elif state in ("off", 0, False, GPIO.LOW):
            state = False
        self.__async_state = state
        self.__async_time = time
        loop = asyncio.get_event_loop()
        await self.__buzz()

    async def __buzz(self):
        GPIO.output(self.pin, self.__async_state)
        if self.__async_time is not None:
            await asyncio.sleep(self.__async_time)
            GPIO.output(self.pin, not self.__async_state)


class IO(object):

    def __init__(self, pin, io, arg1=None):
        if io in ("in", 0):
            io = GPIO.IN
        elif io in ("out", 1):
            io = GPIO.OUT

        if arg1 in ("down", 0):
            arg1 = GPIO.PUD_DOWN
        elif arg1 in ("up", 1):
            arg1 = GPIO.PUD_UP
        
        self.io = io
        self.pin = pin

        if arg1 is None:
            GPIO.setup(self.pin, self.io)
        elif arg1 in (GPIO.PUD_DOWN, GPIO.PUD_UP):
            self.pud = arg1
            GPIO.setup(self.pin, self.io, pull_up_down=self.pud)

    def type(self, io=None):
        if io is None:
            return self.io
        elif io in (GPIO.IN, GPIO.OUT):
            GPIO.setup(self.pin, io)
            self.io = io

    def state(self, state=None):
        if state is None:
            return GPIO.input(self.pin)
        elif state in (1, True, GPIO.HIGH, 0, False, GPIO.LOW):
            GPIO.output(self.pin, state)