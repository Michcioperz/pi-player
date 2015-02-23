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
incr = 0

writequeue = Queue.PriorityQueue()

def incer(i):
    global incr
    return incr <= i

def enqueuechar(priority, y, x, ch, condition=None):
    global writequeue
    writequeue.put((priority, y, x, ch, condition))

def enqueuestring(priority, y, x, st, condition=None):
    global writequeue
    for i in range(0, len(st)):
        enqueuechar(priority, y, x+i, st[i], condition)

def baqueuestring(priority, y, x, st, condition=None):
    global writequeue
    for i in range(0, len(st))[::-1]:
        enqueuechar(priority, y, x+i, st[i], condition)

def notifie(text=""):
    global writequeue, timmy
    timmy = text.center(16)
    baqueuestring(0, 1, 0, text.center(16))

def music_prev(data): notifie("PREVIOUS TRACK"); subprocess.call(['mpc', 'prev'])
def music_next(data): notifie("NEXT TRACK"); subprocess.call(['mpc', 'next'])
def music_play(data): notifie("PLAYBACK START"); subprocess.call(['mpc', 'play'])
def music_pause(data): notifie("PLAYBACK PAUSE"); subprocess.call(['mpc', 'pause'])

def music_getstatus():
    st = mpc.status()
    if "state" in st:
        if st['state'] == "pause": return "|"
        if st['state'] == 'play': return ">"
        if st['state'] == 'stop': return "X"
    return "?"

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
timmy = "%s %s" % (timetemplate, music_getstatus())
enqueuestring(0, 1, 0, timmy)
song = None

def timecheck():
    global timmy
    naotsugu = "%s %s" % (datetime.datetime.now().strftime(timetemplate),music_getstatus())
    if timmy != naotsugu:
        for i in range(0, len(timmy)):
            if timmy[i] != naotsugu[i]:
                enqueuechar(1, 1, i, naotsugu[i])
        timmy = naotsugu

def make_song_text():
    global song
    return unidecode(("%s - %s - %s" % (mpc.currentsong().get('artist', "no artist"), mpc.currentsong().get('title',"no title"), mpc.currentsong().get('album',"no album"))).decode("utf8"))

class Unqueuer(threading.Thread):
    def run(self):
        global writequeue
        while True:
            if not writequeue.empty():
                o = writequeue.get()
                if o[4] is not None:
                    if o[4][0](o[4][1]):
                        lcd.setPosition(o[1], o[2])
                        lcd.writeChar(o[3])
                    else:
                        print 'old thing %s' % repr(o)
                else:
                    lcd.setPosition(o[1], o[2])
                    lcd.writeChar(o[3])

t = Unqueuer()
t.daemon = True
t.start()

while True:
    timecheck()
    if song != mpc.currentsong():
        incr = incr + 1
        song = mpc.currentsong()
        out = make_song_text()
        out = out.center(len(out)+30)
        for i in range(0, len(out)-15):
            baqueuestring(3+i, 2, 0, out[i:i+16], (incer,incr,))
