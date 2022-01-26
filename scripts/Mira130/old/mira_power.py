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


#defines
t_exp_start = 0
t_exp_end = 1
t_read = 11
t_lowpower = 16
t_highpower = 24
t_settle = 30

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

t0=time.time()
while(cap.isOpened()):


    # START EXPOSURE
    if 
    # STOP EXP, request readout

    # powerdown, start readout(cv)

    # powerup

    #wait
    time.sleep(4)





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

