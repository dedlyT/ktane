import machine as m


class Button(object):

    def __init__(self, pin, type=None):
        self.pin = pin

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


class IO(object):
    
    def __init__(self, pin, type, res=None):
        self.pin = pin

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
