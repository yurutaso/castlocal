#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

if os.name == 'nt':
    from msvcrt import getch
    import keymap_windows
    keymap = keymap_windows.keymap
    def getInput():
        key = getch()
        if ord(key) == 224:
            key = ord(getch())
            if keymap.__contains__(key):
                return keymap[key]
            return
        return key.decode('utf-8')

elif os.name == 'posix':
    import termios, tty
    import keymap_linux
    keymap = keymap_linux.keymap

    def readChar():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    def readKey():
        c1 = readChar()
        if ord(c1) != 0x1b:
            # standard ascii characters
            return c1

        # NOTE: there is no way to return ESC key (b'0x1b'),
        #       since it is impossible to know if there is additional characters.

        # special characters
        c2 = readChar()
        if ord(c2) != 0x5b and ord(c2) != 0x4f:
            # alt+X
            return c1+c2

        c3 = readChar()
        if ord(c2) == 0x5b and 0x41 <= ord(c3) <= 0x44:
            # arrow keys
            return c1+c2+c3
        if ord(c2) == 0x4f:
            # F1-F4
            return c1+c2+c3

        c4 = readChar()
        if ord(c4) == 0x7e:
            # HOME, INSERT, DEL, END, PAGE_UP, PAGE_DOWN
            return c1+c2+c3+c4

        # F5-F12
        c5 = readChar()
        return c1+c2+c3+c4+c5

    def getInput():
        key = readKey()
        if len(key) > 1:
            if keymap.__contains__(key):
                return keymap[key]
            return
        return key
else:
    print('OS '+os.name+' is not supported.')
    sys.exit(1)

def listen(player, keyEventHandler):
    print('Press q to exit.')
    print('Press h to show key maps.')
    import time
    while True:
        char = getInput()
        player.update()
        if keyEventHandler(player, char) == 0:
            break

def defaultKeyEventHandler(player, char):
    if char is None:
        return
    elif char  == 'q' or char == '\x1b':
        print('Exit.')
        player.stop()
        return 0
    elif char == 'c':
        print(player.getCurrentTime())
    elif char == 'i':
        player.seek(0.) # restart
    elif char == 'b':
        player.backward(60.) # backward 1 min
    elif char == 'B':
        player.backward(300.) # backward 5 min
    elif char == 'KEY_LEFT':
        player.backward(10.) # backward 10 sec
    elif char == 'f':
        player.forward(60.) # forward 1 min
    elif char == 'F':
        player.forward(300.) # forward 5 min
    elif char == ' ': # Space key
        player.switch() # switch play/pause
    elif char == 'KEY_RIGHT':
        player.forward(10.) # forward 10 sec
    elif ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'].__contains__(char):
        i = float(char)
        player.seek(player.controller.status.duration*i/10.)
    elif char == 'KEY_UP':
        player.volumeUp(0.05)
    elif char == 'KEY_DOWN':
        player.volumeDown(0.05)
    elif char == 'h':
        print("""
Keymaps:
    q: exit
    <space>: pause/play

    <right-arrow>: forward by 10sec
    f: forward by 1min
    F: forward by 5min

    <left-arrow>: backward by 10sec
    b: backward by 1min
    B: backward by 5min

    0-9: seek to 10*N % position
    i: seek to the start position""")
