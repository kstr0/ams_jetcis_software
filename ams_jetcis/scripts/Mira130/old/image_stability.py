"""
description: example PTC capture script
author: Philippe Baetens
date: August 2020
Comment: just run this script WITHOUT LENS!! and even illumination
"""

from driver_access import ImagerTools
import time
import cv2
import os
import fullres
import matplotlib.pyplot as plt
#user input
description='test' #add a comment to the filenames..

exposure = 7000
steps=50
means=[]
vars=[]


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


#init stuff
def printfun(x):
    print(x)

imager = ImagerTools(printfun, 0, None)
imager.setSystype("Nano")
fname = "fullres.py"
sensorInfo = fullres.getSensorInfo(imager)
fullres.resetSensor(imager)
fullres.initSensor(imager)
imager.setformat(sensorInfo["bpp"], sensorInfo["width"], sensorInfo["height"], sensorInfo["widthDMA"], sensorInfo["heightDMA"], True)
print("{} cycle:".format(description))



set_exposure(imager,exposure)

for i in range(0,steps):
    # print(exposure)
    # exposure=exposure+500
    img=imager.Capture_Raw() #count=5 means, take 5 images
    means.append(img.mean())
    vars.append(img.std())
    #plt.clf()
    #plt.close()
    #plt.imshow(img,cmap='gray')
    #plt.pause(0.1)
plt.scatter(means,vars)
plt.show()
#
    

