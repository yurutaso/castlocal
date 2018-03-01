#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time

class Player:
    def __init__(self, controller, playing=True):
        self.controller = controller
        # It is better to use this flag rather than controller.status.player_state,
        # since the time lag in updating the status sometimes cause unexpected behavior.
        self.playing = playing

    def update(self):
        self.controller.update_status()
        time.sleep(0.1) # IMPORTANT

    def getCurrentTime(self):
        """
        get CORRECT current_time of the media_controller c.
        """
        # NOTE: c.status.current_time does not show real time information.
        #       Therefore, it is necessary to pause/play or play/pause in order
        #       to update the status and get the correct current time.
        return self.controller.status.current_time

    def forward(self, sec):
        """
        Forward the location of the media_controller c by a given second.
        """
        current = self.getCurrentTime()
        self.seek(min(current+sec, self.controller.status.duration))

    def backward(self, sec):
        """
        Backward the location of the media_controller c by a given second.
        """
        current = self.getCurrentTime()
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
        self.controller.pause()

    def stop(self):
        self.controller.stop()

    def seek(self, position):
        if self.playing:
            self.controller.seek(position)
            self.play()
        else:
            self.controller.seek(position)
            self.pause()
