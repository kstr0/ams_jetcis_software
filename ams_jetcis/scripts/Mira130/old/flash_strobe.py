#
# This is a very simple example, showing how to script the JetCIS application framework
# Based on Example.py, but simplified
#

import driver_access
import time
import cv2
import os
import gc
import matplotlib.pyplot as plt
import numpy as np
import fullres

def pmsil_flash_init(imager):
    imager.setSensorI2C(0x30)
    imager.type(0) # Reg=8bit, val=8bit
    imager.write(1,0xFC)
    imager.write(2,0xFC)
    imager.write(3,0b11111000)
    imager.write(5,0x43)
    imager.write(6,0xA)
    # imager.write(7,0x3)

    # imager.write(9,3)
    imager.setSensorI2C(0x32)
    imager.type(1) # default 

    #set sensor to 10 fps
    imager.write(0x320E,0x46)
    imager.write(0x320F,0x8)

def pmsil_flash_en(imager):
    imager.setSensorI2C(0x30)
    imager.type(0)
    imager.write(6,0xB)
    imager.setSensorI2C(0x32)

def pmsil(imager,value):
    if (value == 1):
        imager.setSensorI2C(0x30)
        imager.type(0) # Reg=8bit, val=8bit
        imager.write(1,0xFE)
        imager.write(2,0xFE)
        imager.write(3,0x00)
        imager.write(6,9)
        imager.write(9,3)
        imager.setSensorI2C(0x32)
        imager.type(1) # default 
    else:
        imager.setSensorI2C(0x30)
        imager.type(0) # Reg=8bit, val=8bit
        imager.write(1,0xFE)
        imager.write(2,0xFE)
        imager.write(3,0x00)
        imager.write(6,1)
        imager.write(9,3)
        imager.setSensorI2C(0x32)
        imager.type(1) # default 



times=[]
imager = driver_access.ImagerTools(print, 0, None)
imager.setSystype("Nano")





sensorInfo = fullres.getSensorInfo(imager)
fullres.resetSensor(imager)
fullres.initSensor(imager)
testpattern = False
imager.setformat(sensorInfo["bpp"], sensorInfo["width"], sensorInfo["height"], sensorInfo["widthDMA"], sensorInfo["heightDMA"], True)

port=0
tnr=0
ee=0
sensor_mode=0
dgain="1 1"

sensor_w=1080
sensor_h=1280
sensor_wdma=1152
sensor_hdma=1280
bpp=10
sensor_fps=5
v4l2=0
iface =  "nvarguscamerasrc sensor-id={} wbmode=0  tnr-mode={} tnr-strength=0.5 ee-mode={} ee-strength=0.5 sensor-mode={} ".format(port, tnr, ee, sensor_mode)
iface += "saturation=0.0 "
iface += "ispdigitalgainrange=\"{}\" !".format(dgain)
iface += " video/x-raw(memory:NVMM),width=(int){},height=(int){},format=(string)NV12,framerate=(fraction){}/1 !".format(sensor_w, sensor_h, sensor_fps)
#            if (record == False):
iface += " nvvidconv ! video/x-raw ! appsink"
print(iface)
cap = cv2.VideoCapture(iface)
imager.setformat(bpp, sensor_w, sensor_h, sensor_wdma, sensor_hdma, v4l2)
imager.startstream()
#os.system(iface)
time.sleep(1)

frames=[]
pmsil_flash_init(imager)

while(cap.isOpened()):
    t0=time.time()

    #configure led
    pmsil_flash_en(imager)
    ret, frame = cap.read()
    t1=time.time()

    cvimage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
    new=cv2.resize(cvimage,(1080,1280))

    # imager.write(0x3e08, 3)
    # times.append(time.time())
    t2=time.time()
    cv2.imshow('frame',new)

    t3=time.time()



    k=cv2.waitKey(1)
    if k & 0xFF == ord('q'):
        break
    elif k & 0xFF == ord('p'):
        pmsil(imager,1)
    elif k & 0xFF == ord('b'):
        pmsil(imager,0)
    t4=time.time()

    times.append([t0,t1,t2,t3,t4])
    # if len(times)>300:
    #     break


imager.stopstream()
cap.release()
cv2.destroyAllWindows()

plt.plot(np.diff(times,axis=0))
plt.gca().legend(('t0','t1','t2','t3','t4'))
plt.show()

