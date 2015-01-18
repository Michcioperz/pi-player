#!/usr/bin/env python3
from i2clibraries import i2c_lcd_smbus as i2c_lcd
from unidecode import unidecode
import datetime
import atexit
import RPi.GPIO as GPIO
import mpd
import re
import subprocess

mpc = mpd.MPDClient()
mpc.connect('127.0.0.1', 6600)
song = None

def music_prev(data): subprocess.call(['mpc', 'prev'])
def music_next(data): subprocess.call(['mpc', 'next'])
def music_play(data): subprocess.call(['mpc', 'play'])
def music_pause(data): subprocess.call(['mpc', 'pause'])

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
timmy = "hh:mm:ss yymmdd"
lcd.home()
lcd.writeString(timmy)
song = None
while True:
    naotsugu = "%s %s" % (("%s" % datetime.datetime.now().time())[:8], re.sub('-', '', "%s" % datetime.date.today())[2:])
    if timmy != naotsugu:
        for i in range(0, len(timmy)):
            if timmy[i] != naotsugu[i]:
                lcd.setPosition(1,i)
                lcd.writeChar(naotsugu[i])
        timmy = naotsugu
    if song != mpc.currentsong():
        song = mpc.currentsong()
        lcd.setPosition(2,0)
        lcd.writeString(unidecode((song.get('title') or "no song title").decode("utf8"))[:16])
