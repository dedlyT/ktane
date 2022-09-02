import RPi.GPIO as GPIO
import asyncio
import time

GPIO.setmode(GPIO.BOARD)

FUNCS = [
    "on_ready",
    "on_second_passed",
    "on_minute_passed",
    "on_hour_passed",
    "on_button_pressed",
    "on_button_unpressed",
    "on_io_rise",
    "on_io_fall"
]


class Module:
    
    def __init__(self):
        self.__io = []
        self.__buttons = []
        self.__tasks = []
        self.__internal_time = 0

        self.time = {}
        for t in ("s","m","h"):
            self.time[t] = 0

        self.__funcs = {}
        for func in FUNCS:
            self.__funcs[func] = self.__empty

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
                if obj.type == GPIO.IN: raise Exception(f"IO {obj.pin} cannot be initialised; it is set up as an input!")
                list = self.__io

            if list is not None:
                list += [{ "obj":obj, "val":False }]
    
    def get_time(self):
        return self.time

    async def __empty(self, *args, **kwargs): pass

    async def __run(self):
        self.__internal_time = time.time()
        asyncio.gather(self.__funcs["on_ready"]())
        
        while True:
            #TASKS
            run_coros = []
            for task in self.__tasks:
                run_coros += [task()]

            #TIME
            if (time.time() - self.__internal_time) > 1:
                self.__internal_time = time.time()
                time_calls = []
                self.time["s"]+=1
                time_calls += ["on_second_passed"]
                if self.time["s"]>=60:
                    self.time["s"]=0
                    self.time["m"]+=1
                    time_calls += ["on_minute_passed"]
                    if self.time["m"]>=60:
                        self.time["m"]=0
                        self.time["h"]+=1
                        time_calls += ["on_hour_passed"]
                for time_call in time_calls:
                    run_coros += [self.__funcs[time_call](self.time)]

            #BUTTONS
            for button in self.__buttons:
                obj = button["obj"]
                val = button["val"]
                if val != obj.value():
                    if obj.value(): run_coros += [self.__funcs["on_button_pressed"](obj)]
                    if not obj.value(): run_coros += [self.__funcs["on_button_unpressed"](obj)]
                    button["val"] = obj.value()
            
            #IO
            for io in self.__io:
                obj = io["obj"]
                val = io["val"]
                if val != obj.value():
                    if obj.value(): run_coros += [self.__funcs["on_io_rise"](obj)]
                    if not obj.value(): run_coros += [self.__funcs["on_io_fall"](obj)]
                    io["val"] = obj.value()

            asyncio.gather(*run_coros)
            await asyncio.sleep(0.001)

    def run(self):
        asyncio.run(self.__run())


class IO:

    def __init__(self, pin, type, **kwargs):
        if "pud" not in list(kwargs.keys()): kwargs["pud"] = False

        self.pin = pin
        self.val = None
        self.type = (GPIO.IN, GPIO.OUT)[type]
        self.pud = (GPIO.PUD_DOWN, GPIO.PUD_UP)[kwargs["pud"]]

        settings = [self.pin, self.type] if self.type == GPIO.OUT else [self.pin, self.type, self.pud]
        GPIO.setup(*settings)

    def value(self, val=None):
        self.val = val
        if val is None: return GPIO.input(self.pin)
        if self.type is GPIO.PUD_DOWN: raise Exception(f"IO {self.pin} was set up as an input, not an output")
        return GPIO.output(self.pin, val)

    def switch(self):
        if self.type is GPIO.PUD_DOWN: raise Exception(f"IO {self.pin} was set up as an input, not an output")
        return self.value(not self.val)


class Button:

    def __init__(self, pin, pud=False):
        self.pin = pin
        self.__obj = IO(self.pin, False, pud=pud)
    
    def value(self):
        return self.__obj.value()


class LED:

    def __init__(self, pin1, pin2=None, pin3=None):
        self.pin1 = pin1
        self.pin2 = None
        self.pin3 = None

        self.__obj1 = IO(self.pin1, True)

        if pin2 is not None:
            self.pin2 = pin2
            self.__obj2 = IO(self.pin2, True)
            self.pin3 = pin3
            self.__obj3 = IO(self.pin3, True)
    
    def value(self, val1, val2=None, val3=None):
        self.__obj1.value(val1)
        if val2 is not None:
            self.__obj2.value(val2)
            self.__obj3.value(val3)
    
    def switch(self):
        self.__obj1.switch()
        if self.pin2 is not None:
            self.__obj2.switch()
            self.__obj3.switch()
