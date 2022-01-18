import time
import numpy as np
from collections import OrderedDict
from ams_jetcis.sensors.sensor import Sensor

class Mira030(Sensor):
    """
    Implementation of Sensor class for Mira030.
    """

    def __init__(self, imagertools) -> None:
        self.name = 'Mira030'
        self._bpp = None
        self._roi = [None, None]
        self.width = None # remove
        self.height = None
        self.widthDMA = None
        self.heightDMA = None
        self._fps = None
        self.dtMode = None
        self.cfg_to_dtMode = {12: {2: {640: 0, 480: 1}}, 10: {2: {640: 2, 480: 3}}, 8: {2: {640: 4, 480: 5}, 1: {640: 6}}}
        self.ana_table = [1, 1.0625, 1.125, 1.1875, 1.25, 1.3125, 1.375, 1.4375, 1.5, 1.5625, 1.625,
                          1.6875, 1.75, 1.8125, 1.875, 1.9375, 2, 2.125, 2.25, 2.375, 2.5, 2.625, 
                          2.75, 2.875, 3, 3.125, 3.25, 3.375, 3.5, 3.625, 3.75, 3.875, 4, 4.25, 4.5, 
                          4.75, 5, 5.25, 5.5, 5.75, 6, 6.25, 6.5, 6.75, 7, 7.25, 7.5, 7.75, 8, 8.5, 
                          9, 9.5, 10, 10.5, 11, 11.5, 12, 12.5, 13, 13.5, 14, 14.5, 15, 15.5]
        self.dig_table = [1, 1.0625, 1.125, 1.1875, 1.25, 1.3125, 1.375, 1.4375, 1.5, 1.5625, 1.625, 
                          1.6875, 1.75, 1.8125, 1.875, 1.9375, 2, 2.125, 2.25, 2.375, 2.5, 2.625, 
                          2.75, 2.875, 3, 3.125, 3.25, 3.375, 3.5, 3.625, 3.75, 3.875, 4, 4.25, 4.5,
                          4.75, 5, 5.25, 5.5, 5.75, 6, 6.25, 6.5, 6.75, 7, 7.25, 7.5, 7.75]
        self._blc = [None, None, None]
        self._led_driver = [None, None, None]
        super().__init__(imagertools)

    def set_i2c_address(self, ic):
        '''Set the I2C address and the I2C bit depth of register and value.

        Parameters
        ----------
        ic : str
            Integrated circuit on the PCB
        '''
        if ic == 'sensor':
            self.imager.setSensorI2C(0x30)
            self.imager.type(1)
        elif ic == 'pmic':
            self.imager.setSensorI2C(0x2d)
            self.imager.type(0)
        elif ic == 'illumination':
            self.imager.setSensorI2C(0x53)
            self.imager.type(0)
        elif ic == 'temperature':
            self.imager.setSensorI2C(0x4c)
            self.imager.type(0)
        elif ic == 'uC':
            self.imager.setSensorI2C(0x0a)
            self.imager.type(0)
        elif ic == 'power':
            self.imager.setSensorI2C(0x45)
            self.imager.type(2)

    def power_off(self):
        '''Disable the load switch of the PMIC.
        '''
        self.set_i2c_address('pmic')
        self.write_register(0x62, 0x00)
        self.write_register(0x61, 0x00)

    def reset_sensor(self):
        '''Power up sequence with the PMIC and enable some LEDs.
        '''
        # Disable the PMIC
        self.power_off()

        # Set LDOs on 0V
        self.write_register(0x05, 0x00) # DCDC1=0V
        self.write_register(0x0E, 0x00) # DCDC4=0V
        self.write_register(0x11, 0x00) # LDO1=0V
        self.write_register(0x14, 0x00) # LDO2=0V
        self.write_register(0x17, 0x00) # LDO3=0V
        self.write_register(0x1A, 0x00) # LDO4=0V 
        self.write_register(0x1C, 0x00) # LDO5=0V
        self.write_register(0x1D, 0x00) # LDO6=0V
        self.write_register(0x1E, 0x00) # LDO7=0V 
        self.write_register(0x1F, 0x00) # LDO8=0V
        self.write_register(0x24, 0x48) # Disable LDO9 Lock
        self.write_register(0x20, 0x00) # LDO9=0V AVDD 
        self.write_register(0x21, 0x00) # LDO10=0V DVDD
        self.write_register(0x01, 0x00) # DCDC2=0V
        self.write_register(0x08, 0x00) # DCDC2=0V
        self.write_register(0x02, 0x00) # DCDC3=0V
        self.write_register(0x0B, 0x00) # DCDC3=0V

        # Enable master switch
        time.sleep(50e-6)
        self.write_register(0x62, 0x0D)
        time.sleep(50e-6)

        # Keep LDOs always on
        time.sleep(50e-3)
        try:
            self.read_register(0x20)
        except:
            pass
        self.write_register(0x27, 0xFF)
        self.write_register(0x28, 0xFF)
        self.write_register(0x29, 0x00)
        self.write_register(0x2A, 0x00)
        self.write_register(0x2B, 0x00)

        # set GPIO1=0
        self.write_register(0x41, 0x04)
                
        # Enable LDO9=2.80V for AVDD
        time.sleep(50e-6)
        self.read_register(0x20)
        self.write_register(0x20, 0xB8)
        self.read_register(0x20)

        ## Enable LDO10=1.5V for VDDLO_ANA
        time.sleep(700e-6)
        self.write_register(0x21, 0x9C)

        ## Enable 1.80V Enable DCDC1/4=1.8V for VINLDO1P8/DOVDD/VDDIO
        time.sleep(50e-6)
        self.write_register(0x00, 0x00)
        self.write_register(0x04, 0x34)
        self.write_register(0x06, 0xBF)
        self.write_register(0x05, 0xB4)
        self.write_register(0x03, 0x00)
        self.write_register(0x0D, 0x34)
        self.write_register(0x0F, 0xBF)
        self.write_register(0x0E, 0xB4)

        # Enable CLK_IN with GPIO2 for mclk XTALL
        time.sleep(50e-6)
        self.write_register(0x42, 5)

        # Enable green LED for confirmation
        time.sleep(50e-6)
        self.write_register(0x45, 0x40)
        self.write_register(0x57, 0x02)
        self.write_register(0x5D, 0x10)
        self.write_register(0x61, 0x10)

        # I2C address LED and length (addr=8bit, val=8bit)
        self.set_i2c_address('illumination')
        # Turn off LED driver
        self.write_register(0x10, 0x08)

        # init sensor
        self.set_i2c_address('sensor')
        # set input clock speed to 24MHz
        self.imager.setmclk(24000000)
        self.imager.setDelay(0)
        # and reset sensor
        self.imager.reset(2) # Keep in reset
        self.imager.wait(100)
        self.imager.reset(3) # Leave reset
        self.imager.wait(2000)

    def check_sensor(self):
        '''Check if sensor is present.

        Returns
        -------
        int : 
            0 if detected
        '''
        self.set_i2c_address('sensor')
        if self.read_double_register(0x3107) == 0x0031:
            self.imager.pr('Mira030 detected')
            self.set_i2c_address('uC')
            # led seq -- use this to turn on leds. abc0000- 1110000 for all leds
            self.write_register(0x61, 0b110000)
            return 0
        else:
            self.imager.pr('Mira030 not detected')
            self.set_i2c_address('uC')
            # led seq -- use this to turn on leds. abc0000- 1110000 for all leds
            self.write_register(0x61, 0b1010000)
            return 1

    def init_sensor(self, bit_mode='12bit', fps=30, w=640, h=480, nb_lanes=2, analog_gain=1):
        '''Execute a configuration sequence.

        Parameters
        ----------
        bit_mode : str
            Bit depth for a pixel (8bit, 10bit or 12bit)
        
        fps : int
            The frame rate

        w : int
            The width (640 or 480)
            
        h : int
            The height (480 or 360)
        
        nb_lanes : int
            The amount of data lanes

        analog_gain : int
            The analog gain (1 until 15.5)
        '''
        if (nb_lanes == 1):
            if (bit_mode == '8bit') and (w == 640) and (h == 480):
                self.cfg_640x480_8bit_1lane_50fps()
                self.nb_lanes = nb_lanes
                self._bpp = 8
                self.imager.setformat(8, 640, 480, 640, 480, True)
                self.roi = [w, h]
                self.dtMode = self.cfg_to_dtMode[8][1][640]
            else:
                raise NotImplementedError(f'The requested configuration for 1 lane is not implemented')
        else:
            if (bit_mode == '12bit') or (bit_mode == '10bit') or (bit_mode == '8bit'):
                getattr(self, f'cfg_640x480_{bit_mode}_2lane')(60 if fps >= 60 else 30)
                self.nb_lanes = nb_lanes
                self._bpp = int(bit_mode.split('b')[0])
                self.imager.setformat(self._bpp, 640, 480, 640, 480, True)
                self.roi = [w, h]
            else:
                raise NotImplementedError(f'The bit mode of {bit_mode} is not implemented')
        
        self.fps = fps
        self.set_analog_gain(analog_gain)
        self._blc = ['Auto', '1 channel', 160]

    @property
    def bpp(self):
        '''Get the programmed bit depth per pixel.

        Returns
        -------
        int : 
            Bit depth for a pixel (8, 10 or 12)
        '''
        self.set_i2c_address('sensor')
        mipi_dtype = self.read_register(0x3031) % (2**4)
        if (mipi_dtype == 0x08) or (mipi_dtype == 0x0a) or (mipi_dtype == 0x0c):
            self._bpp = mipi_dtype
            return self._bpp
        else:
            raise ValueError('Unknown MIPI data type.')

    @bpp.setter
    def bpp(self, bit_mode):
        '''Set the bit depth.

        Parameters
        ----------
        bit_mode : str
            Bit depth for a pixel (8bit, 10bit or 12bit)
        '''
        self.set_i2c_address('sensor')
        if ((bit_mode == '12bit') or (bit_mode == '10bit') or (bit_mode == '8bit')) and (self.nb_lanes == 2):
            # Get state
            roi = self.roi
            fps = self.fps

            # Apply config
            getattr(self, f'cfg_640x480_{bit_mode}_2lane')(60 if fps >= 60 else 30)

            # Recover state
            self._bpp = int(bit_mode.split('b')[0])
            self.roi = roi
            self.fps = fps
            self.imager.setformat(self._bpp, roi[0], roi[1], roi[0], roi[1], True)

        elif (bit_mode == '8bit') and (self.nb_lanes == 1):
            self._bpp = 8
        else:
            raise NotImplementedError(f'The bit mode of {bit_mode} for {self.nb_lanes} mipi lanes is not implemented')

    @property
    def roi(self):
        '''Get the region of interest.

        Returns
        -------
        list : 
            [0] : width
            [1] : height
        '''
        self.set_i2c_address('sensor')
        w = self.read_double_register(0x3208)
        h = self.read_double_register(0x320a)
        self._roi = [w, h]
        return self._roi
    
    @roi.setter
    def roi(self, roi):
        '''Set the region of interest.
        
        Parameters
        ----------
        roi : list
            [0] : width (640 or 480)
            [1] : height (480 or 360)
        '''
        w, h = roi
        self.set_i2c_address('sensor')
        if (w == 480) and (h == 360) and (self.nb_lanes == 2):
            self.write_double_register(0x3208, 480)
            self.write_double_register(0x320a, 360)
            self.write_double_register(0x3210, 88)
            self.write_double_register(0x3212, 68)
            self.width = w
            self.height = h
            self.widthDMA = w
            self.heightDMA = h
            self.imager.setformat(self.imager.bpp, self.width, self.height, self.widthDMA, self.heightDMA, self.imager.v4l2)
            self.dtMode = self.cfg_to_dtMode[self.imager.bpp][2][w]
            self._roi = roi
        elif (w == 640) and (h == 480):
            self.write_double_register(0x3208, 640)
            self.write_double_register(0x320a, 480)
            self.write_double_register(0x3210, 8)
            self.write_double_register(0x3212, 8)
            self.width = w
            self.height = h
            self.widthDMA = w
            self.heightDMA = h
            self.imager.setformat(self.imager.bpp, self.width, self.height, self.widthDMA, self.heightDMA, self.imager.v4l2)
            self.dtMode = self.cfg_to_dtMode[self.imager.bpp][2][w]
            self._roi = roi
        else:
            raise NotImplementedError(f'Requested ROI of {w}x{h} for {self.nb_lanes} mipi lanes is not implemented.')
    
    @property
    def fps(self):
        '''Get the frame rate.

        Returns
        -------
        float : 
            Frame rate of the sensor
        '''
        self.set_i2c_address('sensor')
        frame_length_atm = self.read_double_register(0x320e)
        line_length_atm = self.read_double_register(0x320c)
        self._fps = 1 / (frame_length_atm * self.Tpclk * line_length_atm)
        return self._fps

    @fps.setter
    def fps(self, fps):
        '''Set the frame rate.

        Parameters
        ----------
        fps : float
            Frame rate of the sensor
        '''
        self.set_i2c_address('sensor')
        line_length_atm = self.read_double_register(0x320c)
        frame_length_new = int(1 / (self.Tpclk * line_length_atm * fps))
        self.write_double_register(0x320e, frame_length_new)
        self._fps = fps

    @property
    def analog_gain(self):
        '''Get the programmed analog gain.

        Returns
        -------
        float : 
            analog gain
        '''
        self.set_i2c_address('sensor')
        coarse_value = self.extract_bits(self.read_register(0x3e08), 3, 2)
        fine_value = self.read_register(0x3e09)

        coarse = int(np.log2(coarse_value + 1))
        fine = fine_value - 0x10

        self._analog_gain = self.ana_table[16 * coarse + fine]
        return self._analog_gain

    @analog_gain.setter
    def analog_gain(self, ana_gain):
        '''Set analog gain and related registers.

        Parameters
        ----------
        ana_gain : float
            Analog gain
        '''
        self.set_i2c_address('sensor')
        ana_gain_mapped = min(self.ana_table, key=lambda x: abs(x - ana_gain))
        mapped_index = self.ana_table.index(ana_gain_mapped)
        
        # Logic patch
        if ana_gain_mapped < 2:
            self.write_register(0x3314, 0x1e)
            self.write_register(0x3317, 0x10)
        else:
            self.write_register(0x3314, 0x4f)
            self.write_register(0x3317, 0x0f)

        coarse_reg = self.read_register(0x3e08)
        coarse = (1 << (mapped_index // 16)) - 1
        self.write_register(0x3e08, self.replace_bits(coarse_reg, coarse, 3, 2))
        fine = mapped_index % 16 + 0x10
        self.write_register(0x3e09, fine)
        self._analog_gain = ana_gain_mapped

    @property
    def digital_gain(self):
        '''Get the programmed digital gain.

        Returns
        -------
        float : 
            digital gain
        '''
        self.set_i2c_address('sensor')
        coarse_value = self.extract_bits(self.read_register(0x3e06), 2, 0)
        fine_value = self.read_register(0x3e07)
        coarse = int(np.log2(coarse_value + 1))
        fine = (fine_value - 0x80) // 8
        self._digital_gain = self.dig_table[16 * coarse + fine]
        return self._digital_gain

    @digital_gain.setter
    def digital_gain(self, dig_gain):
        '''Set digital gain and related registers.

        Parameters
        ----------
        dig_gain : float
            digital gain
        '''
        self.set_i2c_address('sensor')
        dig_gain_mapped = min(self.dig_table, key=lambda x: abs(x - dig_gain))
        mapped_index = self.dig_table.index(dig_gain_mapped)
        coarse_reg = self.read_register(0x3e06)
        coarse = (1 << (mapped_index // 16)) - 1
        self.write_register(0x3e06, self.replace_bits(coarse_reg, coarse, 2, 0))
        fine = 0x80 + (mapped_index % 16 ) * 8
        self.write_register(0x3e07, fine)
        self._digital_gain = dig_gain_mapped

    @property
    def exposure_us(self):
        '''Get the programmed exposure time.

        Returns
        -------
        float : 
            Exposure time in us
        '''
        self.set_i2c_address('sensor')
        line_length = self.read_double_register(0x320c)
        step = (1e6 / 16) * line_length * self.Tpclk
        self._exposure_us = self.read_double_register(0x3e01) * step
        return self._exposure_us

    @exposure_us.setter
    def exposure_us(self, time_us):
        '''Set the exposure time in us in master mode.

        Parameters
        ----------
        fps : float
            Exposure time of the sensor
        '''
        self.set_i2c_address('sensor')
        [exposure_length_max, step] = self.get_exposure_limit()
        exposure_time_max = exposure_length_max * step

        if time_us > exposure_time_max:
            time_us = exposure_time_max
            exposure_length = exposure_length_max
        elif time_us < 0:
            time_us = 0
            exposure_length = 0
        else:
            exposure_length = round(time_us / step)

        self.write_double_register(0x3e01, exposure_length)
        self._exposure_us = time_us

    def get_exposure_limit(self):
        '''Get the exposure time limit.

        Returns
        -------
        list : 
            [0] : maximum exposure register value
            [1] : conversion between length to time in us
        '''
        self.set_i2c_address('sensor')

        line_length = self.read_double_register(0x320c)
        step = (1e6 / 16) * line_length * self.Tpclk

        frame_length = self.read_double_register(0x320e)
        exposure_length_max = ((frame_length - 6) * 16)

        return [exposure_length_max, step]

    def lines_to_time(self, lines):
        '''Convert lines to time.
        
        Parameters
        ----------
        lines : int
            Amount of lines
        
        Returns
        -------
        float :
            Time in us
        '''
        self.set_i2c_address('sensor')
        line_length = self.read_double_register(0x320c)
        line_time = (line_length * self.Tpclk) * 1e6
        return lines * line_time
    
    def time_to_lines(self, time_us):
        '''Convert time to lines.
        
        Parameters
        ----------
        time_us : float
            Time in us
        
        Returns
        -------
        int :
            Amount of lines
        '''
        self.set_i2c_address('sensor')
        line_length = self.read_double_register(0x320c)
        line_time = (line_length * self.Tpclk) * 1e6
        return int(round(time_us / line_time))

    @property
    def hflip(self):
        '''Get the programmed horizontal flip.

        Returns
        -------
        int : 
            0 if no flipping, 1 if horizontal flipped.
        '''
        self.set_i2c_address('sensor')
        read_value = self.extract_bits(self.read_register(0x3221), 2, 1)
        if read_value == 0:
            self._hflip = 0
        elif read_value == 3:
            self._hflip = 1
        return self._hflip

    @hflip.setter
    def hflip(self, hflip):
        '''Configures the horizontal mirroring.

        Parameters
        ----------
        hflip : bool or int
            True/1 : image is horizontal flipped
            False/0 : no horizontal flipping
        '''
        self.set_i2c_address('sensor')
        read_value = self.read_register(0x3221)
        if hflip == 0:
            self._hflip = hflip
            self.write_register(0x3221, self.replace_bits(read_value, 0, 2, 1))
        elif hflip == 1:
            self._hflip = hflip
            self.write_register(0x3221, self.replace_bits(read_value, 3, 2, 1))       

    @property
    def vflip(self):
        '''Get the programmed vertical flip.

        Returns
        -------
        int : 
            0 if no flipping, 1 if vertical flipped.
        '''
        self.set_i2c_address('sensor')
        read_value = self.extract_bits(self.read_register(0x3221), 2, 5)
        if read_value == 0:
            self._vflip = 0
        elif read_value == 3:
            self._vflip = 1
        return self._vflip

    @vflip.setter
    def vflip(self, vflip):
        '''Configures the vertical flip.

        Parameters
        ----------
        vflip : bool or int
            True/1 : image is vertical flipped
            False/0 : no vertical flipping
        '''
        self.set_i2c_address('sensor')
        read_value = self.read_register(0x3221)
        if vflip == 0:
            self._vflip = vflip
            self.write_register(0x3221, self.replace_bits(read_value, 0, 2, 5))
        elif vflip == 1:
            self._vflip = vflip
            self.write_register(0x3221, self.replace_bits(read_value, 3, 2, 5))

    @property
    def test_image(self):
        '''Get the programmed test image status.

        Returns
        -------
        bool : 
            The test image status
        '''
        self.set_i2c_address('sensor')
        self._test_image = self.extract_bits(self.read_register(0x4501), 1, 3)
        return self._test_image

    @test_image.setter
    def test_image(self, enable):
        '''Configures the test image.

        Parameters
        ----------
        enable : bool
            The test image status
        '''
        self.set_i2c_address('sensor')
        if (enable == 0) or (enable == 1):
            self.write_register(0x4501, self.replace_bits(self.read_register(0x4501), enable, 1, 3))
            self._test_image = enable

    @property
    def blc(self):
        '''Get the programmed properties of the black level control.

        Returns
        -------
        list : 
            [0] : mode ('Off', 'Manual' or 'Auto')
            [1] : channels ('1 channel', '4 channels' or '8 channels')
            [2] : target value
        '''
        self.set_i2c_address('sensor')

        value_en = self.extract_bits(self.read_register(0x3900), 1, 0)
        value_auto = self.extract_bits(self.read_register(0x3902), 1, 6)
        if value_en == 0:
            mode = "Off"
        elif (value_en == 1) and (value_auto == 0):
            mode = "Manual"
        elif (value_en == 1) and (value_auto == 1):
            mode = "Auto"
        else:
            mode = self._blc[0]
        
        value_4_8 = self.extract_bits(self.read_register(0x3928), 1, 0)
        value_1 = self.extract_bits(self.read_register(0x3905), 1, 6)
        if value_1 == 1:
            channels = "1 channel"
        elif (value_1 == 0) and (value_4_8 == 1):
            channels = "4 channels"
        elif (value_1 == 0) and (value_4_8 == 0):
            channels = "8 channels"
        else:
            channels = self._blc[1]

        high = self.extract_bits(self.read_register(0x3907), 5, 0)
        low = self.read_register(0x3908)
        target = (high << 8) + low

        self._blc = [mode, channels, target]
        return self._blc

    @blc.setter
    def blc(self, blc):
        '''Configures the black level control. Specific parameter is ignored when None is given.

        Parameters
        ----------
        blc : list
            [0] : mode ('Off', 'Manual' or 'Auto')
            [1] : channels ('1 channel', '4 channels' or '8 channels')
            [2] : target value
        '''
        self.set_i2c_address('sensor')
        [mode, channels, target] = blc
        
        if mode:
            read_en = self.read_register(0x3900)
            read_auto = self.read_register(0x3902)
            if (mode == 'Off'):
                self.write_register(0x3900, self.replace_bits(read_en, 0, 1, 0))
            elif (mode == 'Manuel'):
                self.write_register(0x3900, self.replace_bits(read_en, 1, 1, 0))
                self.write_register(0x3902, self.replace_bits(read_auto, 0, 1, 6))
            elif (mode == 'Auto'):
                self.write_register(0x3900, self.replace_bits(read_en, 1, 1, 0))
                self.write_register(0x3902, self.replace_bits(read_auto, 1, 1, 6))
            else:
                mode = self._blc[0]
            self._blc[0] = mode
        
        if channels:
            read_4_8 = self.read_register(0x3928)
            read_1 = self.read_register(0x3905)
            if channels == "1 channel":
                self.write_register(0x3905, self.replace_bits(read_1, 1, 1, 6))
            elif channels == "4 channels":
                self.write_register(0x3928, self.replace_bits(read_4_8, 1, 1, 0))
                self.write_register(0x3905, self.replace_bits(read_1, 0, 1, 6))
            elif channels == "8 channels":
                self.write_register(0x3928, self.replace_bits(read_4_8, 0, 1, 0))
                self.write_register(0x3905, self.replace_bits(read_1, 0, 1, 6))
            else:
                channels = self._blc[1]
            self._blc[1] = channels

        if target != None:
            read_high = self.read_register(0x3907)
            self.write_register(0x3907, self.replace_bits(read_high, self.extract_bits(target, 5, 8), 5, 0))
            self.write_register(0x3908, self.extract_bits(target, 8, 0))
            self._blc[2] = target

    @property
    def led_driver(self):
        '''Get the programmed settings of the led driver.

        Returns
        -------
        list : 
            [0] : 1 if enabled
            [1] : current level in mA
            [2] : time-out time in ms
        '''
        self.set_i2c_address('illumination')
        enable = 0 if (self.read_register(0x10) % (2**4)) == 0x08 else 1
        current = ([80, 150, 220, 280] + list(range(350, 1020, 60)))[self.read_register(0xb0) % (2**4)]
        timeout = ([60] + list(range(125, 760, 125)) + [1100])[self.read_register(0xc0) % (2**3)]
        self._led_driver = [enable, current, timeout]
        return self._led_driver

    @led_driver.setter
    def led_driver(self, led_driver):
        '''Sets the PMSILPlus flood illuminator settings.
        
        Parameters
        ----------
        led_driver : list
            [0] : enable the flash mode if 1
            [1] : Desired current level in mA (80, 150, 220, 280, 350, 410, 470, 530, 590, 650, 710, 770, 830, 890, 950 or 1010)
            [2] : Time-out time in ms (60, 125, 250, 375, 500, 625, 750 or 1100)
        '''
        self.set_i2c_address('illumination')
        [enable, current, timeout] = led_driver
        if enable == 1:
            self.write_register(0x10, 0x01) # torch enable = blinks with strobe
        else:
            self.write_register(0x10, 0x08) # turn off led driver
        self._led_driver[0] = enable
            
        if current != None:
            try:
                current_ix = ([80, 150, 220, 280] + list(range(350, 1020, 60))).index(current)
                self.write_register(0xb0, current_ix) # flash current
                self._led_driver[1] = current
            except:
                raise ValueError(f'Led driver current of {current}mA is not supported.')
            
        if timeout != None:
            try:
                timeout_ix = ([60] + list(range(125, 760, 125)) + [1100]).index(timeout)
                self.write_register(0xc0, timeout_ix)
                self._led_driver[2] = current
            except:
                raise ValueError(f'Led driver timeout of {timeout}ms is not supported.')

    @property
    def illumination_trigger(self):
        '''Get the programmed test illumination strobe status.

        Returns
        -------
        bool : 
            The illumination strobe status
        '''
        self.set_i2c_address('sensor')
        value = self.extract_bits(self.read_register(0x3361), 2, 6)
        if value == 0:
            self._illumination_trigger = 1
        elif value == 3:
            self._illumination_trigger = 0
        return self._illumination_trigger

    @illumination_trigger.setter
    def illumination_trigger(self, enable):
        '''Configures the illumination strobe.

        Parameters
        ----------
        enable : bool
            The illumination strobe status
        '''
        self.set_i2c_address('sensor')        
        if enable == 1:
            self.write_register(0x3361, self.replace_bits(self.read_register(0x3361), 0, 2, 6))
            self._illumination_trigger = enable
        elif enable == 0:
            self.write_register(0x3361, self.replace_bits(self.read_register(0x3361), 3, 2, 6))
            self._illumination_trigger = enable

    @property
    def get_pcb_temperature(self):
        '''Reads uncalibrated temperature sensor on the backside of the PCB and converts it to degrees Celcius.

        Returns
        -------
        float : 
            Temperature of sensor in degrees Celcius 
        '''         
        self.set_i2c_address('temperature')
        pcb_temp_bits = format(self.read_register(0x01), '08b') + format(self.read_register(0x10), '08b')[0:3]
        self._pcb_temperature = self.two_to_dec(pcb_temp_bits) / 8
        return self._pcb_temperature

    def two_to_dec(self, s):
        '''Converts two's complement binary number to decimal number.

        Parameters
        ----------
        s : str
            Two's complement number

        Returns
        -------
        int : 
            Decoded number
        '''
        if s[0] == "1":
            return -1 * (int("".join("1" if x == "0" else "0" for x in s), 2) + 1)
        else:
            return int(s, 2)

    def set_analog_gain(self, gain): #Should be removed, still in abstract class
        self.analog_gain = gain

    def set_digital_gain(self, gain): #Should be removed, still in abstract class
        self.digital_gain = gain

    def set_exposure_us(self, time_us): #Should be removed, still in abstract class
        self.exposure_us = time_us

    def extract_bits(self, number, k, p): 
        '''Extract k bits from p position and return an integer.
        E.g. [2:0] -> k=3; p=0

        Parameters
        ----------
        number : int
            Input number

        k : int
            Number of bits to extract
        
        p : int
            Start position

        Returns
        -------
        int : 
            Extracted number
        '''  
        return (((1 << k) - 1) & (number >> p))

    def replace_bits(self, number, replacement, k, p):
        '''Replace k bits from p position with the replacement integer.

        Parameters
        ----------
        number : int
            Input number

        replacement : int
            Integer to replace

        k : int
            Number of bits to replace
        
        p : int
            Start position

        Returns
        -------
        int : 
            Edited number 
        '''
        high = self.extract_bits(number, 8-k-p, k+p)
        low = self.extract_bits(number, p, 0)
        return (high << (k+p)) + (replacement << p) + low

    def write_register(self, address, value):
        '''Write value to the given address.
        
        Parameters
        ----------
        address : int
            Address of register

        value : int
            Value to write
        '''
        self.imager.write(address, value)

    def read_register(self, address):
        '''Read the register value at given address.
        
        Parameters
        ----------
        address : int
            Address of register

        Returns
        -------
        int : 
            Value at given address
        '''
        return self.imager.read(address)

    def write_double_register(self, address, value):
        '''Write higher 8 bits of value to given address and lower 8 bits to address + 1.
        
        Parameters
        ----------
        address : int
            Address of register

        value : int
            Value to write
        '''
        self.write_register(address, value >> 8)
        self.write_register(address + 1, value % 0x100)

    def read_double_register(self, address):
        '''Read the register value at given address and given address + 1.
        
        Parameters
        ----------
        address : int
            Address of register

        Returns
        -------
        int : 
            Value at given address
        '''
        return (self.read_register(address) << 8) + self.read_register(address + 1)

    def read_all_registers(self, ic='sensor', dtype='int'):
        ''' Return all register adresses with their current values

        Returns:
            dict: {regaddress : regvalues}
        '''
        self.set_i2c_address(ic)
        d = OrderedDict()
        if dtype == 'int':
            for i in range(0, 0x5990):
                d[i] = self.read_register(i) 
        elif dtype == 'hex':
            for i in range(0, 0x5990):
                d[hex(i)] = hex(self.read_register(i))
        return d

    def cfg_640x480_12bit_2lane(self, fps):
        ''' I2C sensor uploads for 640x480, 12b and 2lanes.

        Parameters
        ----------        
        fps : int
            The frame rate (30 or 60)
        '''
        self.set_i2c_address('sensor')
        self.write_register(0x0103, 0x01)
        self.write_register(0x0100, 0x00)
        self.write_register(0x36e9, 0x80)
        self.write_register(0x36f9, 0x80)
        self.write_register(0x3001, 0x00)
        self.write_register(0x3000, 0x00)
        self.write_register(0x300f, 0x0f)
        self.write_register(0x3018, 0x33)
        self.write_register(0x3019, 0xfc)
        self.write_register(0x301c, 0x78)
        if fps == 30:
            self.write_register(0x301f, 0x10)
        elif fps == 60:
            self.write_register(0x301f, 0x11)
        self.write_register(0x3031, 0x0c)
        self.write_register(0x3037, 0x40)
        self.write_register(0x303f, 0x01)
        self.write_register(0x320c, 0x04)
        self.write_register(0x320d, 0xb0)
        if fps == 30:
            self.write_double_register(0x320e, 0x07d0)
            self.Tpclk = 1 / (30 * 0x07d0 * 0x04b0)
        elif fps == 60:
            self.write_double_register(0x320e, 0x03e8)
            self.Tpclk = 1 / (60 * 0x03e8 * 0x04b0)
        self.write_register(0x3220, 0x10)
        self.write_register(0x3221, 0x60)
        self.write_register(0x3250, 0xc0)
        self.write_register(0x3251, 0x02)
        self.write_register(0x3252, 0x02)
        self.write_register(0x3253, 0xa6)
        self.write_register(0x3254, 0x02)
        self.write_register(0x3255, 0x07)
        self.write_register(0x3304, 0x48)
        self.write_register(0x3306, 0x38)
        self.write_register(0x3309, 0x68)
        self.write_register(0x330b, 0xe0)
        self.write_register(0x330c, 0x18)
        self.write_register(0x330f, 0x20)
        self.write_register(0x3310, 0x10)
        self.write_register(0x3314, 0x1e)
        self.write_register(0x3315, 0x38)
        self.write_register(0x3316, 0x40)
        self.write_register(0x3317, 0x10)
        self.write_register(0x3329, 0x34)
        self.write_register(0x332d, 0x34)
        self.write_register(0x332f, 0x38)
        self.write_register(0x3335, 0x3c)
        self.write_register(0x3344, 0x3c)
        self.write_register(0x335b, 0x80)
        self.write_register(0x335f, 0x80)
        self.write_register(0x3366, 0x06)
        self.write_register(0x3385, 0x31)
        self.write_register(0x3387, 0x51)
        self.write_register(0x3389, 0x01)
        self.write_register(0x33b1, 0x03)
        self.write_register(0x33b2, 0x06)
        self.write_register(0x3621, 0xa4)
        self.write_register(0x3622, 0x05)
        self.write_register(0x3624, 0x47)
        self.write_register(0x3630, 0x46)
        self.write_register(0x3631, 0x48)
        self.write_register(0x3633, 0x52)
        self.write_register(0x3635, 0x18)
        self.write_register(0x3636, 0x25)
        self.write_register(0x3637, 0x89)
        self.write_register(0x3638, 0x0f)
        self.write_register(0x3639, 0x08)
        self.write_register(0x363a, 0x00)
        self.write_register(0x363b, 0x48)
        self.write_register(0x363c, 0x06)
        self.write_register(0x363d, 0x00)
        self.write_register(0x363e, 0xf8)
        self.write_register(0x3640, 0x00)
        self.write_register(0x3641, 0x01)
        self.write_register(0x36ea, 0x34)
        self.write_register(0x36eb, 0x0f)
        self.write_register(0x36ec, 0x1f)
        self.write_register(0x36ed, 0x33)
        self.write_register(0x36fa, 0x3a)
        self.write_register(0x36fb, 0x00)
        self.write_register(0x36fc, 0x01)
        self.write_register(0x36fd, 0x03)
        self.write_register(0x3908, 0x91)
        self.write_register(0x3d08, 0x01)
        self.write_register(0x3e01, 0x14)
        self.write_register(0x3e02, 0x80)
        self.write_register(0x3e06, 0x0c)
        self.write_register(0x4500, 0x59)
        self.write_register(0x4501, 0xc4)
        self.write_register(0x4603, 0x00)
        self.write_register(0x4809, 0x01)
        self.write_register(0x4837, 0x38)
        self.write_register(0x5011, 0x00)
        self.write_register(0x36e9, 0x20)
        self.write_register(0x36f9, 0x00)
        self.write_register(0x0100, 0x01)
        self.write_register(0x4418, 0x08)
        self.write_register(0x4419, 0x8e)
        #self.write_register(0x3314, 0x1e) [gain<2]
        #self.write_register(0x3317, 0x10)
        #self.write_register(0x3314, 0x4f) [4>gain>=2]
        #self.write_register(0x3317, 0x0f)
        #self.write_register(0x3314, 0x4f) [gain>=4]
        #self.write_register(0x3317, 0x0f)
        return 0

    def cfg_640x480_10bit_2lane(self, fps):
        ''' I2C sensor uploads for 640x480, 10b and 2lanes.
        
        Parameters
        ----------        
        fps : int
            The frame rate (30 or 60)
        '''
        self.set_i2c_address('sensor')
        self.write_register(0x0103, 0x01)
        self.write_register(0x0100, 0x00)
        self.write_register(0x36e9, 0x80)
        self.write_register(0x36f9, 0x80)
        self.write_register(0x3001, 0x00)
        self.write_register(0x3000, 0x00)
        self.write_register(0x300f, 0x0f)
        self.write_register(0x3018, 0x33)
        self.write_register(0x3019, 0xfc)
        self.write_register(0x301c, 0x78)
        if fps == 30:
            self.write_register(0x301f, 0x0e)
        elif fps == 60:
            self.write_register(0x301f, 0x0f)
        self.write_register(0x3031, 0x0a)
        self.write_register(0x3037, 0x20)
        self.write_register(0x303f, 0x01)
        self.write_register(0x320c, 0x04)
        self.write_register(0x320d, 0xb0)
        if fps == 30:
            self.write_double_register(0x320e, 0x07d0)
            self.Tpclk = 1 / (30 * 0x07d0 * 0x04b0)
        elif fps == 60:
            self.write_double_register(0x320e, 0x03e8)
            self.Tpclk = 1 / (60 * 0x03e8 * 0x04b0)
        self.write_register(0x3220, 0x10)
        self.write_register(0x3221, 0x60)
        self.write_register(0x3250, 0xc0)
        self.write_register(0x3251, 0x02)
        self.write_register(0x3252, 0x02)
        self.write_register(0x3253, 0xa6)
        self.write_register(0x3254, 0x02)
        self.write_register(0x3255, 0x07)
        self.write_register(0x3304, 0x48)
        self.write_register(0x3306, 0x38)
        self.write_register(0x3309, 0x68)
        self.write_register(0x330b, 0xe0)
        self.write_register(0x330c, 0x18)
        self.write_register(0x330f, 0x20)
        self.write_register(0x3310, 0x10)
        self.write_register(0x3314, 0x1e)
        self.write_register(0x3315, 0x38)
        self.write_register(0x3316, 0x40)
        self.write_register(0x3317, 0x10)
        self.write_register(0x3329, 0x34)
        self.write_register(0x332d, 0x34)
        self.write_register(0x332f, 0x38)
        self.write_register(0x3335, 0x3c)
        self.write_register(0x3344, 0x3c)
        self.write_register(0x335b, 0x80)
        self.write_register(0x335f, 0x80)
        self.write_register(0x3366, 0x06)
        self.write_register(0x3385, 0x31)
        self.write_register(0x3387, 0x51)
        self.write_register(0x3389, 0x01)
        self.write_register(0x33b1, 0x03)
        self.write_register(0x33b2, 0x06)
        self.write_register(0x3621, 0xa4)
        self.write_register(0x3622, 0x05)
        self.write_register(0x3624, 0x47)
        self.write_register(0x3630, 0x46)
        self.write_register(0x3631, 0x48)
        self.write_register(0x3633, 0x52)
        self.write_register(0x3635, 0x18)
        self.write_register(0x3636, 0x25)
        self.write_register(0x3637, 0x89)
        self.write_register(0x3638, 0x0f)
        self.write_register(0x3639, 0x08)
        self.write_register(0x363a, 0x00)
        self.write_register(0x363b, 0x48)
        self.write_register(0x363c, 0x06)
        self.write_register(0x363d, 0x00)
        self.write_register(0x363e, 0xf8)
        self.write_register(0x3640, 0x00)
        self.write_register(0x3641, 0x01)
        self.write_register(0x36ea, 0x3b)
        self.write_register(0x36eb, 0x0e)
        self.write_register(0x36ec, 0x1e)
        self.write_register(0x36ed, 0x33)
        self.write_register(0x36fa, 0x3a)
        self.write_register(0x36fc, 0x01)
        self.write_register(0x3908, 0x91)
        self.write_register(0x3d08, 0x01)
        self.write_register(0x3e01, 0x14)
        self.write_register(0x3e02, 0x80)
        self.write_register(0x3e06, 0x0c)
        self.write_register(0x4500, 0x59)
        self.write_register(0x4501, 0xc4)
        self.write_register(0x4603, 0x00)
        self.write_register(0x4809, 0x01)
        self.write_register(0x4837, 0x38)
        self.write_register(0x5011, 0x00)
        self.write_register(0x36e9, 0x00)
        self.write_register(0x36f9, 0x00)
        self.write_register(0x0100, 0x01)
        self.write_register(0x4418, 0x08)
        self.write_register(0x4419, 0x8e)
        #self.write_register(0x3314, 0x1e) [gain<2]
        #self.write_register(0x3317, 0x10)
        #self.write_register(0x3314, 0x4f) [4>gain>=2]
        #self.write_register(0x3317, 0x0f)
        #self.write_register(0x3314, 0x4f) [gain>=4]
        #self.write_register(0x3317, 0x0f)
        return 0

    def cfg_640x480_8bit_2lane(self, fps):
        ''' I2C sensor uploads for 640x480, 8b and 2lanes.
                
        Parameters
        ----------        
        fps : int
            The frame rate (30 or 60)
        '''
        self.set_i2c_address('sensor')
        self.write_register(0x0103, 0x01)
        self.write_register(0x0100, 0x00)
        self.write_register(0x36e9, 0x80)
        self.write_register(0x36f9, 0x80)
        self.write_register(0x3001, 0x00)
        self.write_register(0x3000, 0x00)
        self.write_register(0x300f, 0x0f)
        self.write_register(0x3018, 0x33)
        self.write_register(0x3019, 0xfc)
        self.write_register(0x301c, 0x78)
        if fps == 30:
            self.write_register(0x301f, 0x0c)
        elif fps == 60:
            self.write_register(0x301f, 0x0d)
        self.write_register(0x3031, 0x08)
        self.write_register(0x3037, 0x00)
        self.write_register(0x303f, 0x01)
        self.write_register(0x320c, 0x04)
        self.write_register(0x320d, 0xb0)
        if fps == 30:
            self.write_double_register(0x320e, 0x07d0)
            self.Tpclk = 1 / (30 * 0x07d0 * 0x04b0)
        elif fps == 60:
            self.write_double_register(0x320e, 0x03e8)
            self.Tpclk = 1 / (60 * 0x03e8 * 0x04b0)
        self.write_register(0x3220, 0x10)
        self.write_register(0x3221, 0x60)
        self.write_register(0x3250, 0xc0)
        self.write_register(0x3251, 0x02)
        self.write_register(0x3252, 0x02)
        self.write_register(0x3253, 0xa6)
        self.write_register(0x3254, 0x02)
        self.write_register(0x3255, 0x07)
        self.write_register(0x3304, 0x48)
        self.write_register(0x3306, 0x38)
        self.write_register(0x3309, 0x68)
        self.write_register(0x330b, 0xe0)
        self.write_register(0x330c, 0x18)
        self.write_register(0x330f, 0x20)
        self.write_register(0x3310, 0x10)
        self.write_register(0x3314, 0x1e)
        self.write_register(0x3315, 0x38)
        self.write_register(0x3316, 0x40)
        self.write_register(0x3317, 0x10)
        self.write_register(0x3329, 0x34)
        self.write_register(0x332d, 0x34)
        self.write_register(0x332f, 0x38)
        self.write_register(0x3335, 0x3c)
        self.write_register(0x3344, 0x3c)
        self.write_register(0x335b, 0x80)
        self.write_register(0x335f, 0x80)
        self.write_register(0x3366, 0x06)
        self.write_register(0x3385, 0x31)
        self.write_register(0x3387, 0x51)
        self.write_register(0x3389, 0x01)
        self.write_register(0x33b1, 0x03)
        self.write_register(0x33b2, 0x06)
        self.write_register(0x3621, 0xa4)
        self.write_register(0x3622, 0x05)
        self.write_register(0x3624, 0x47)
        self.write_register(0x3630, 0x46)
        self.write_register(0x3631, 0x48)
        self.write_register(0x3633, 0x52)
        self.write_register(0x3635, 0x18)
        self.write_register(0x3636, 0x25)
        self.write_register(0x3637, 0x89)
        self.write_register(0x3638, 0x0f)
        self.write_register(0x3639, 0x08)
        self.write_register(0x363a, 0x00)
        self.write_register(0x363b, 0x48)
        self.write_register(0x363c, 0x06)
        self.write_register(0x363d, 0x00)
        self.write_register(0x363e, 0xf8)
        self.write_register(0x3640, 0x00)
        self.write_register(0x3641, 0x01)
        self.write_register(0x36ea, 0x3a)
        self.write_register(0x36eb, 0x0d)
        self.write_register(0x36ec, 0x1d)
        self.write_register(0x36ed, 0x13)
        self.write_register(0x36fa, 0x3a)
        self.write_register(0x36fb, 0x00)
        self.write_register(0x36fc, 0x01)
        self.write_register(0x36fd, 0x03)
        self.write_register(0x3908, 0x91)
        self.write_register(0x3d08, 0x01)
        self.write_register(0x3e01, 0x14)
        self.write_register(0x3e02, 0x80)
        self.write_register(0x3e06, 0x0c)
        self.write_register(0x4500, 0x59)
        self.write_register(0x4501, 0xc4)
        self.write_register(0x4603, 0x00)
        self.write_register(0x4809, 0x01)
        self.write_register(0x4837, 0x38)
        self.write_register(0x5011, 0x00)
        self.write_register(0x36e9, 0x00)
        self.write_register(0x36f9, 0x00)
        self.write_register(0x0100, 0x01)
        self.write_register(0x4418, 0x08)
        self.write_register(0x4419, 0x8e)    
        #self.write_register(0x3314, 0x1e) [gain<2]
        #self.write_register(0x3317, 0x10)
        #self.write_register(0x3314, 0x4f) [4>gain>=2]
        #self.write_register(0x3317, 0x0f)
        #self.write_register(0x3314, 0x4f) [gain>=4]
        #self.write_register(0x3317, 0x0f)
        return 0

    def cfg_640x480_8bit_1lane_50fps(self):
        ''' I2C sensor uploads for 640x480, 8b and 1lane.
        '''
        self.set_i2c_address('sensor')
        self.write_register(0x0103, 0x01)
        self.write_register(0x0100, 0x00)
        self.write_register(0x3000, 0x00)
        self.write_register(0x3001, 0x00)
        self.write_register(0x300f, 0x0f)
        self.write_register(0x3018, 0x13)
        self.write_register(0x3019, 0xfc)
        self.write_register(0x301c, 0x78)
        self.write_register(0x3031, 0x08)
        self.write_register(0x3037, 0x00)
        self.write_register(0x303f, 0x01)
        self.write_register(0x320c, 0x05)
        self.write_register(0x320d, 0x54)
        self.write_register(0x320e, 0x04)
        self.write_register(0x320f, 0x4b)
        self.Tpclk = 1 / (50 * 0x04b4 * 0x0554)
        self.write_register(0x3220, 0x10)
        self.write_register(0x3221, 0x60)
        self.write_register(0x3250, 0xf0)
        self.write_register(0x3251, 0x02)
        self.write_register(0x3252, 0x02)
        self.write_register(0x3253, 0x25)
        self.write_register(0x3254, 0x02)
        self.write_register(0x3255, 0x07)
        self.write_register(0x3304, 0x48)
        self.write_register(0x3306, 0x60)
        self.write_register(0x3309, 0x50)
        self.write_register(0x330a, 0x00)
        self.write_register(0x330b, 0xb0)
        self.write_register(0x330c, 0x18)
        self.write_register(0x330f, 0x40)
        self.write_register(0x3310, 0x10)
        self.write_register(0x3314, 0x1e)
        self.write_register(0x3315, 0x30)
        self.write_register(0x3316, 0x48)
        self.write_register(0x3317, 0x20)
        self.write_register(0x3329, 0x3c)
        self.write_register(0x332d, 0x3c)
        self.write_register(0x332f, 0x40)
        self.write_register(0x3335, 0x44)
        self.write_register(0x3344, 0x44)
        self.write_register(0x335b, 0x80)
        self.write_register(0x335f, 0x80)
        self.write_register(0x3366, 0x06)
        self.write_register(0x3385, 0x31)
        self.write_register(0x3387, 0x39)
        self.write_register(0x3389, 0x01)
        self.write_register(0x33b1, 0x03)
        self.write_register(0x33b2, 0x06)
        self.write_register(0x33bd, 0xe0)
        self.write_register(0x33bf, 0x10)
        self.write_register(0x3621, 0xa4)
        self.write_register(0x3622, 0x05)
        self.write_register(0x3624, 0x47)
        self.write_register(0x3630, 0x46)
        self.write_register(0x3631, 0x68)
        self.write_register(0x3633, 0x52)
        self.write_register(0x3635, 0x18)
        self.write_register(0x3636, 0x25)
        self.write_register(0x3637, 0x89)
        self.write_register(0x3638, 0x0f)
        self.write_register(0x3639, 0x08)
        self.write_register(0x363a, 0x00)
        self.write_register(0x363b, 0x48)
        self.write_register(0x363c, 0x06)
        self.write_register(0x363d, 0x00)
        self.write_register(0x363e, 0xf8)
        self.write_register(0x3640, 0x00)
        self.write_register(0x3641, 0x01)
        self.write_register(0x36e9, 0x24)
        self.write_register(0x36ea, 0x3b)
        self.write_register(0x36eb, 0x0d)
        self.write_register(0x36ec, 0x0d)
        self.write_register(0x36ed, 0x23)
        self.write_register(0x36f9, 0x24)
        self.write_register(0x36fa, 0x3b)
        self.write_register(0x36fb, 0x00)
        self.write_register(0x36fc, 0x02)
        self.write_register(0x36fd, 0x03)
        self.write_register(0x3908, 0x91)
        self.write_register(0x3d08, 0x01)
        self.write_register(0x3e01, 0x18)
        self.write_register(0x3e02, 0xf0)
        self.write_register(0x3e06, 0x0c)
        self.write_register(0x4500, 0x59)
        self.write_register(0x4501, 0xc4)
        self.write_register(0x4603, 0x00)
        self.write_register(0x5011, 0x00)
        self.write_register(0x4800, 0x64)
        self.write_register(0x4809, 0x01)
        self.write_register(0x5988, 0x02)
        self.write_register(0x598e, 0x05)
        self.write_register(0x598f, 0x17)
        self.write_register(0x3217, 0x00)
        self.write_register(0x3218, 0x00)
        self.write_register(0x4810, 0x00)
        self.write_register(0x4811, 0x01)
        self.write_register(0x323b, 0x00)
        self.write_register(0x3305, 0x00)
        self.write_register(0x3306, 0x98)
        self.write_register(0x330a, 0x01)
        self.write_register(0x330b, 0x18)
        self.write_register(0x3f04, 0x03)
        self.write_register(0x3f05, 0x80)
        self.write_register(0x36e9, 0x40)
        self.write_register(0x36ea, 0x2f)
        self.write_register(0x36eb, 0x0d)
        self.write_register(0x36ec, 0x0d)
        self.write_register(0x36ed, 0x23)
        self.write_register(0x36f9, 0x62)
        self.write_register(0x36fa, 0x2f)
        self.write_register(0x36fb, 0x10)
        self.write_register(0x36fc, 0x02)
        self.write_register(0x36fd, 0x03)
        self.write_register(0x3223, 0x50)
        self.write_register(0x36ed, 0x20)
        self.write_register(0x36fd, 0x00)
        self.write_register(0x4837, 0x18)
        self.write_register(0x391b, 0x81)
        self.write_register(0x3252, 0x04)
        self.write_register(0x3253, 0x46)
        self.write_register(0x3316, 0x68)
        self.write_register(0x3344, 0x64)
        self.write_register(0x3335, 0x64)
        self.write_register(0x332f, 0x60)
        self.write_register(0x332d, 0x5c)
        self.write_register(0x3329, 0x5c)
        self.write_register(0x3314, 0x1e)
        self.write_register(0x3317, 0x1b)
        self.write_register(0x3631, 0x68)
        self.write_register(0x0100, 0x01)
        self.write_register(0x4418, 0x08)
        self.write_register(0x4419, 0x8e)
        self.write_register(0x4419, 0x80)
        self.write_register(0x363d, 0x10)
        self.write_register(0x3630, 0x48)
        #self.write_register(0x3314, 0x1e) [gain<2]
        #self.write_register(0x3317, 0x1b)
        #self.write_register(0x3631, 0x68)
        #self.write_register(0x3314, 0x6f) [4>gain>=2]
        #self.write_register(0x3317, 0x10)
        #self.write_register(0x3631, 0x48)
        #self.write_register(0x3314, 0x76) [gain>=4]
        #self.write_register(0x3317, 0x0f)
        #self.write_register(0x3631, 0x48)
        return 0