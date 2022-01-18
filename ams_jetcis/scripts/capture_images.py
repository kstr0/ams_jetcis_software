import time
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import sys
import csv
from PIL import Image
import os
import pandas as pd
import cv2
import pathlib
from numpy.lib.npyio import save

from ams_jetcis.sensors.sensor import Sensor
from ams_jetcis.sensors.mira220.mira220 import Mira220
from ams_jetcis.sensors.mira130.mira130 import Mira130
from ams_jetcis.sensors.mira050.mira050 import Mira050
from ams_jetcis.sensors.mira030.mira030 import Mira030
from ams_jetcis.common.driver_access import ImagerTools
# import ams_jetcis.characterization.standard_tests.ptc as char
import characterization.stats_engine.stats as stats
import characterization.standard_tests.ptc as ptc

class Automated_measurement():
    """
    class for doing an automated measurement
    """

    def __init__(self) -> None:
        self.comment = None
        self.test_case = 'dark'
        self.device = 0  # camera port, 0 or 1
        self.sensor = 'mira050'
        self.bitmodes = ['12bit']  # ,'10bit', '10bithighspeed']
        self.exposures_us = [100, 1000]  # np.arange(100, 1000, 200)
        self.agains = [1]  # ,2,4]
        self.dgains = [1]  # ,4]
        self.pictures_per_shot = 10
        self.timestring = str(int(time.time()))

        self.im_dir = pathlib.Path('~/ams/results/'+self.sensor + self.timestring)

    def capture(self):
        """
        capture series of images.
        """
        # USER INPUTS #

        # DONT TOUCH #

        sensor = Mira050(imagertools=ImagerTools(
            printfun=None, port=0, rootPW='jetcis'))
        sensor.cold_start()
        sensor.init_sensor(bit_mode='12bit', analog_gain=1)
        # sensor.temperature = int(sensor.get_temperature())
        # if not os.path.exists(im_dir):
        #     os.makedirs(im_dir)
        # if not pathlib.Path(im_dir).exists:
        pathlib.Path(self.im_dir).mkdir(parents=True, exist_ok=True)
        print(self.im_dir)

        # Execute measurements
        if not os.path.exists(self.im_dir/'results.csv'):
            exists = False
        else:
            exists = True
        # with open(dir_results/'results.txt', "a") as f:
        with open(self.im_dir/'results.csv', "a+") as f:
            writer = csv.writer(f)
            header = ['bitmode', 'again', 'dgain', 'exp_us', 'filename', 'count', 'testcase', 'amount']

            if not exists:
                writer.writerow(header)

            for bitmode in self.bitmodes:
                for again in self.agains:
                    for dgain in self.dgains:

                        # sensor.cold_start()
                        # sensor.check_sensor()
                        sensor.cold_start()

                        sensor.temp_cor = True

                        sensor.init_sensor(bit_mode=bitmode, analog_gain=again)
                        # set_dgain(imager, dgain,sensor)
                        time.sleep(0.1)

                        for exposure_us in self.exposures_us:
                            sensor.set_exposure_us(time_us=exposure_us)
                            images = []
                            time.sleep(0.4)
                            images = sensor.imager.grab_images(
                                self.pictures_per_shot)
                            fname = f'{bitmode}_again_{again}_dgain_{dgain}_exp_us_{exposure_us:4.0f}_{self.test_case}'
                            sensor.imager.save_images(
                                imgs=images, dir_fname=self.im_dir/fname)

                            data = [bitmode, again, dgain, exposure_us,
                                    fname, self.test_case, self.pictures_per_shot]
                            writer.writerow(data)

    def process(self):


        dir_results = self.im_dir
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



def run():
    m = Automated_measurement()
    m.capture()
    m.process()


if __name__ == '__main__':
    run()
