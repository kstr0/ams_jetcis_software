"""
Example below shows a videostream from left and right camera simultaneaously, using the HW accelerated pipeline. no root required to run this.
author: Philippe.Baetens@ams.com

usage: dualcam.py [-h] [-e EXP_TIME] [-d DEVICES [DEVICES ...]] [-v]

optional arguments:
  -h, --help            show this help message and exit
  -e EXP_TIME, --exp_time EXP_TIME
                        the exp time in ms
  -d DEVICES [DEVICES ...], --devices DEVICES [DEVICES ...]
                        the devices id, 0 or 1 or 0 1
  -v, --verbosity

example use:
python3 dualcam.py -e 5 -d 0 1 
"""

import argparse
import glob
import os
import shutil
import subprocess
import sys
import time
from os import path
import cv2
import cv2 as cv
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
sys.path.append("/home/jetcis/JetCis")
import driver_access

port = 0
tnr = 0
ee = 0
sensor_mode = 0
dgain = "1 1"

sensor_w = 800
sensor_h = 600
sensor_wdma = 1600
sensor_hdma = 1200
bpp = 10
sensor_fps = 30
v4l2 = 0
iface = []


def printfun(x):
    print(x)


# Initialize the sensor
def start_sensor(imager, exp_time):
    fname = "/home/jetcis/JetCis/Mira220/config_files/fullres_30fps.py"
    try:
        with open(fname, "r") as file:
            eobj = compile(file.read(), fname, "exec")
            exec(eobj, globals())
    except:
        print("ERROR: unable to execute init script")
    sensorInfo = getSensorInfo(imager)
    resetSensor(imager)
    initSensor(imager)
    imager.setformat(sensorInfo["bpp"], sensorInfo["width"], sensorInfo["height"],
                     sensorInfo["widthDMA"], sensorInfo["heightDMA"], True)

    # Exposure registers
    imager.setSensorI2C(0x54)
    imager.type(1)
    row_length = imager.read(0x102B) + 256 * imager.read(0x102C)
    reg_shutter = round(exp_time / (row_length / 38400000 * 1000))
    imager.write(0x100c, reg_shutter % 256)  # Exposure time
    imager.write(0x100d, reg_shutter // 256)  # Exposure time


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--exp_time", type=int,
                        default=1, help="the exp time in ms")
    parser.add_argument("-d", "--devices",  nargs='+',
                        default=['0'], help="the devices id, 0 or 1 or 0 1")
    parser.add_argument("-v", "--verbosity", action="count", default=2)

    args = parser.parse_args()
    exp_time = args.exp_time
    devices = [int(i) for i in args.devices]

    if args.verbosity >= 2:
        print("Running '{}'".format(__file__))
    if args.verbosity >= 1:
        print(f"starting noise script w parameters {exp_time}  {devices}")

    imagers = []
    for i in devices:
        imagers.append(driver_access.ImagerTools(print, i, None))

    for imager in imagers:
        start_sensor(imager, exp_time)

    caps = []
    iface = [0, 0]
    for port in devices:
        iface[port] = "nvarguscamerasrc sensor-id={} wbmode=0  tnr-mode={} tnr-strength=0.5 ee-mode={} ee-strength=0.5 sensor-mode={} ".format(
            port, tnr, ee, sensor_mode)
        iface[port] += "saturation=0.0 "
        iface[port] += "ispdigitalgainrange=\"{}\" !".format(dgain)
        iface[port] += " video/x-raw(memory:NVMM),width=(int){},height=(int){},format=(string)NV12,framerate=(fraction){}/1 !".format(
            sensor_w, sensor_h, sensor_fps)
        #            if (record == False):
        iface[port] += " nvvidconv ! video/x-raw ! appsink"
        print(iface[port])
        caps.append(cv2.VideoCapture(iface[port]))

    for imager in imagers:
        imager.setformat(bpp, sensor_w, sensor_h,
                         sensor_wdma, sensor_hdma, v4l2)

    # os.system(iface)
    time.sleep(1)

    frames = [0, 0]

    while(all([cap.isOpened() for cap in caps])):
        for i in range(len(caps)):
            ret, frames[i] = caps[i].read()
            cvimage1 = cv2.cvtColor(frames[i], cv2.COLOR_BGR2RGBA)

            cv2.imshow(f'frame{i}', cvimage1)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    for cap in caps:
        cap.release()

    cv2.destroyAllWindows()
