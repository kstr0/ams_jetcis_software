#
# This is a very simple example, showing how to script the JetCIS application framework
# Based on Example.py, but simplified
#

import driver_access
import time
import cv2
import os
import matplotlib.pyplot as plt
import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt
import fullres

exposure = 21472
mean = 128
# def controlSet(imager, onoff):
#     # Get checkbutton value
#     # Read register and convert to 8 bit
#     current_address_value = imager.read(0x4501)
#     current_address_value_bin = format(current_address_value, '08b')
#     # Change bit 3
#     if (onoff == False):
#         write_value = current_address_value_bin[:4] + '0' + current_address_value_bin[5:]
#     else:
#         write_value = current_address_value_bin[:4] + '1' + current_address_value_bin[5:]
#     # Write to register
#     imager.write(0x4501, int(write_value, 2))

# Step4:    The driver_access class has to be used
#           The initialization has three parameters:
#               Param1 = callback function for outputs (could be piped in GUI frameworks or files
#               Param2 = Videoport (either 0 for /dev/video0 or 1 for /dev/video1)
#               Param3 = an instance of the connection to the SyncServer, which is useful in certain stereo scenarios.
#                        use "None" in doubt
#           setSystype defines the used hardware platform. Actually "Nano" and "TX2" are supported.

#open params
mtx = np.load("calib/Original camera matrix.npy")
dist = np.load("calib/Distortion coefficients.npy")
newcameramtx = np.load("calib/Optimal camera matrix.npy")

def calibrate(img,mtx,dist,newcameramtx):
    
    h,  w = img.shape[:2]
    newcameramtx, roi=cv2.getOptimalNewCameraMatrix(mtx,dist,(w,h),1,(w,h))

    # undistort
    dst = cv2.undistort(img, mtx, dist, None, newcameramtx)
    # crop the image
    x,y,w,h = roi
    dst = dst[y:y+h, x:x+w]

    return dst

def auto_exposure(mean,exposure):

    if mean<120:
        exposure=exposure*1.2
        print(f'increasing exposure. new value is {exposure}')
        set_exposure(imager0,exposure)
        set_exposure(imager1,exposure)
    if mean>180:
        exposure=exposure*0.9
        print(f'decreasing exposure. new value is {exposure}')
        set_exposure(imager0,exposure)
        set_exposure(imager1,exposure)  
    return exposure

def set_exposure(imager,value):
    value = int(value)
    frame_length = imager.read(0x320e) * 256 + imager.read(0x320f)
    max_value = (frame_length - 8) * 16

    if value > max_value:
        value = max_value

    high = value // (2**16)
    middle_temp = value % (2**16)
    middle = middle_temp // (2**8)
    low = middle_temp % (2**8)

    imager.write(0x3e00, high)
    imager.write(0x3e01, middle)
    imager.write(0x3e02, low)


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

sensor_w=1080
sensor_h=1280
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
    new=cv2.resize(cvimage,(1080,1280))
    #cv2.imshow('right',new)
    #cv2.resizeWindow('frame0', (540,640))
    right=cv2.cvtColor(new,cv2.COLOR_RGBA2GRAY)

    ret, frame = cap1.read()

    cvimage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
    new=cv2.resize(cvimage,(1080,1280))
    left=cv2.cvtColor(new,cv2.COLOR_RGBA2GRAY)
    mean=new.mean()
    #cv2.imshow('left',new)
    #cv2.resizeWindow('frame1', (540,640))
    exposure=auto_exposure(mean,exposure)


    #stereo = cv.StereoBM_create(numDisparities=16, blockSize=15)
    #disparity = stereo.compute(left,right)
    #cv2.imshow('disparity',disparity)
    if cv2.waitKey(33) == ord('a'):
            print("save img")
            filename = f'calib/Left{i}.jpg'
            cv2.imwrite(filename, left) 
            filename = f'calib/Right{i}.jpg'
            cv2.imwrite(filename, right) 
            i=i+1



    left2 = calibrate(left,mtx,dist,newcameramtx)
    right2 =calibrate(right,mtx,dist,newcameramtx)
    cv2.imshow('left2',left2)
    cv2.imshow('right2',right2)


    stereo = cv.StereoBM_create(numDisparities=16, blockSize=15)
    disparity = stereo.compute(left2,right2)
    norm_image = cv2.normalize(disparity, None, alpha = 0, beta = 1, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_32F)
    cv2.imshow('disparitymap',norm_image)

    if cv2.waitKey(100) & 0xFF == ord('q'):
        break
# for i in range(10):
        
#     retval, frame = cap.read()

#     #testpattern = not testpattern
#     #controlSet(imager, testpattern)

#     cvimage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
#     new=cv2.resize(cvimage,(1080,1280))


#     cv2.imshow("img", new); cv2.waitKey(0); cv2.destroyAllWindows()

imager0.stopstream()
cap0.release()
imager1.stopstream()
cap1.release()
cv2.destroyAllWindows()
