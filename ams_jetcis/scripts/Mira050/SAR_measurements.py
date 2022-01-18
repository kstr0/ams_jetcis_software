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
  -n NB_IM, --nb_im NB_IM           the nr of images taken
  -s, --save_im                     save images if argument is present
  -d DEVICE, --device DEVICE        the device id, 0 or 1
  -v, --verbosity

example: python3 noise_measurement.py -e 1 -n 50 -d 0


We share the RAW file test shooting environment to easily check the performance difference between MIRA220 and MIRA050. 
1.	Common environment: All Correction off. Lenses of MIRA220 and, there should be no difference in optical characteristics. MIRA050 mira220 will have the same lens as the 050. so image will be cropped on mira220 or we send the raw image to Samsung and they do it themeselves
2.	1. D65 Light, 200lux / Lens Fno : 2.2 / EIT : 7ms, 5.25ms , 3.5ms, 1.75ms , 0.7ms , 0.35ms / Gain : x1 / Macbeth chart 10 consecutive shots. 
3.    Dark (ambient temperature 25, 60℃) / EIT : 125ms / Gain x1 ~ Max Analog Gain (Step : x0.5) / 15 continuous shots 
       for each gain. Use a thermostream
4.   Dark (ambient temperature 25, 60℃) / EIT : 200ms / Gain x1, x2, x4, x8 / 15 continuous shots for each gain 3-4 probably the same measurements
5.   Light box 5000K / Gain x1 / EIT 10ms to output 1000code (include pedestal) Light box brightness adjustment / This is probably a simple response measurement, we concluded that we should do this without lenses.
      Change to the exposure time conditions below / 5 continuous shots per step
    1) Minimum exposure time ~ 0.1ms : Minimum step unit 
    2) 0.1ms ~ 1ms : in units of 0.05ms 
    3) 1ms ~ Center 100x100 saturation: 0.2ms increments 
    4) Up to full video saturation: 0.5ms increments 
    5) 100ms ~ 700ms (or up to the longest settable time): 100ms increments 


"""

import argparse
import subprocess
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np
import glob
import shutil
import time
import driver_access
from os import path
import os
import sys
sys.path.append("/home/jetcis/JetCis")
import pathlib

def printfun(x):
    print(x)


# Initialize the sensor


def start_sensor(imager,sensor, mode, gain):
    if sensor=='Mira050':
        if mode == '10bit' and gain == 1:
            fname = "../../Mira050/config_files/800_600_10b_mira050_normal_gain1_patch.py"
        elif mode == '10bit' and gain == 2:
            fname = "../../Mira050/config_files/800_600_10b_mira050_normal_gain2_patch.py"
        elif mode == '10bit' and gain == 4:
            fname = "../../Mira050/config_files/800_600_10b_mira050_normal_gain4_patch.py"

        elif mode == '12bit' and gain ==1:
            fname = "../../Mira050/config_files/800_600_12b_mira050_normal_gain1_patch.py"
        elif mode == '12bit' and gain ==2:
            fname = "../../Mira050/config_files/800_600_12b_mira050_normal_gain2_patch.py"
        elif mode == '12bit' and gain ==4:
            fname = "../../Mira050/config_files/800_600_12b_mira050_normal_gain4_patch.py"

        elif mode == '10bithighspeed' and gain ==1:
            fname = "../../Mira050/config_files/800_600_10b_mira050_highspeed_gain1_patch.py"
        elif mode == '10bithighspeed' and gain ==2:
            fname = "../../Mira050/config_files/800_600_10b_mira050_highspeed_gain2_patch.py"
        elif mode == '10bithighspeed' and gain ==4:
            fname = "../../Mira050/config_files/800_600_10b_mira050_highspeed_gain4_patch.py"
        else:
            raise ValueError('incorrect mode argument or file not present')
        try:
            with open(fname, "r") as file:
                eobj = compile(file.read(), fname, "exec")
                exec(eobj, globals())
        except:
            print("ERROR: unable to execute init script")
        sensorInfo = getSensorInfo(imager)
        resetSensor(imager)
        initSensor(imager)
        # trim_sensor(imager)

        imager.setformat(sensorInfo["bpp"], sensorInfo["width"], sensorInfo["height"],
                        sensorInfo["widthDMA"], sensorInfo["heightDMA"], True)


    elif sensor=='Mira220':
        raise Warning('not yet defined')
        
    else:
        raise ValueError('undefined Sensor type')

def set_exposure(imager, exposure_ms,sensor):
    if sensor=='Mira050':
        
        # Exposure registers
        imager.setSensorI2C(0x36)
        imager.type(1)

        # Get the entry value

        value = int(exposure_ms*1000)

        # Split value
        b3 = value >> 24 & 255
        b2 = value >> 16 & 255
        b1 = value >> 8 & 255
        b0 = value & 255

        # Write to registers
        imager.enablePrint()

        imager.write(0xe004,  0)
        imager.write(0xe000,  1)
        imager.write(0x000E, b3)
        imager.write(0x000F, b2)
        imager.write(0x0010, b1)
        imager.write(0x0011, b0)

    elif sensor=='Mira220':
        raise Warning('not yet defined')
        
    else:
        raise ValueError('undefined Sensor type')

def set_dgain(imager, dgain,sensor):

    if sensor=='Mira050':
        
        # Exposure registers
        imager.setSensorI2C(0x36)
        imager.type(1)

        # Get the entry value

        imager.write(0xe004,  0)
        imager.write(0xe000,  1)
        imager.write(0x0024,int(dgain)*16-1)

    elif sensor=='Mira220':
        raise Warning('not yet defined')
        
    else:
        raise ValueError('undefined Sensor type')

def grab_images(imager, count=1, save_im=0, fname=None):
    extra_columns_to_fit_buffer = imager.w % 16
    extra_rows_to_fit_buffer = imager.h % 16
    format = "--set-fmt-video=width={},height={},pixelformat={}".format(
        imager.w + extra_columns_to_fit_buffer, imager.h + extra_rows_to_fit_buffer, "RG" + str(imager.bpp))
    print(format)
    sp = subprocess.Popen(["/usr/bin/v4l2-ctl", "-d", imager.fname, format, "--set-ctrl", "bypass_mode=0",
                          "--stream-mmap", "--stream-count={}".format(count), "--stream-to=/tmp/record.raw"], stdin=subprocess.PIPE)

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
        img = img.reshape(count, imager.bufh + extra_rows_to_fit_buffer,
                          imager.w + extra_columns_to_fit_buffer)
        print("done reshaping, scaling now")

        img_calc = img[::, 0:imager.h, 0:imager.w].copy()
        img = img[::, 0:imager.h, 0:imager.w] * \
            2**(16-imager.bpp)  # scale to 16 bit tiff

        print(img.shape)
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
    parser.add_argument("-c", "--comment", type=str,
                        default='', help="comment of measurment")
    parser.add_argument("-tc", "--test_case", type=int,
                        default=1, help="test case number")
    parser.add_argument("-t", "--temperature", type=int,
                        default=25, help="the temperature of environment in C")
    parser.add_argument("-d", "--device", type=int,
                        default=0, help="the device id, 0 or 1")
    parser.add_argument("-s", "--sensor", type=str,
                        default='Mira050', help="sensor type, Mira050 or Mira220")

    args = parser.parse_args()

    comment = args.comment
    test_case = args.test_case
    temperature = args.temperature
    device = args.device
    sensor = args.sensor

    # TC 1:  D65 Light, 200lux / Lens Fno : 2.2 / EIT : 7ms, 5.25ms , 3.5ms, 1.75ms , 0.7ms , 0.35ms / Gain : x1 / Macbeth chart 10 consecutive shots.
    if test_case == 1:
        bitmodes_050 = ['10bit', '12bit', '10bithighspeed']
        bitmodes_220 = ['10bit', '12bit']
        exposures_ms = np.arange(0,30,2)
        exposures_ms = np.append(exposures_ms,[7,5.25,3.5,1.75,0.7,0.35])

        exposures_ms = np.sort(exposures_ms)
        agains = [1,4]
        dgains = [1,4]
        pictures_per_shot = 5
        print(exposures_ms)

    # TC 2: Dark (ambient temperature 25, 60℃) / EIT : 125ms and 200 / Gain x1 ~ Max Analog Gain (Step : x0.5) / 15 continuous shots
    # for each gain. Use a thermostream
    elif test_case == 2:
        bitmodes_050 = ['10bit', '12bit', '10bithighspeed']
        bitmodes_220 = ['10bit', '12bit']
        exposures_ms = [1, 20, 200]
        agains = [1,4]
        dgains = [1,4]
        pictures_per_shot = 5


    # TC 3: Light box 5000K / Gain x1 / EIT 10ms to output 1000code (include pedestal) Light box brightness adjustment /
    # Change to the exposure time conditions below / 5 continuous shots per step
    # 1) Minimum exposure time ~ 0.1ms : Minimum step unit
    # 2) 0.1ms ~ 1ms : in units of 0.05ms
    # 3) 1ms ~ Center 100x100 saturation: 0.2ms increments
    # 4) Up to full video saturation: 0.5ms increments
    # 5) 100ms ~ 700ms (or up to the longest settable time): 100ms increments
    elif test_case == 3:
        bitmodes_050 = ['10bit', '12bit', '10bithighspeed']
        bitmodes_220 = ['10bit', '12bit']
        exposures_ms = np.arange(0.1, 1.0, 0.05)
        exposures_ms=np.append(exposures_ms, np.arange(1.0, 15.0, 0.5))
        exposures_ms=np.append(exposures_ms, np.arange(50, 200, 50))

        print(exposures_ms)
        agains = [1]
        pictures_per_shot = 5
    else:
        raise ValueError('invalid argument value for testcase')
    if sensor == 'Mira050':
        bitmodes = bitmodes_050
    else:
        bitmodes = bitmodes_220
    imager = driver_access.imagerTools(printfun, device, None)
    imager.setSystype("Nano")
    imager.disablePrint()
    # dir_results = os.path.splitext(os.path.abspath(__file__))[0]
    dir_results=pathlib.Path(r'./SAR_results')
    print(dir_results)
    im_dir = dir_results / sensor / str(f"testcase{test_case}")
    print(im_dir)

    # if not os.path.exists(im_dir):
    #     os.makedirs(im_dir)
    # if not pathlib.Path(im_dir).exists:
    pathlib.Path(im_dir).mkdir(parents=True, exist_ok=True)
    print(im_dir)
    # Execute measurements
    for bitmode in bitmodes:
        for again in agains:
            for dgain in dgains:
                start_sensor(imager, sensor, bitmode, again)
                set_dgain(imager, dgain,sensor)
                time.sleep(0.01)   

                for exposure_ms in exposures_ms:
                    set_exposure(imager, exposure_ms,sensor)

                    time.sleep(0.1)
                    imgs = grab_images(imager, count=pictures_per_shot, save_im=1,
                                        fname=(f'./{im_dir}/{bitmode}_again_{again}_dgain_{dgain}_exp_ms_{exposure_ms:3.2f}_temp_{temperature}_{comment}'))
