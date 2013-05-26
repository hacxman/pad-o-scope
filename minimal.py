#!/usr/bin/python

import rostock
machine = rostock.Rostock()
machine.dry_run = not True
machine.connect()
machine.init()

machine.send('G1 X0 Y0 Z80')
machine.send('G1 X0 Y0 Z180')
machine.end()
