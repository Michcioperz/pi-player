#!/usr/bin/env python3
from i2clibraries import i2c_lcd_smbus as i2c_lcd
from unidecode import unidecode
import datetime
import atexit
import RPi.GPIO as GPIO
import mpd
import math
import re
import subprocess
import time
import threading
import Queue


mpc = mpd.MPDClient()
mpc.connect('127.0.0.1', 6600)
song = None
oldsong = None
incr = 0

writequeue = Queue.PriorityQueue()

def incer(i):
    global incr
    return incr <= i

def enqueuechar(priority, y, x, ch, condition=None, dontcheck=True):
    global writequeue
    writequeue.put((priority, y, x, ch, condition, dontcheck))

def enqueuestring(priority, y, x, st, condition=None, dontcheck=True):
    global writequeue
    for i in range(0, len(st)):
        enqueuechar(priority, y, x+i, st[i], condition, dontcheck=dontcheck)

def baqueuestring(priority, y, x, st, condition=None, dontcheck=True):
    global writequeue
    for i in range(0, len(st))[::-1]:
        priority = priority + 0.01
        enqueuechar(priority, y, x+i, st[i], condition, dontcheck=dontcheck)

def notifie(text=""):
    global t, writequeue, timmy
    timmy = text.center(16)
    enqueuestring(0.5, 2, 0, t.scr[2])
    baqueuestring(0, 2, 0, text.center(16))

def music_prev(data): notifie(" "*9+"PREV"); subprocess.call(['mpc', 'prev'])
def music_next(data): notifie(" "*9+"NEXT"); subprocess.call(['mpc', 'next'])
def music_play(data): notifie(" "*9+"PLAY"); subprocess.call(['mpc', 'play'])
def music_pause(data): notifie(" "*9+"PAUS"); subprocess.call(['mpc', 'pause'])

def music_getstatus():
    st = mpc.status()
    if "state" in st:
        if st['state'] == "pause": return "|"
        if st['state'] == 'play': return ">"
        if st['state'] == 'stop': return "X"
    return "?"

def checkdiff(y, x, c):
    global t
    return t.scr[y][x] != c

GPIO.setmode(GPIO.BOARD)
pins = {16:music_prev, 12:music_pause, 22:music_play, 18:music_next}
for pin in pins:
    GPIO.setup(pin, GPIO.IN, GPIO.PUD_UP)
    GPIO.add_event_detect(pin, GPIO.RISING, pins[pin])
atexit.register(GPIO.cleanup)

lcd = i2c_lcd.i2c_lcd(0x27, 1, 2, 1, 0, 4, 5, 6, 7, 3)
atexit.register(lcd.clear)
lcd.backLightOn()

lcd.clear()
timetemplate = "%H:%M:%S %d.%m"
song = None

def timecheck():
    naotsugu = "%s %s" % (datetime.datetime.now().strftime(timetemplate),music_getstatus())
    for i in range(len(naotsugu)):
        if checkdiff(1, i, naotsugu[i]):
            enqueuechar(0, 1, i, naotsugu[i], dontcheck=False)

def make_song_text():
    global song
    return unidecode(("%s - %s - %s" % (song.get('artist', "no artist"), song.get('title',"no title"), song.get('album',"no album"))).decode("utf8"))

class Butler(threading.Thread):
    def run(self):
        global song
        btl = mpd.MPDClient()
        btl.connect("127.0.0.1", 6600)
        song = btl.currentsong()
        while True:
            btl.idle()
            song = btl.currentsong()

class Unqueuer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.scr = [None, [" "]*16, [" "]*16]
    def run(self):
        global writequeue, lcd
        while True:
            if not writequeue.empty():
                o = writequeue.get()
                if o[4] is not None:
                    if o[4][0](o[4][1]):
                        if checkdiff(o[1], o[2], o[3]) or o[5]:
                            self.scr[o[1]][o[2]] = o[3]
                            lcd.setPosition(o[1], o[2])
                            lcd.writeChar(o[3])
                        else:
                            #print 'already there %s' % repr(o)
                    else:
                        #print 'old thing %s' % repr(o)
                else:
                    self.scr[o[1]][o[2]] = o[3]
                    lcd.setPosition(o[1], o[2])
                    lcd.writeChar(o[3])
            else:
                time.sleep(0.2)

t = Unqueuer()
t.daemon = True
t.start()

u = Butler()
u.daemon = True
u.start()

while True:
    timecheck()
    if song != oldsong:
        incr = incr + 1
        oldsong = song
        out = make_song_text()
        out = out.center(len(out)+32)
        for i in range(0, len(out)-15):
            baqueuestring(3+i, 2, 0, out[i:i+16], (incer,incr,), dontcheck=False)
    time.sleep(0.3)
