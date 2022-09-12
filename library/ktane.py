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
    
    def __init__(self, **kwargs):
        self.__io = []
        self.__buttons = []
        self.__tasks = []
        self.__internal_time = 0
        self.paused = False

        if "identifier" not in kwargs.keys(): 
            raise ValueError("Module missing identifier!")
        self.identifier = kwargs["identifier"]

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
    
    def get_time(self):
        return self.time

    @classmethod
    async def _empty(self, *args, **kwargs): pass

    @property
    def time(self): return self.__time

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

    async def __run(self):
        self.__internal_time = time.time()
        self.__started = False
        asyncio.gather(self.__funcs["on_ready"]())
        
        while True:
            #TASKS
            run_coros = []
            for task in self.__tasks:
                run_coros += [task()]
            
            #TIME
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
                if not self.paused:
                    for time_call in time_calls:
                        run_coros += [self.__funcs[time_call](self.__time)]

            #BUTTONS
            for button in self.__buttons:
                obj = button["obj"]
                val = button["val"]
                if val != obj.value():
                    if obj.value(): 
                        if not self.__started:
                            if obj.pressed_start: run_coros += [obj.pressed()]
                        else: 
                            run_coros += [obj.pressed()]
                        run_coros += [self.__funcs["on_button_pressed"](obj)]
                    if not obj.value():
                        if not self.__started:
                            if obj.unpressed_start: run_coros += [obj.unpressed()]
                        else: 
                            run_coros += [obj.unpressed()]
                        run_coros += [self.__funcs["on_button_unpressed"](obj)]
                    button["val"] = obj.value()
            
            #IO
            for io in self.__io:
                obj = io["obj"]
                val = io["val"]
                if val != obj.value():
                    if obj.value(): 
                        if not self.__started:
                            if obj.rise_start: run_coros += [obj.rise()]
                        else: 
                            run_coros += [obj.rise()]
                        run_coros += [self.__funcs["on_io_rise"](obj)]
                    if not obj.value(): 
                        if not self.__started:
                            if obj.fall_start: run_coros += [obj.fall()]
                        else: 
                            run_coros += [obj.fall()]
                        run_coros += [self.__funcs["on_io_fall"](obj)]
                    io["val"] = obj.value()

            asyncio.gather(*run_coros)
            self.__started = True
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
        self.__handlers = {"rise": {"func":Module._empty, "on_startup":True}, 
                            "fall": {"func":Module._empty, "on_startup":True}}

        settings = [self.pin, self.type] if self.type == GPIO.OUT else [self.pin, self.type, self.pud]
        GPIO.setup(*settings)

    def value(self, val=None):
        self.val = val
        if val is None: return GPIO.input(self.pin)
        if self.type is GPIO.IN: raise Exception(f"IO {self.pin} was set up as an input, not an output")
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
