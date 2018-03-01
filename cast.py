#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pychromecast
from os import path
import os
import sys
import time
import threading
import atexit
from keyListener import listen, defaultKeyEventHandler
from player import Player

# Configuration of HTTPServer
PORT = 8080
IP_ADDRESS = "192.168.11.18"

def getMediaURL(filepath):
    """
    Returns a URL of the media as a relative path to the document root.
    TODO: - Handle filepath containing space characters.
    """
    if len(filepath) == 0:
        return 'http://'+IP_ADDRESS+':'+str(PORT)
    if os.name == 'nt':
        return 'http://'+IP_ADDRESS+':'+str(PORT)+'/'+path.abspath(filepath)
    else:
        return 'http://'+IP_ADDRESS+':'+str(PORT)+path.abspath(filepath)

def HTTPServer(filepath):
    from flask import Flask, send_from_directory
    # The directory of the filepath must be set "static_folder",
    # from which Flask can serve static files.
    d = path.dirname(path.abspath(filepath))
    app = Flask(__name__, static_folder=d)
    # <path:filename> means that app accepts filepath (by putting <path:>),
    #  and it is accesible through a variable named "filename" (<path:filename>).
    @app.route('/<path:filename>')
    def send_file(filename):
        if os.name != 'nt':
            # Initial '/' is trimed on linux
            filename = '/'+filename
        return send_from_directory(path.dirname(filename), path.basename(filename))
    app.run(host='0.0.0.0', port=PORT)

def getCastByFriendlyName(name):
    """
    Returns a pychromecast.Chromecast object with a given "friendly name",
    which is a nickname of the device visible from any device supporting Cast.
    "friendly name" can be modified from any Android device by using GoogleHome app.
    Make sure all devices have different name, otherwise something might be wrong.
    """
    casts = pychromecast.get_chromecasts()
    try:
        cast = next(cc for cc in casts if cc.device.friendly_name == name)
        cast.wait()
    except:
        print("Cast device named '"+name+"' not found.")
        return
    return cast

def getCastByDevice(name):
    """
    Returns a pychromecast.Chromecast instance with a given model name.
    'name' should be "Chromecast" or "Google Home".
    """
    casts = pychromecast.get_chromecasts()
    try:
        cast = next(cc for cc in casts if cc.device.model_name == name)
        cast.wait()
    except:
        print("Cast device of model '"+name+"' not found.")
        return
    return cast

def streamFileTo(filepath, cast):
    """
    stream starts streaming the media with a given filename to the given cast device.
    filename is a absolute/relative path to the file.
    cast is a pychromecast.Chromecast instance.
    stream runs a local HTTP server using Flask to serve the file through HTTP request,
    then send the exact URL of the file to the cast device.
    """
    # Start HTTP server as a thread
    print("Starting HTTP server.")
    t = threading.Thread(target=HTTPServer, args=[filepath])
    t.daemon = True # NOTE: running HTTP server as a daemon process is necessary.
    t.start()

    # If the cast device is Googlg Home, only cast audio.
    # If the cast device is Chromecast, cast video.
    # Otherwise, finish without casting a file.
    _, ext = path.splitext(filepath)
    # TODO: Check if the file extension (ext) is one of the audio/video's extensions such as mp3, mp4, m4a, aac etc.
    # NOTE: Some audio/video formats (containers?) are not supported by Cast devices.
    #       Since flv video, for example, seems not to be supported by Chromecast,
    #       converting it to another format like mp4 is necessary in advance.
    modelName = cast.device.model_name
    if modelName == 'Chromecast':
        mime = 'video/'+ext
    elif modelName == 'Google Home':
        mime = 'audio/'+ext
    else:
        print("Unknown model_name " + modelName)
        return 1

    # Get URL of the file from filepath
    url = getMediaURL(filepath)
    print("Streaming the media on "+url)

    # Send the URL to the cast device and start streaming
    time.sleep(1) # wait until HTTP server starts
    cast.media_controller.play_media(url, mime)

    # Stop cast when terminate
    def stop():
        try:
            # stop media just in case of unusual procedure.
            c.stop()
        except:
            pass
    atexit.register(stop)

def main():
    # Read commandline args
    args = sys.argv
    if len(args) != 3:
        print("Usage: "+args[0]+" 'name of cast device' 'filename'")
        sys.exit(1)
    castname = args[1]
    filename = args[2]

    # Find cast device
    cast = getCastByFriendlyName(castname)
    if cast is None:
        sys.exit(1)
    print("Found cast device '"+castname+"'.")

    # Disconnect from cast when terminate
    def disconnect():
        cast.disconnect()
    atexit.register(disconnect)

    # Start streaming
    if streamFileTo(filename, cast) == 1:
        print("Unable to start streaming")
        sys.exit(1)

    # Listen key event
    player = Player(cast)
    listen(player, defaultKeyEventHandler)

if __name__ == '__main__':
    main()
