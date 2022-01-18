"""
Description: script to take images when switching between contexts for Mira220 sensor.
Author: kristof.stroobants@ams.com
Date: 11/2020
Comment: make sure to close all python applications/GUIs before running this script.
"""
from os import path
import os
import sys
sys.path.append(path.dirname(path.dirname(os.getcwd())))
import driver_access
import time

# Access the driver
imager = driver_access.ImagerTools(print, 0, None)
imager.setSystype("Nano")

# Initialize the sensor
fname = "../../Mira220/config_files/fullres_30fps.py"
try:
    with open(fname, "r") as file:
        eobj = compile(file.read(), fname, "exec")
        exec(eobj, globals())
except:
    print("ERROR: unable to execute init script")
sensorInfo = getSensorInfo(imager)
resetSensor(imager)
initSensor(imager)
imager.setformat(sensorInfo["bpp"], sensorInfo["width"], sensorInfo["height"], sensorInfo["widthDMA"], sensorInfo["heightDMA"], True)

# Tuning parameters
exp_timeA = 20  # ms
exp_timeB = 5  # ms
nb_im = 1

# Write context A registers
imager.setSensorI2C(0x54)
imager.type(1)
imager.write(0x1012, 0xfa)  # vblank
imager.write(0x1013, 0x0a)  # vblank
imager.write(0x107d, 0x0)  # vstart
imager.write(0x107e, 0x0)  # vstart
imager.write(0x1087, 0x78)  # vsize
imager.write(0x1088, 0x5)  # vsize
row_lengthA = imager.read(0x102B) + 256 * imager.read(0x102C)
reg_shutterA = round(exp_timeA / (row_lengthA / 38400000 * 1000))
imager.write(0x100c, reg_shutterA % 256)  # reg_shutter
imager.write(0x100d, reg_shutterA // 256)  # reg_shutter
imager.write(0x2008, 0x20)  # hsize
imager.write(0x2009, 0x3)  # hsize
imager.write(0x200a, 0x0)  # hstart
imager.write(0x200b, 0x0)  # hstart
imager.write(0x400A, 8)  # gain

# Write context B registers
imager.write(0x1103, 0x37)  # vblank
imager.write(0x1104, 0x5d)  # vblank
imager.write(0x1105, 0x0)  # vstart
imager.write(0x1106, 0x0)  # vstart
imager.write(0x110a, 0x78)  # vsize
imager.write(0x110b, 0x5)  # vsize
row_lengthB = imager.read(0x1113) + 256 * imager.read(0x1114)
reg_shutterB = round(exp_timeB / (row_lengthB / 38400000 * 1000))
imager.write(0x1115, reg_shutterB % 256)  # reg_shutter
imager.write(0x1116, reg_shutterB // 256)  # reg_shutter
imager.write(0x2098, 0x20)  # hsize
imager.write(0x2099, 0x3)  # hsize
imager.write(0x209a, 0x0)  # hstart
imager.write(0x209b, 0x0)  # hstart
imager.write(0x401A, 8)  # gain

# Get path
dir_results = os.path.splitext(os.path.abspath(__file__))[0]

# Make directories
im_dirA = os.path.join(dir_results, "images_contextA")
if not os.path.exists(im_dirA):
    os.makedirs(im_dirA)
im_dirB = os.path.join(dir_results, "images_contextB")
if not os.path.exists(im_dirB):
    os.makedirs(im_dirB)

# Select context A and save image
print("Taking image with context A")
imager.write(0x1100, 0x2)
imager.saveTiff(im_dirA + "/img.tiff", count=nb_im)

# Select context B and save image
print("Taking image with context B")
imager.write(0x1100, 0x3)
imager.saveTiff(im_dirB + "/img.tiff", count=nb_im)

