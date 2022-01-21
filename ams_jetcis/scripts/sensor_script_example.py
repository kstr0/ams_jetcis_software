"""
example script to init a sensor and take pictures
"""

import time
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import sys
import csv
import os
from PIL import Image
import os
# from numpy.core.numerictypes import _add_array_type
import pandas as pd
import cv2
import pathlib
from numpy.lib.npyio import save
# sys.path.insert(0, os.path.abspath(os.path.join(
#     os.path.dirname(__file__), '../..')))  # add parent folder to path
# sys.path.insert(0, os.path.abspath(os.path.join(
#     os.path.dirname(__file__), '..')))  # add parent folder to path
# sys.path.insert(0, os.path.abspath(os.path.join(
#     os.path.dirname(os.getcwd()), '../..')))  # add parent folder to path
# sys.path.insert(0, os.path.abspath(os.path.join(
    # os.path.dirname(os.getcwd()), '.')))  # add parent folder to path
# matplotlib.use('Agg')
# matplotlib.use("gtk")
# system imports
import ams_jetcis
from ams_jetcis.sensors.sensor import Sensor
from ams_jetcis.sensors.mira220.mira220 import Mira220
from ams_jetcis.sensors.mira130.mira130 import Mira130
from ams_jetcis.sensors.mira050.mira050 import Mira050
from ams_jetcis.sensors.mira030.mira030 import Mira030
from ams_jetcis.common.driver_access import ImagerTools
# import mira_xs_api
# from mira_xs_api.mira_xs_api import MiraXS_API
# from mira_xs_api.calibration import (
#     upload_device_specific_black_level,
#     upload_device_specific_trim_settings)
# from mira_xs_api.sensor_input_interfaces.SensorModelInterface import (
#         AddressBasedProgrammingSequence,
#         NameBasedProgrammingSequence,
#         NameBasedWriteInstruction,
#         ProgrammingSequence
#     )
import ams_jetcis.scripts.plotter as plotter

# import ams_jetcis.characterization.standard_tests.ptc as char
def printfun(x):
    print(x)

def live_view(sensor='Mira130'):
    # Access the driver
    imagertools = ImagerTools(printfun=None, port=0, rootPW='jetcis')
    sensor = Mira130(imagertools)

    sensor.reset_sensor()
    sensor.check_sensor()
    sensor.init_sensor(bit_mode='10bit', w=1080, h=1280, fps=30)

    sensor.set_exposure(1000)
    sensor.set_analog_gain(1.5)
    port = 0
    tnr = 0
    ee = 0
    sensor_mode = 0
    dgain = "1 1"

    dgain = "1 1"
    tnr = 0
    caps = []
    iface = [0, 0]
    devices = [0]
    for port in devices:
        iface[port] = "nvarguscamerasrc sensor-id={} wbmode=0  tnr-mode={} tnr-strength=0.5 ee-mode={} ee-strength=0.5 sensor-mode={} ".format(
            port, tnr, ee, sensor_mode)
        iface[port] += "saturation=0.0 "
        iface[port] += "ispdigitalgainrange=\"{}\" !".format(dgain)
        iface[port] += " video/x-raw(memory:NVMM),width=(int){},height=(int){},format=(string)NV12,framerate=(fraction){}/1 !".format(
            sensor.width, sensor.height, sensor.fps)
        #            if (record == False):
        iface[port] += " nvvidconv ! video/x-raw ! appsink"
        print(iface[port])
        caps.append(cv2.VideoCapture(iface[port]))

    # os.system(iface)
    time.sleep(1)

    frames = [0, 0]

    while(all([cap.isOpened() for cap in caps])):
        for i in range(len(caps)):
            ret, frames[i] = caps[i].read()
            cvimage1 = cv2.cvtColor(frames[i], cv2.COLOR_BGR2RGBA)
            print(cvimage1.mean())
            cv2.imshow(f'frame{i}', cvimage1)
            break
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    for cap in caps:
        cap.release()

    cv2.destroyAllWindows()

def test_miraxs_api():
    import mira_xs_api

def test_mira130_gain():
    imagertools = ImagerTools(printfun=None, port=0, rootPW = 'jetcis')
    sensor = Mira130(imagertools)
    sensor.imager.setSensorI2C(0x0)
    sensor.imager.write(0x3e02,223)
    sensor.reset_sensor()
    sensor.cold_start()
    sensor.init_sensor(bit_mode='10bit')
    imgs = sensor.imager.grab_images(5)
    np.mean(imgs)
        
def test_mira130():
    imagertools = ImagerTools(printfun=None, port=0, rootPW = 'jetcis')
    sensor = Mira130(imagertools)
    sensor.imager.setSensorI2C(0x0)
    sensor.imager.write(0x3e02,223)
    sensor.reset_sensor()
    sensor.cold_start()

    # sensor.init_sensor(bit_mode='10bit')
    # sensor.imager.setSensorI2C(0x30)
    # sensor.imager.type(1)  # reg=16bit, val=8bit

    # sensor.imager.read(0x3108)

    # imgs = sensor.imager.grab_images(5)
    # print(imgs.shape)
    # while True:
    #     sensor.check_sensor()
    #     time.sleep(2)
    
    # plt.imshow(imgs[0], cmap=plt.get_cmap('gray'), vmin = 0, vmax = (1 << sensor.bpp) - 1)          
    # plt.show()
    # statistics(images)

def test_mira220_context():
    sensor = Mira220(imagertools=ImagerTools(printfun=None, port=0, rootPW='jetcis'))
    sensor.cold_start()
    sensor.init_sensor()
    
    print(f'active context: {sensor.context_active}')
    print(f'observe context: {sensor.context_observe}')
    print(f'fps: {sensor.fps}')
    print('------------------')
    sensor.context_observe = 'B'
    print(f'active context: {sensor.context_active}')
    print(f'observe context: {sensor.context_observe}')
    print(f'fps: {sensor.fps}')

def test_mira220():
    sensor = Mira220(imagertools=ImagerTools(printfun=None, port=0, rootPW='jetcis'))
    sensor.cold_start()
    sensor.init_sensor()
    images = sensor.imager.grab_images(count =5)
    statistics(images)

def test_mira220_uc_ext():
    sensor = Mira220(imagertools=ImagerTools(printfun=None, port=0, rootPW='jetcis'))
    sensor.cold_start()
    sensor.init_sensor()
    sensor.set_exposure_us(10*1e3)

    sensor.stop_img_capture()
    nb_pins = 2
    fps_uc = 20
    t_exp_uc = 1 * 1e3 #us
    sensor.set_uc_timing_triggers(t_exp_uc, fps_uc, cont=True, nb_pins=nb_pins)
    sensor.start_img_capture(master=False, nb_pins=nb_pins, exp_pw_sel=0, exp_delay=None)
    
    # imgs = sensor.imager.grab_images(2)
    # print(imgs.shape)
    # plt.imshow(imgs[0], cmap=plt.get_cmap('gray'), vmin = 0, vmax = (1 << sensor.bpp) - 1)          
    # plt.show()

def test_mira130_with_dtb_handling():
    imagertools = ImagerTools(printfun=None, port=0, rootPW = 'jetcis')
    sensor = Mira130(imagertools)


    sensor.cold_start()
    sensor.init_sensor(bit_mode='10bit')



def ina3221(imager):
    imager.setSensorI2C(65)
    imager.type(2)  # reg=16bit, val=8bit
    print(imager.write(0,0x7FD7))
    time.sleep(0.1)
    print(hex(imager.read(0x00)))
    print((imager.read(0x02)))
    print((imager.read(0x04)))
    print((imager.read(0x06)))
    print((imager.read(0x02)))
    print((imager.read(0x04)))
    print((imager.read(0x06)))

    # print(imager.read(0xFE))
    print(hex(imager.read(0xFF)))
    # imager.setSensorI2C(0x0A)
    # imager.type(0)
    # imager.write(12, 0b11110111)
    return 0


def test_mira050_calibration():
    from mira_xs_api.dummy_api import DummyAPI
    dummy=DummyAPI()
    imager = imagertools=ImagerTools(printfun=None, port=0, rootPW='jetcis')
    sensor = Mira050(imager)
    sensor.cold_start()
    device_id = '1971003'
    import ams_jetcis.sensors.mira050.trim_settings
    directory=os.path.dirname(ams_jetcis.sensors.mira050.trim_settings.__file__)
    trim_file = pathlib.Path(directory, f'{device_id}.txt')
    upload = NameBasedProgrammingSequence.from_file(trim_file)
    upload2=mira_xs_api.mira_xs_api.MiraXS_API(dummy)._convert_to_address_based_programming_sequence(upload)
    print(upload2)
    print(upload)
    for x in upload2.instructions:
        print(x)

def test_mira050():
    imager = imagertools=ImagerTools(printfun=None, port=0, rootPW='jetcis')
    sensor = Mira050(imager)
    sensor.cold_start()
   
    # ina3221(imager)
    # imager.getSensorType()
    # imager.getSensorID()
    # sensor = Mira050(imager)
    # sensor.cold_start()
    sensor.init_sensor(bit_mode='10bit', analog_gain=8)
    sensor.illum_trig(False)
    # sensor.led_driver=[1,650,60]

    # sensor.imager.enablePrint()
    # sensor.get_temperature()
    sensor.set_exposure_us(time_us = 150)
    # ina3221(imager)
    time.sleep(0.4)
    images = sensor.imager.grab_images(count =20)
    sensor.imager.save_images(imgs=images, dir_fname = '/home/jetcis/10bgain8')

    statistics(images)

def automated_measurement_050():
    comment = 'black'
    test_case = 1
    temperature = 25
    device = 0
    sensor = 'mira050'
    bitmodes =  ['12bit']#, '12bit', '10bithighspeed']
    exposures_us = [100]  # np.arange(0,100,2)
    agains = [1]
    dgains = [1]
    pictures_per_shot = 20
    print(exposures_us)
    dir_results = pathlib.Path(r'./12bit_sweep_mira050_dark')
    print(dir_results)
    im_dir = dir_results / sensor / str(f"testcase{test_case}")
    print(im_dir)

    for bitmode in bitmodes:
        for again in agains:
            sensor = Mira050(imagertools=ImagerTools(printfun=None, port=0, rootPW='jetcis'))
            sensor.cold_start()
            sensor.init_sensor(bit_mode=bitmode, analog_gain=again)
            images = sensor.imager.grab_images(count =1)
            print(np.mean(images))

def test_interposer_gpio():
    
    pass

def test_mira050_config():
    sensor = Mira050(imagertools=ImagerTools(printfun=None, port=0, rootPW='jetcis'))
    sensor.cold_start()
    sensor.init_sensor(bit_mode='10bithighspeed', analog_gain=1)



    # reg_seq = sensor.config_parser(fname = r'12-bit mode_anagain1_30fps_exp0.05ms_continuous_clk_datarate_1400.txt')
    # sensor.init_from_config(reg_seq)
    # sensor.init_sensor(bit_mode='12bit', analog_gain=1)
    # sensor.imager.enablePrint()

    # while True:
    #     sensor.imager.read(0xE000)
    #     time.sleep(0.1)
    images = sensor.imager.grab_images(count =5)


    print(images)
    # print(sensor.imager.getSensorType())
    # print(sensor.imager.getSensorID())
    statistics(images)


    # sensor.imager.setSensorI2C(0x36)
    # sensor.imager.type(1)
    # sensor.imager.write(0xE000,0) # banksel


    # black_level = 200
    # sensor.set_black_level(bit_mode='12bit', analog_gain=1, target = black_level)
    # images = sensor.imager.saveTiff(fname='beeldje', count=5, save=False)
    # print(images.shape)
    # print(sensor.imager.getSensorType())
    # print(sensor.imager.getSensorID())
    # statistics(images)
    # print('######################################')
    
    # # For 12-bit, Analog Gain x1
    # tsens_slope = 1.29
    # tsens_offset = 400
    # dn_per_degree = -2.64662 / 4

    # #reeadout temperature
    # raw_temp = get_temp_050(sensor)
    # print(f'raw temp is {raw_temp}')
    # # get offset
    # adc_cyc_act1 = sensor.imager.read(0x018B)*256 + sensor.imager.read(0x018C)
    # offset = 2* adc_cyc_act1
    # # get calbirated temp
    # raw_tsens_data = raw_temp - offset
    # temp = (raw_tsens_data - tsens_offset) / tsens_slope
    # print(f'real temp is {temp}')

    # temp_delta = 60 - temp
    # black_level_adj = temp_delta*dn_per_degree
    # print(f"Black level adjustment = {black_level_adj}DN")
    # sensor.set_black_level(bit_mode='12bit', analog_gain=1, target = black_level+black_level_adj)

    # images = sensor.imager.saveTiff(fname='beeldje', count=5, save=False)
    # print(images.shape)
    # print(sensor.imager.getSensorType())
    # print(sensor.imager.getSensorID())
    # statistics(images)
    # print('######################################')

def get_otp_050(sensor='mira050'):
    sensor = Mira050(imagertools=ImagerTools(
        printfun=None, port=0, rootPW='jetcis'))
    sensor.cold_start()
    sensor.init_sensor(bit_mode='10bit', analog_gain=2)
    # exposures = range(100, 50000, 3000)
    print(f'wafer id: {sensor.get_wafer_id()}')
    print(f'x: {sensor.get_wafer_x_location()}')
    print(f'y: {sensor.get_wafer_y_location()}')
    print(f'chucktemp1: {sensor.get_temp_wafer()}')
    print(f'versionmap: {sensor.get_map_version()}')


def get_temp_050(sensor):
    
    sensor.imager.setSensorI2C(0x36)
    sensor.imager.type(1)
    sensor.imager.write(0xE000,0) # banksel
    temps = []
    for i in range(10):
        sensor.imager.write(0x74, 1)
        raw_temp = sensor.imager.read(0x72)*256 + sensor.imager.read(0x73)
        sensor.imager.write(0x74, 0)
        temps.append(raw_temp)
    avg = np.mean(temps)
    print(temps)
    return avg


def test_mira050_lowfpn():
    sensor = Mira050(imagertools=ImagerTools(
        printfun=None, port=0, rootPW='jetcis'))
    sensor.cold_start()
    sensor.init_sensor(bit_mode='10bit', analog_gain=2)
    # exposures = range(100, 50000, 3000)
    images = sensor.imager.grab_images(count = 15)
    statistics(images)
    print(sensor.get_temperature())
    print(sensor.get_temperature())
    sensor.cold_start()
    sensor.init_sensor(bit_mode='12bit', analog_gain=1)
    print(sensor.get_temperature())
    print(sensor.get_temperature())

def test_mira050_exposures():
    means = []
    sensor = Mira050(imagertools=ImagerTools(
        printfun=None, port=0, rootPW='jetcis'))
    sensor.cold_start()
    sensor.init_sensor(bit_mode='12bit', analog_gain=1)
    exposures = range(100, 50000, 3000)
    for exposure in exposures:
        sensor.set_exposure_us(time_us=exposure)
        time.sleep(0.1)
        images = sensor.imager.saveTiff(fname='beeldje', count=5, save=False)
        means.append(statistics(images)[0])
    print(means)
    plt.figure(0)
    plt.plot(exposures, means)
    plt.show()

def process_automated_measurement():
    import characterization.stats_engine.stats as stats
    import characterization.standard_tests.ptc as ptc

    dir_results = pathlib.Path(r'./12bit_sweep_mira050_lowfpn_1_dark')
    df=pd.read_csv(dir_results/'results.csv')
    print(df)
    ptclist=[]
    imnames=df['filename']
    bitmode=df['bitmode'][0]
    bpp=int(bitmode.split('bit')[0])
    for imname in imnames:
        images=[]
        for imname2 in dir_results.glob(f'./mira050/testcase1/{imname}*.tiff'):
            im = Image.open(imname2)
            images.append(np.array(im))
        images=np.array(images)
        images=images/(2**(16-bpp))
        ptclist = [i for i in ptclist]
        ptclist.append(images)

    agres = stats.agg_results(images)  
    df.rename(columns = {'mean':'meanold'}, inplace = True)
    ptc.get_stats(ptclist, df=df)
    ptc.ptc(ptclist, df, 'exp_us')



def automated_measurement():
    comment = 'dark'
    test_case = 1
    device = 0
    sensor = 'mira050'
    bitmodes =  ['12bit'] #,'10bit', '10bithighspeed']
    exposures_us = np.arange(100,1000, 200)
    agains = [1] #,2,4]
    dgains = [1] #,4]
    pictures_per_shot = 10
    
    dir_results = pathlib.Path(r'./12bit_sweep_mira050_lowfpn_1_dark')
    im_dir = dir_results / sensor / str(f"testcase{test_case}")
    sensor = Mira050(imagertools=ImagerTools(printfun=None, port=0, rootPW='jetcis'))
    sensor.cold_start()
    sensor.init_sensor(bit_mode='12bit', analog_gain=1)
    sensor.temperature=int(sensor.get_temperature())
    # if not os.path.exists(im_dir):
    #     os.makedirs(im_dir)
    # if not pathlib.Path(im_dir).exists:
    pathlib.Path(im_dir).mkdir(parents=True, exist_ok=True)
    print(im_dir)
    means = []
    fpns = []
    row_fpns = []
    col_fpns = []
    noises = []
    row_noises = []
    # Execute measurements
    if not os.path.exists(dir_results/'results.csv'):
        exists = False
    else:
        exists = True
    #with open(dir_results/'results.txt', "a") as f:
    with open(dir_results/'results.csv', "a+") as f:
        writer = csv.writer(f)
        header = ['bitmode', 'again', 'dgain', 'exp_us', 'temp', 'mean', 'fpn', 'row_fpn', 'col_fpn', 't_noise', 'row_noise', 'lowfpn', 'filename','count']

        if not exists:
            writer.writerow(header)

        for low_fpn in [True]:
            sensor.low_fpn = low_fpn
            for bitmode in bitmodes:
                for again in agains:
                    for dgain in dgains:
             
                        # sensor.cold_start()
                        #sensor.check_sensor()
                        sensor.cold_start()

                        sensor.temp_cor=True

                        sensor.init_sensor(bit_mode=bitmode, analog_gain=again)
                        # set_dgain(imager, dgain,sensor)
                        time.sleep(0.1)

                        for exposure_us in exposures_us:
                            sensor.set_exposure_us(time_us=exposure_us)
                            images = []
                            time.sleep(0.4)
                            images = sensor.imager.grab_images(pictures_per_shot)
                            comment=f'lowfpn{low_fpn}'
                            fname=f'{bitmode}_again_{again}_dgain_{dgain}_exp_us_{exposure_us:4.0f}_temp_{sensor.temperature}_{comment}'
                            sensor.imager.save_images(imgs=images, dir_fname = im_dir/fname)
                            #images = sensor.imager.saveTiff(
                            #    fname=f'{bitmode}_again_{again}_dgain_{dgain}_exp_us_{exposure_us:4.0f}_temp_{temperature}_{comment}', count=pictures_per_shot, save=False)
                            mean, fpn, row_fpn, col_fpn, t_noise, row_noise = statistics(
                                images[:,60:160,290:390])
                            # imgs = sensor.imager.grab_images(imager, count=pictures_per_shot, save_im=1,
                            #                     fname=(f'./{im_dir}/{bitmode}_again_{again}_dgain_{dgain}_exp_ms_{exposure_ms:3.2f}_temp_{temperature}_{comment}'))
                            print(f'MEAN of 1 series: {np.mean(images,axis =(1,2))}')
                            means.append(mean)
                            fpns.append(fpn)
                            row_fpns.append(row_fpn)
                            col_fpns.append(col_fpn)
                            noises.append(t_noise)
                            row_noises.append(row_noise)
                            # f.write(f'### {bitmode}_again_{again}_dgain_{dgain}_exp_us_{exposure_us:4.0f}_temp_{sensor.temperature}_ ###\n')
                            # f.write("mean [DN]: {:.03f}\n".format(mean))
                            # f.write("FPN [DN]: {:.03f}\n".format(fpn))
                            # f.write("row FPN [DN]: {:.03f}\n".format(row_fpn))
                            # f.write("col FPN [DN]: {:.03f}\n".format(col_fpn))
                            # f.write("Noise [DN]: {:.03f}\n".format(t_noise))
                            # f.write("Row noise [DN]: {:.03f}\n".format(row_noise))
                            # f.write("\n".format(row_noise))
                            data = [bitmode, again, dgain, exposure_us, sensor.temperature, mean, fpn, row_fpn, col_fpn, t_noise, row_noise, low_fpn, fname, pictures_per_shot]
                            writer.writerow(data)
                        print(f'means: {means}')
                        print(f'means 12b 10b 10bhs 124')
                        
                        # plt.style.use('seaborn-whitegrid')

                        # plt.scatter(means, fpns)
                        # plt.savefig(f'fpn_{again}')
                        # plt.close()
                        # plt.scatter(means, row_fpns)
                        # plt.savefig(f'row_fpn_{again}')
                        # plt.close()
                        # plt.scatter(means, col_fpns)
                        # plt.savefig(f'col_fpn_{again}')
                        # plt.close()
                        # plt.scatter(means, noises)
                        # plt.savefig(f'noise_{again}')
                        # plt.close()

#######################################################3

def apply_process_roi(imgs, roi_process_w=None, roi_process_h=None):
    '''Crop the given images.

    Parameters
    ----------        
    imgs : np.array
        Three dimensional input images

    roi_process_w : int
        Process width / amount of columns

    roi_process_h : int
        Process height / amount of rows

    Returns
    -------
    np.array : 
        Cropped images
    '''
    if (roi_process_w is not None) and (roi_process_h is not None):
        roi_grab_h = imgs.shape[1]
        roi_grab_w = imgs.shape[2]
        if (roi_grab_w < roi_process_w) or (roi_grab_h < roi_process_h):
            raise Exception(f'Given processing ROI {roi_process_w}x{roi_process_h} exceeds the image dimensions {roi_grab_w}x{roi_grab_h}')
        h = (roi_grab_h - roi_process_h)//2
        w = (roi_grab_w - roi_process_w)//2
        return imgs[:, h:roi_grab_h-h, w:roi_grab_w-w]
    else:
        return imgs
        
def find_sat_exposure_time(sensor, guard_banded=1.1, roi_process_w=None, roi_process_h=None):
    '''Find exposure time when the image is saturated.

    Parameters
    ----------
    sensor : Sensor object
        The attached image sensor PCB on the EVK. E.g. Mira220
    
    guard_banded : float
        Extra increase of found exposure time
        
    roi_process_w : int
        Process width / amount of columns

    roi_process_h : int
        Process height / amount of rows

    Returns
    -------
    float : 
        Saturation exposure time in ms
    '''
    
    # Find saturation DN value
    sensor.exposure_us = sensor.lines_to_time(2) # dummy otherwise black image
    time.sleep(0.5)
    exp_max = 1e6 / sensor.fps - 1e3 # Assumption: FOT+readout < 1ms
    sensor.exposure_us = exp_max
    time.sleep(0.5)
    imgs = sensor.imager.grab_images(2)
    imgs_roi = apply_process_roi(imgs, imgs.shape[2]//10, imgs.shape[1]//10)
    sat_limit = np.mean(imgs_roi)
    plotter.image_with_rect(imgs[0], sensor.exposure_us, sat_limit, np.mean(np.var(imgs_roi, axis=0, ddof=1)), 
                            sensor.bpp, 'Find saturation level', imgs_roi.shape[2], imgs_roi.shape[1])

    # Find two points on the response curve
    sensor.exposure_us = sensor.lines_to_time(2)
    exp1 = sensor.exposure_us
    time.sleep(0.5)
    imgs = sensor.imager.grab_images(2)
    imgs_roi = apply_process_roi(imgs, roi_process_w, roi_process_h)
    temp_mean_1 = np.mean(imgs_roi)
    plotter.image_with_rect(imgs[0], exp1, temp_mean_1, np.mean(np.var(imgs_roi, axis=0, ddof=1)), 
                            sensor.bpp, 'Searching with low exposure time', roi_process_w, roi_process_h)
    sensor.exposure_us = sensor.lines_to_time(10)
    exp2 = sensor.exposure_us
    time.sleep(0.5)
    imgs = sensor.imager.grab_images(2)
    imgs_roi = apply_process_roi(imgs, roi_process_w, roi_process_h)
    temp_mean_2 = np.mean(imgs_roi)

    # Calculated guess for the saturation exposure time  based on linearity
    slope = (temp_mean_2 - temp_mean_1) / (exp2 - exp1)
    offset = temp_mean_1 - slope * exp1
    exp_sat_limit = (sat_limit - offset) / slope

    # Plot image around halfsat to check uniform illumination
    exp = exp_sat_limit / 2
    sensor.exposure_us = exp
    time.sleep(0.5)
    imgs = sensor.imager.grab_images(2)
    imgs_roi = apply_process_roi(imgs, roi_process_w, roi_process_h)
    plotter.image_with_rect(imgs[0], sensor.exposure_us, np.mean(imgs_roi), np.mean(np.var(imgs_roi, axis=0, ddof=1)), 
                            sensor.bpp, 'Searching with half saturation exposure time', roi_process_w, roi_process_h)

    # Check if saturation guess is okay
    temp_mean = 0
    exp_sat_guard_banded = exp_sat_limit
    while (sat_limit - temp_mean) >= 2:
        exp_sat_guard_banded *= guard_banded
        sensor.exposure_us = exp_sat_guard_banded
        time.sleep(0.5)
        imgs = sensor.imager.grab_images(2)
        imgs_roi = apply_process_roi(imgs, roi_process_w, roi_process_h)
        temp_mean = np.mean(imgs_roi)
        plotter.image_with_rect(imgs[0], sensor.exposure_us, temp_mean, np.mean(np.var(imgs_roi, axis=0, ddof=1)), 
                                sensor.bpp, 'Searching with saturation exposure time', roi_process_w, roi_process_h)

    return exp_sat_guard_banded
    
    
def config_illum_trigger_from_exp(sensor, exposure_time):
    '''Set the illumination trigger high during exposure time with some margin (early start).

    Parameters
    ----------
    sensor : Sensor object
        The attached image sensor PCB on the EVK. E.g. Mira220

    exposure_time : float
        Exposure time in us
    '''
    limit = 1e6 / sensor.fps
    margin_us = 4e3
    if exposure_time + margin_us > limit:
        length = (limit - exposure_time) / 2 + exposure_time
    else:
        length = exposure_time + margin_us
    delay = -1 * (length - exposure_time) / 2
    sensor.illumination_trigger = [True, sensor.time_to_lines(delay), sensor.time_to_lines(length), 
                                   None, None, None, None]


def generate_exp_points(method, nb_steps, params={'nb_intervals':2, 'percentages':[50, 50], 'points':[0, 10, 100]}):
    '''Choose exposure points on a 0 - 100 range.

    Parameters
    ----------
    method : str
        Method of distributing the points (evenly_lin, evenly_log, multiple_lin)
    
    nb_steps : int
        Extra increase of found exposure time
        
    params : dict
        nb_intervals: the number of intervals
        percentages: the number of points per interval in percentage
        points: the start and stop points used for the intervals

    Returns
    -------
    np.array : 
        Points over the interval
    '''
    if method == 'evenly_lin':
        exp_cfg = np.linspace(0, 100, nb_steps)
    
    elif method == 'evenly_log':
        exp_cfg = np.logspace(np.log10(1), np.log10(100), nb_steps)
    
    elif method == 'multiple_lin':
        exp_cfg = np.concatenate([np.linspace(params['points'][i],
                                              params['points'][i+1],
                                              int(nb_steps/100*params['percentages'][i]), 
                                              endpoint=([False]*(params['nb_intervals']-1)+[True])[i]) 
                                  for i in range(params['nb_intervals'])])
    return exp_cfg
    

def live_raw(sensor_name, port, bit_mode, fps, w, h, nb_lanes, analog_gain):
    sensor = select_sensor(sensor_name, port)
    sensor.cold_start()
    sensor.init_sensor(bit_mode=bit_mode, fps=fps, w=w, h=h, nb_lanes=nb_lanes, analog_gain=analog_gain)
    sensor.exposure_us = 1e4
    
    while True:
        try:
            im = cv2.resize(sensor.imager.grab_images(1)[0] << (16-sensor.bpp), (w//2, h//2))
            cv2.imshow("Live, press q to quit", im)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                print("Release video resource")
                break
            
        except KeyboardInterrupt:
            cv2.destroyAllWindows()
            print("Release video resource")
            break


def test_sensor_type(sensor_name='Mira050', port=0):
    sensor = Mira050(imagertools=ImagerTools(
        printfun=None, port=0, rootPW='jetcis'))
    sensor.imager.getUcDump()
    sensor.reset_sensor()

    print(f'UcId: {sensor.imager.getUcId()}')
    print(f'UcFirmware: {sensor.imager.getUcFirmware()}')
    print(f'SensorID: {sensor.imager.getSensorID()}')
    print(f'SensorType: {sensor.imager.getSensorType()}')
    print(f'BoardRevision: {sensor.imager.getBoardRevision()}')
    print(f'BoardSerialNo: {sensor.imager.getBoardSerialNo()}')
    sensor.cold_start()
    sensor.init_sensor()
    imgs = sensor.imager.grab_images(1)    

def show_raw_image(sensor_name, port, bit_mode, fps, w, h, nb_lanes, analog_gain):
    sensor = select_sensor(sensor_name, port)
    sensor.cold_start()
    sensor.init_sensor(bit_mode=bit_mode, fps=fps, w=w, h=h, nb_lanes=nb_lanes, analog_gain=analog_gain)
    
    imgs = sensor.imager.grab_images(1)    
    plt.imshow(imgs[0], cmap=plt.get_cmap('gray'), vmin = 0, vmax = (1 << sensor.bpp) - 1)          
    plt.show()


def calc_noise(sensor_name, port, bit_mode, fps, w, h, nb_lanes, analog_gain):
    sensor = select_sensor(sensor_name, port)
    sensor.cold_start()
    sensor.init_sensor(bit_mode=bit_mode, fps=fps, w=w, h=h, nb_lanes=nb_lanes, analog_gain=analog_gain)
    
    imgs = sensor.imager.grab_images(50)
    print(imgs.shape)
    # statistics(imgs)
    df = char.get_stats(imgs)
    print(df)


def statistics(imgs):
    mean = np.mean(np.mean(imgs))
    fpn_frame = np.mean(imgs, axis=0)  # 3d array [number,height,width]
    fpn = np.std(fpn_frame, ddof=1)
    row_fpn = np.std(np.mean(fpn_frame, axis=1), ddof=1)
    col_fpn = np.std(np.mean(fpn_frame, axis=0), ddof=1)
    t_noise = np.mean(np.std(imgs, axis=0))
    row_noise = np.mean(np.std(np.mean(imgs - fpn_frame, axis=2), axis=1))

    print("mean [DN]: {:.03f}".format(np.mean(np.mean(imgs))))
    print("FPN [DN]: {:.03f}".format(fpn))
    print("row FPN [DN]: {:.03f}".format(row_fpn))
    print("col FPN [DN]: {:.03f}".format(col_fpn))
    print("Noise [DN]: {:.03f}".format(t_noise))
    print("Row noise [DN]: {:.03f}".format(row_noise))

    return mean, fpn, row_fpn, col_fpn, t_noise, row_noise


def show_pcb_temperature(sensor_name, port, bit_mode, fps, w, h, nb_lanes, analog_gain):
    sensor = select_sensor(sensor_name, port)
    sensor.cold_start()
    sensor.init_sensor(bit_mode=bit_mode, fps=fps, w=w, h=h, nb_lanes=nb_lanes, analog_gain=analog_gain)

    temperature = sensor.pcb_temperature
    print(f'The PCB temperature is {round(temperature, 3)} degrees.')


def select_sensor(sensor_name, port):
    '''Create the sensor object based on sensor name
    '''
    if sensor_name.lower() == 'mira030':
        sensor = Mira030(imagertools=ImagerTools(printfun=None, port=port))
    elif sensor_name.lower() == 'mira050':
        sensor = Mira050(imagertools=ImagerTools(printfun=None, port=port))
    elif sensor_name.lower() == 'mira130':
        sensor = Mira130(imagertools=ImagerTools(printfun=None, port=port))
    elif sensor_name.lower() == 'mira220':
        sensor = Mira220(imagertools=ImagerTools(printfun=None, port=port))
    else:
        print(f'{sensor_name} sensor not valid.')
        sys.exit()
    return sensor


def get_port():
    '''Returns a list with the active ports
    '''
    imager0 = ImagerTools(printfun=len, port=0)
    imager0.setSensorI2C(0x2d)
    imager0.type(0)
    
    if imager0.read(5) == -1:
        active_ports = []
    else:
        active_ports = [0]

    imager1 = ImagerTools(printfun=len, port=1)
    imager1.setSensorI2C(0x2d)
    imager1.type(0)
    if imager1.read(5) == -1:
        pass
    else:
        active_ports += [1]
    return active_ports


def run():
    # for port in get_port():
    # #    live_raw('Mira220', port, '12bit', 30, 1600, 1400, 2, 1)
    #     # test_sensor_type('Mira220', port)
    #     # show_raw_image('Mira220', port, '12bit', 30, 1600, 1400, 2, 1)
    #     calc_noise('Mira220', port, '12bit', 30, 1600, 1400, 2, 1)
    #     # show_pcb_temperature('Mira220', port, '12bit', 30, 1600, 1400, 2, 1)

    # test_miraxs_api()
    # test_mira130()
    # test stability switching between v4l2 and gstreamer pipeline
    # test_mira220()
    # test_sensor_type()
    test_mira050()
    # test_mira130()
    # test_mira030()
    # test_mira050_lowfpn()
    # get_otp_050()
    #test_sensor_type()
    # check_calibrate_mira050()
    # automated_measurement()
    # process_automated_measurement()
    # print('ok')
    # live_view()

if __name__ == "__main__":
    run()