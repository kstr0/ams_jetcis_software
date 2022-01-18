"""
module to manage device tree / kernel on jetson nano
- first version on jetson nano uses jetpack 4.4
- newer version uses jetpack 4.6

JetPack 4.6 is the latest production release, and supports all Jetson modules including Jetson AGX Xavier Industrial module.
JetPack 4.6 includes support for Triton Inference Server, new versions of CUDA, cuDNN and TensorRT, VPI 1.1 with support for new computer vision algorithms and python bindings, 
L4T 32.6.1 with Over-The-Air update features, security features, and a new flashing tool to flash internal or external media connected to Jetson.

usage: kernel.py [-h] [-i INFO] [-s SENSOR]

optional arguments:
  -h, --help            show this help message and exit
  -i INFO, --info INFO  get info
  -s SENSOR, --sensor SENSOR
                        the sensor. options are mira050, mira220, mira030,
                        mira130
"""

import os
import argparse
import sys
import platform
import pathlib

import ams_jetcis.sensors
import ams_jetcis.sensors.mira220 
import ams_jetcis.sensors.mira130 
import ams_jetcis.sensors.mira050
import ams_jetcis.sensors.mira030

class Kernel_DTB_manager():
    """
    class to manage device tree/ kernel stuff on jetson nano
    """
    
    def __init__(self, printfun=None) -> None:
        self.pr = printfun or self.printfun
        self.platform_version = platform.platform()   
        if ( self.platform_version==r'Linux-4.9.140-tegra-aarch64-with-Ubuntu-18.04-bionic'):
            self.jetpack='4.4'
        elif (self.platform_version==r'Linux-4.9.253-tegra-aarch64-with-Ubuntu-18.04-bionic'):
            self.jetpack = '4.6'
        else:
            self.jetpack = None
            raise SystemError('Unsupported kernel')
        self.systype = "Nano"
        self.rootPW= 'jetcis'
        self.current_sensor = None
        try:    
            with  open("/boot/sensor.conf", "r") as fin:
                self.current_sensor = fin.readline().replace('\n','').split("_")[0]

        except FileNotFoundError:
            self.current_sensor = None
        self.get_info()

    def get_info(self):
        """print kernel and sensor"""
        self.pr(f'Current sensor loaded: {self.current_sensor}')
        self.pr(f'Current jetpack loaded: {self.jetpack}')
        self.pr(f'Current kernel loaded: {self.platform_version}')

    def check_current_sensor(self,sensor_name):
        """return 0 when ok"""
        sensor_name = sensor_name.lower()
        sensor_name = sensor_name.split("_")[0]
        if str(sensor_name) == str(self.current_sensor):
            self.pr('Correct sensor driver loaded')
            return 0
        else:
            self.pr('Warning: Incorrect sensor driver loaded')
            self.pr(f'Expected {repr(sensor_name)} but currently {repr(self.current_sensor)} is loaded')

            return 1

    def load_kernel_and_dtb(self,sensor_name=None):
        """
        kernel dtb
        """
        sensor_name = sensor_name.lower()
        dir = pathlib.Path(ams_jetcis.__file__).parent/'sensors'
        if self.jetpack == '4.4':
            kernel = dir/sensor_name/'kernelnano.img'
            dtb = dir/sensor_name/'dtbnano.dtb'
        elif self.jetpack == '4.6':    
            kernel = dir/sensor_name/'kernelnano_L4T_32_6_1.img'
            dtb = dir/sensor_name/'dtbnano_L4T_32_6_1.dtb'
        else:
            return 1
        isp = dir/sensor_name/'camera_overrides.isp'

        # Adjust the kernel configuration
        if(self.systype == "Nano"):
            print(f'changing kernel to {sensor_name} with jetpack {self.jetpack}')
            # program the new dtb
            os.system("echo {} | sudo -S cp {} /boot/dtbnano.dtb".format(self.rootPW, dtb))
            # and also program the new kernel
            os.system("echo {} | sudo -S cp {} /boot/Image".format(self.rootPW, kernel))
            # and also program the new isp_overrides
            os.system("echo {} | sudo -S cp {} /var/nvidia/nvcam/settings/camera_overrides.isp".format(self.rootPW, isp))
            # Update the sensor configuration
            os.system("echo \"{}\" > /tmp/sensor.conf".format(sensor_name))
            os.system("echo \"{}\" > /tmp/jetpack.conf".format(self.jetpack))

            os.system("echo {} | sudo -S cp /tmp/sensor.conf /boot/sensor.conf".format(self.rootPW))
            os.system("echo {} | sudo -S cp /tmp/jetpack.conf /boot/jetpack.conf".format(self.rootPW))

            return 0
        else:
            raise SystemError("ERROR","board is not supported by the actual JetCis Software")
            
        return(1)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i","--info", type=int, default=0, help="get info")
    parser.add_argument("-s","--sensor", type=str, default=None, help="the sensor. options are mira050, mira220, mira030, mira130")

    args = parser.parse_args()

    info = args.info
    sensor = args.sensor
    
    manager = Kernel_DTB_manager()
    if info:
        manager.get_info()
    if sensor:
        manager.load_kernel_and_dtb(sensor)
    else:
        print('no arguments provided')