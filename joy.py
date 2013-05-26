#!/usr/bin/python
import pygame.joystick
import threading
BAUDRATE = 250000
DEVICE = "/dev/ttyUSB0"

import sys
import serial
import Queue
import copy
import time
import os
import pygame.camera
import pygame.image
from operator import add
import math

MACHINE_BOX = [[-50, 50], [-50, 50], [-1.0, 100]]

M_INIT = '''
G28 ; home
G1 F3000
G21
G91
'''
R_INIT = '''
G28 ; home all
G1 F10000
G90 ; use absolute coords
G21 ; set units to millimeters
G1 Z10.0 ; Z 10mm
G4 P100 ; wait
G1 X0.00 Y0.00 F8000.00
G4 P100 ; wait
'''
INIT = M_INIT

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

dryrun = False
nocam = False
camfile = '/dev/video1'

CALIB_NONE = 0
CALIB_SAVE = 1
CALIB_LOAD = 2
calibaction = CALIB_NONE

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

            response = self.bot.readline()
            while response[:3] != "ok":
                sys.stderr.write('Unexpected response: {0}'.format(response))
                response = self.bot.readline()

def signum(a):
  if a > 0:
    return 1
  elif a == 0:
    return 0
  else:
    return -1

def gcodespitter(speed=10.0, stepsize=1.0, scaler=lambda x,y: (x,y)):
    rostock = Rostock()
    rostock.connect()
    time.sleep(0.1)
    rostock.init()
    dt = stepsize / speed
    steps = 1.0 / dt

    machine_pos = [0.0, 0.0, 0.0]

    while True:
        item = q.get()
        print >> sys.stderr,  item
        s = item.split()
        if s[0] == 'G1':
          (x,y,z) = reduce(lambda u, v: map(lambda (_w, _z): add(_w, _z), zip(u,v)),
              map(lambda (pos, val):
                  (val, 0, 0) if pos=='X' else (
                  (0, val, 0) if pos=='Y' else (
                  (0, 0, val) if pos=='Z' else
                  (0, 0, 0))),
                map(lambda nuf: (nuf[0], float(nuf[1:].strip())), s[1:])), (0,0,0))
          print >> sys.stderr, (x,y,z)

          #mv = map(lambda _x: signum(_x) * stepsize, [x,y,z])
          vlen = math.sqrt(reduce(add, map(lambda _x: _x*_x, [x,y,z]), 0))
          if vlen > 1.0 or vlen <= 0.01:
            # dead zone
            print >> sys.stderr, 'dead zone'
            pass
          else:
            mv = map(lambda _x: (_x / vlen) * stepsize, [x,y,z])
            next_machine_pos = map(lambda (a,b): a+b, zip(machine_pos, mv))
            print >> sys.stderr, next_machine_pos
            if len(filter(lambda (_x, (_u, _v)):
                    (_x <= _u) or (_x >= _v),
                    zip(next_machine_pos, MACHINE_BOX))) == 0:
                cmd = ' '.join(['G1']+map(lambda (_x,_y): str(_y)+str(_x),
                filter(lambda (_x, _): _x!=0, zip(mv+[vlen*speed*60], 'XYZF'))))
                print >> sys.stderr, cmd
                machine_pos = next_machine_pos
                rostock.send(cmd)
            else:
                print >> sys.stderr, "NOT GOING"
            pass
        q.task_done()
        time.sleep(dt)

q = Queue.Queue(maxsize=2)

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
        print 'put joystick to down and press B0'
        st += 1
    elif st == 8:
        print 'put joystick to up and press B0'
        st += 1
    elif st == 10:
        print 'put joystick to bottom and press B0'
        st += 1
    elif st == 12:
        print 'put joystick to top and press B0'
        st += 1

    elif st == 1 and but:
        st += 20
        cfg[1] = [x, y, z]
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

    time.sleep(0.01)
    return st


def correct(cfg, coord):
    out = [0] * 3
    for i in range(len(coord)):
        try:
            if coord[i] < cfg[1][i]:
                out[i] = -1.0 + (coord[i] - cfg[0][i]) / (cfg[1][i] - cfg[0][i])
            else:
                out[i] = (coord[i] - cfg[1][i]) / (cfg[2][i] - cfg[1][i])
        except ZeroDivisionError as e:
            out[i] = 0.0

#        out[i] = (coord[i] - cfg[0][i]) / (cfg[2][i] - cfg[0][i])

    return out

q_gui = Queue.Queue()
pygame.init()
def camera_gui():
    screen = pygame.display.set_mode([800,480])

    t2 = threading.Thread(target=goon)
    t2.daemon = True
    t2.start()

    pygame.camera.init()

    cam = pygame.camera.Camera(camfile,(640,480))
    # start the camera
    cam.start()

    pygame.display.init()
    while True:
      print 'lol'
      time.sleep( 0.05 )

      # fetch the camera image
      image = cam.get_image()
      # blank out the screen
      screen.fill([0,0,0])
      # copy the camera image to the screen
      screen.blit( image, ( 100, 0 ) )
      # update the screen to show the latest screen image
      pygame.display.update()
      try:
        msg = q_gui.get(block=False)
        if msg == 'save':
          fnm = time.strftime('%H%M%S-%Y%m%d.png')
          pygame.image.save(image, fnm)
          print fnm, 'saved'
        if msg == 'quit':
          return
      except Queue.Empty as a:
        pass



def goon():
    global q, q_gui
    if not dryrun:
      t = threading.Thread(target=gcodespitter)
      t.daemon = True
      t.start()

    st = 0
    b0 = b1 = b2 = b3 = 0
    correction = [[0,0,0], [0, 0, 0], [0,0,0]]
    def print_(x):
        print >> sys.stderr, x
    calibd = skip_calib #False
    if calibaction == CALIB_LOAD:
        calibd = True
        with open(calibfile, 'r') as f:
          correction = map(lambda j: map(float, j),
              map(lambda x:
                  map(lambda z: z.strip(), x.split(',')), f.readlines()))


    pygame.joystick.init() #initialize joystick module
    pygame.joystick.get_init() #verify initialization (boolean)

    joystick_count = pygame.joystick.get_count()#get number of joysticks
    # it's for some case, important to get the joystick number ...

    if joystick_count == 1:
      joystick = pygame.joystick.Joystick(0)
      joystick.get_name()
      joystick.init()
      joystick.get_init()

    while True:
      time.sleep(0.05)

      if joystick_count == 1:

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
              print >> sys.stderr, 'put joystick to center and press B0',
          elif st == 3:
              print >> sys.stderr, 'put joystick to left and press B0',
          elif st == 5:
              print >> sys.stderr, 'put joystick to right and press B0',
          elif st == 7:
              print >> sys.stderr, 'put joystick to down and press B0',
          elif st == 9:
              print >> sys.stderr, 'put joystick to up and press B0',
          elif st == 11:
              print >> sys.stderr, 'put joystick to bottom and press B0',
          elif st == 13:
              print >> sys.stderr, 'put joystick to top and press B0',

          if not calibd:
              st = calib(st, b0, (xax_, yax_, zax_), correction)
              print >> sys.stderr, correction
              if st == 14:
                  print >> sys.stderr, 'CALIBRATED.',
                  calibd = True
                  if calibaction == CALIB_SAVE:
                      with open(calibfile, 'w+') as f:
                          f.write('\n'.join(
                              map(lambda x: ','.join(map(str,x)), correction)))
              continue

          (xax, yax, zax) = correct(correction, (xax_, yax_, zax_))
#          print >> sys.stderr, correction,
#          print >> sys.stderr, (xax, yax, zax)
      if not dryrun:
          if b1 != b2:
              if b1:
                  #q.put('G1 Z10', block=False)
                  put_nonblock(q, 'G1 Z%f' % (zax))
              if b2:
                  #q.put('G1 Z-10', block=False)
                  put_nonblock(q, 'G1 Z%f' % (-zax))
                  #q.put('G1 Z-%f' % (zax), block=False)
          if b3:
              put_nonblock(q, 'G1 X%f Y%f' % (xax, yax))
              #q.put('G1 X%f Y%f' % (xax, yax), block=False)

          print 'q.join'
          #q.join()
      if b0:
        q_gui.put('save')

def put_nonblock(_q, w):
  try:
    _q.put(w, block=False)
  except Queue.Full as e:
    pass

def show_help():
    print """usage: ./joy.py [-h] [-d] [-c /dev/videoX] [-nc] [(-sc|-lc) FILE]
                 -h  show this help and exit
                 -d  (dry run) don't enqueue printer commands
                 -c  use camera FILE (by default /dev/video1)
                 -nocam  don't use camera
                 -nc skip calibration
                 -sc save calibration to FILE
                 -sc load calibration from FILE
"""

if __name__ == "__main__":

  skip_calib = False
  if len(sys.argv) > 1:
    if '-h' in sys.argv:
      show_help()
      exit(1)
    if '-d' in sys.argv:
      dryrun = True
    if '-c' in sys.argv:
      camfile = sys.argv[sys.argv.index('-c') + 1]
    if '-nc' in sys.argv:
      skip_calib = True
    if '-sc' in sys.argv:
      calibfile = sys.argv[sys.argv.index('-sc') + 1]
      calibaction = CALIB_SAVE
    if '-lc' in sys.argv:
      calibfile = sys.argv[sys.argv.index('-lc') + 1]
      calibaction = CALIB_LOAD
    if '-nocam' in sys.argv:
      nocam = True

  if not nocam:
    camera_gui()
  else:
    goon()
