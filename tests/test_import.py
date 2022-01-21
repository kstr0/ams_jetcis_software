# coding=utf-8
import pytest
import time
import ams_jetcis
from ams_jetcis.sensors.sensor import Sensor
from ams_jetcis.sensors.mira220.mira220 import Mira220
from ams_jetcis.sensors.mira130.mira130 import Mira130
from ams_jetcis.sensors.mira050.mira050 import Mira050
from ams_jetcis.sensors.mira030.mira030 import Mira030
from ams_jetcis.common.driver_access import ImagerTools

def test_imports():
    try:
        import ams_jetcis    
        import ams_jetcis.sensors    


    except ModuleNotFoundError as exc:
        pytest.fail(exc, pytrace=True)

def test_dummy():
    assert 1==2

def test_mira050():
    try:

        imager = imagertools=ImagerTools(printfun=None, port=0, rootPW='jetcis')
        sensor = Mira050(imager)
        sensor.cold_start()

        sensor.init_sensor(bit_mode='10bit', analog_gain=8)
        sensor.illum_trig(False)
        sensor.set_exposure_us(time_us = 150)
        # ina3221(imager)
        time.sleep(0.4)
        images = sensor.imager.grab_images(count =20)
        sensor.imager.save_images(imgs=images, dir_fname = '/home/jetcis/10bgain8')
    except Exception as exc:
        pytest.fail(exc, pytrace=True)