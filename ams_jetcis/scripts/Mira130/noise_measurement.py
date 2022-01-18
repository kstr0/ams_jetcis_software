"""
Description: script to do noise measurement for Mira130 sensor.
Author: kristof.stroobants@ams.com, philippe.baetens@ams.com
Date: 01/2021
Comment: make sure to close all python applications/GUIs before running this script. Run this script without
         illumination by covering the sensor.
         
usage: noise_measurement.py [-h] [-e EXP_TIME] [-n NB_IM] [-s] [-d DEVICE] [-v]

optional arguments:
  -h, --help                        show this help message and exit
  -e EXP_TIME, --exp_time EXP_TIME  the exp time in ms
  -n NB_IM, --nb_im NB_IM           the nr of images taken
  -s, --save_im                     save images if argument is present
  -d DEVICE, --device DEVICE        the device id, 0 or 1
  -v, --verbosity

example: python3 noise_measurement.py -e 1 -n 5 -d 0 -s

"""

from os import path
import os
import sys
sys.path.append("/home/jetcis/JetCis")
import driver_access_new as driver_access
import time
import shutil
import glob
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import subprocess
import argparse


def printfun(x):
    print(x)


# Initialize the sensor
def start_sensor(imager, exp_time):
    fname = "/home/jetcis/JetCis/Mira130/fullres.py"
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
    #imager.setSensorI2C(0x54)
    #imager.type(1)
    #row_length = imager.read(0x102B) + 256 * imager.read(0x102C)
    #reg_shutter = round(exp_time / (row_length / 38400000 * 1000))
    #imager.write(0x100c, reg_shutter % 256)  # Exposure time
    #imager.write(0x100d, reg_shutter // 256);  # Exposure time


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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-e","--exp_time", type=int, default=1, help="the exp time in ms")
    parser.add_argument("-n","--nb_im", type=int, default=50, help="the nr of images taken")
    parser.add_argument("-d","--device", type=int, default=0, help="the device id, 0 or 1")
    parser.add_argument("-s","--save_im", action="count", default=0, help="save images if argument is present")
    parser.add_argument("-v", "--verbosity", action="count", default=2)

    args = parser.parse_args()

    exp_time = args.exp_time
    nb_im = args.nb_im
    save_im = args.save_im
    device = args.device

    if args.verbosity >= 2:
        print("Running '{}'".format(__file__))
    if args.verbosity >= 1:
        print(f"starting noise script w parameters {exp_time} {nb_im} {save_im} {device}")

    # Access the driver
    imager = driver_access.ImagerTools(printfun, device, None)
    imager.setSystype("Nano")
    imager.disablePrint()

    # Get path
    dir_results = os.path.splitext(os.path.abspath(__file__))[0]

    # Init sensor and take images
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
    meanlvl=np.mean(imgs)
    t_noise = np.mean(np.std(imgs, axis=0))
    row_noise = np.mean(np.std(np.mean(imgs - fpn_frame, axis=2), axis=1))
    print(f"mean level: {meanlvl:.03f}")
    print("FPN [DN]: {:.03f}".format(fpn))
    print("Noise [DN]: {:.03f}".format(t_noise))
    print("Row noise [DN]: {:.03f}".format(row_noise))
