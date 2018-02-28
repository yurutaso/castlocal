Cast a local audio/video file to Google Home or Chromecast using pychromecast.

Usage: python cast.py "name of the cast device" "/path/to/media/file"

Requirements: pip install Flask PyChromecast pynput

On Windows, it is covinient to put SendToCast.bat at the shell:sendto directly 
to cast the media file from the context menu.
Modify the /path/to/python.exe, /path/to/cast.py and "name of the cast device" for the .bat file to work.