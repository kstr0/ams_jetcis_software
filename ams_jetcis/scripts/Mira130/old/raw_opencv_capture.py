"""
description: script to capture raw images from mira130 sensor, saved as TIFF 16b.
author: philippe.baetens@ams.com
date: August 2020
comment: make sure to close all python applications/GUIs before running this script.
"""
import driver_access
import time
import cv2
import os

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
imager.saveTiff_Usermode("testtiff22222_{}.tiff".format(lp),count=5) #count=5 means, take 5 images

