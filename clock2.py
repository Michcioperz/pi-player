#!/usr/bin/env python3
from unidecode import unidecode
from lcdh import Screener
import datetime
import atexit
import RPi.GPIO as GPIO
import mpd
import math
import re
import subprocess
import time
import threading

song = None
st = {}
oldsong = None
incr = 0

def incer(i):
    global incr
    return incr <= i

def notifie(text=""):
    global t
    t.enqueuestring(0.5, 2, 0, t.scr[2])
    t.baqueuestring(0, 2, 0, text.center(16))

def music_prev(data): notifie(" "*9+"PREV"); subprocess.call(['mpc', 'prev'])
def music_next(data): notifie(" "*9+"NEXT"); subprocess.call(['mpc', 'next'])
def music_play(data): notifie(" "*9+"PLAY"); subprocess.call(['mpc', 'play'])
def music_pause(data): notifie(" "*9+"PAUS"); subprocess.call(['mpc', 'pause'])

def music_getstatus():
    global st
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

timetemplate = "%H:%M:%S %d.%m"
song = None

def timecheck():
    naotsugu = "%s %s" % (datetime.datetime.now().strftime(timetemplate),music_getstatus())
    for i in range(len(naotsugu)):
        if t.checkdiff(1, i, naotsugu[i]):
            t.enqueuechar(0, 1, i, naotsugu[i], dontcheck=False)

def make_song_text():
    global song
    return unidecode(("%s - %s - %s" % (song.get('artist', "no artist"), song.get('title',"no title"), song.get('album',"no album"))))

class Butler(threading.Thread):
    def run(self):
        global song, st
        btl = mpd.MPDClient()
        btl.connect("127.0.0.1", 6600)
        while True:
            st = btl.status()
            song = btl.currentsong()
            btl.idle()

t = Screener()
t.daemon = True
t.start()

u = Butler()
u.daemon = True
u.start()

timecheck()
while not t.queue.empty(): pass

while True:
    timecheck()
    if song != oldsong:
        incr = incr + 1
        oldsong = song
        out = make_song_text()
        out = out.center(len(out)+32)
        for i in range(0, len(out)-15):
            t.baqueuestring(3+i, 2, 0, out[i:i+16], (incer,incr,), dontcheck=False)
    time.sleep(0.1)
