__author__ = "Denver Lloyd"
__copyright__ = "Copyright 2021, AMS Characterization"


import sys
from os import path
import os
sys.path.insert(0,r'/home/jetcis/jetcis/software/trunk/sw')
import subprocess
from ams_jetcis.sensors import set_sensor
import configparser as cp
import numpy as np
from PIL import Image
import pdb
import argparse
import pandas as pd


class Server_App_Host:
    def __init__(self,
                 sensor_name='Mira050',
                 config_path=r'/home/jetcis/jetcis/software/trunk/sw/ams_jetcis/configs/Mira050.ini',
                 hpath=r'/home/jetcis/staged_images'):
        """
        Class for reading in a config to set the sensor state and saving
        images and state file with image paths to `hpath`
        Keyword Arguments:
            sensor_name (str): name of sensor under test, used to set the
                               state properly
            config_path (str): path to config for setting the sensor state
            hpath (str): path to directory where images and state file will
                         be saved
        """

        # instance variables
        self.sensor_name = sensor_name
        self.set_sensor = object
        self.sensor_params = {}
        self.open = False
        self.frame_count = int
        self.config_path = config_path
        self.hpath = hpath
        self.raw = pd.DataFrame()

        # init the sensor and create instance of socket manager
        self.init_sensor()

    def init_sensor(self):
        """
        Initilize the sensor based on input init_script and
        start the socket manager
        """

        # read config
        self.read_config()

        # set the sensor state
        self.set_sensor = \
            set_sensor.Set_Sensor(sensor_name=self.sensor_name,
                                  **self.sensor_params)

    def read_config(self):
        """
        Reads the config file
        Note: Only supports a single section at the moment
        """

        # read in the config as a dictionary
        config = cp.RawConfigParser()
        config.read(self.config_path)

        # try and get config
        try:
            key = [k for k in dict(config).keys() if 'default' not in k.lower()][0]
        except(IndexError):
            print(f'Check config path and structure {self.config_path}')
            sys.exit()
        
        # set sensor params
        self.sensor_params = dict(config[key])

        # convert exposure to an iterable for looping the capture
        # based on user input
        self.sensor_params['exposure'] = \
            self.parse_exposure()

        return self

    def parse_exposure(self):
        """
        Parses config exposure input
        Currently supported in config:
            exposure = start:end:steps
            exposure = [1, 2, 5, 7]
            exposure = 10
        """

        # get exposure value input into config
        exp = self.sensor_params['exposure']
        exp_up = object

        # linear sweep case
        if ':' in exp:
            expl = exp.split(':')
            start = float(expl[0])
            end = float(expl[1])
            step = int(expl[2])
            exp_up = np.linspace(start, end, step)

        # list of values case
        elif '[' in exp:
            exp = exp.strip('][').split(', ')
            exp_up = [float(e) for e in exp]

        # scalar case
        else:
            exp_up = [float(exp)]

        return exp_up

    def capture(self):
        """
        Calls the capture function for sensor under test

        Returns:
            imgs (np.array): array of images (nimages, width, height)
        """

        # get number of frames
        count = self.set_sensor.frame_count

        # capture
        imgs = \
            self.set_sensor.sensor.imager.saveTiff(fname='beeldje',
                                                   count=count,
                                                   save=False)

        return imgs

    def save_img(self, img, fno, exp, depth=12):
        """
        Save an image as a .tiff
        TODO: need to add better support for 'depth' keyword

        Keyword Arguments:
            img (np.array): single image to be saved
            fno (int): frame number in the stack
            exp (float): exposure value to be added to image name
            depth (int): bit-depth of image data
        Returns:
            name (str): full path of saved image
        """

        path = self.hpath

        # check that staging directroy exists
        if not os.path.exists(path):
            os.mkdir(path)

        # scale for 16bit container
        im_ = img * 2**(16-depth)

        # update image name
        name = os.path.join(path, f'fno{fno}_' + f'exp_{exp}' + '.tiff')

        # save the image
        Image.fromarray(im_).save(name)

        return name

    def main(self):
        """
        Runs the capture and save sequence
        """

        temp = pd.DataFrame()

        # iterate over all exposure levels
        for exp in sa.sensor_params['exposure']:

            # round exposure
            exp = round(exp, 1)

            # set exposure
            sa.set_sensor.exposure = exp

            # update the state and get current state
            sa.set_sensor.update_state()
            temp_params = sa.set_sensor.current_state.copy()

            # capture
            imgs = sa.capture()

            # save images and add to DataFrame
            for idx, img in enumerate(imgs):

                # save image
                save_path = sa.save_img(img, idx, exp)

                # add state to DataFrame
                temp = \
                    pd.DataFrame(dict([(k, pd.Series(v)) for
                                       k, v in temp_params.items()]))

                # add save path
                temp['image_path'] = save_path

                # concat to main structure
                self.raw = pd.concat([self.raw, temp]).reset_index(drop=True)

        # save main dataframe
        self.raw.to_csv(os.path.join(self.hpath, 'RAW.csv'), index=False)

        return self


if __name__ == "__main__":
    """
    this allows for the class to be called from receiver
    machine and run the capture and save the images and
    state file to the staging folder for later use
    """

    cpath = r'/home/jetcis/jetcis/software/trunk/sw/ams_jetcis/configs/Mira050.ini'
    hpath = r'/home/jetcis/staged_images'

    parser = argparse.ArgumentParser()

    parser.add_argument("-sn", "--sensor_name",
                        type=str, default='Mira220',
                        help="Sensor to run")
    parser.add_argument("-cp", "--config_path",
                        type=str, default=cpath,
                        help="config path on host machine")
    parser.add_argument("-hp", "--host_path",
                        type=str, default=hpath,
                        help="host path to save staged images")

    args = parser.parse_args()

    # get the arguments
    sensor_name = args.sensor_name
    config_path = args.config_path
    host_path = args.host_path

    # create an instance of server_app_host
    sa = Server_App_Host(sensor_name=sensor_name,
                         config_path=config_path,
                         hpath=hpath)

    # run the capture and save sequence
    sa.main()
