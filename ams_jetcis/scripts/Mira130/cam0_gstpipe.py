import driver_access_new as driver_access
import time
import cv2
import os
import numpy as np
import gi
import fullres

gi.require_version('Gst', '1.0')
#gi.require_version('Gtk', '3.0')
from gi.repository import Gst, GObject#, Gtk


imager = driver_access.ImagerTools(print, 0, None)
imager.setSystype("Nano")

sensorInfo = fullres.getSensorInfo(imager)
fullres.resetSensor(imager)
fullres.initSensor(imager)

testpattern = False
lp=10 #add a number to the filename..
imager.setformat(sensorInfo["bpp"], sensorInfo["width"], sensorInfo["height"], sensorInfo["widthDMA"], sensorInfo["heightDMA"], True)
print("{} cycle:".format(lp))

# imager.initISP_test(sensorInfo["width"], sensorInfo["height"], sensorInfo["fps"], 0, 0)

Gst.init(None)
gstpipe = Gst.Pipeline.new("Capture")
src = Gst.ElementFactory.make("nvarguscamerasrc", "src")
src.set_property("sensor-id", id)
src.set_property("wbmode", 0)
src.set_property("sensor-mode", mode)
caps1 = Gst.ElementFactory.make("capsfilter", "caps1")
txt = "video/x-raw(memory:NVMM), width=(int){}, height=(int){}, format=(string)NV12, framerate=(fraction){}/1".format(
    w, h, fps)
txt = Gst.Caps.from_string(txt)
caps1.set_property("caps", txt)
filter1 = Gst.ElementFactory.make("nvvidconv", "filter1")
caps2 = Gst.ElementFactory.make("capsfilter", "caps2")
txt = "video/x-raw, width={}, height={}, format=(string)RGBA".format(w, h)
txt = Gst.Caps.from_string(txt)
caps2.set_property("caps", txt)
sink = Gst.ElementFactory.make("appsink", "sink")
sink.set_property("max-buffers", 5 )
sink.set_property("drop", True )
gstpipe.add(src)
gstpipe.add(caps1)
gstpipe.add(filter1)
gstpipe.add(caps2)
gstpipe.add(sink)
src.link(caps1)
caps1.link(filter1)
filter1.link(caps2)
caps2.link(sink)

# connect LiveUpdate callback
bus = gstpipe.get_bus()
bus.add_signal_watch()
bus.enable_sync_message_emission()
bus.connect("message", liveMessage)
#        bus.connect("sync-message::element", liveView)
sink.set_property("emit-signals", True)
handler_id = sink.connect("new-sample", callback)
# Finally start the stream
gstpipe.set_state(Gst.State.PLAYING)
return 0



cap = cv2.VideoCapture(gstpipe) #what to put here?

time.sleep(1)

        
while(cap.isOpened()):
    ret, frame = cap.read()
    cvimage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
    new=cv2.resize(cvimage,(1080,1280))
    cv2.imshow('frame1',new)
    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

# imager.stopstream()
cap.release()
cv2.destroyAllWindows()