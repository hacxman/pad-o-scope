#!/usr/bin/python
BAUDRATE = 250000
DEVICE = "/dev/ttyUSB0"

import sys
import serial
import time

INIT = '''
G28 ; home all
M204 S2000 T2000 ; set default acceleration
G1 F12000
G90 ; use absolute coords
G21 ; set units to millimeters
G1 Z10.0 ; Z 10mm
G1 X0.00 Y0.00 F12000.00
'''
# G4 P100 ; wait
# G28 ; home all
END = '''
M84 ; disable motors
'''
square = '''
G1 X50 Y-50
G1 X50 Y50
G1 X-50 Y50
G1 X-50 Y-50
'''

diag = '''
G1 X0 Y100
G1 X0 Y0
'''

class Rostock(object):
    def __init__(self, dev=DEVICE, baud=BAUDRATE,
                 echo=True, dry_run=False):
        self.dev = dev
        self.baud = baud
        self.echo = echo
        self.dry_run = dry_run

    def connect(self):
        if not self.dry_run:
            sys.stderr.write('Connecting\n')
            self.bot = serial.Serial(self.dev, self.baud, timeout=30)
            sys.stderr.write('Connected\n')
        else:
            sys.stderr.write('Dry run enabled, not connecting\n')

    def init(self):
        sys.stderr.write('Init\n')
        self.send(INIT)
        sys.stderr.write('Init done\n')

    def end(self):
        sys.stderr.write('End\n')
        self.send(END)
        sys.stderr.write('End done\n')

    def send(self, data):
        if '\n' in data:
            lines = data.splitlines()
        elif type(data) != list:
            lines = [data]
        else:
            lines = data

        for line in lines:
            if not line:
                continue

            line = line.split(';')[0]

            if self.echo:
                print('> {0}'.format(line))

            if self.dry_run:
                continue

            self.bot.write('{0}\n'.format(line))

            response = self.bot.readline()
            sys.stderr.write('< {0}'.format(response))

if __name__ == "__main__":
    rostock = Rostock()

    dry = not True
    if dry:
        rostock.dry_run = True
    else:
        rostock.connect()

    time.sleep(0.1)
    rostock.init()
    for i in range(4):
        rostock.send(square)
    rostock.send('G1 X0 Y0 Z180')
    rostock.end()
