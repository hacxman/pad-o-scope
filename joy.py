import pygame.joystick
import threading
BAUDRATE = 250000
DEVICE = "/dev/ttyUSB0"

import sys
import serial
import Queue
import copy
import time

INIT = '''
G28 ; home all
G1 F10000
G90 ; use absolute coords
G21 ; set units to millimeters
G1 Z10.0 ; Z 10mm
G4 P100 ; wait
G1 X0.00 Y0.00 F8000.00
G4 P100 ; wait
'''

END = '''
G28 ; home all
M84 ; disable motors
'''

square = '''
G1 X10 Y0
G1 X10 Y10
G1 X0 Y10
G1 X0 Y0
'''


class Rostock(object):
    def __init__(self, dev=DEVICE, baud=BAUDRATE,
                 echo=True):
        self.dev = dev
        self.baud = baud
        self.echo = echo

    def connect(self):
        sys.stderr.write('Connecting\n')
        self.bot = serial.Serial(self.dev, self.baud, timeout=30)
        sys.stderr.write('Connected\n')

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

            if self.echo:
                print(line)
            self.bot.write('{0}\n'.format(line))

            '''
            response = self.bot.readline()
            while response[:3] != "ok:":
                sys.stderr.write('Unexpected response: {0}'.format(response))
                response = self.bot.readline()
            '''



pygame.display.init()

pygame.joystick.init() #initialize joystick module
pygame.joystick.get_init() #verify initialization (boolean)

joystick_count = pygame.joystick.get_count()#get number of joysticks
# it's for some case, important to get the joystick number ...

def gcodespitter():
    rostock = Rostock()
    rostock.connect()
    rostock.init()

    while True:
        item = q.get()
        q.task_done()

q = Queue.Queue()

def calib(st, but, (x, y, z), cfg):
    if st == 0:
        print 'put joystick to center and press B0'
        st += 1
    elif st == 2:
        print 'put joystick to left and press B0'
        st += 1
    elif st == 4:
        print 'put joystick to right and press B0'
        st += 1
    elif st == 6:
        print 'put joystick to up and press B0'
        st += 1
    elif st == 8:
        print 'put joystick to down and press B0'
        st += 1
    elif st == 10:
        print 'put joystick to top and press B0'
        st += 1
    elif st == 12:
        print 'put joystick to bottom and press B0'
        st += 1

    elif st == 1 and but:
        st += 20
        cfg = [[0,0,0], [x, y, z], [0,0,0]]
    elif st == 3 and but:
        cfg[0][0] = x
        st += 20
    elif st == 5 and but:
        cfg[2][0] = x
        st += 20
    elif st == 7 and but:
        cfg[0][1] = y
        st += 20
    elif st == 9 and but:
        cfg[2][1] = y
        st += 20
    elif st == 11 and but:
        cfg[0][2] = z
        st += 20
    elif st == 13 and but:
        cfg[2][2] = z
        st += 20

    elif st >= 20 and st <= 33 and (but):
        st -= 19

    time.sleep(0.1)
    return st


def correct(cfg, coord):
    out = [0] * 3
    for i in range(len(coord)):
        out[i] = (coord[i] - cfg[0][i]) / (cfg[2][i] - cfg[0][i])

    return out

st = 0
correction = [[0,0,0], [0, 0, 0], [0,0,0]]
calibd = False

while True:
  if joystick_count == 1:
      joystick = pygame.joystick.Joystick(0)
      joystick.get_name()
      joystick.init()
      joystick.get_init()
      #verify initialization (maybe cool to do some error trapping with this so    game doesn't crash
      pygame.event.pump()
      # So Now i can get my joystick Axis events

      xax_ = joystick.get_axis(0)
      yax_ = joystick.get_axis(1)
      zax_ = joystick.get_axis(3)

      buttons = joystick.get_numbuttons()
      b0 = joystick.get_button(0)
      b1 = joystick.get_button(1)
      b2 = joystick.get_button(2)
      b3 = joystick.get_button(3)

      if st == 1:
          print 'put joystick to center and press B0'
      elif st == 3:
          print 'put joystick to left and press B0'
      elif st == 5:
          print 'put joystick to right and press B0'
      elif st == 7:
          print 'put joystick to up and press B0'
      elif st == 9:
          print 'put joystick to down and press B0'
      elif st == 11:
          print 'put joystick to top and press B0'
      elif st == 13:
          print 'put joystick to bottom and press B0'

      if not calibd:
          st = calib(st, b0, (xax_, yax_, zax_), correction)
          print correction
          if st == 14:
              calibd = True
          continue

      (xax, yax, zax) = correct(correction, (xax_, yax_, zax_))
      print correction,
      print (xax, yax, zax)
#      if b1 != b2:
#          if b1:
#              q.put('G1 Z10')
#          if b2:
#              q.put('G1 Z-10')
#      if b3:
#          q.put('G1 X%d Y%d' % (xax, yax))
#
#      q.join()
