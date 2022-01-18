"""
Description: script to do noise measurement for Mira220 sensor.
Author: kristof.stroobants@ams.com, philippe.baetens@ams.com
Date: 01/2021
Comment: make sure to close all python applications/GUIs before running this script. Run this script without
         illumination by covering the sensor.
         
usage: noise_measurement.py [-h] [-e EXP_TIME] [-n NB_IM] [-s] [-d DEVICE] [-v]

optional arguments:
  -h, --help                        show this help message and exit
  -e EXP_TIME, --exp_time EXP_TIME  the exp time in ms
  -s, --save_im                     save images if argument is present
  -d DEVICE, --device DEVICE        the device id, 0 or 1
  -v, --verbosity

example: python3 noise_measurement.py -e 1 -n 50 -d 0

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
import argparse


def printfun(x):
    print(x)


# Initialize the sensor

def trim_sensor(imager):
    for addr in range(0,255):
        imager.write(0xe000,0)
        imager.write(0x0066,0)
        imager.write(0x0067,addr) #addr
        imager.write(0x0064,1)
        imager.write(0x0064,0)
        count=0
        time.sleep(0.01)
        while(imager.read(0x0065)!=0) and count<3:
            time.sleep(0.01)
            count=count+1    
        dout=imager.read(0x006C)
        print(f"OTP addr {addr:4d} {dout:4d}")


def start_sensor(imager, exp_time):
    
    fname = "../../Mira050/config_files/800_600_10b_mira050_normal.py"
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
    imager.setSensorI2C(0x36)
    imager.type(1)

    # Get the entry value
    
    value = int(exp_time)

    # Split value
    b3 = value >> 24 & 255
    b2 = value >> 16 & 255
    b1 = value >> 8  & 255
    b0 = value       & 255
    
    # Write to registers
    imager.enablePrint()

    imager.write(0xe004,  0)
    imager.write(0xe000,  1)
    imager.write(0x000E, b3)
    imager.write(0x000F, b2)
    imager.write(0x0010, b1)
    imager.write(0x0011, b0)


def grab_images(imager, count=1, save_im=0, fname=None):
    extra_columns_to_fit_buffer = imager.w % 16
    extra_rows_to_fit_buffer = imager.h % 16
    format = "--set-fmt-video=width={},height={},pixelformat={}".format(imager.w + extra_columns_to_fit_buffer, imager.h + extra_rows_to_fit_buffer, "RG" + str(imager.bpp))
    print(format)
    sp = subprocess.Popen(["/usr/bin/v4l2-ctl", "-d", imager.fname, format, "--set-ctrl", "bypass_mode=0", "--stream-mmap", "--stream-count={}".format(count), "--stream-to=/tmp/record.raw"], stdin=subprocess.PIPE)

    #sp = subprocess.Popen(["/usr/bin/v4l2-ctl", "-d", imager.fname, imager.format, "--set-ctrl", "bypass_mode=0", "--stream-mmap", "--stream-count={}".format(count), "--stream-to=/tmp/record.raw"], stdin=subprocess.PIPE)
    sp.wait()

    # Copy raw from RAM to return variable. Remove stuffing data and extract single frames
    if (imager.bpp > 8):
        dt = np.uint16
    else:
        dt = np.uint8
    sp.wait()
    
    if(fname != "/dev/null"):
        # cut out data
        print("loading raw image...")
        img = np.fromfile("/tmp/record.raw", dtype=dt)
        print(img.shape)
        print(img)
        print("loaded raw image.")
        print("scaling raw image to tiff...")
        img = img.reshape(count, imager.bufh + extra_rows_to_fit_buffer, imager.w + extra_columns_to_fit_buffer)
        print("done reshaping, scaling now")
        img_calc = img[::, 0:imager.h, 0:imager.w].copy()
        img = img[::, 0:imager.h, 0:imager.w] * \
            2**(16-imager.bpp)  # scale to 16 bit tiff


        print("scaled raw image to tiff...")
        if save_im:
            for fno in range(0, count):
                print("saving tiff...")
                f = "{}_{}.tiff".format(fname, fno)
                Image.fromarray(img[fno]).save(f)
                print("saved tiff.")
    print("cleaning up...")
    sp = subprocess.Popen(["/bin/rm", "/tmp/record.raw"])
    sp.wait()
    print("cleaned up.")

    return img_calc


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-e","--exp_time", type=int, default=10, help="the exp time in ms")
    #parser.add_argument("-n","--nb_im", type=int, default=50, help="the nr of images taken")
    parser.add_argument("-d","--device", type=int, default=0, help="the device id, 0 or 1")
    parser.add_argument("-s","--save_im", action="count", default=0, help="save images if argument is present")
    parser.add_argument("-v", "--verbosity", action="count", default=2)

    args = parser.parse_args()

    exp_time = args.exp_time
    #nb_im = args.nb_im
    save_im = args.save_im
    device = args.device

    if args.verbosity >= 2:
        print("Running '{}'".format(__file__))
    if args.verbosity >= 1:
        print(f"starting noise script w parameters {exp_time} {save_im} {device}")

    # Access the driver
    imager = driver_access.ImagerTools(printfun, device, None)
    imager.setSystype("Nano")
    imager.disablePrint()

    # Get path
    dir_results = os.path.splitext(os.path.abspath(__file__))[0]
    # long images

    # short image
    # Init sensor and take images
    start_sensor(imager, exp_time)
    long = grab_images(imager, count=20, save_im=0)

    start_sensor(imager, 0.01)
    short = grab_images(imager, count=20, save_im=0)


    # Noise
    longmean = np.mean(np.mean(long,axis=2))
    shortmean = np.mean(np.mean(short,axis=2))
    print(f"{longmean} {shortmean}")
    DC=(longmean-shortmean)/(exp_time/1000)
    print("DC [DN]: {:.03f}".format(DC))
