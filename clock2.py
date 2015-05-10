#!/usr/bin/env python3
from unidecode import unidecode
from lcdh import Screener
import datetime
import atexit
import RPi.GPIO as GPIO
import mpd
import subprocess
import time
import threading
import re

song = None
st = {}
oldsong = None
incr = 0

def incer(i): return incr <= i

def notifie(text=""):
    t.enqueuestring(0.5, 2, 0, t.scr[2])
    t.baqueuestring(0, 2, 0, text.center(16))
    return True

pins = {16: (lambda data: notifie(" "*9+"PREV") and subprocess.call(['mpc', 'prev'])), 18: (lambda data: notifie(" "*9+"NEXT") and subprocess.call(['mpc', 'next'])), 22: (lambda data: notifie(" "*9+"PLAY") and subprocess.call(['mpc', 'play'])), 12: (lambda data: notifie(" "*9+"PAUS") and subprocess.call(['mpc', 'pause']))}

def music_getstatus():
    if "state" in st:
        if st['state'] == "pause": return "|"
        if st['state'] == 'play': return ">"
        if st['state'] == 'stop': return "X"
    return "?"

GPIO.setmode(GPIO.BOARD)
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
    if song.get('album', song.get('title','no title')).lower().startswith(song.get('title','no title').lower()):
        return [unidecode(song.get('artist', "no artist")), unidecode(song.get('title',"no title"))]
    else:
        return [unidecode(song.get('artist', "no artist")), unidecode(song.get('title',"no title")), unidecode(song.get('album',"no album"))]

class Butler(threading.Thread):
    def run(self):
        global song, st
        btl = mpd.MPDClient()
        btl.connect("127.0.0.1", 6600)
        while True:
            st = btl.status()
            song = btl.currentsong()
            btl.idle()
            print("idlend")

t = Screener()
t.daemon = True
t.start()

u = Butler()
u.daemon = True
u.start()

timecheck()
while not t.queue.empty(): pass

def calm(): time.sleep(0.2)

def megasplit(text):
    targ = []
    sp = text.split()
    i = 0
    while i < len(sp)-1:
        if len(sp[i]) < 14 and (len(sp[i])+len(sp[i+1])+1) < 16:
            sp[i] += " " + sp.pop(i+1)
        else:
            i += 1
    for w in sp:
        if len(w) <= 16:
            targ.append(w)
        else:
            spl = list(filter(None, re.findall(".{,14}", w)))
            targ.append(spl[0]+"-")
            targ.extend(["-"+x+"-" for x in spl[1:-1]])
            targ.append("-"+spl[-1])
    return targ

while True:
    timecheck()
    if song != oldsong:
        incr = incr + 1
        oldsong = song
        out = [""]
        for i in make_song_text():
            out.extend(megasplit(i)+[""])
        for i in range(len(out)):
            if i % 2:
                t.baqueuestring(3+i, 2, 0, out[i].center(16), (incer,incr,), dontcheck=1)
            else:
                t.enqueuestring(3+i, 2, 0, out[i].center(16), (incer,incr,), dontcheck=1)
    time.sleep(0.1)
