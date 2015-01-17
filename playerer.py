#!/usr/bin/env python3
from i2clibraries import i2c_lcd_smbus as i2c_lcd
from unidecode import unidecode
from math import ceil
from time import sleep
import time
import atexit
import RPi.GPIO as GPIO
import mpd
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
lcd.writeString("Loading...")

def writefull():
    lcd.clear()
    lcd.writeString(songtitle[:16])
    lcd.setPosition(2, 0)
    lcd.writeString(songartist[:16])

def splitinto16(text):
    splits = []
    for i in range(0, int(ceil(len(text)/16.0))):
        splits.append(text[16*i:16*i+16])
    return splits

song = None
while True:
    if song != mpc.currentsong():
        song = mpc.currentsong()
        lcd.clear()
        songtitle = unidecode(song.get('title').decode('utf8') or ':::')
        songartist = unidecode(song.get('artist').decode('utf8') or ':::')
        writefull()
        if len(songtitle) > 16 or len(songartist) > 16:
            sleep(1)
            if len(songtitle) > 16:
                for split in splitinto16(songtitle)[1:]:
                    lcd.setPosition(1,0)
                    lcd.writeString("                ")
                    lcd.setPosition(1,0)
                    lcd.writeString(split)
                    sleep(1)
                lcd.setPosition(1,0)
                lcd.writeString("                ")
                lcd.setPosition(1,0)
                lcd.writeString(songtitle[:16])
            if len(songartist) > 16:
                for split in splitinto16(songartist)[1:]:
                    lcd.setPosition(2,0)
                    lcd.writeString("                ")
                    lcd.setPosition(2,0)
                    lcd.writeString(split)
                    sleep(1)
                lcd.setPosition(2,0)
                lcd.writeString("                ")
                lcd.setPosition(2,0)
                lcd.writeString(songartist[:16])
