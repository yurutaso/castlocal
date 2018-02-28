#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

if os.name == 'nt':
    from msvcrt import getch
    keymaps = {
        71: 'HOME',
        72: 'KEY_UP',
        73: 'PAGE_UP',
        75: 'KEY_LEFT',
        77: 'KEY_RIGHT',
        79: 'END',
        80: 'KEY_DOWN',
        81: 'PAGE_DOWN',
        82: 'INSERT',
        83: 'DEL',
    }
    def getInput():
        key = getch()
        if ord(key) == 224:
            key = ord(getch())
            if keymaps.__contains__(key):
                return keymaps[key]
            return
        return key.decode('utf-8')

elif os.name == 'posix':
    import termios, tty
    keymaps = {
        '\x1b\x4f\x50': 'F1',
        '\x1b\x4f\x51': 'F2',
        '\x1b\x4f\x52': 'F3',
        '\x1b\x4f\x53': 'F4',
        '\x1b\x5b\x32\x30\x7e': 'F9',
        '\x1b\x5b\x32\x31\x7e': 'F10',
        '\x1b\x5b\x32\x33\x7e': 'F11',
        '\x1b\x5b\x32\x34\x7e': 'F12',
        '\x1b\x5b\x31\x35\x7e': 'F5',
        '\x1b\x5b\x31\x37\x7e': 'F6',
        '\x1b\x5b\x31\x38\x7e': 'F7',
        '\x1b\x5b\x31\x39\x7e': 'F8',
        '\x1b\x5b\x31\x7e': 'HOME',
        '\x1b\x5b\x32\x7e': 'INSERT',
        '\x1b\x5b\x33\x7e': 'DEL',
        '\x1b\x5b\x34\x7e': 'END',
        '\x1b\x5b\x35\x7e': 'PAGE_UP',
        '\x1b\x5b\x36\x7e': 'PAGE_DOWN',
        '\x1b\x5b\x41': 'KEY_UP',
        '\x1b\x5b\x42': 'KEY_DOWN',
        '\x1b\x5b\x43': 'KEY_RIGHT',
        '\x1b\x5b\x44': 'KEY_LEFT',
    }

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
            if keymaps.__contains__(key):
                return keymaps[key]
            return
        return key
else:
    print('OS '+os.name+' is not supported.')
    sys.exit(1)

def listen(player, keyEventHandler):
    print('Press q to exit.')
    print('Press h to show key maps.')
    while True:
        keyEventHandler(player, getInput())

def defaultKeyEventHandler(player, char):
    if char is None:
        return
    elif char  == 'q' or char == '\x1b':
        print('Exit.')
        sys.exit(0)
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