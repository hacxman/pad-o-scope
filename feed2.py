#!/usr/bin/python

import math

import rostock
machine = rostock.Rostock()
machine.dry_run = True
machine.connect()
machine.init()

t = 0
x = 0
y = 0
z = 0
scale = 50
zoffset = 20
STEP = 0.1
exp = 3
up = True
try:
    while True:
        t += STEP
        # y = 5 * math.sin(x/4) * math.cos(x/8)
        # y = -3 * math.sin(x/3) + 5 * math.cos(x/7)
        x = scale * math.sin(t)**exp
        # y = 5 * math.sin(x / 4)
        y = scale * math.cos(t)**exp
        z =  scale * math.sin(t/10) + zoffset
        #z = zoffset
        machine.send('G1 X{0} Y{1} Z{2}'.format(x, y, z))
        #machine.send('G1 Y{0}'.format(y))

except KeyboardInterrupt:
    pass

machine.send('G1 X0 Y0 Z180')
machine.end()
