import sys
from os import path
import os
sys.path.insert(0, r'/home/jetcis/jetcis/software/trunk/sw/ams_jetcis')
from common.driver_access import ImagerTools
from ams_jetcis.sensors.mira050.mira050 import Mira050
from ams_jetcis.sensors.mira130.mira130 import Mira130
from ams_jetcis.sensors.mira220.mira220 import Mira220
import pdb


class Set_Sensor:
    def __init__(self,
                 sensor_name='mira050',
                 **kwargs):
        """
        Class for setting the state of the sensor
        Keyword Arguments:
            sensor_name (str): name of sensor being tested
            kwargs (dict): dictionary of state values to be set
                Currently supported:
                - analog_gain
                - digital_gain
                - frame_count
                - bit_mode
                - exposure

        """

        # instance variables
        self.sensor_name = sensor_name
        self.sensor = object
        self.kwargs = kwargs
        self.valid_sensors = ['mira050', 'mira130', 'mira220']
        self.current_state = {}
        self.exp = float
        self.again = int
        self.dgain = int
        self.frate = int
        self.fcount = int
        self.bmode = int

        # initilize the sensor
        self.select_sensor()

        # initilize the sensor
        self.init_sensor()

        # set the state based on dictionary
        #self.set_state()

    def select_sensor(self):
        """
        initilize the sensor based on sensor name
        """

        if self.sensor_name.lower() == 'mira050':
            self.sensor = \
                Mira050(imagertools=ImagerTools(printfun=None,
                                                port=0))
        elif self.sensor_name.lower() == 'mira130':
            self.sensor = \
                Mira130(imagertools=ImagerTools(printfun=None,
                                                port=0))
        elif self.sensor_name.lower() == 'mira220':
            self.sensor = \
                Mira220(imagertools=ImagerTools(printfun=None,
                                                port=0))
        else:
            print('Sensor not in valid sensor list: {self.valid_sensors}')
            sys.exit()

        return self

    def init_sensor(self):
        """
        Initilize the sensor
        """
        # init the sensor
        self.sensor.cold_start()
        self.sensor.init_sensor(bit_mode=self.bit_mode,
                                analog_gain=self.analog_gain)

    def set_state(self):
        """
        set the initial state of the sensor
        """

        for kk in self.kwargs.keys():

            # analog gain case
            if kk.lower() == 'analog_gain':
                self.analog_gain = self.kwargs[kk]

            # digital gain case
            if kk.lower() == 'digital_gain':
                self.digital_gain = self.kwargs[kk]

            # exposure case
            if kk.lower() == 'exposure':
                if len(self.kwargs[kk]) > 1:
                    self.exposure = 1
                else:
                    self.exposure = self.kwargs[kk]

            # frame count case
            if kk.lower() == 'frame_count':
                self.frame_count = self.kwargs[kk]

            # bit_mode (bit_depth) case
            if kk.lower() == 'bit_mode':
                self.bit_mode = self.kwargs[kk]

        # update current state
        self.current_state = self.kwargs

        return self

    def update_state(self):
        """
        update the state of the sensor
        """

        self.current_state['exposure'] = self.exposure
        self.current_state['analog_gain'] = self.analog_gain
        self.current_state['digital_gain'] = self.digital_gain
        self.current_state['frame_count'] = self.frame_count
        self.current_state['bit_mode'] = self.bit_mode

        return self

    @property
    def exposure(self):
        """
        exposure getter
        """

        return self.exp

    @exposure.setter
    def exposure(self, exp):
        """
        exposure setter
        """

        if not isinstance(exp, float):
            exp = float(exp)

        self.sensor.set_exposure(exp)
        self.exp = exp

        return self

    @property
    def frame_count(self):
        """
        frame count getter
        """

        return self.fcount

    @frame_count.setter
    def frame_count(self, count):
        """
        frame count setter
        """

        if not isinstance(count, int):
            count = int(count)

        self.fcount = count

        return self

    @property
    def analog_gain(self):
        """
        analog gain getter
        """

        return self.again

    @analog_gain.setter
    def analog_gain(self, gain):
        """
        analog gain setter
        """

        if not isinstance(gain, int):
            gain = int(gain)

        self.sensor.set_analog_gain(gain)
        self.again = gain

        return self

    @property
    def digital_gain(self):
        """
        digital gain getter
        """

        return self.dgain

    @digital_gain.setter
    def digital_gain(self, gain):
        """
        digital gain setter
        """

        if not isinstance(gain, int):
            gain = int(gain)

        self.sensor.set_digital_gain(gain)
        self.dgain = gain

        return self

    @property
    def bit_mode(self):
        """
        bit mode getter
        """

        return self.bmode

    @bit_mode.setter
    def bit_mode(self, depth):
        """
        bit mode setter
        """

        if not isinstance(depth, int):
            depth = str(depth)

        # check 'bit' is in depth
        if 'bit' not in depth:
            depth = depth + 'bit'

        self.bmode = depth

        return self
