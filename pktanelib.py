import machine as m
import uasyncio
import utime

FUNCS = [
    "on_ready",
    "on_timer_update",
    "on_button_pressed",
    "on_button_unpressed",
    "on_io_rise",
    "on_io_fall",]


class Module(object):

    def __init__(self, name, *args, **kwargs):
        self.name = name
        self._buttons, self._io, self.__tasks, self.__tasks_sec = [],[],[],[]
        self.__time = [0,0,0,0]

        for func in FUNCS:
            setattr(self, f"__{func}", self._empty)
    
    def event(self, func):
        if func.__name__ in FUNCS:
            setattr(self, f"__{func.__name__}", func)
    
    def task(self, func):
        self.__tasks+=[func]
    
    def s_task(self, func):
        self.__tasks_sec+=[func]

    def init(self, obj):
        if isinstance(obj, Button):
            self._buttons+=[obj]
        if isinstance(obj, IO):
            self._io+=[obj]

    async def _empty(self, *a, **b):
        pass

    async def __loop(self):
        time = utime.time()+1
        #EVENT: on_ready
        await self.__on_ready() # type: ignore
        while True:
            #TASKS
            for task in self.__tasks:
                await task()
            
            #EVENT: on_button_pressed/on_button_unpressed
            for btn in self._buttons:
                if btn.value() and not btn._was_enabled:
                    btn._was_enabled = True
                    await self.__on_button_pressed(btn.pin) # type: ignore
                elif not btn.value() and btn._was_enabled:
                    btn._was_enabled = False
                    await self.__on_button_unpressed(btn.pin) # type: ignore

            #EVENT: on_io_rise/on_io_fall
            for io in self._io:
                if io.value() and not io._was_enabled:
                    io._was_enabled = True
                    await self.__on_io_rise(io.pin) # type: ignore
                elif not io.value() and io._was_enabled:
                    io._was_enabled = False
                    await self.__on_io_fall(io.pin) # type: ignore

            #EVENT: on_timer_update
            if utime.time() >= time:
                time = utime.time()+1
                self.__time[0]+=1
                if self.__time[0] == 60:
                    self.__time[0]=0
                    self.__time[1]+=1
                    if self.__time[1] == 60:
                        self.__time[1]=0
                        self.__time[2]+=1
                        if self.__time[2] == 60:
                            self.__time[2]=0
                            self.__time[3]+=1
                
                await self.__on_timer_update(self.__time) # type: ignore
                for task in self.__tasks_sec:
                    await task()

    def run(self):
        uasyncio.run(self.__loop())


class Button(object):

    def __init__(self, pin, type=None):
        self.pin = pin
        self._was_enabled = False

        if type is None:
            type = m.Pin.PULL_UP
        else:
            type = m.Pin.PULL_DOWN
        self.__type = type

        self.__obj = m.Pin(self.pin, self.__type)

    def value(self):
        return self.__obj.value()
    
    val = value
    v = value


class LED(object):
    
    def __init__(self, pin, type=1):
        self._pin = []
        self._pin.append(pin)
        self.__pins = []
        self.__type = min(max(type, 1), 3)
        for num in range(self.__type):
            num-=1
            temp = m.Pin(self._pin[num], m.Pin.OUT)
            self.__pins+=[temp]
            setattr(self, f"__{['r','g','b'][num]}", temp)
        
    
    def value(self, val=None):
        if val is None:
            res = []
            for p in self.__pins:
                res+=[p.value()]
            if len(res) == 1:
                res = res[0]
            return res
        else:
            for num in range(self.__type):
                num-=1
                self.__pins[num].value(val[num])
    
    def toggle(self):
        for num in range(self.__type):
            num-=1
            self.__pins[num].value(not self.__pins[num].value())

    val = value
    v = value


class IO(object):
    
    def __init__(self, pin, type, res=None):
        self.pin = pin
        self._was_enabled = False

        if type not in ("in", "out"):
            raise ValueError(f"'type' must be either 'in' or 'out', not '{type}'")
        else:
            self.__type = {"in": m.Pin.IN, "out": m.Pin.OUT}[type]
        
        if res is not None:
            self.__res = {"up": m.Pin.PULL_UP, "down": m.Pin.PULL_DOWN}[res]
            self.__obj = m.Pin(self.pin, self.__type, self.__res)
        else:
            self.__obj = m.Pin(self.pin, self.__type)

    def value(self, state=None):
        if state is None:
            return self.__obj.value()
        elif state in (2, -1, "t", "toggle"):
            self.__obj.toggle()
        else:
            try:
                bool(state)
            except:
                raise ValueError(f"'state' mustbe either '1' or '0', not '{state}'")
            self.__obj.value(state)

    v = value
    val = value