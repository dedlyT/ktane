import RPi.GPIO as GPIO
import asyncio
import serial
import random
import json
import time

GPIO.setmode(GPIO.BOARD)

FUNCS = [
    "on_ready",
    "on_message_received",
    "on_second_passed",
    "on_minute_passed",
    "on_hour_passed",
    "on_button_pressed",
    "on_button_unpressed",
    "on_io_rise",
    "on_io_fall",
    "on_turn_off",
    "on_turn_on"
]
STATUS_LED_STATES = {
    -3: (1,1,1),
    -2: (1,0,0),
    -1: (0,0,0),
    0: (0,1,0),
    1: (1,0,1)
}



class Module:
    
    def __init__(self, **kwargs):
        self.__id = "".join([str(random.randint(0,9)) for i in range(5)])

        self.__run_coros_buf = []
        self.__io = []
        self.__buttons = []
        self.__tasks = []
        self.__internal_time = 0
        self.__UART = serial.Serial(port = "/dev/ttyS0", baudrate = 115200, timeout = 1)
        self.__UART_buf = []
        self.__connected_modules = {}
        self.__status_led = None
        self.__status_led_time = 0
        self.__status_led_state = 0
        self.__setup = False
        self.__boom = False
        self.__bomb_data = {}
        self.__led_state = -1

        if "identifier" not in kwargs.keys(): 
            raise ValueError("Module missing identifier!")
        self.identifier = kwargs["identifier"]

        if self.identifier == "T": 
            self.__id = 0
            self.__setup = True

        self.__time = {}
        for t in ("s","m","h"):
            self.__time[t] = 0

        self.__funcs = {}
        for func in FUNCS:
            self.__funcs[func] = self._empty

    def event(self, func): #DECORATOR
        if func.__name__ in FUNCS:
            self.__funcs[func.__name__] = func
    
    def task(self, func): #DECORATOR
        self.__tasks += [func]

    def init(self, *objs):
        for obj in objs:
            list = None
            if isinstance(obj, Button): list = self.__buttons
            if isinstance(obj, IO): 
                if obj.type == GPIO.OUT: raise Exception(f"IO {obj.pin} cannot be initialised; it is set up as an output!")
                list = self.__io

            if list is not None:
                list += [{ "obj":obj, "val":None }]

    def send(self, auth, msg):
        self.__UART_buf += [(False, auth, msg)]

    @classmethod
    async def _empty(self, *args, **kwargs): pass

    @property
    def time(self): return self.__time

    @property
    def id(self): return self.__id

    @property
    def modules(self): return self.__connected_modules

    @property
    def bomb_data(self): return self.__bomb_data

    @property
    def status_led(self): return self.__status_led

    @property
    def led_state(self): return self.__led_state

    @time.setter
    def time(self, val):
        if type(val) not in (list, dict, int, float): raise ValueError("`time` attribute must be dict or list!")
        
        if type(val) in (int, float):
            for t in ("s", "m", "h"):
                self.__time[t] = val
                
        if val is list:
            for i,v in enumerate(val): 
                self.__time[("s", "m", "h")[i]] = v
        
        if val is dict:
            for t,v in val.items():
                self.__time[t] = v
    
    @status_led.setter
    def status_led(self, led_obj):
        if not isinstance(led_obj, LED): raise ValueError("`status_led` attribute must be a `ktane.LED`!")
        self.__status_led = led_obj
    
    @led_state.setter
    def led_state(self, state):
        if state not in list(STATUS_LED_STATES.keys()): raise ValueError("Not a valid state for status LED!")
        self.__led_state = state

    #CORE THREADS
    async def __status_led_thread(self):
        while True:
            await asyncio.sleep(0)
            if self.__setup is False:
                if time.time() >= self.__status_led_time:
                    if self.__status_led_state == 1:
                        self.__status_led_state = 0
                        self.__status_led.value(1,1,0)
                        self.__status_led_time = (time.time() + 1)
                    else:
                        self.__status_led_state = 1
                        self.__status_led.value(0,0,0)
                        self.__status_led_time = (time.time() + 1)
                continue
            
            if self.__boom is True:
                if time.time() >= self.__status_led_time:
                    if self.__status_led_state == 1:
                        self.__status_led_state = 0
                        self.__status_led.value(1,0,0)
                        self.__status_led_time = (time.time() + 0.5)
                    else:
                        self.__status_led_state = 1
                        self.__status_led.value(0,0,0)
                        self.__status_led_time = (time.time() + 0.5)
            
            self.__status_led.value(STATUS_LED_STATES[self.__led_state])
            
    async def __UART_buffer(self):
        while True:
            if len(self.__UART_buf):
                data = self.__UART_buf.pop(0)

                passing = data[0]
                auth = data[1]
                msg = data[2]
                
                tx = f"{self.identifier}:{self.__id}:{auth}>{msg}\n"
                if passing: tx = f"{msg}\n"

                self.__UART.write(tx.encode("utf-8"))
            
            if self.__UART.inWaiting():
                b = self.__UART.readline()
                if b != b"\x00":
                    rx = b.decode("utf-8")[:-1]
                    args = rx.split(">")
                    address = args[0].split(":")

                    msg = args[1]

                    #Is message mine?
                    if address[1] == str(self.__id):
                        if msg == "@~SETUP":
                            self.__led_state = -2
                            self.__setup = None
                            print("setup failed.")
                        continue
                    
                    #Is message for me?
                    if address[2] in ("-1", str(self.__id)):
                        if address[2] == "-1":
                            if str(self.__id) != "0": self.__UART_buf += [(True, None, rx)]

                        if msg == "@~SETUP":
                            self.__connected_modules[address[1]] = {"type": address[0], "defused": False}
                            self.send(address[1], "@~SETUP_OK")
                            continue
                        if msg == "@~SEND_SETUP":
                            self.send(0, "@~SETUP")
                            continue
                        if msg == "@~SETUP_OK":
                            self.__led_state = 0
                            self.__setup = True
                            self.__run_coros_buf += [self.__funcs["on_turn_on"]()]
                            print("setup complete!")
                            continue
                        if msg == "@~TURN_OFF":
                            self.__led_state = -1
                            self.__run_coros_buf += [self.__funcs["on_turn_off"]()]
                            continue
                        if msg == "@~BOOM":
                            self.__boom = False
                            self.__run_coros_buf += [self.__funcs["on_turn_off"]()]
                            continue
                        if msg == "@~TURN_ON":
                            self.__led_state = 0
                            self.__run_coros_buf += [self.__funcs["on_turn_on"]()]
                            continue
                        if msg.startswith("@~BOMB_DETAILS"):
                            data = msg.split("#")[1]
                            self.__bomb_data = json.loads(data)
                            continue
                        
                        self.__run_coros_buf += [self.__funcs["on_message_received"]((*address[0:2],), msg)]
                    else:
                        self.__UART_buf += [(True, None, rx)]
            
            await asyncio.sleep(0)
    
    async def __time_tracker(self):
        while True:
            if (time.time() - self.__internal_time) >= 1:
                self.__internal_time = time.time()
                time_calls = []
                self.__time["s"]+=1
                time_calls += ["on_second_passed"]
                if self.__time["s"]>=60:
                    self.__time["s"]=0
                    self.__time["m"]+=1
                    time_calls += ["on_minute_passed"]
                    if self.__time["m"]>=60:
                        self.__time["m"]=0
                        self.__time["h"]+=1
                        time_calls += ["on_hour_passed"]
                for time_call in time_calls:
                    self.__run_coros_buf += [self.__funcs[time_call](self.__time)]
            
            await asyncio.sleep(0)

    async def __main_loop(self):
        self.__internal_time = time.time()
        self.__started = False
        await asyncio.gather(self.__funcs["on_ready"]())
        
        while True:
            #BUTTONS
            for button in self.__buttons:
                obj = button["obj"]
                val = button["val"]
                if val != obj.value():
                    if obj.value(): 
                        if not self.__started:
                            if obj.pressed_start: self.__run_coros_buf += [obj.pressed()]
                        else: 
                            self.__run_coros_buf += [obj.pressed()]
                        self.__run_coros_buf += [self.__funcs["on_button_pressed"](obj)]
                    if not obj.value():
                        if not self.__started:
                            if obj.unpressed_start: self.__run_coros_buf += [obj.unpressed()]
                        else: 
                            self.__run_coros_buf += [obj.unpressed()]
                        self.__run_coros_buf += [self.__funcs["on_button_unpressed"](obj)]
                    button["val"] = obj.value()
            
            #IO
            for io in self.__io:
                obj = io["obj"]
                val = io["val"]
                if val != obj.value():
                    if obj.value(): 
                        if not self.__started:
                            if obj.rise_start: self.__run_coros_buf += [obj.rise()]
                        else: 
                            self.__run_coros_buf += [obj.rise()]
                        self.__run_coros_buf += [self.__funcs["on_io_rise"](obj)]
                    if not obj.value(): 
                        if not self.__started:
                            if obj.fall_start: self.__run_coros_buf += [obj.fall()]
                        else: 
                            self.__run_coros_buf += [obj.fall()]
                        self.__run_coros_buf += [self.__funcs["on_io_fall"](obj)]
                    io["val"] = obj.value()

            #EMPTY BUFFER
            self.__run_coros_buf += [x() for x in self.__tasks]
            while self.__run_coros_buf:
                coro = self.__run_coros_buf.pop(0)
                task = asyncio.create_task(coro)
                await task
            
            self.__started = True
            await asyncio.sleep(0)
    
    async def __run(self):
        if str(self.__id) == "0":
            self.send(-1, "@~SEND_SETUP")

        task1 = asyncio.create_task(self.__main_loop())
        task2 = asyncio.create_task(self.__UART_buffer())
        task3 = asyncio.create_task(self.__time_tracker())
        task4 = asyncio.create_task(self.__status_led_thread())

        await task1
        await task2
        await task3
        await task4

    def run(self):
        asyncio.run(self.__run())



class IO:

    def __init__(self, pin, type, **kwargs):
        if "pud" not in list(kwargs.keys()): kwargs["pud"] = False
        if "pwm" not in list(kwargs.keys()): kwargs["pwm"] = False

        self.pin = pin
        self.val = None
        self.type = (GPIO.IN, GPIO.OUT)[type]
        self.pud = (GPIO.PUD_DOWN, GPIO.PUD_UP)[kwargs["pud"]]
        self.pwm = kwargs["pwm"]
        self.freq = 100
        self.__handlers = {"rise": {"func":Module._empty, "on_startup":True}, 
                            "fall": {"func":Module._empty, "on_startup":True}}

        settings = [self.pin, self.type] if self.type == GPIO.OUT else [self.pin, self.type, self.pud]
        GPIO.setup(*settings)
        if self.pwm:
            self.__obj = GPIO.PWM(self.pin, self.freq)
            self.__obj.start(0)

    def value(self, val=None):
        self.val = val
        if val is None: return GPIO.input(self.pin)
        if self.type is GPIO.IN: raise Exception(f"IO {self.pin} was set up as an input, not an output")
        if self.pwm:
            if val>1: val /= 100
            val *= 100 
            return self.__obj.ChangeDutyCycle(val)
        return GPIO.output(self.pin, val)

    def switch(self):
        if self.type is GPIO.IN: raise Exception(f"IO {self.pin} was set up as an input, not an output")
        return self.value(not self.val)

    #DECORATOR
    def handler(self, type, on_startup=True):
        def decorator(func):
            if type not in self.__handlers.keys(): raise ValueError(f"`{type}` is not a handler!")
            self.__handlers[type]["func"] = func
            self.__handlers[type]["on_startup"] = on_startup
        return decorator

    @property
    def rise(self): return self.__handlers["rise"]["func"]

    @property
    def rise_start(self): return self.__handlers["rise"]["on_startup"]
    
    @property
    def fall(self): return self.__handlers["fall"]["func"]

    @property
    def fall_start(self): return self.__handlers["fall"]["on_startup"]



class Button:

    def __init__(self, pin, pud=False):
        self.pin = pin
        self.__obj = IO(self.pin, False, pud=pud)
        self.__handlers = {"pressed": {"func":Module._empty, "on_startup":True}, 
                        "unpressed": {"func": Module._empty, "on_startup":True}}
    
    def value(self):
        return self.__obj.value()

    #DECORATOR
    def handler(self, type, on_startup=True):
        def decorator(func):
            if type not in self.__handlers.keys(): raise ValueError(f"`{type}` is not a handler!")
            self.__handlers[type]["func"] = func
            self.__handlers[type]["on_startup"] = on_startup
        return decorator

    @property
    def pressed(self): return self.__handlers["pressed"]["func"]

    @property
    def pressed_start(self): return self.__handlers["pressed"]["on_startup"]
    
    @property
    def unpressed(self): return self.__handlers["unpressed"]["func"]

    @property
    def unpressed_start(self): return self.__handlers["unpressed"]["on_startup"]



class LED:

    def __init__(self, pin1, pin2=None, pin3=None, **kwargs):
        if "pwm" not in list(kwargs.keys()): kwargs["pwm"] = False

        self.pin1 = pin1
        self.pin2 = None
        self.pin3 = None
        self.__pwm = kwargs["pwm"]

        self.__obj1 = IO(self.pin1, True, pwm=self.__pwm)

        if pin2 is not None:
            self.pin2 = pin2
            self.__obj2 = IO(self.pin2, True, pwm=self.__pwm)
            self.pin3 = pin3
            self.__obj3 = IO(self.pin3, True, pwm=self.__pwm)
    
    def value(self, val1, val2=None, val3=None):
        if isinstance(val1, tuple) or isinstance(val1, list):
            objs = [self.__obj1, self.__obj2, self.__obj3]
            for obj,val in zip(objs, val1):
                obj.value(val)
        else:
            self.__obj1.value(val1)
            if val2 is not None:
                self.__obj2.value(val2)
                self.__obj3.value(val3)
    
    def switch(self):
        self.__obj1.switch()
        if self.pin2 is not None:
            self.__obj2.switch()
            self.__obj3.switch()