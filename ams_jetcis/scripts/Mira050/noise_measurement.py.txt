"""
Description: script to do noise measurement for Mira220 sensor.
Author: kristof.stroobants@ams.com, philippe.baetens@ams.com
Date: 01/2021
Comment: make sure to close all python applications/GUIs before running this script. Run this script without
         illumination by covering the sensor.
         
usage: noise_measurement.py [-h] [-e EXP_TIME] [-ag AGAIN] [-dg DGAIN]
                            [-n NB_IM] [-d DEVICE] [-s] [-b BIT_MODE] [-v]

optional arguments:
  -h, --help            show this help message and exit
  -e EXP_TIME, --exp_time EXP_TIME
                        the exp time in us
  -ag AGAIN, --again AGAIN
                        the gain
  -dg DGAIN, --dgain DGAIN
                        the gain
  -n NB_IM, --nb_im NB_IM
                        the nr of images taken
  -d DEVICE, --device DEVICE
                        the device id, 0 or 1
  -s, --save_im         save images if argument is present
  -b BIT_MODE, --bit_mode BIT_MODE
                        bit mode: 10bit or 12bit or 10bithighspeed
  -v, --verbosity

example: python3 noise_measurement.py -e 1000 -b '12bit' -n 50 -dg 1 -ag 1 -s

"""

from os import path
import os
import sys
import time
import shutil
import glob
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import subprocess
import argparse
import pathlib
os.getcwd()
sys.path.append('/home/jetcis/ams')
from ams_jetcis.common.driver_access import ImagerTools
from ams_jetcis.sensors.mira050.mira050 import Mira050
from ams_jetcis.sensors.sensor import Sensor


# # get current directory
# path = pathlib.Path(__file__)
# print("Current File", path)
# print("Current File par", path.parent)

# print("Current File par4", path.parent.parent.parent.parent.absolute())
# path4=(str(path.parent.parent.parent.parent.absolute()))
# print(path4)
# __path__ = [path4]
# print(sys.path)


def printfun(x):
    print(x)


# Initialize the sensor


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--exp_time", type=int,
                        default=1000, help="the exp time in us")
    parser.add_argument("-ag", "--again", type=int, default=1, help="the gain")
    parser.add_argument("-dg", "--dgain", type=int, default=1, help="the gain")
    parser.add_argument("-n", "--nb_im", type=int,
                        default=20, help="the nr of images taken")
    parser.add_argument("-d", "--device", type=int,
                        default=0, help="the device id, 0 or 1")
    parser.add_argument("-s", "--save_im", action="count",
                        default=0, help="save images if argument is present")
    parser.add_argument("-b", "--bit_mode", type=str, default='10bit',
                        help="bit mode: 10bit or 12bit or 10bithighspeed")
    parser.add_argument("-v", "--verbosity", action="count", default=2)

    args = parser.parse_args()

    exp_time = args.exp_time
    again = args.again
    dgain = args.dgain
    nb_im = args.nb_im
    save_im = args.save_im
    device = args.device
    mode = args.bit_mode
    sensor = 'Mira050'
    if args.verbosity >= 2:
        print("Running '{}'".format(__file__))
    if args.verbosity >= 1:
        print(
            f"starting noise script w parameters {exp_time} {nb_im} {save_im} {device} {mode} {again} {dgain}")

    # Get path
    dir_results = os.path.splitext(os.path.abspath(__file__))[0]

    # Init sensor and take images
    sensor = Mira050(imagertools=ImagerTools(
        printfun=None, port=0, rootPW='jetcis'))
    sensor.cold_start()
    sensor.init_sensor(bit_mode=mode, analog_gain=again)
    sensor.set_digital_gain(dgain)
    sensor.set_exposure_us(time_us=exp_time)
    time.sleep(0.1)
    imgs = sensor.imager.saveTiff(
        dir_fname=f'./results/noise_measurement/mira050_{mode}_ag{again}_dg{dgain}_exp{exp_time}', count=nb_im, save=save_im)
    if sensor.low_fpn==True:
        print('LOW FPN MODE OK')
    else:
        print('probably using old settings')
    # Noise
    fpn_frame = np.mean(imgs, axis=0)  # 3d array [number,height,width]
    fpn = np.std(fpn_frame)
    t_noise = np.mean(np.std(imgs, axis=0))
    row_noise = np.mean(np.std(np.mean(imgs - fpn_frame, axis=2), axis=1))

    print("mean [DN]: {:.03f}".format(np.mean(np.mean(imgs))))
    print("FPN [DN]: {:.03f}".format(fpn))
    print("Noise [DN]: {:.03f}".format(t_noise))
    print("Row noise [DN]: {:.03f}".format(row_noise))
