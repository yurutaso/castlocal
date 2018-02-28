#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class Player:
    def __init__(self, controller):
        self.controller = controller
        self.playing = False
        self.position = 0.

    def getCurrentTime(self):
        """
        get CORRECT current_time of the media_controller c.
        """
        # NOTE: c.status.current_time does not show real time information.
        #       Therefore, it is necessary to pause/play or play/pause in order
        #       to update the status and get the correct current time.
        if self.playing:
            self.pause()
            self.play()
            return self.controller.status.current_time
        else:
            self.play()
            self.pause()
            return self.controller.status.current_time

    def forward(self, sec):
        """
        Forward the location of the media_controller c by a given second.
        """
        current = self.getCurrentTime()
        if self.playing:
            self.seek(min(current+sec, self.controller.status.duration))
        else:
            self.seek(min(current+sec, self.controller.status.duration))

    def backward(self, sec):
        """
        Backward the location of the media_controller c by a given second.
        """
        current = self.getCurrentTime()
        if self.playing:
            self.seek(max(current-sec, 0))
        else:
            self.seek(max(current-sec, 0))

    def switch(self):
        """
        Switch the play/pause status of the media_controller c.
        """
        if self.playing:
            self.pause()
        else:
            self.play()
    
    def play(self):
        self.playing = True
        self.controller.play()

    def pause(self):
        self.playing = False
        self.controller.play()
    
    def seek(self, position):
        if self.playing:
            self.controller.seek(position)
            self.play()
        else:
            self.controller.seek(position)
            self.pause()