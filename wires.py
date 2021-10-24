from pktanelib import IO
import random as rn

conv = ["in", "down"]
r = IO(15, *conv)
g = IO(14, *conv)
b = IO(13, *conv)
y = IO(12, *conv)
led = IO(25, "out")

val = []
for i in range(4):
    val += [rn.randint(0,1)]
val = tuple(val)
print(val)

while True:
    if (r.v(), g.v(), b.v(), y.v()) == val:
        led.v(1)
    else:
        led.v(0)
