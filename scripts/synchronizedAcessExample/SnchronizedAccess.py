import driver_access
import time
import cv2
import os
import numpy as np
import gi
gi.require_version('Gst', '1.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gst, GObject, Gtk


imager = driver_access.ImagerTools(print, 0, None)
imager.setSystype("Nano")

fname = "fullres.py"
try:
    with open(fname, "r") as file:
        eobj = compile(file.read(), fname, "exec")
        exec(eobj, globals())
except:
    print("ERROR: unable to execute init script")
sensorInfo = getSensorInfo(imager)
resetSensor(imager)
initSensor(imager)

testpattern = False
lp=10 #add a number to the filename..
imager.setformat(sensorInfo["bpp"], sensorInfo["width"], sensorInfo["height"], sensorInfo["widthDMA"], sensorInfo["heightDMA"], True)
print("{} cycle:".format(lp))

# setup a Gstreamer callback that is called everytime a new image arrives
def gstCallback(sink):
    # Get actual image buffer
    sample = sink.emit("pull-sample")
    caps = sample.get_caps()
    # Extract the width and height info from the sample's caps
    height = caps.get_structure(0).get_value("height")
    width = caps.get_structure(0).get_value("width")
    # Get the actual data
    buffer = sample.get_buffer()
    # Get read access to the buffer data
    success, map_info = buffer.map(Gst.MapFlags.READ)
    if not success:
        raise RuntimeError("Could not map buffer data!")
    cvimage = np.ndarray(shape=(height, width, 4), dtype=np.uint8, buffer=map_info.data)
    # Clean up the buffer mapping
    buffer.unmap(map_info)

# Finally start the pipeline:
imager.initISP(sensorInfo["width"], sensorInfo["height"], sensorInfo["fps"], 0, 0, gstCallback)
# Create a main loop that idles while the frames are received by the callback function
while(True):
    time.sleep(0.01)
