"""
Description: script to do noise measurement for Mira030 sensor.
Author: kristof.stroobants@ams.com
Date: 01/2021
Comment: make sure to close all python applications/GUIs before running this script. Run this script without
         illumination by covering the sensor.
"""
from os import path
import os
import sys
sys.path.append("/home/jetcis/JetCis")
import driver_access
import time
import shutil
import glob
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import subprocess


# Tuning parameters
exp_time = 1  # ms
nb_im = 50
save_im = 0
device = 0


# Access the driver
imager = driver_access.ImagerTools(print, device, None)
imager.setSystype("Nano")
imager.disablePrint()


# Exposure time
def set_exposure_time(imager, value_ms):
    # Calculate the pixel clock period in ms
    fps_original = 30
    frame_length_original = 0x07d0
    line_length_original = 0x04b0
    Tpclk = (1e3) / (fps_original * frame_length_original * line_length_original)

    # Calculate the given exposure time to the exposure length
    line_length_new = (imager.read(0x320c) << 8) + imager.read(0x320d)
    line_time_new = line_length_new * Tpclk
    exposure_length = round(16 * value_ms / line_time_new)
    frame_length_new = (imager.read(0x320e) << 8) + imager.read(0x320f)
    if exposure_length > (frame_length_new - 6) * 16:
        exposure_length = (frame_length_new - 6) * 16

    # Split value
    high = exposure_length // (2 ** 8)
    low = exposure_length % (2 ** 8)

    # Write to registers
    imager.write(0x3e01, high)
    imager.write(0x3e02, low)


# Initialize the sensor
def start_sensor(imager, exp_time):
    fname = "/home/jetcis/JetCis/Mira030/config_files/mira030_640x480_30fps_10b_2lane.py"
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
        
    # Exposure registers
    imager.setSensorI2C(0x30)
    imager.type(1)
    set_exposure_time(imager, exp_time)

# Get path
dir_results = os.path.splitext(os.path.abspath(__file__))[0]


def grab_images(imager, count=1, save_im=0, fname=None):
    sp = subprocess.Popen(["/usr/bin/v4l2-ctl", "-d", imager.fname, imager.format, "--set-ctrl", "bypass_mode=0", "--stream-mmap", "--stream-count={}".format(count), "--stream-to=/tmp/record.raw"], stdin=subprocess.PIPE)
    sp.wait()

    # Copy raw from RAM to return variable. Remove stuffing data and extract single frames
    if (imager.bpp > 8):
        dt = np.uint16
    else:
        dt = np.uint8
    sp.wait()
    
    # Cut out data
    img = np.fromfile("/tmp/record.raw", dtype=dt)
    img = img.reshape(count, imager.bufh, imager.bufw)
    img = img[::, 0:imager.h, 0:imager.w]

    if (save_im==1):
        for fno in range(0, count):
            Image.fromarray(img[fno]*2**(16-imager.bpp)).save("{}_{}.tiff".format(fname, fno))
    
    sp = subprocess.Popen(["/bin/rm", "/tmp/record.raw"])
    sp.wait()
    
    return img


start_sensor(imager, exp_time)
if save_im == 1:
    im_dir = os.path.join(dir_results, "images")
    if not os.path.exists(im_dir):
        os.makedirs(im_dir)
    imgs = grab_images(imager, count=nb_im, save_im=1, fname=(im_dir + "/img"))
else:
    imgs = grab_images(imager, count=nb_im, save_im=0)

# Noise
fpn_frame = np.mean(imgs, axis=0)
fpn = np.std(fpn_frame)
t_noise = np.mean(np.std(imgs, axis=0))
row_noise = np.mean(np.std(np.mean(imgs - fpn_frame, axis=2), axis=1))

print("FPN [DN]: {:.03f}".format(fpn))
print("Noise [DN]: {:.03f}".format(t_noise))
print("Row noise [DN]: {:.03f}".format(row_noise))

