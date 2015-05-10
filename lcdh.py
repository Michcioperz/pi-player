#!/usr/bin/env python3
from i2clibraries import i2c_lcd
import atexit
import time
import threading
import queue

class Screener(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.lcd = i2c_lcd.i2c_lcd(0x27, 1, 2, 1, 0, 4, 5, 6, 7, 3)
        atexit.register(self.lcd.clear)
        self.lcd.clear()
        self.lcd.backLightOn()
        self.scr = [None, [" "]*16, [" "]*16]
        self.queue = queue.PriorityQueue()
    def checkdiff(self, y, x, c): return self.scr[y][x] != c
    def enqueuechar(self, priority, y, x, ch, condition=None, dontcheck=True, callback=None):
        self.queue.put((priority, y, x, ch, condition, dontcheck, callback))
    def enqueuestring(self, priority, y, x, st, condition=None, dontcheck=True, callback=None):
        for i in range(0, len(st)):
            self.enqueuechar(priority, y, x+i, st[i], condition, dontcheck, callback)
    def baqueuestring(self, priority, y, x, st, condition=None, dontcheck=True):
        for i in range(0, len(st))[::-1]:
            priority = priority + 0.01
            self.enqueuechar(priority, y, x+i, st[i], condition, dontcheck=dontcheck)
    def run(self):
        while True:
            if not self.queue.empty():
                o = self.queue.get()
                if o[1] not in [1,2] or o[2] not in range(16): continue
                if o[4] is not None:
                    if o[4][0](o[4][1]):
                        if o[5] or self.checkdiff(o[1], o[2], o[3]):
                            self.scr[o[1]][o[2]] = o[3]
                            self.lcd.setPosition(o[1], o[2])
                            self.lcd.writeChar(o[3])
                            if o[0] > 2: time.sleep((abs(o[2]-(7 if o[2]>7 else 8))^2)*0.01)
                        else:
                            pass #print 'already there %s' % repr(o)
                    else:
                        pass #print 'old thing %s' % repr(o)
                else:
                    self.scr[o[1]][o[2]] = o[3]
                    self.lcd.setPosition(o[1], o[2])
                    self.lcd.writeChar(o[3])
            else:
                time.sleep(0.1)
