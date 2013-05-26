#!/usr/bin/python

import math

import rostock
machine = rostock.Rostock()
dry = not True
if dry:
    machine.dry_run = True
else:
    machine.connect()
machine.init()

t = 0
x = 0
y = 0
y = 0
scale = 50
zoffset = 20
STEP = 0.1
up = True
try:
    while True:
        t += STEP
        # y = 5 * math.sin(x/4) * math.cos(x/8)
        # y = -3 * math.sin(x/3) + 5 * math.cos(x/7)
        x = scale * math.sin(t)
        # y = 5 * math.sin(x / 4)
        y = scale * math.cos(t)
        z =  scale * math.sin(t/10) + zoffset
        #z = zoffset
        machine.send('G1 X{0} Y{1} Z{2}'.format(x, y, z))
        #machine.send('G1 Y{0}'.format(y))

except KeyboardInterrupt:
    pass

machine.send('G1 X0 Y0 Z180')
machine.end()
