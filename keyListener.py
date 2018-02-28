#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pynput import keyboard
import sys

def getCurrentTime(c):
    """
    get CORRECT current_time of the media_controller c.
    """
    # NOTE: c.status.current_time does not show real time information.
    #       Therefore, it is necessary to pause/play or play/pause in order
    #       to update the status and get the correct current time.
    if isPlaying(c):
        c.pause()
        c.block_until_active()
        c.play()
        c.block_until_active()
        return c.status.current_time
    else:
        c.play()
        c.block_until_active()
        c.pause()
        c.block_until_active()
        return c.status.current_time

def isPlaying(c):
    if c.status.player_state == 'PLAYING':
        return True
    return False

def forward(c, sec):
    """
    Forward the location of the media_controller c by a given second.
    """
    current = getCurrentTime(c)
    if isPlaying(c):
        c.seek(min(current+sec, c.status.duration))
        c.block_until_active()
    else:
        c.seek(min(current+sec, c.status.duration))
        c.block_until_active()
        c.pause()
        c.block_until_active()

def backward(c, sec):
    """
    Backward the location of the media_controller c by a given second.
    """
    current = getCurrentTime(c)
    if isPlaying(c):
        c.seek(max(current-sec, 0))
        c.block_until_active()
    else:
        c.seek(max(current-sec, 0))
        c.block_until_active()
        c.pause()
        c.block_until_active()

def switch(c):
    """
    Switch the play/pause status of the media_controller c.
    """
    if c.status.player_state=='PLAYING':
        c.pause()
        c.block_until_active()
    else:
        c.play()
        c.block_until_active()

def listen(c):
    def on_press(key):
        try:
            if key.char == 'h':
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

    i: seek to the start position""")
            if key.char  == 'q':
                print('Exit.')
                sys.exit(0)
            if key.char == 'i':
                backward(c, c.status.duration) # go to the start position
            if key.char == 'b':
                backward(c, 60) # backward 1 min
            if key.char == 'B':
                backward(c, 300) # backward 5 min
            if key.char == 'f':
                forward(c, 60) # forward 1 min
            if key.char == 'F':
                forward(c, 300) # forward 5 min
        except AttributeError:
            if key == keyboard.Key.space:
                switch(c) # switch play/pause
            if key == keyboard.Key.right:
                forward(c, 10) # forward 10 sec
            if key == keyboard.Key.left:
                backward(c, 10) # backward 10 sec
            if key == keyboard.Key.esc:
                print('Exit.')
                sys.exit(0)
    print('Press q to exit.')
    print('Press h to show key maps.')
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()