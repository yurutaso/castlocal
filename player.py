#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time

class Player:
    def __init__(self, cast, playing=True):
        self.cast = cast
        self.controller = cast.media_controller
        # It is better to use this flag rather than controller.status.player_state,
        # since the time lag in updating the status sometimes cause unexpected behavior.
        self.playing = playing

    def update(self):
        self.controller.update_status()
        time.sleep(0.1) # IMPORTANT

    def getCurrentTime(self):
        """
        Get current_time of the media_controller
        """
        # NOTE: It is necessary to call Player.update(), which internally calls media_controller.update_status()
        #       BEFORE calling getCurrentTIme(). Otherwise, this function returns the old status.
        return self.controller.status.current_time

    def volumeUp(self, delta=0.1):
        self.cast.volume_up(delta)

    def volumeDown(self, delta=0.1):
        self.cast.volume_down(delta)

    def forward(self, sec):
        """
        Forward the location of the media_controller by a given second.
        """
        current = self.getCurrentTime()
        self.seek(min(current+sec, self.controller.status.duration))

    def backward(self, sec):
        """
        Backward the location of the media_controller by a given second.
        """
        current = self.getCurrentTime()
        self.seek(max(current-sec, 0))

    def switch(self):
        """
        Switch the play/pause status of the media_controller.
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
