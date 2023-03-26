import RPi.GPIO as GPIO
import asyncio
import serial
import random



class Module:

    ALLOWED_EVENTS = [
        "on_ready",
        "on_second_passed",
        "on_minute_passed",
        "on_hour_passed",
        "on_message_received"
    ]

    def __init__(self, type, status_led):
        self.type = type
        self.__status_led = status_led
        self.__id = "".join([str(random.randint(0,9)) for _ in range(3)])

        self.__uart = serial.Serial(port = "/dev/ttyS0", baudrate = 115200, timeout = 1)

        # structure: [BOOL,             INT,    STR     ]
        #            [passing_flag,     rx,     content ]
        #            [false,            1,      "wake"  ]
        self._uart_buffer = []

        self._time = {}
        for time in ("s", "m", "h"):
            self._time[time] = 0

        self.__tasks = []
        self.__events = {}
        for event in self.ALLOWED_EVENTS:
            self.__events[event] = self.__null

        self._task_queue = []
        self._event_queue = []
    
    # ==================== PROPERTIES ====================
    @property
    def id(self): return self.__id

    @property
    def time(self): return self._time

    @property
    def status_led(self): return self.__status_led
    
    # @@@@@ ============== TASKS DECORATOR ============== @@@@@
    def task(self, func):
        if callable(func):
            self.__tasks.append(func)
    
    # @@@@@ ============== EVENTS DECORATOR ============== @@@@@
    def event(self, func):
        if callable(func):
            if func.__name__ in self.ALLOWED_EVENTS:
                self.__events[func.__name__] = func
                return
            raise ValueError(f"Function '{func.__name__}()' is not a recognised event!")
        raise TypeError("An event must be a function!")

    def __uart_special_cases(self, tx, rx, content):
        pass

    async def __null(self, *args, **kwargs):
        pass
    
    # ==================== CLEAR UART BUFFER ====================
    async def __uart_write(self):
        while True:
            await asyncio.sleep(0.0001)

            if len(self._uart_buffer) > 0:
                passing_flag, rx, content = self.__uart_buffer.pop(0)
                final = (f"{self.type}#{self.__id}^{rx}^{content}\n", f"{content}\n")[passing_flag]
                self.__uart.write(final.encode("utf-8"))
            
    # ==================== READ UART MESSAGES ====================
    async def __uart_read(self):
        while True:
            await asyncio.sleep(0.0001)

            if self.__uart.inWaiting():
                message = self.__uart.readline().decode("utf-8")[:-1]
                print(message)

                # PARSE MESSAGE (e.g. "T#0^1^wake")
                tx, rx, content = message.split("^")
                tx = tx.split("#")

                # MESSAGE IS MINE?
                if tx[1] == self.__id:
                    continue

                # MESSAGE FOR ME? (-1 == GLOBAL)
                if rx not in ("-1", self.__id):
                    self._uart_buffer.append([True, int(rx), content])
                    continue
                
                self.__uart_special_cases(self, tx, rx, content)
                
                # on_message_received(tx_type, tx_id, content)
                self._event_queue.append(self.__events["on_message_received"](*tx, content))

    # ==================== MAIN ==================== 
    async def __main_loop(self):
        while True:
            await asyncio.sleep(0.0001)
            loop = asyncio.get_event_loop()

            # EXECUTES
            z = self._task_queue + self._event_queue
            if len(z) > 0:
                coroutines = [loop.create_task(event) for event in z]
                await asyncio.wait(coroutines)

    # ==================== ENTRY POINT ==================== 
    def run(self):
        loop = asyncio.new_event_loop()

        async def __internal():
            a = loop.create_task(self.__uart_write())
            b = loop.create_task(self.__uart_read())
            c = loop.create_task(self.__main_loop())
            await asyncio.wait([a,b,c])

        try:
            loop.run_until_complete(__internal())
        except KeyboardInterrupt:
            print("EXIT (ctrl+c)")
            return