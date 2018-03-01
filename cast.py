#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pychromecast
import os
import sys
import time
import threading
import atexit
import subprocess
import tempfile
from keyListener import listen, defaultKeyEventHandler
from player import Player

# Configuration of HTTPServer

def getIPAddress():
    import socket
    return [(s.connect(('8.8.8.8', 80)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]

def getMediaURL(filepath, port=8080):
    """
    Returns a URL of the media as a absolute path.
    """
    ip = getIPAddress()
    if len(filepath) == 0:
        return 'http://'+ip+':'+str(port)
    if os.name == 'nt':
        return 'http://'+ip+':'+str(port)+'/'+os.path.abspath(filepath)
    else:
        return 'http://'+ip+':'+str(port)+os.path.abspath(filepath)

def HTTPServer(filepath, port=8080):
    from flask import Flask, send_from_directory
    # The directory of the filepath must be set "static_folder",
    # from which Flask can serve static files.
    d = os.path.dirname(os.path.abspath(filepath))
    app = Flask(__name__, static_folder=d)
    # <path:filename> means that app accepts filepath (by putting <path:>),
    #  and it is accesible through a variable named "filename" (<path:filename>).
    @app.route('/<path:filename>')
    def send_file(filename):
        if os.name != 'nt':
            filename = '/'+filename # NOTE: Initial '/' is trimed on linux
        return send_from_directory(os.path.dirname(filename), os.path.basename(filename))
    app.run(host='0.0.0.0', port=port)

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

def streamURLTo(url, cast):
    """
    stream starts streaming the media in a given URL to the given cast device.
    cast is a pychromecast.Chromecast instance.
    """
    # If the cast device is Googlg Home, only cast audio.
    # If the cast device is Chromecast, cast video.
    # Otherwise, finish without casting a file.
    _, ext = os.path.splitext(url)
    # TODO: Check if the file extension (ext) is one of the audio/video's extensions such as mp3, mp4, m4a, aac etc.
    # NOTE: Some audio/video formats (containers?) are not supported by Cast devices.
    #       For example, flv is not supported by Chromecast, and m4a is not supported by Google Home.
    modelName = cast.device.model_name
    if modelName == 'Chromecast':
        mime = 'video/'+ext
    elif modelName == 'Google Home':
        mime = 'audio/'+ext
    else:
        print("Unknown model_name " + modelName)
        return 1

    # Send the URL to the cast device and start streaming.
    # There is no problem to use local web server, but never use http://localhost/xxx.
    print("Streaming the media on "+url)
    cast.media_controller.play_media(url, mime)

    # Stop cast when terminate
    def stop():
        try:
            # try to stop media just in case of unusual termination.
            cast.media_controller.stop()
            time.sleep(2.) # wait until the cast device close the file.
        except:
            pass
    atexit.register(stop)

def streamFileTo(filepath, cast):
    """
    stream starts streaming the media with a given filename to the given cast device.
    filename is a absolute/relative path to the file.
    cast is a pychromecast.Chromecast instance.
    stream runs a local HTTP server using Flask to serve the file through HTTP request,
    then send the URL of the file to the cast device.
    """

    model = cast.device.model_name
    if not ['Google Home', 'Chromecast'].__contains__(model):
        print('model must be "Chromecast" or "Google Home"')
        sys.exit(1)
    # check if the media is readable by the cast device
    # If not, convert it to mp3 (Google Home) or mp4 (Chromecast) with ffmpeg.
    # "filepath" is updated to the generated (temporaly) file in this case.
    filepath = checkMedia(filepath, model)

    # Start HTTP server as a daemon with thread
    print("Starting HTTP server.")
    t = threading.Thread(target=HTTPServer, args=[filepath])
    t.daemon = True # NOTE: running HTTP server as a daemon process is necessary.
    t.start()
    time.sleep(1) # wait for HTTP server to start

    # Stream the media from the local web server.
    return streamURLTo(getMediaURL(filepath), cast)

def getStreams(filepath):
    """
    Get information of audio/video streams using FFMPEG
    """
    res = subprocess.run(['ffmpeg', '-i', filepath], stderr=subprocess.PIPE)
    if res.returncode != 1:
        print('Unable to get media information.')
        print('error code:', res.returncode)
        print('error message:', res.stderr)
    raw = res.stderr.decode('utf-8')
    stream = {'containers': [], 'audio':[], 'video':[]}
    try:
        Input = raw.split('Input')[1]
        stream['container'] = [s.strip() for s in Input.split('from')[0].split(',')[1:-1]]
        streams = Input.split('Stream ')[1:]
        for s in streams:
            stream_map = s.split('(')[0][1:]
            stream_format = s.split(':')[3].split('(')[0].strip()
            stream_type = s.split(':')[2].strip()
            if stream_type == 'Audio':
                stream['audio'].append({'map': stream_map, 'format': stream_format})
            if stream_type == 'Video':
                stream['video'].append({'map': stream_map, 'format': stream_format})
        return stream
    except:
        return {'container': [], 'audio': [], 'video': []}

def convertToMP3(filepath, fileout):
    cmd = ['ffmpeg', '-loglevel', 'error', '-y', '-i', filepath, '-vn']
    audiostreams = getStreams(filepath)['audio']
    try:
        audiostream = audiostreams[0]
        cmd.append('-map')
        cmd.append(audiostream['map'])
        if audiostream['format'] == 'mp3':
            cmd.append('-acodec')
            cmd.append('copy')
    except IndexError:
        print('No audio stream found.')
        sys.exit(1)
    cmd.append(fileout)
    return subprocess.run(cmd)

def convertToMP4(filepath, fileout):
    cmd = ['ffmpeg', '-loglevel', 'error', '-y', '-i', filepath]

    streams = getStreams(filepath)
    try:
        audiostream = streams['audio'][0]
        if audiostream['format'] == 'aac':
            cmd.append('-acodec')
            cmd.append('copy')
    except IndexError:
        audiostream = None
    try:
        videostream = streams['video'][0]
        if videostream['format'] == 'h264':
            cmd.append('-vcodec')
            cmd.append('copy')
    except IndexError:
        videostream = None

    if (audiostream is None) and (videostream is None):
        print('Neither audio nor video found.')
        sys.exit(1)
    cmd.append(fileout)
    return subprocess.run(cmd)

def rmtmp(filepath, timeout=5.):
    try:
        print('cleanup tempfile')
        os.remove(filepath)
    except PermissionError:
        print('cleanup failed by PermissionError.')
        print('retry after', timeout,'seconds.')
        time.sleep(timeout)
        try:
            os.remove(filepath)
        except PermissionError:
            print('Failed. You should manually remove ', filepath)

def hasFFMPEG():
    """
    Check if ffmpeg is available
    """
    cmd = ['ffmpeg', '-version']
    if subprocess.run(cmd).returncode == 0:
        return True
    return False

def checkMedia(filepath, model):
    if not hasFFMPEG():
        print('Warning! ffmpeg does not exist in the PATH.')
        print('Skip checking media file.')
        return filepath

    streams = getStreams(filepath)
    try:
        audiostream = streams['audio'][0]
    except IndexError:
        audiostream = None

    if model == 'Chromecast':
        if streams['container'].__contains__('flv'):
            tmp = tempfile.NamedTemporaryFile(prefix='castlocal_', suffix='.mp4', delete=False)
            atexit.register(rmtmp, tmp.name)
            print('Video type', streams['container'], 'is not supported by Chromecast.')
            print('Converting to mp4 by ffmpeg as', tmp.name)
            res = convertToMP4(filepath, tmp.name)
            if res.returncode != 0:
                print('Failed.')
                print('error code:', res.returncode)
                print('error message:', res.stderr)
                sys.exit(1)
            print('Done. Conversion success.')
            tmp.close()
            #ffmpeg = threading.Thread(target=convertToMP4, args=[filepath, tmp.name])
            #ffmpeg.daemon = True
            #ffmpeg.start()
            return tmp.name
        return filepath
    elif model == 'Google Home':
        if audiostream is None:
            print('No audio stream is found')
            sys.exit(1)
        if not ['mp3', 'opus'].__contains__(audiostream['format']):
            tmp = tempfile.NamedTemporaryFile(prefix='castlocal_', suffix='.mp3', delete=False)
            atexit.register(rmtmp, tmp.name)
            print('Audio type', audiostream['format'], 'is not supported by Google Home.')
            print('Converting to mp3 by ffmpeg as', tmp.name)
            res = convertToMP3(filepath, tmp.name)
            if res.returncode != 0:
                print('Failed.')
                print('error code:', res.returncode)
                print('error message:', res.stderr)
                sys.exit(1)
            print('Done. Conversion success.')
            tmp.close()
            #ffmpeg = threading.Thread(target=convertToMP3, args=[filepath, tmp.name])
            #ffmpeg.daemon = True
            #ffmpeg.start()
            return tmp.name
        return filepath

def isURL(path):
    try:
        if path[0:7] == 'http://' or path[0:8] == 'https://':
            return True
        return False
    except:
        return False

def main():
    # Read commandline args
    args = sys.argv
    if len(args) != 3:
        print("Usage: "+args[0]+" 'name of cast device' 'filepath or URL'")
        sys.exit(1)
    castname = args[1]
    path = args[2]

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
    if isURL(path):
        ok = streamURLTo(path, cast)
    else:
        ok = streamFileTo(path, cast)
    if ok is not None:
        print("Unable to start streaming")
        sys.exit(1)

    # Listen key event
    player = Player(cast)
    listen(player, defaultKeyEventHandler)

if __name__ == '__main__':
    main()