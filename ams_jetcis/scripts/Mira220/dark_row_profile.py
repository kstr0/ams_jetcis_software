"""
description: script to plot row profile of dark images for Mira220 sensor.
author: kristof.stroobants@ams.com
date: 08/2020
comment: make sure to close all python applications/GUIs before running this script.
"""
from os import path
import os
import sys
sys.path.append(path.dirname(path.dirname(os.getcwd())))
import driver_access
import glob
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import time
import subprocess

# Access the driver
imager = driver_access.ImagerTools(print, 0, None)
imager.setSystype("Nano")

# Initialize the sensor
fname = "../../Mira220/config_files/mira220_1600x1400_30fps_12b.py"
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
exp_times = [1, 10] # ms
gains = [1, 4]
nb_im = 32
save_im = 0
save_profile = 0

# Set gain
def set_gain(imager, value):
    global otp_gain_trims, f_clk_in

    # I2C address and length (addr=16bit, val=8bit)
    imager.setSensorI2C(0x54)
    imager.type(1)

    # Write values to sensor
    if len(otp_gain_trims) == 0:
        if value == 1:
            imager.write(0x400A, 0x08)
            imager.write(0x402A, 0x63)
        elif value == 2:
            imager.write(0x400A, 0x04)
            imager.write(0x402A, 0x5F)
        elif value == 4:
            imager.write(0x400A, 0x02)
            imager.write(0x402A, 0x5E)
        else:
            # Print error in StatusArea
            imager.pr("ERROR: Only x1, x2, x4 is supported")
            imager.write(0x400A, 0x08)
            imager.write(0x402A, 0x63) 
    else:
        if value == 1:
            imager.write(0x400A, 0x08)
            imager.write(0x4009, otp_gain_trims[0])
        elif value == 2:
            imager.write(0x400A, 0x04)
            imager.write(0x4009, otp_gain_trims[1])
        elif value == 4:
            imager.write(0x400A, 0x02)
            imager.write(0x4009, otp_gain_trims[2])
        else:
            # Print error in StatusArea
            imager.pr("ERROR: Only x1, x2, x4 or x8 is supported")
            imager.write(0x400A, 0x08)
            imager.write(0x4009, otp_gain_trims[0])


def set_exposure(imager, value):
    global f_clk_in
    imager.setSensorI2C(0x54)
    imager.type(1)
    row_length = imager.read(0x102B) + 256 * imager.read(0x102C)
    reg_shutter = round(value / (row_length / f_clk_in * 1000))
    imager.write(0x100C, reg_shutter % 256)
    imager.write(0x100D, reg_shutter // 256)


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


for exp_time in exp_times:
    for gain in gains:
        time.sleep(1)
        # Set gain and exposure time
        set_gain(imager, gain)
        set_exposure(imager, exp_time)

        # Take nb_im images
        print("Taking images with ET=", exp_time, " and gain=", gain)
        if save_im == 1:
            dir_results = os.path.splitext(os.path.abspath(__file__))[0]
            im_dir = os.path.join(dir_results, "dark_images_ET{}_gain{}".format(str(exp_time).replace(".", "_"), gain))
            if not os.path.exists(im_dir):
                os.makedirs(im_dir)
            imgs = grab_images(imager, count=nb_im, save_im=1, fname=(im_dir + "/img"))
        else:
            imgs = grab_images(imager, count=nb_im, save_im=0)

        # Calculate the row profile
        im_row_profile = np.mean(np.mean(imgs, axis=0), axis=1)

        # Save row profile
        plt.figure()
        plt.plot(im_row_profile)
        plt.title("Row profile dark ET={} and gain={}".format(exp_time, gain))
        plt.xlabel("Row")
        plt.ylabel("DN")
        if save_profile == 1:
            dir_results = os.path.splitext(os.path.abspath(__file__))[0]
            im_dir = os.path.join(dir_results, "dark_images_ET{}_gain{}".format(str(exp_time).replace(".", "_"), gain))
            if not os.path.exists(im_dir):
                os.makedirs(im_dir)
            plt.savefig(im_dir + "/row_profile_ET{}_gain{}.png".format(str(exp_time).replace(".", "_"), gain))
        else:
            plt.show()

