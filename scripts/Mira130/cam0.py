#
# This is a very simple example, showing how to script the JetCIS application framework
# Based on Example.py, but simplified
#

import driver_access_new as driver_access
import time
import cv2
import os
import matplotlib.pyplot as plt
import gi
import fullres

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
imager = driver_access.ImagerTools(print, 0, None)
imager.setSystype("Nano")

# Step3:    First important thing is to initialize the sensor. This could be done either by directly by using the
#           driver_access i2c commands or by using an already existing init script
#           This example loads an init script:
#               - The fullres.py is loaded and - by using the compile command - integrated in the actual code
#               - After this, all functions from fullres.py could be executed
#               - getSensorInfo loads a structure into sensorInfo describing all important resolution informations
#               - resetSensor resets the sensor
#               - initSensor configures the sensor


sensorInfo = fullres.getSensorInfo(imager)
fullres.resetSensor(imager)
fullres.initSensor(imager)

# Step 4:   The last step of this example creates one image as tiff file, switches to testpattern, waits a second
#           and creates a second image. This repeats 5 times before the program ends
testpattern = False
imager.setformat(sensorInfo["bpp"], sensorInfo["width"], sensorInfo["height"], sensorInfo["widthDMA"], sensorInfo["heightDMA"], True)

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
sensor_wdma=1080
sensor_hdma=1280
bpp=10
sensor_fps=30
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
# imager.startstream()
#os.system(iface)
time.sleep(1)

# while(cap.isOpened()):
#     ret, frame = cap.read()

#     cvimage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
#     new=cv2.resize(cvimage,(1080,1280))
#     cv2.imshow('frame',new)
#     if cv2.waitKey(10) & 0xFF == ord('q'):
#         break


        
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
