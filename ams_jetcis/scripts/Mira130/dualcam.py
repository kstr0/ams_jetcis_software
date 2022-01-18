"""
Example below shows a videostream from left and right camera simultaneaously, using the HW accelerated pipeline. no root required to run this.
Auto exposure function included to show how to read/write registers..
author: Philippe.Baetens@ams.com
"""

import driver_access_new as driver_access
import time
import cv2
import os
import matplotlib.pyplot as plt
import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt
import fullres


imager0 = driver_access.ImagerTools(print, 0, None)
imager1 = driver_access.ImagerTools(print, 1, None)

imager1.setSystype("Nano")
imager0.setSystype("Nano")

# Step3:    First important thing is to initialize the sensor. This could be done either by directly by using the
#           driver_access i2c commands or by using an already existing init script
#           This example loads an init script:
#               - The fullres.py is loaded and - by using the compile command - integrated in the actual code
#               - After this, all functions from fullres.py could be executed
#               - getSensorInfo loads a structure into sensorInfo describing all important resolution informations
#               - resetSensor resets the sensor
#               - initSensor configures the sensor


sensorInfo = fullres.getSensorInfo(imager1)
fullres.resetSensor(imager1)
fullres.initSensor(imager1)
fullres.resetSensor(imager0)
fullres.initSensor(imager0)

# Step 4:   The last step of this example creates one image as tiff file, switches to testpattern, waits a second
#           and creates a second image. This repeats 5 times before the program ends
testpattern = False
imager0.setformat(sensorInfo["bpp"], sensorInfo["width"], sensorInfo["height"], sensorInfo["widthDMA"], sensorInfo["heightDMA"], True)
imager1.setformat(sensorInfo["bpp"], sensorInfo["width"], sensorInfo["height"], sensorInfo["widthDMA"], sensorInfo["heightDMA"], True)
    # imager.saveRaw("~/test{}.raw".format(lp))
    # iface = "/usr/bin/gst-launch-1.0 "
    # iface += "nvarguscamerasrc num-buffers=1 sensor-id=0 wbmode=0 tnr-mode=0 tnr-strength=0.5 ee-mode=0 ee-strength=0.5 sensor-mode=0"
    # iface += " saturation=0.0 !"
    # iface += " \"video/x-raw(memory:NVMM),width=(int){},height=(int){},format=(string)NV12,framerate=(fraction){}/1\" !".format(
    #     sensorInfo["width"], sensorInfo["height"], sensorInfo["fps"])
    # iface += " nvvidconv ! video/x-raw ! filesink location=test{}.raw".format(lp)
port=0
tnr=0
ee=0
sensor_mode=0
dgain="1 1"

sensor_w=540
sensor_h=640
sensor_wdma=1152
sensor_hdma=1280
bpp=10
sensor_fps=30
v4l2=0
iface=[0,0]
for port in [0,1]:
    iface[port] =  "nvarguscamerasrc sensor-id={} wbmode=0  tnr-mode={} tnr-strength=0.5 ee-mode={} ee-strength=0.5 sensor-mode={} ".format(port, tnr, ee, sensor_mode)
    iface[port] += "saturation=0.0 "
    iface[port] += "ispdigitalgainrange=\"{}\" !".format(dgain)
    iface[port] += " video/x-raw(memory:NVMM),width=(int){},height=(int){},format=(string)NV12,framerate=(fraction){}/1 !".format(sensor_w, sensor_h, sensor_fps)
    #            if (record == False):
    iface[port] += " nvvidconv ! video/x-raw ! appsink"
    print(iface[port])
cap0 = cv2.VideoCapture(iface[0])
cap1 = cv2.VideoCapture(iface[1])            

imager0.setformat(bpp, sensor_w, sensor_h, sensor_wdma, sensor_hdma, v4l2)
imager0.startstream()
imager1.setformat(bpp, sensor_w, sensor_h, sensor_wdma, sensor_hdma, v4l2)
imager1.startstream()
#os.system(iface)
time.sleep(1)
i=10
while(cap0.isOpened() and cap1.isOpened()):
    
    ret, frame = cap0.read()
    cvimage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)

    cv2.imshow('right',cvimage)
    #cv2.resizeWindow('frame0', (540,640))
    right=cv2.cvtColor(cvimage,cv2.COLOR_RGBA2GRAY)

    ret, frame = cap1.read()

    cvimage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
    
    left=cv2.cvtColor(cvimage,cv2.COLOR_RGBA2GRAY)
    cv2.imshow('left',cvimage)
    #cv2.resizeWindow('frame1', (540,640))




    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

            


imager0.stopstream()
cap0.release()
imager1.stopstream()
cap1.release()
cv2.destroyAllWindows()
