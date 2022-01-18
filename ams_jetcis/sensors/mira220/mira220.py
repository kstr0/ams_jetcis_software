import time
import numpy as np
from collections import OrderedDict
from ams_jetcis.sensors.sensor import Sensor

class Mira220(Sensor):
    """
    Implementation of Sensor class for Mira220.
    """
    # TODO: roi multiple windows, power save roi;

    def __init__(self, imagertools) -> None:
        self.name = 'Mira220'
        self._roi = [None, None, None, None]
        self.width = None
        self.height = None
        self.widthDMA = None
        self.heightDMA = None
        self._bpp = None
        self._fps = None
        self._analog_gain = None
        self._digital_gain = None
        self._exposure = None
        self.dtMode = None
        self._context_active = 'A'
        self._context_observe = 'A'
        self._rnc = [None, None]
        self._dpc = [None, None, None, None, None]
        self._led_driver = [None, None, None]
        self._illumination_trigger = [None, None, None, None, None, None, None]
        self._ulps = [0, 'BOTH']
        self._mipi_speed = 1500
        self.cfg_to_dtMode = {12: {1600: 0, 1280: 1, 640: 2}, 10: {1600: 3, 1280: 4, 640: 5}, 8: {1600: 6, 1280: 7, 640: 8}}
        super().__init__(imagertools)

    def set_i2c_address(self, ic):
        '''Set the I2C address and the I2C bit depth of register and value.

        Parameters
        ----------
        ic : str
            Integrated circuit on the PCB
        '''
        if ic == 'sensor':
            self.imager.setSensorI2C(0x54)
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
        # Reset low
        self.imager.reset(2)

        # Disable the PMIC
        self.power_off()

        # Set LDOs on 0V
        self.write_register(0x05, 0x00)
        self.write_register(0x0E, 0x00)
        self.write_register(0x11, 0x00)
        self.write_register(0x14, 0x00)
        self.write_register(0x17, 0x00)
        self.write_register(0x1A, 0x00)
        self.write_register(0x1C, 0x00)
        self.write_register(0x1D, 0x00)
        self.write_register(0x1E, 0x00)
        self.write_register(0x1F, 0x00)
        self.write_register(0x24, 0x48)
        self.write_register(0x20, 0x00)
        self.write_register(0x21, 0x00)
        self.write_register(0x1A, 0x00)
        self.write_register(0x01, 0x00)
        self.write_register(0x08, 0x00)
        self.write_register(0x02, 0x00)
        self.write_register(0x0B, 0x00)
        self.write_register(0x14, 0x00)
        self.write_register(0x17, 0x00)
        self.write_register(0x1C, 0x00)
        self.write_register(0x1D, 0x00)
        self.write_register(0x1F, 0x00)

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
    
        ## Enable LDO9=2.50V for VDD25
        time.sleep(50e-6)
        self.read_register(0x20)
        self.write_register(0x20, 0xB2)
        self.read_register(0x20)

        ## Enable LDO1/7/10=1.35V for VDD13P/D/A
        time.sleep(700e-6)
        self.write_register(0x12, 0x16)
        self.write_register(0x10, 0x16)
        self.write_register(0x11, 0x96)
        self.write_register(0x1E, 0x96)
        self.write_register(0x21, 0x96)

        ## Enable DCDC1/4=1.8V for VINLDO1P8/VDD18
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
        self.f_clk_in = 38.4e6

        # Enable green LED for confirmation
        time.sleep(50e-6)
        self.write_register(0x45, 0x40)
        self.write_register(0x57, 0x02)
        self.write_register(0x5D, 0x10)
        self.write_register(0x61, 0x10)

        # Set I2C address to LED driver
        self.set_i2c_address('illumination')

        # Turn off LED driver
        if self.write_register(0x10, 0x08) == 1:
            # JTAG to GND. Interposer has no led driver
            self.set_i2c_address('uC')
            self.write_register(11, 0b11011111)
            self.write_register(15, 0b00000000)
            self.write_register(6, 1)

        # Reset sensor
        self.set_i2c_address('sensor')
        self.imager.setDelay(0)
        self.imager.reset(3)
        self.imager.wait(2000)

    def hard_reset(self):
        '''Execute hard reset.
        '''
        self.set_i2c_address('sensor')
        self.imager.reset(2) # Keep in reset
        self.imager.wait(100)
        self.imager.reset(3) # Leave reset

    def soft_reset(self):
        '''Execute soft reset (self-clearing).
        '''
        self.set_i2c_address('sensor')
        self.write_register(0x0040, 0x01)

    def check_sensor(self):
        '''Check if sensor is present.

        Returns
        -------
        int : 
            0 if detected
        '''
        self.set_i2c_address('sensor')
        if self.read_register(0x0003) > 0: #todo better
            self.imager.pr('Mira220 detected with ID ' + self.get_internal_id())
            self.set_i2c_address('pmic')
            # led seq -- use this to turn on leds. abc0000- 1110000 for all leds
            self.write_register(0x61, 0b110000)
            return 0
        else:
            self.set_i2c_address('pmic')
            # led seq -- use this to turn on leds. abc0000- 1110000 for all leds
            self.write_register(0x61, 0b1010000)
            return 1

    def init_sensor(self, bit_mode='12bit', fps=30, w=1600, h=1400, nb_lanes=2, analog_gain=1):
        '''Execute a configuration sequence.

        Parameters
        ----------
        bit_mode : str
            Bit depth for a pixel (8bit, 10bit or 12bit)
        
        fps : int
            The frame rate

        w : int
            The width (1600, 1280 or 640)
            
        h : int
            The height (1400, 1120 or 480)

        nb_lanes : int
            The amount of data lanes
        
        analog_gain : int
            The analog gain (1, 2 or 4)
        '''
        if nb_lanes == 2:
            # Execute default configuration
            self.config_1600_1400_30fps_12b_2lanes()
            self.imager.setformat(12, 1600, 1400, 1600, 1400, True)

            # Set requested sensor parameters
            self.bpp = bit_mode
            self.roi = [w, h, None, None]
            self.fps = fps
            self.analog_gain = analog_gain
        else:
            raise NotImplementedError(f'Given {nb_lanes} data lanes are not implemented.') 

    def get_fot_length(self):
        '''Get the FOT/GLOB length.

        Returns
        -------
        int : 
            Frame overhead time length
        '''
        self.set_i2c_address('sensor')
        self.write_register(0x3013, 0x0a)      
        addr_start_eoi = self.read_double_register(0x305A)
        addr_stop_eoi = self.read_double_register(0x305C)
        val = '{:08b}'.format(self.read_register(0x302F))
        gran_eoi = 2 ** int(val[-4:-2], 2)
        fot_length = 0
        for addr in range(addr_start_eoi, addr_stop_eoi + 1, 1):
            cmd = 0
            for b in range(0, 6, 1):
                cmd += (self.read_register(0x3300 + b + addr * 6) << 8 * b)
            dly = cmd % 0x400
            fot_length += dly * gran_eoi
        self.write_register(0x3013, 0x0b)
        return fot_length

    def otp_power_on(self):
        '''Power up the OTP of the sensor.
        '''
        self.set_i2c_address('sensor')
        self.write_register(0x0080, 0x04)

    def otp_power_off(self):
        '''Power down the OTP of the sensor.
        '''
        self.set_i2c_address('sensor')
        self.write_register(0x0080, 0x08)

    def get_otp_status(self):
        '''Get the OTP status.
        
        Returns
        -------
        list : 
            [0] : 1 if ready for next command
            [1] : 1 if power on
            [2] : 1 if standby
        '''
        self.set_i2c_address('sensor')
        otp_status = format(self.read_register(0x0081), '08b')
        return [int(otp_status[7]), int(otp_status[6]), int(otp_status[5])]
    
    def otp_read(self, otp_address, offset):
        '''Read the given OTP address.
        
        Parameters
        ----------
        otp_address : int
            OTP address to be read

        offset : int
            The byte to be read from the 32 bit (4 bytes) OTP word
            
        Returns
        -------
        int : 
            OTP value
        '''
        self.set_i2c_address('sensor')
        self.write_register(0x0086, otp_address)
        self.write_register(0x0080, 0x02)
        return self.read_register(0x0082 + offset)

    def get_sensor_revision(self):
        '''Get the revision of the sensor programmed in OTP.

        Returns
        -------
        int : 
            1 if rev A sensor; 2 if rev B sensor
        '''
        self.set_i2c_address('sensor')
        self.otp_power_on()
        # Check if extra trim value for rev B is programmed
        if (self.otp_read(0x0d, 0) >> 5) == 0:
            value = 2
        else:
            value = 1
        self.otp_power_off()
        return value

    def trim_restore(self, rev):
        '''Restore voltage and gain trims from the OTP to the sensor.

        Parameters
        ----------
        rev : int
            1 if rev A sensor; 2 if rev B sensor
        '''
        self.otp_gain_trims = []
        self.set_i2c_address('sensor')
        self.otp_power_on()
        # Write OTP data to image sensor when programmed
        if (self.otp_read(0x1d, 0) != 0xff):
            reg_list = [0x4015, 0x4016, 0x4017, 0x4018, 0x403B, 0x4040, 0x4041, 0x4042, 0x402a, 0x4029, 0x4009]
            for i in range(0, len(reg_list)):
                otp_data = self.otp_read(i, 0)
                self.write_register(reg_list[i], otp_data)
            self.otp_gain_trims = [otp_data, self.otp_read(0x0b, 0), self.otp_read(0x0c, 0)]
            if rev == 2:
                self.write_register(0x403e, self.otp_read(0x0d, 0))
        self.otp_power_off()

    def get_internal_id(self):
        '''Get the internal id of the sensor programmed in OTP.

        Returns
        -------
        str : 
            internal id
        '''
        self.set_i2c_address('sensor')
        self.otp_power_on()
        b0 = '{0:0{1}X}'.format(self.otp_read(0x25, 0), 2)
        b1 = '{0:0{1}X}'.format(self.otp_read(0x1e, 0), 2)
        b2 = '{0:0{1}X}'.format(self.otp_read(0x1e, 1), 2)
        b3 = '{0:0{1}X}'.format(self.otp_read(0x1e, 2), 2)
        b4 = '{0:0{1}X}'.format(self.otp_read(0x1d, 0), 2)
        b5 = '{0:0{1}X}'.format(self.otp_read(0x1d, 1), 2)
        b6 = '{0:0{1}X}'.format(self.otp_read(0x1d, 2), 2)
        b7 = '{0:0{1}X}'.format(self.otp_read(0x1d, 3), 2)      
        self.otp_power_off()
        return b0 + ':' + b1 + ':' + b2 + ':' + b3 + ':' + b4 + ':' + b5 + ':' + b6 + ':' + b7 

    def get_otp_dark_mean(self):
        '''Get the dark mean value stored in OTP.

        Returns
        -------
        int : 
            dark mean value
        '''
        self.set_i2c_address('sensor')
        self.otp_power_on()
        dark_mean = (self.otp_read(0x0e, 1) << 8) + self.otp_read(0x0e, 0)
        self.otp_power_off()
        return dark_mean

    def get_otp_temperature_calibration(self):
        '''Get the temperature factor stored in OTP.

        Returns
        -------
        float : 
            calibration factor (None if OTP is not programmed)
        '''
        self.set_i2c_address('sensor')
        self.otp_power_on()
        signal_level = ((self.otp_read(0x1b, 1) << 8) + self.otp_read(0x1b, 0)) % (2**12)
        reset_level = ((self.otp_read(0x1c, 1) << 8) + self.otp_read(0x1c, 0)) % (2**10)
        self.otp_power_off()
        if (signal_level == 0xfff) and (reset_level == 0x3ff):
            T_factor = None
        else:
            T_wafer_expected = 60
            T_wafer_measured = self.sensor_temperature_conversion(signal_level, reset_level, 1)
            T_factor = T_wafer_expected / T_wafer_measured
        return T_factor

    def config_1600_1400_30fps_12b_2lanes(self):
        '''Sensor I2C uploads the initialize the sensor in a known state.
        '''
        ## Set I2C address
        self.set_i2c_address('sensor')
        self.imager.wait(100)

        ## Get sensor revision
        rev = self.get_sensor_revision()
        
        ## Disable internal LDOs connected to VDD25
        if rev == 2:
            self.write_register(0x401e, 0x02)
            self.write_register(0x4038, 0x3b)
        else:
            self.set_i2c_address('pmic')
            self.write_register(0x20, 0xB9) # VDD28 on 2.85V for older PCBs
            self.set_i2c_address('sensor')
        
        ## Sensor uploads
        # Stop sensor at a row boundary (stop sensor in a known state)
        self.stop_img_capture('row')
        # MIPI TX controller disable
        self.write_register(0x6006, 0x00)
        # MIPI 2 lane mode
        self.write_register(0x6012, 0x01)
        # MIPI continuous PHY clocking
        self.write_register(0x6013, 0x00)
        # MIPI TX controller enable
        self.write_register(0x6006, 0x01)
        # Disable statistics
        self.write_register(0x205d, 0x00)
        self.write_register(0x2063, 0x00)
        # Defect pixel correction disabled
        self.write_register(0x24dc, 0x13)
        self.write_register(0x24dd, 0x03)
        self.write_register(0x24de, 0x03)
        self.write_register(0x24df, 0x00)
        # 2.24MP window
        self.write_register(0x4006, 0x08)
        self.write_register(0x401c, 0x6f)
        # Row noise correction enabled, with flat field target of 100
        self.write_register(0x204b, 0x03)
        self.write_register(0x205b, 0x64)
        self.write_register(0x205c, 0x00)
        # Some default values for references (some trim values are in OTP, better to use those)
        self.write_register(0x4018, 0x3f)
        self.write_register(0x403b, 0x0b )
        self.write_register(0x403e, 0x0e)
        self.write_register(0x402b, 0x06)
        # Misc. sensor settings that should not be touched
        self.write_register(0x1077, 0x00)
        self.write_register(0x1078, 0x00)
        self.write_register(0x1009, 0x08)
        self.write_register(0x100a, 0x00)
        self.write_register(0x110f, 0x08)
        self.write_register(0x1110, 0x00)
        self.write_register(0x1006, 0x02)
        self.write_register(0x402c, 0x64)
        self.write_register(0x3064, 0x00 )
        self.write_register(0x3065, 0xf0)
        self.write_register(0x4013, 0x13)
        self.write_register(0x401f, 0x09)
        self.write_register(0x4020, 0x13)
        self.write_register(0x4044, 0x75) if rev == 2 else self.write_register(0x4044, 0x65)
        self.write_register(0x4027, 0x00) if rev == 2 else self.write_register(0x4027, 0x33)
        self.write_register(0x3215, 0x69)
        self.write_register(0x3216, 0x0f)
        self.write_register(0x322B, 0x69)
        self.write_register(0x322C, 0x0f)
        self.write_register(0x4051, 0x80)
        self.write_register(0x4052, 0x10)
        self.write_register(0x4057, 0x80)
        self.write_register(0x4058, 0x10)
        self.write_register(0x3212, 0x59)
        self.write_register(0x4047, 0x8f)
        self.write_register(0x4026, 0x10) if rev == 2 else self.write_register(0x4026, 0x1f)
        self.write_register(0x4032, 0x53)
        self.write_register(0x4036, 0x17)
        self.write_register(0x50b8, 0xf4)
        # Related to pixel timing, do not adjust these
        self.write_register(0x3016, 0x00)
        self.write_register(0x3017, 0x2c)
        self.write_register(0x3018, 0x8c)
        self.write_register(0x3019, 0x45)
        self.write_register(0x301a, 0x05)
        self.write_register(0x3013, 0x0a)
        self.write_register(0x301b, 0x00)
        self.write_register(0x301c, 0x04)
        self.write_register(0x301d, 0x88)
        self.write_register(0x301e, 0x45)
        self.write_register(0x301f, 0x05)
        self.write_register(0x3020, 0x00)
        self.write_register(0x3021, 0x04)
        self.write_register(0x3022, 0x88)
        self.write_register(0x3023, 0x45)
        self.write_register(0x3024, 0x05)
        self.write_register(0x3025, 0x00)
        self.write_register(0x3026, 0x04)
        self.write_register(0x3027, 0x88)
        self.write_register(0x3028, 0x45)
        self.write_register(0x3029, 0x05)
        self.write_register(0x302f, 0x00)
        self.write_register(0x3056, 0x00)
        self.write_register(0x3057, 0x00)
        self.write_register(0x3300, 0x01)
        self.write_register(0x3301, 0x00)
        self.write_register(0x3302, 0xb0)
        self.write_register(0x3303, 0xb0)
        self.write_register(0x3304, 0x16)
        self.write_register(0x3305, 0x15)
        self.write_register(0x3306, 0x01)
        self.write_register(0x3307, 0x00)
        self.write_register(0x3308, 0x30)
        self.write_register(0x3309, 0xa0)
        self.write_register(0x330a, 0x16)
        self.write_register(0x330b, 0x15)
        self.write_register(0x330c, 0x01)
        self.write_register(0x330d, 0x00)
        self.write_register(0x330e, 0x30)
        self.write_register(0x330f, 0xa0)
        self.write_register(0x3310, 0x16)
        self.write_register(0x3311, 0x15)
        self.write_register(0x3312, 0x01)
        self.write_register(0x3313, 0x00)
        self.write_register(0x3314, 0x30)
        self.write_register(0x3315, 0xa0)
        self.write_register(0x3316, 0x16)
        self.write_register(0x3317, 0x15)
        self.write_register(0x3318, 0x01)
        self.write_register(0x3319, 0x00)
        self.write_register(0x331a, 0x30)
        self.write_register(0x331b, 0xa0)
        self.write_register(0x331c, 0x16)
        self.write_register(0x331d, 0x15)
        self.write_register(0x331e, 0x01)
        self.write_register(0x331f, 0x00)
        self.write_register(0x3320, 0x30)
        self.write_register(0x3321, 0xa0)
        self.write_register(0x3322, 0x16)
        self.write_register(0x3323, 0x15)
        self.write_register(0x3324, 0x01)
        self.write_register(0x3325, 0x00)
        self.write_register(0x3326, 0x30)
        self.write_register(0x3327, 0xa0)
        self.write_register(0x3328, 0x16)
        self.write_register(0x3329, 0x15)
        self.write_register(0x332a, 0x2b)
        self.write_register(0x332b, 0x00)
        self.write_register(0x332c, 0x30)
        self.write_register(0x332d, 0xa0)
        self.write_register(0x332e, 0x16)
        self.write_register(0x332f, 0x15)
        self.write_register(0x3330, 0x01)
        self.write_register(0x3331, 0x00)
        self.write_register(0x3332, 0x10)
        self.write_register(0x3333, 0xa0)
        self.write_register(0x3334, 0x16)
        self.write_register(0x3335, 0x15)
        self.write_register(0x3058, 0x08)
        self.write_register(0x3059, 0x00)
        self.write_register(0x305a, 0x09)
        self.write_register(0x305b, 0x00)
        self.write_register(0x3336, 0x01)
        self.write_register(0x3337, 0x00)
        self.write_register(0x3338, 0x90)
        self.write_register(0x3339, 0xb0)
        self.write_register(0x333a, 0x16)
        self.write_register(0x333b, 0x15)
        self.write_register(0x333c, 0x1f)
        self.write_register(0x333d, 0x00)
        self.write_register(0x333e, 0x10)
        self.write_register(0x333f, 0xa0)
        self.write_register(0x3340, 0x16)
        self.write_register(0x3341, 0x15)
        self.write_register(0x3342, 0x52)
        self.write_register(0x3343, 0x00)
        self.write_register(0x3344, 0x10)
        self.write_register(0x3345, 0x80)
        self.write_register(0x3346, 0x16)
        self.write_register(0x3347, 0x15)
        self.write_register(0x3348, 0x01)
        self.write_register(0x3349, 0x00)
        self.write_register(0x334a, 0x10)
        self.write_register(0x334b, 0x80)
        self.write_register(0x334c, 0x16)
        self.write_register(0x334d, 0x1d)
        self.write_register(0x334e, 0x01)
        self.write_register(0x334f, 0x00)
        self.write_register(0x3350, 0x50)
        self.write_register(0x3351, 0x84)
        self.write_register(0x3352, 0x16)
        self.write_register(0x3353, 0x1d)
        self.write_register(0x3354, 0x18)
        self.write_register(0x3355, 0x00)
        self.write_register(0x3356, 0x10)
        self.write_register(0x3357, 0x84)
        self.write_register(0x3358, 0x16)
        self.write_register(0x3359, 0x1d)
        self.write_register(0x335a, 0x80) if rev == 2 else self.write_register(0x335a, 0xa0)
        self.write_register(0x335b, 0x02) if rev == 2 else self.write_register(0x335b, 0x00)
        self.write_register(0x335c, 0x10)
        self.write_register(0x335d, 0xc4)
        self.write_register(0x335e, 0x14)
        self.write_register(0x335f, 0x1d)
        self.write_register(0x3360, 0xa5)
        self.write_register(0x3361, 0x00)
        self.write_register(0x3362, 0x10)
        self.write_register(0x3363, 0x84)
        self.write_register(0x3364, 0x16)
        self.write_register(0x3365, 0x1d)
        self.write_register(0x3366, 0x01)
        self.write_register(0x3367, 0x00)
        self.write_register(0x3368, 0x90)
        self.write_register(0x3369, 0x84)
        self.write_register(0x336a, 0x16)
        self.write_register(0x336b, 0x1d)
        self.write_register(0x336c, 0x12)
        self.write_register(0x336d, 0x00)
        self.write_register(0x336e, 0x10)
        self.write_register(0x336f, 0x84)
        self.write_register(0x3370, 0x16)
        self.write_register(0x3371, 0x15)
        self.write_register(0x3372, 0x32)
        self.write_register(0x3373, 0x00)
        self.write_register(0x3374, 0x30)
        self.write_register(0x3375, 0x84)
        self.write_register(0x3376, 0x16)
        self.write_register(0x3377, 0x15)
        self.write_register(0x3378, 0x26)
        self.write_register(0x3379, 0x00)
        self.write_register(0x337a, 0x10)
        self.write_register(0x337b, 0x84)
        self.write_register(0x337c, 0x16)
        self.write_register(0x337d, 0x15)
        self.write_register(0x337e, 0x80) if rev == 2 else self.write_register(0x337e, 0xa0)
        self.write_register(0x337f, 0x02) if rev == 2 else self.write_register(0x337f, 0x00)
        self.write_register(0x3380, 0x10)
        self.write_register(0x3381, 0xc4)
        self.write_register(0x3382, 0x14)
        self.write_register(0x3383, 0x15)
        self.write_register(0x3384, 0xa9)
        self.write_register(0x3385, 0x00)
        self.write_register(0x3386, 0x10)
        self.write_register(0x3387, 0x84)
        self.write_register(0x3388, 0x16)
        self.write_register(0x3389, 0x15)
        self.write_register(0x338a, 0x41)
        self.write_register(0x338b, 0x00)
        self.write_register(0x338c, 0x10)
        self.write_register(0x338d, 0x80)
        self.write_register(0x338e, 0x16)
        self.write_register(0x338f, 0x15)
        self.write_register(0x3390, 0x02)
        self.write_register(0x3391, 0x00)
        self.write_register(0x3392, 0x10)
        self.write_register(0x3393, 0xa0)
        self.write_register(0x3394, 0x16)
        self.write_register(0x3395, 0x15)
        self.write_register(0x305c, 0x18)
        self.write_register(0x305d, 0x00)
        self.write_register(0x305e, 0x19)
        self.write_register(0x305f, 0x00)
        self.write_register(0x3396, 0x01)
        self.write_register(0x3397, 0x00)
        self.write_register(0x3398, 0x90)
        self.write_register(0x3399, 0x30)
        self.write_register(0x339a, 0x56)
        self.write_register(0x339b, 0x57)
        self.write_register(0x339c, 0x01)
        self.write_register(0x339d, 0x00)
        self.write_register(0x339e, 0x10)
        self.write_register(0x339f, 0x20)
        self.write_register(0x33a0, 0xd6)
        self.write_register(0x33a1, 0x17)
        self.write_register(0x33a2, 0x01)
        self.write_register(0x33a3, 0x00)
        self.write_register(0x33a4, 0x10)
        self.write_register(0x33a5, 0x28)
        self.write_register(0x33a6, 0xd6)
        self.write_register(0x33a7, 0x17)
        self.write_register(0x33a8, 0x03)
        self.write_register(0x33a9, 0x00)
        self.write_register(0x33aa, 0x10)
        self.write_register(0x33ab, 0x20)
        self.write_register(0x33ac, 0xd6)
        self.write_register(0x33ad, 0x17)
        self.write_register(0x33ae, 0x61)
        self.write_register(0x33af, 0x00)
        self.write_register(0x33b0, 0x10)
        self.write_register(0x33b1, 0x20)
        self.write_register(0x33b2, 0xd6)
        self.write_register(0x33b3, 0x15)
        self.write_register(0x33b4, 0x01)
        self.write_register(0x33b5, 0x00)
        self.write_register(0x33b6, 0x10)
        self.write_register(0x33b7, 0x20)
        self.write_register(0x33b8, 0xd6)
        self.write_register(0x33b9, 0x1d)
        self.write_register(0x33ba, 0x01)
        self.write_register(0x33bb, 0x00)
        self.write_register(0x33bc, 0x50)
        self.write_register(0x33bd, 0x20)
        self.write_register(0x33be, 0xd6)
        self.write_register(0x33bf, 0x1d)
        self.write_register(0x33c0, 0x2c)
        self.write_register(0x33c1, 0x00)
        self.write_register(0x33c2, 0x10)
        self.write_register(0x33c3, 0x20)
        self.write_register(0x33c4, 0xd6)
        self.write_register(0x33c5, 0x1d)
        self.write_register(0x33c6, 0x01)
        self.write_register(0x33c7, 0x00)
        self.write_register(0x33c8, 0x90)
        self.write_register(0x33c9, 0x20)
        self.write_register(0x33ca, 0xd6)
        self.write_register(0x33cb, 0x1d)
        self.write_register(0x33cc, 0x83)
        self.write_register(0x33cd, 0x00)
        self.write_register(0x33ce, 0x10)
        self.write_register(0x33cf, 0x20)
        self.write_register(0x33d0, 0xd6)
        self.write_register(0x33d1, 0x15)
        self.write_register(0x33d2, 0x01)
        self.write_register(0x33d3, 0x00)
        self.write_register(0x33d4, 0x10)
        self.write_register(0x33d5, 0x30)
        self.write_register(0x33d6, 0xd6)
        self.write_register(0x33d7, 0x15)
        self.write_register(0x33d8, 0x01)
        self.write_register(0x33d9, 0x00)
        self.write_register(0x33da, 0x10)
        self.write_register(0x33db, 0x20)
        self.write_register(0x33dc, 0xd6)
        self.write_register(0x33dd, 0x15)
        self.write_register(0x33de, 0x01)
        self.write_register(0x33df, 0x00)
        self.write_register(0x33e0, 0x10)
        self.write_register(0x33e1, 0x20)
        self.write_register(0x33e2, 0x56)
        self.write_register(0x33e3, 0x15)
        self.write_register(0x33e4, 0x07)
        self.write_register(0x33e5, 0x00)
        self.write_register(0x33e6, 0x10)
        self.write_register(0x33e7, 0x20)
        self.write_register(0x33e8, 0x16)
        self.write_register(0x33e9, 0x15)
        self.write_register(0x3060, 0x26)
        self.write_register(0x3061, 0x00)
        self.write_register(0x302a, 0xff)
        self.write_register(0x302b, 0xff)
        self.write_register(0x302c, 0xff)
        self.write_register(0x302d, 0xff)
        self.write_register(0x302e, 0x3f)
        self.write_register(0x3013, 0x0b)
        # Related to ADC timing, do not adjust these
        self.write_register(0x102b, 0x2c)
        self.write_register(0x102c, 0x01)
        self.write_register(0x1035, 0x54)
        self.write_register(0x1036, 0x00)
        self.write_register(0x3090, 0x2a)
        self.write_register(0x3091, 0x01)
        self.write_register(0x30c6, 0x05)
        self.write_register(0x30c7, 0x00)
        self.write_register(0x30c8, 0x00)
        self.write_register(0x30c9, 0x00)
        self.write_register(0x30ca, 0x00)
        self.write_register(0x30cb, 0x00)
        self.write_register(0x30cc, 0x00)
        self.write_register(0x30cd, 0x00)
        self.write_register(0x30ce, 0x00)
        self.write_register(0x30cf, 0x05)
        self.write_register(0x30d0, 0x00)
        self.write_register(0x30d1, 0x00)
        self.write_register(0x30d2, 0x00)
        self.write_register(0x30d3, 0x00)
        self.write_register(0x30d4, 0x00)
        self.write_register(0x30d5, 0x00)
        self.write_register(0x30d6, 0x00)
        self.write_register(0x30d7, 0x00)
        self.write_register(0x30f3, 0x05)
        self.write_register(0x30f4, 0x00)
        self.write_register(0x30f5, 0x00)
        self.write_register(0x30f6, 0x00)
        self.write_register(0x30f7, 0x00)
        self.write_register(0x30f8, 0x00)
        self.write_register(0x30f9, 0x00)
        self.write_register(0x30fa, 0x00)
        self.write_register(0x30fb, 0x00)
        self.write_register(0x30d8, 0x05)
        self.write_register(0x30d9, 0x00)
        self.write_register(0x30da, 0x00)
        self.write_register(0x30db, 0x00)
        self.write_register(0x30dc, 0x00)
        self.write_register(0x30dd, 0x00)
        self.write_register(0x30de, 0x00)
        self.write_register(0x30df, 0x00)
        self.write_register(0x30e0, 0x00)
        self.write_register(0x30e1, 0x05)
        self.write_register(0x30e2, 0x00)
        self.write_register(0x30e3, 0x00)
        self.write_register(0x30e4, 0x00)
        self.write_register(0x30e5, 0x00)
        self.write_register(0x30e6, 0x00)
        self.write_register(0x30e7, 0x00)
        self.write_register(0x30e8, 0x00)
        self.write_register(0x30e9, 0x00)
        self.write_register(0x30f3, 0x05)
        self.write_register(0x30f4, 0x02)
        self.write_register(0x30f5, 0x00)
        self.write_register(0x30f6, 0x17)
        self.write_register(0x30f7, 0x01)
        self.write_register(0x30f8, 0x00)
        self.write_register(0x30f9, 0x00)
        self.write_register(0x30fa, 0x00)
        self.write_register(0x30fb, 0x00)
        self.write_register(0x30d8, 0x03)
        self.write_register(0x30d9, 0x01)
        self.write_register(0x30da, 0x00)
        self.write_register(0x30db, 0x19)
        self.write_register(0x30dc, 0x01)
        self.write_register(0x30dd, 0x00)
        self.write_register(0x30de, 0x00)
        self.write_register(0x30df, 0x00)
        self.write_register(0x30e0, 0x00)
        self.write_register(0x30a2, 0x05)
        self.write_register(0x30a3, 0x02)
        self.write_register(0x30a4, 0x00)
        self.write_register(0x30a5, 0x22)
        self.write_register(0x30a6, 0x00)
        self.write_register(0x30a7, 0x00)
        self.write_register(0x30a8, 0x00)
        self.write_register(0x30a9, 0x00)
        self.write_register(0x30aa, 0x00)
        self.write_register(0x30ab, 0x05)
        self.write_register(0x30ac, 0x02)
        self.write_register(0x30ad, 0x00)
        self.write_register(0x30ae, 0x22)
        self.write_register(0x30af, 0x00)
        self.write_register(0x30b0, 0x00)
        self.write_register(0x30b1, 0x00)
        self.write_register(0x30b2, 0x00)
        self.write_register(0x30b3, 0x00)
        self.write_register(0x30bd, 0x05)
        self.write_register(0x30be, 0x9f)
        self.write_register(0x30bf, 0x00)
        self.write_register(0x30c0, 0x7d)
        self.write_register(0x30c1, 0x00)
        self.write_register(0x30c2, 0x00)
        self.write_register(0x30c3, 0x00)
        self.write_register(0x30c4, 0x00)
        self.write_register(0x30c5, 0x00)
        self.write_register(0x30b4, 0x04)
        self.write_register(0x30b5, 0x9c)
        self.write_register(0x30b6, 0x00)
        self.write_register(0x30b7, 0x7d)
        self.write_register(0x30b8, 0x00)
        self.write_register(0x30b9, 0x00)
        self.write_register(0x30ba, 0x00)
        self.write_register(0x30bb, 0x00)
        self.write_register(0x30bc, 0x00)
        self.write_register(0x30fc, 0x05)
        self.write_register(0x30fd, 0x00)
        self.write_register(0x30fe, 0x00)
        self.write_register(0x30ff, 0x00)
        self.write_register(0x3100, 0x00)
        self.write_register(0x3101, 0x00)
        self.write_register(0x3102, 0x00)
        self.write_register(0x3103, 0x00)
        self.write_register(0x3104, 0x00)
        self.write_register(0x3105, 0x05)
        self.write_register(0x3106, 0x00)
        self.write_register(0x3107, 0x00)
        self.write_register(0x3108, 0x00)
        self.write_register(0x3109, 0x00)
        self.write_register(0x310a, 0x00)
        self.write_register(0x310b, 0x00)
        self.write_register(0x310c, 0x00)
        self.write_register(0x310d, 0x00)
        self.write_register(0x3099, 0x05)
        self.write_register(0x309a, 0x96)
        self.write_register(0x309b, 0x00)
        self.write_register(0x309c, 0x06)
        self.write_register(0x309d, 0x00)
        self.write_register(0x309e, 0x00)
        self.write_register(0x309f, 0x00)
        self.write_register(0x30a0, 0x00)
        self.write_register(0x30a1, 0x00)
        self.write_register(0x310e, 0x05)
        self.write_register(0x310f, 0x02)
        self.write_register(0x3110, 0x00)
        self.write_register(0x3111, 0x2b)
        self.write_register(0x3112, 0x00)
        self.write_register(0x3113, 0x00)
        self.write_register(0x3114, 0x00)
        self.write_register(0x3115, 0x00)
        self.write_register(0x3116, 0x00)
        self.write_register(0x3117, 0x05)
        self.write_register(0x3118, 0x02)
        self.write_register(0x3119, 0x00)
        self.write_register(0x311a, 0x2c)
        self.write_register(0x311b, 0x00)
        self.write_register(0x311c, 0x00)
        self.write_register(0x311d, 0x00)
        self.write_register(0x311e, 0x00)
        self.write_register(0x311f, 0x00)
        self.write_register(0x30ea, 0x00)
        self.write_register(0x30eb, 0x00)
        self.write_register(0x30ec, 0x00)
        self.write_register(0x30ed, 0x00)
        self.write_register(0x30ee, 0x00)
        self.write_register(0x30ef, 0x00)
        self.write_register(0x30f0, 0x00)
        self.write_register(0x30f1, 0x00)
        self.write_register(0x30f2, 0x00)
        self.write_register(0x313b, 0x03)
        self.write_register(0x313c, 0x31)
        self.write_register(0x313d, 0x00)
        self.write_register(0x313e, 0x07)
        self.write_register(0x313f, 0x00)
        self.write_register(0x3140, 0x68)
        self.write_register(0x3141, 0x00)
        self.write_register(0x3142, 0x34)
        self.write_register(0x3143, 0x00)
        self.write_register(0x31a0, 0x03)
        self.write_register(0x31a1, 0x16)
        self.write_register(0x31a2, 0x00)
        self.write_register(0x31a3, 0x08)
        self.write_register(0x31a4, 0x00)
        self.write_register(0x31a5, 0x7e)
        self.write_register(0x31a6, 0x00)
        self.write_register(0x31a7, 0x08)
        self.write_register(0x31a8, 0x00)
        self.write_register(0x31a9, 0x03)
        self.write_register(0x31aa, 0x16)
        self.write_register(0x31ab, 0x00)
        self.write_register(0x31ac, 0x08)
        self.write_register(0x31ad, 0x00)
        self.write_register(0x31ae, 0x7e)
        self.write_register(0x31af, 0x00)
        self.write_register(0x31b0, 0x08)
        self.write_register(0x31b1, 0x00)
        self.write_register(0x31b2, 0x03)
        self.write_register(0x31b3, 0x16)
        self.write_register(0x31b4, 0x00)
        self.write_register(0x31b5, 0x08)
        self.write_register(0x31b6, 0x00)
        self.write_register(0x31b7, 0x7e)
        self.write_register(0x31b8, 0x00)
        self.write_register(0x31b9, 0x08)
        self.write_register(0x31ba, 0x00)
        self.write_register(0x3120, 0x05)
        self.write_register(0x3121, 0x45)
        self.write_register(0x3122, 0x00)
        self.write_register(0x3123, 0x1d)
        self.write_register(0x3124, 0x00)
        self.write_register(0x3125, 0xa9)
        self.write_register(0x3126, 0x00)
        self.write_register(0x3127, 0x6d)
        self.write_register(0x3128, 0x00)
        self.write_register(0x3129, 0x05)
        self.write_register(0x312a, 0x15)
        self.write_register(0x312b, 0x00)
        self.write_register(0x312c, 0x0a)
        self.write_register(0x312d, 0x00)
        self.write_register(0x312e, 0x45)
        self.write_register(0x312f, 0x00)
        self.write_register(0x3130, 0x1d)
        self.write_register(0x3131, 0x00)
        self.write_register(0x3132, 0x05)
        self.write_register(0x3133, 0x7d)
        self.write_register(0x3134, 0x00)
        self.write_register(0x3135, 0x0a)
        self.write_register(0x3136, 0x00)
        self.write_register(0x3137, 0xa9)
        self.write_register(0x3138, 0x00)
        self.write_register(0x3139, 0x6d)
        self.write_register(0x313a, 0x00)
        self.write_register(0x3144, 0x05)
        self.write_register(0x3145, 0x00)
        self.write_register(0x3146, 0x00)
        self.write_register(0x3147, 0x30)
        self.write_register(0x3148, 0x00)
        self.write_register(0x3149, 0x00)
        self.write_register(0x314a, 0x00)
        self.write_register(0x314b, 0x00)
        self.write_register(0x314c, 0x00)
        self.write_register(0x314d, 0x03)
        self.write_register(0x314e, 0x00)
        self.write_register(0x314f, 0x00)
        self.write_register(0x3150, 0x31)
        self.write_register(0x3151, 0x00)
        self.write_register(0x3152, 0x00)
        self.write_register(0x3153, 0x00)
        self.write_register(0x3154, 0x00)
        self.write_register(0x3155, 0x00)
        self.write_register(0x31d8, 0x05)
        self.write_register(0x31d9, 0x3a)
        self.write_register(0x31da, 0x00)
        self.write_register(0x31db, 0x2e)
        self.write_register(0x31dc, 0x00)
        self.write_register(0x31dd, 0x9e)
        self.write_register(0x31de, 0x00)
        self.write_register(0x31df, 0x7e)
        self.write_register(0x31e0, 0x00)
        self.write_register(0x31e1, 0x05)
        self.write_register(0x31e2, 0x04)
        self.write_register(0x31e3, 0x00)
        self.write_register(0x31e4, 0x04)
        self.write_register(0x31e5, 0x00)
        self.write_register(0x31e6, 0x73)
        self.write_register(0x31e7, 0x00)
        self.write_register(0x31e8, 0x04)
        self.write_register(0x31e9, 0x00)
        self.write_register(0x31ea, 0x05)
        self.write_register(0x31eb, 0x00)
        self.write_register(0x31ec, 0x00)
        self.write_register(0x31ed, 0x00)
        self.write_register(0x31ee, 0x00)
        self.write_register(0x31ef, 0x00)
        self.write_register(0x31f0, 0x00)
        self.write_register(0x31f1, 0x00)
        self.write_register(0x31f2, 0x00)
        self.write_register(0x31f3, 0x00)
        self.write_register(0x31f4, 0x00)
        self.write_register(0x31f5, 0x00)
        self.write_register(0x31f6, 0x00)
        self.write_register(0x31f7, 0x00)
        self.write_register(0x31f8, 0x00)
        self.write_register(0x31f9, 0x00)
        self.write_register(0x31fa, 0x00)
        self.write_register(0x31fb, 0x05)
        self.write_register(0x31fc, 0x00)
        self.write_register(0x31fd, 0x00)
        self.write_register(0x31fe, 0x00)
        self.write_register(0x31ff, 0x00)
        self.write_register(0x3200, 0x00)
        self.write_register(0x3201, 0x00)
        self.write_register(0x3202, 0x00)
        self.write_register(0x3203, 0x00)
        self.write_register(0x3204, 0x00)
        self.write_register(0x3205, 0x00)
        self.write_register(0x3206, 0x00)
        self.write_register(0x3207, 0x00)
        self.write_register(0x3208, 0x00)
        self.write_register(0x3209, 0x00)
        self.write_register(0x320a, 0x00)
        self.write_register(0x320b, 0x00)
        self.write_register(0x3164, 0x05)
        self.write_register(0x3165, 0x14)
        self.write_register(0x3166, 0x00)
        self.write_register(0x3167, 0x0c)
        self.write_register(0x3168, 0x00)
        self.write_register(0x3169, 0x44)
        self.write_register(0x316a, 0x00)
        self.write_register(0x316b, 0x1f)
        self.write_register(0x316c, 0x00)
        self.write_register(0x316d, 0x05)
        self.write_register(0x316e, 0x7c)
        self.write_register(0x316f, 0x00)
        self.write_register(0x3170, 0x0c)
        self.write_register(0x3171, 0x00)
        self.write_register(0x3172, 0xa8)
        self.write_register(0x3173, 0x00)
        self.write_register(0x3174, 0x6f)
        self.write_register(0x3175, 0x00)
        self.write_register(0x31c4, 0x05)
        self.write_register(0x31c5, 0x24)
        self.write_register(0x31c6, 0x01)
        self.write_register(0x31c7, 0x04)
        self.write_register(0x31c8, 0x00)
        self.write_register(0x31c9, 0x05)
        self.write_register(0x31ca, 0x24)
        self.write_register(0x31cb, 0x01)
        self.write_register(0x31cc, 0x04)
        self.write_register(0x31cd, 0x00)
        self.write_register(0x31ce, 0x05)
        self.write_register(0x31cf, 0x24)
        self.write_register(0x31d0, 0x01)
        self.write_register(0x31d1, 0x04)
        self.write_register(0x31d2, 0x00)
        self.write_register(0x31d3, 0x05)
        self.write_register(0x31d4, 0x73)
        self.write_register(0x31d5, 0x00)
        self.write_register(0x31d6, 0xb1)
        self.write_register(0x31d7, 0x00)
        self.write_register(0x3176, 0x05)
        self.write_register(0x3177, 0x10)
        self.write_register(0x3178, 0x00)
        self.write_register(0x3179, 0x56)
        self.write_register(0x317a, 0x00)
        self.write_register(0x317b, 0x00)
        self.write_register(0x317c, 0x00)
        self.write_register(0x317d, 0x00)
        self.write_register(0x317e, 0x00)
        self.write_register(0x317f, 0x05)
        self.write_register(0x3180, 0x6a)
        self.write_register(0x3181, 0x00)
        self.write_register(0x3182, 0xad)
        self.write_register(0x3183, 0x00)
        self.write_register(0x3184, 0x00)
        self.write_register(0x3185, 0x00)
        self.write_register(0x3186, 0x00)
        self.write_register(0x3187, 0x00)
        # Exposure time, in row lengths
        self.write_register(0x100c, 0x7e)
        self.write_register(0x100d, 0x00)
        # Vertical blanking, in row lengths
        self.write_register(0x1012, 0x32)
        self.write_register(0x1013, 0x0b)
        # Enable continuous running
        self.write_register(0x1002, 0x04)

        ## Application settings
        self.fot_length = self.get_fot_length()
        self.trim_restore(rev)
        self.temperature_calibration = self.get_otp_temperature_calibration()
        # Context B settings
        self.write_double_register(0x110a, 0x0578)
        self.write_double_register(0x110c, 0x0000)
        self.write_double_register(0x1105, 0x0000)
        self.write_double_register(0x209A, 0x0000)
        self.context_observe = 'B'
        self.row_length = 0x012c
        self.context_observe = 'A'
        self.write_register(0x401A, 0x08)
        self.write_double_register(0x1103, 0x2c88)

        # Start the sensor
        self.start_img_capture()
        return 0

    def start_img_capture(self, master=True, nb_frames=0, nb_pins=None, exp_pw_sel=None, exp_delay=None):
        '''Start image capturing.

        Preconditions
        -------------
            All image related settings are done.

        Parameters
        ----------
        master : bool (default = True)
            True : select master (internal) exposure control mode
            False : select slave (external) exposure control mode

        nb_frames : int (default = 0) (master mode only)
            0 : run image capturing in continuous mode
            >0 : run image capturing for nb_frames number of frames

        nb_pins : int (default = None) (slave mode only)
            1 : single pin mode (REQ_EXP starts readout)
            2 : dual pin mode (REQ_FRAME starts readout)

        exp_pw_sel : int (default = None) (slave mode only)
            0 : length of exposure with external pulse width
            1 : length of exposure with exp_time register

        exp_delay : int (default = None) (slave mode only)
            delay between request for exposure and actual epxosure in row lengths
        '''
        self.set_i2c_address('sensor')
        self.master_exp_ctrl_mode = master
        # Slave exposure control mode
        if not master:
            self.write_register(0x1003, 0x08)
            if (nb_pins == 1) or (nb_pins == 2):
                bit6 = str(nb_pins - 1)
                bits = f'{self.read_register(0x1001):08b}'
                self.write_register(0x1001, int(bits[0] + bit6 + bits[2:], 2))
            if (exp_pw_sel == 0) or (exp_pw_sel == 1):
                self.write_register(0x1001, ((self.read_register(0x1001) >> 1) << 1) + exp_pw_sel)
            if exp_delay:
                self.write_double_register(0x10d0, abs(exp_delay))

        # Master exposure control mode
        else:
            self.write_register(0x1003, 0x10)
            if nb_frames == 0:
                self.write_register(0x1002, 0x04) # continuous mode
            else:
                self.write_register(0x1002, 0x00) # single frame capture mode
                if self.context_active == 'A':
                    self.write_double_register(0x10f2, nb_frames)
                else:
                    self.write_double_register(0x1111, nb_frames)
            self.write_register(0x10f0, 0x01) # internal trigger)

    def stop_img_capture(self, twhen='frame'):
        '''Stop image capturing (sensor setting).
        
        Parameters
        ----------
        twhen : str (default = frame)
            row : stops at row boundary
            frame : stops at frame boundary
        '''
        self.set_i2c_address('sensor')
        if twhen == 'row':
            self.write_register(0x1003, 0x02)
        elif twhen == 'frame':
            self.write_register(0x1003, 0x04)
        else:
            raise ValueError(f'Unknown stop value: {twhen}')

    @property
    def context_active(self):
        '''Returns the active context.

        Returns
        -------
        str : 
            'A' or 'B': active context
        '''
        self.set_i2c_address('sensor')
        if self.read_register(0x1100) % 2 == 0:
            self._context_active = 'A'
        else:
            self._context_active = 'B'
        return self._context_active

    @context_active.setter
    def context_active(self, context):
        '''Activates the selected context.

        Parameters
        ----------
        context: str
            'A': select context A
            'B': select context B

        Raises
        ------
        ValueError
            When context is not 'A' and not 'B'
        '''
        self.set_i2c_address('sensor')
        context = context.upper()
        if ('A' == context) or ('B' == context):
            context_observe_temp = self.context_observe
            self.context_observe = context
            [w, h, _, _] = self.roi
            self.context_observe = context_observe_temp
            self.write_double_register(0x207d, w)
            self.write_register(0x1100, {'A':0x2, 'B':0x3}[context])
            self.dtMode = self.cfg_to_dtMode[self.bpp][w]
            self.width = w
            self.height = h
            self.widthDMA = w
            self.heightDMA = h
            self.imager.setformat(self.imager.bpp, self.width, self.height, self.widthDMA, self.heightDMA, self.imager.v4l2)
            self._context_active = context
        else:
            raise ValueError(f'Erroneous context selected, {context} not valid')

    @property
    def context_observe(self):
        '''Returns the observed context.

        Returns
        -------
        str : 
            'A' or 'B': observed context
        '''
        return self._context_observe

    @context_observe.setter
    def context_observe(self, context):
        '''Sets the context to observe.

        Parameters
        ----------
        context: str
            'A': select context A
            'B': select context B

        Raises
        ------
        ValueError
            When context is not 'A' and not 'B'
        '''
        if ('A' == context) or ('B' == context):
            self._context_observe = context
        else:
            raise ValueError(f'Erroneous context selected, {context} not valid')

    @property       
    def bpp(self):
        '''Get the programmed bit depth per pixel.

        Returns
        -------
        int : 
            Bit depth for a pixel (8, 10 or 12)
        '''
        self.set_i2c_address('sensor')
        csi2_dtype = self.read_register(0x208D)
        if csi2_dtype == 0x01:
            self._bpp = 8
            return self._bpp
        elif csi2_dtype == 0x02:
            self._bpp = 10
            return self._bpp
        elif csi2_dtype == 0x04:
            self._bpp = 12
            return self._bpp
        else:
            raise ValueError('Unknown MIPI data type.')

    @bpp.setter
    def bpp(self, bit_mode):
        '''Set the bit depth per pixel.

        Parameters
        ----------
        bit_mode : str
            Bit depth for a pixel (8bit, 10bit or 12bit)
        '''
        self.set_i2c_address('sensor')
        self.stop_img_capture()
        if bit_mode == '12bit':
            self.write_register(0x209E, 0x02)
            self.write_register(0x208D, 0x04)
            self._bpp = 12
        elif bit_mode == '10bit':
            self.write_register(0x209E, 0x04)
            self.write_register(0x208D, 0x02)
            self._bpp = 10
        elif bit_mode == '8bit':
            self.write_register(0x209E, 0x06)
            self.write_register(0x208D, 0x01)
            self._bpp = 8
        else:
            raise NotImplementedError(f'Given bit depth of {bit_mode} is not available.')
        self.dtMode = self.cfg_to_dtMode[self._bpp][self.imager.w]
        self.imager.setformat(self._bpp, self.imager.w, self.imager.h, self.imager.bufw, self.imager.bufh, self.imager.v4l2)
        self.start_img_capture(self.master_exp_ctrl_mode)

    @property
    def roi(self):
        '''Get the programmed region of interest.

        Returns
        -------
        list : 
            [0] : width of window (always centered around  horizontal center)
            [1] : height of window
            [2] : horizontal start of window
            [3] : vertical start of window
        '''
        self.set_i2c_address('sensor')
        context = self.context_observe
        if context == 'A':
            hsize = self.read_double_register(0x2008) % 0x400
            vsize = self.read_double_register(0x1087) % 0x800
            hstart = self.read_double_register(0x200a) % 0x400
            vstart = self.read_double_register(0x107d) % 0x800
            self._roi = [2 * hsize, vsize, hstart, vstart]
        elif context == 'B':
            hsize = self.read_double_register(0x2098) % 0x400
            vsize = self.read_double_register(0x110a) % 0x800
            hstart = self.read_double_register(0x209a) % 0x400
            vstart = self.read_double_register(0x1105) % 0x800
            self._roi = [2 * hsize, vsize, hstart, vstart]
        return self._roi

    @roi.setter
    def roi(self, roi):
        '''Set the region of interest.
        
        Parameters
        ----------
        roi : list
            [0] : width (1600, 1280 or 640)
            [1] : height (1400, 1120 or 480)
            [2] : width start, if None ROI is centered around vertical middle
            [3] : height start, if None ROI is centered around horizontal middle
        '''
        self.set_i2c_address('sensor')
        if self.context_observe == self.context_active:
            self.stop_img_capture()
        [w, h, w_start, h_start] = roi
        if ((w == 1600) and (h == 1400)) or ((w == 1280) and (h == 1120)) or ((w == 640) and (h == 480)):
            if h_start == None:
                h_start = (1400 - h) // 2
            if w_start == None:
                w_start = (800 - (w // 2)) // 2
            if (h + h_start > 1400):
                raise ValueError(f'Mira220 has 1400 rows, height ({h}) + h_start ({h_start}) is too high')
            if self.context_observe == 'A':
                self.write_double_register(0x1087, h)
                self.write_double_register(0x107D, h_start)
                self.write_double_register(0x2008, w // 2)
                self.write_double_register(0x200A, w_start)
            elif self.context_observe == 'B':
                self.write_double_register(0x110a, h)
                self.write_double_register(0x1105, h_start)
                self.write_double_register(0x2098, w // 2)
                self.write_double_register(0x209A, w_start)

            if self.context_observe == self.context_active:
                self.write_double_register(0x207D, w)
                self.dtMode = self.cfg_to_dtMode[self.bpp][w]
                self.width = w
                self.height = h
                self.widthDMA = w
                self.heightDMA = h
                self.imager.setformat(self.imager.bpp, self.width, self.height, self.widthDMA, self.heightDMA, self.imager.v4l2)
                self._roi = [w, h, w_start, h_start]
        else:
            raise NotImplementedError(f'Given ROI of {w}x{h} is not available.')
        if self.context_observe == self.context_active:
            self.start_img_capture(self.master_exp_ctrl_mode)

    @property
    def row_length(self):
        '''Get the programmed row length.

        Returns
        -------
        int : 
            row length
        '''
        self.set_i2c_address('sensor')
        context = self.context_observe
        if context == 'A': 
            self._row_length = self.read_double_register(0x102b)
        elif context == 'B': 
            self._row_length = self.read_double_register(0x1113)
        return self._row_length

    @row_length.setter
    def row_length(self, row_length):
        '''Set the row length.

        Parameters
        ----------
        row_length : int
            Row length of the sensor
        '''
        self.set_i2c_address('sensor')
        context = self.context_observe
        if context == 'A': 
            self.write_double_register(0x102b, row_length)
        elif context == 'B': 
            self.write_double_register(0x1113, row_length)
        self._row_length = row_length

    @property
    def fps(self):
        '''Get the programmed frame rate.
        
        Returns
        -------
        float : 
            frame rate
        '''
        self.set_i2c_address('sensor')
        context = self.context_observe
        if context == 'A':
            vsize = self.read_double_register(0x1087) % 0x800
            vblank = self.read_double_register(0x1012)
            self._fps = self.f_clk_in / (self.row_length * (vsize + vblank))
        elif context == 'B':
            vsize = self.read_double_register(0x110a) % 0x800
            vblank = self.read_double_register(0x1103)
            self._fps = self.f_clk_in / (self.row_length * (vsize + vblank))
        return self._fps

    def get_fps_limit(self):
        '''Get the frame rate limits.

        Returns
        -------
        list : 
            [0] : minimum possible frame rate in master mode
            [1] : maximum possible frame rate in master mode
            [2] : minimum vblank register value
            [3] : maximum vblank register value
        '''
        self.set_i2c_address('sensor')
        if self.context_observe == 'A': 
            vsize = self.read_double_register(0x1087) % 0x800
        elif self.context_observe == 'B': 
            vsize = self.read_double_register(0x110a) % 0x800
        row_length = self.row_length

        # Min boundary value
        vblank_max = 0xffff
        fps_min = self.f_clk_in / (row_length * (vsize + vblank_max))

        # Max boundary value
        vblank_min_cte = self.read_double_register(0x1009) + self.read_double_register(0x1006)
        vblank_min = int(self.fot_length / row_length) + 1 + vblank_min_cte
        fps_max = self.f_clk_in / (row_length * (vsize + vblank_min))

        return [fps_min, fps_max, vblank_min, vblank_max]

    @fps.setter
    def fps(self, fps):
        '''Set the frame rate.

        Parameters
        ----------
        fps : float
            Frame rate of the sensor
        '''
        self.set_i2c_address('sensor')
        context = self.context_observe
        if context == 'A':  
            vsize = self.read_double_register(0x1087) % 0x800
        elif context == 'B':
            vsize = self.read_double_register(0x110a) % 0x800
        row_length = self.row_length
        vblank = int(self.f_clk_in // (row_length * fps)) - vsize

        # Min/max boundary value
        [fps_min, fps_max, vblank_min, vblank_max] = self.get_fps_limit()

        # Write vblank register
        if vblank < vblank_min:
            vblank = vblank_min
            self._fps = fps_max
            raise ValueError(f'The frame rate of {fps_max} is out of the limits')
        elif vblank > vblank_max:
            vblank = vblank_max
            self._fps = fps_min
            raise ValueError(f'The frame rate of {fps_min} is out of the limits')
        else:
            self._fps = fps
        
        if context == 'A': 
            self.write_double_register(0x1012, vblank)
        elif context == 'B':
            self.write_double_register(0x1103, vblank)

    @property
    def analog_gain(self):
        '''Get the programmed analog gain.

        Returns
        -------
        int : 
            analog gain
        '''
        self.set_i2c_address('sensor')
        context = self.context_observe
        if context == 'A':  
            self._analog_gain = 8 // self.read_register(0x400A)
        elif context == 'B':  
            self._analog_gain = 8 // self.read_register(0x401A)
        return self._analog_gain

    @analog_gain.setter
    def analog_gain(self, gain):
        '''Set analog gain and related registers.

        Parameters
        ----------
        gain : int
            Analog gain (1, 2 or 4)
        '''
        self.set_i2c_address('sensor')
        if (gain == 1) or (gain == 2) or (gain == 4):
            self._analog_gain = 8 // gain
            if self.context_observe == 'A':
                self.write_register(0x400A, self._analog_gain)
            elif self.context_observe == 'B':
                self.write_register(0x401A, self._analog_gain)
            if len(self.otp_gain_trims) > 0:
                self.write_register(0x4009, self.otp_gain_trims[gain // 2])
        else:
            raise NotImplementedError(f'Only x1, x2 or x4 is supported. Not x{gain}.')

    @property
    def digital_gain(self):
        return None
    
    @digital_gain.setter
    def digital_gain(self, gain):
        self.imager.pr('Remark: Mira220 has no digital gain')
    
    @property
    def exposure_us(self):
        '''Get the programmed exposure time.

        Returns
        -------
        float : 
            exposure time in us
        '''
        self.set_i2c_address('sensor')
        context = self.context_observe
        time_conversion = self.row_length / self.f_clk_in # in seconds
        if context == 'A':
            exposure_time = self.read_double_register(0x100c) * time_conversion * 1e6
        elif context == 'B':
            exposure_time = self.read_double_register(0x1115) * time_conversion * 1e6
        [exposure_time_max, _] = self.get_exposure_limit()
        if exposure_time > exposure_time_max: # sensor takes automatically the max possible but keeps the register value
            exposure_time = exposure_time_max
        self._exposure_time = exposure_time
        return self._exposure_time

    def get_exposure_limit(self):
        '''Get the exposure time limit.

        Returns
        -------
        list : 
            [0] : maximum possible exposure time in us in master mode
            [1] : maximum exposure register value
        '''
        self.set_i2c_address('sensor')
        context = self.context_observe
        row_length = self.row_length
        if context == 'A':
            vsize = self.read_double_register(0x1087) % 0x800
            vblank = self.read_double_register(0x1012)
        elif context == 'B':
            vsize = self.read_double_register(0x110a) % 0x800
            vblank = self.read_double_register(0x1103)
        time_conversion = row_length / self.f_clk_in
        exposure_length_max = int(((row_length * (vsize + vblank) - self.fot_length) / self.f_clk_in) / time_conversion)
        exposure_time_max = exposure_length_max * time_conversion * 1e6
        return [exposure_time_max, exposure_length_max]

    @exposure_us.setter
    def exposure_us(self, time_us):
        '''Set the exposure time in us in master mode.

        Parameters
        ----------
        exposure : float
            Exposure time of the sensor
        '''
        self.set_i2c_address('sensor')
        context = self.context_observe
        reg_list = {'A':0x100c, 'B':0x1115}
        [exposure_time_max, exposure_length_max] = self.get_exposure_limit()
        if time_us > exposure_time_max:
            time_us = exposure_time_max
            self.write_double_register(reg_list[context], int(exposure_length_max))
            raise ValueError(f'The exposure time of {time_us}us is out of the limits')
        elif time_us < 0:
            time_us = 0
            self.write_double_register(reg_list[context], 0)
            raise ValueError(f'The exposure time of {time_us}us is out of the limits')
        else:
            time_conversion = self.row_length / self.f_clk_in
            exposure_length = round(time_us / 1e6 / time_conversion)
            self.write_double_register(reg_list[context], int(exposure_length))
        self._exposure_time = time_us

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
        row_time = (self.row_length / self.f_clk_in) * 1e6
        return lines * row_time
    
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
        row_time = (self.row_length / self.f_clk_in) * 1e6
        return int(round(time_us / row_time))

    @property
    def hflip(self):
        '''Get the programmed horizontal flip.

        Returns
        -------
        int : 
            0 if no flipping, 1 if horizontal flipped.
        '''
        self.set_i2c_address('sensor')
        context = self.context_observe
        self._hflip = self.read_register({'A':0x209c, 'B':0x209d}[context])
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
        context = self.context_observe
        self.write_register({'A':0x209c, 'B':0x209d}[context], hflip)
        self._hflip = hflip

    @property
    def vflip(self):
        '''Get the programmed vertical flip.

        Returns
        -------
        int : 
            0 if no flipping, 1 if vertical flipped.
        '''
        self.set_i2c_address('sensor')
        self._vflip = self.read_register(0x1095)
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
        self.write_register(0x1095, vflip)
        self._vflip = vflip

    @property
    def rnc(self):
        '''Get the programmed rownoise correction.

        Returns
        -------
        list : 
            [0] : 1 if enabled
            [1] : flat field target value
        '''
        self.set_i2c_address('sensor')
        enable = self.read_register(0x204B) % 2
        flat_field_target = self.read_double_register(0x205B)
        self._rnc = [enable, flat_field_target]
        return self._rnc

    @rnc.setter
    def rnc(self, rnc):
        '''Configures rownoise correction.
        
        Parameters
        ----------
        rnc : list
            [0] : if True, enables rownoise correction.
            [1] : flat field target. If None, value isn't changed.            
        '''
        self.set_i2c_address('sensor')
        [enable, flat_field_target] = rnc
        if enable:
            self.write_register(0x204B, 0x3)
        else:
            self.write_register(0x204B, 0x0)
        self._rnc[0] = enable

        if flat_field_target != None: # Need to check
            self.write_double_register(0x205B, flat_field_target)
            max_counter = 4095 - flat_field_target - 50
            self.write_double_register(0x3215, max_counter)
            self.write_double_register(0x322B, max_counter)
            self._rnc[1] = flat_field_target

    @property
    def dpc(self):
        '''Get the programmed properties of the defect correction module.

        Returns
        -------
        list : 
            [0] : pixel correction mode
            [1] : pixel correction algorithm
            [2] : low limit boundary
            [3] : high limit boundary
            [4] : mode setting for interpretation of high limit boundary
        '''
        self.set_i2c_address('sensor')
        mode = ['Off', 'Kernel', 'Off','Line'][int(self.read_register(0x24DC) % (2 ** 2))]
        algo = ['Median', 'Mean', 'Max', 'Min'][int((self.read_register(0x24DC) >> 4) % (2 ** 2))]
        limit_l = self.read_register(0x24DD)
        limit_h = self.read_register(0x24DE)
        limit_h_mode = ['Mode 0', 'Mode 1'][self.read_register(0x24DF) % 2]
        self._dpc = [mode, algo, limit_l, limit_h, limit_h_mode]
        return self._dpc

    @dpc.setter
    def dpc(self, dpc):
        '''Configures the defect pixel correction module.

        Parameters
        ----------
        dpc : list
            [0] : pixel correction mode
                    'OFF': turn off pixel correction mode
                    'LINE': single line correction mode
                    'KERNEL': kernel (multi-line) correction mode
            [1] : pixel correction algorithm. Ignored when mode is 'OFF'.
                    'MEDIAN': use median value of surrounding pixels
                    'MEAN': use mean value of surrounding pixels
                    'MAX': use maximum value of surrounding pixels
                    'MIN': use minimum value of surrounding pixels
            [2] : low limit boundary. A higher value results in more aggressive pixel correction.
            [3] : high limit boundary. A higher value results in more aggressive pixel correction.
            [4] : mode setting for interpretation of high limit boundary (0 or 1)

        Raises
        ------
        ValueError
            When mode is not 'OFF' and not 'LINE' and not 'KERNEL'

        ValueError
            When algo is not 'MEDIAN' and not 'MEAN' and not 'MAX' and not 'MIN'
        '''
        self.set_i2c_address('sensor')
        [mode, algo, limit_l, limit_h, limit_h_mode] = dpc

        if (mode != None) or (algo != None):
            dpc_old = self.dpc
            if mode != None:
                mode = mode.upper()
            else:
                mode = dpc_old[0].upper()
            
            if algo != None:
                algo = algo.upper()
            else:
                algo = dpc_old[1].upper()

            # Make sure defects are counted
            if (mode != 'OFF'):
                self.write_register(0x24E3, 0x01)
            else:
                self.write_register(0x24E3, 0x00)

            # Defect pixel correction settings
            if 'OFF' == mode:
                dc_mode = 0x0
                self._dpc[0] = mode
            elif 'KERNEL' == mode:
                dc_mode = 0x1
                self._dpc[0] = mode
            elif 'LINE' == mode:
                dc_mode = 0x3
                self._dpc[0] = mode
            else:
                raise ValueError(f'Unknown defect pixel correction mode {mode}')

            if 'MEDIAN' == algo:
                dc_replacement = 0x0
                self._dpc[1] = algo
            elif 'MEAN' == algo:
                dc_replacement = 0x1
                self._dpc[1] = algo
            elif 'MIN' == algo:
                dc_replacement = 0x2
                self._dpc[1] = algo
            elif 'MAX' == algo:
                dc_replacement = 0x3
                self._dpc[1] = algo
            else:
                raise ValueError(f'Unknown defect pixel correction algorithm {algo}')

            self.write_register(0x24DC, (dc_replacement << 4) + dc_mode)

        # Defect pixel detection settings
        if limit_l != None:
            self.write_register(0x24DD, limit_l)
            self._dpc[2] = limit_l
        if limit_h != None:
            self.write_register(0x24DE, limit_h)
            self._dpc[3] = limit_h
        if limit_h_mode != None:
            self.write_register(0x24DF, limit_h_mode)
            self._dpc[4] = limit_h_mode

    @property
    def test_image(self):
        '''Get the programmed test image pattern.

        Returns
        -------
        str : 
            The test image pattern
        '''
        self.set_i2c_address('sensor')
        value = self.read_register(0x2091)
        if value == 0:
            self._test_image = 'Off'
        elif value == 1:
            self._test_image = 'Vertical'
        elif value == 17:
            self._test_image = 'Diagonal'
        elif value == 65:
            self._test_image = 'Walking 1'
        elif value == 81:
            self._test_image = 'Walking 0'
        return self._test_image

    @test_image.setter
    def test_image(self, pattern):
        '''Configures the test image.

        Parameters
        ----------
        pattern : str
            The test image pattern
        '''
        self.set_i2c_address('sensor')
        if pattern == 'Off':
            self.write_register(0x2091, 0)
        elif pattern == 'Vertical':
            self.write_register(0x2091, 1)
        elif pattern == 'Diagonal':
            self.write_register(0x2091, 17)
        elif pattern == 'Walking 1':
            self.write_register(0x2091, 65)
        elif pattern == 'Walking 0':
            self.write_register(0x2091, 81)
        else:
            raise ValueError(f'The {pattern} test image is unknown.')
        self._test_image = pattern

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
        '''Get the programmed settings of the illumination trigger.

        Returns
        -------
        list : 
            [0] : 1 if enabled
            [1] : Delay in row lengths
            [2] : Length high in row lengths
            [3] : Length low in row lengths
            [4] : Number of illum_trigger pulses
            [5] : Idle value
            [6] : Polarity
        '''
        self.set_i2c_address('sensor')
        delay = ((-2 * self.read_register(0x10d4)) + 1) * self.read_double_register(0x10d2)
        pw_h = self.read_double_register(0x10d5)
        enable = self.read_register(0x10d7)
        polarity = self.read_register(0x10d8) >> 1
        idle_val = self.read_register(0x10d9) >> 2
        nb_pulses = self.read_register(0x10da)
        pw_l = self.read_double_register(0x10db)
        self._illumination_trigger = [enable, delay, pw_h, pw_l, nb_pulses, idle_val, polarity]
        return self._illumination_trigger

    @illumination_trigger.setter
    def illumination_trigger(self, illumination_trigger):
        '''Configure illumination trigger pin.
        
        Parameters
        ----------
        illumination_trigger : list
            [0] : Enable the trigger
            [1] : Delay expresssed in row lengths (default = 0)
                    - In master (interal) exposure mode:
                        Negative delay will result in illum_trigger enabled before
                        integration starts
                        Positive delay will result in illum_trigger enabled after
                        integration starts
                    - In slave (external) exposure mode:
                        Negative or positive delay will both result in illum trigger
                        enabled AFTER integration starts
            [2] : Length high in row lengths (default = 0)
                    If 0, illum_trigger wil follow integration/exposure time.
                    The time illum_trigger is high.
            [3] : Length low in row lengths (default = 0)
                    Only needed if nb_pulses is 2 or higher.
                    The time illum_trigger is low.
            [4] : Number of illum_trigger pulses (default = 1)
                    Between 1 and 15 (both values included)
            [5] : Value of illum_trigger when disabled or image capturing has stopped (default = 0)
                    It ignores polarity setting.
            [6] : Polarity (default = 1)
                    0 : active low  (0 = on, 1 = off)
                    1 : active high (0 = off, 1 = on)
        
        Raises
        ------
        ValueError
            When nb_pulses is below 1 or above 255
            When pw_h or pw_l is negative
        '''
        self.set_i2c_address('sensor')
        [enable, delay, pw_h, pw_l, nb_pulses, idle_val, polarity] = illumination_trigger
        if delay == None:
            delay = 0
        if pw_h == None:
            pw_h = 0
        if pw_l == None:
            pw_l = 0
        if nb_pulses == None:
            nb_pulses = 1 
        if idle_val == None:
            idle_val = 0
        if polarity == None:
            polarity = 1 

        dneg = 0
        if (nb_pulses < 1) or (nb_pulses > 15):
            raise ValueError('At least 1 pulse needed. To disable put enable=0')
        if pw_h < 0:
            raise ValueError('pw_h should be 0 or positive')
        if pw_l < 0:
            raise ValueError('pw_l should be 0 or positive')
        if delay < 0:
            dneg = 1
            delay = abs(delay)
        self.write_double_register(0x10d2, delay)
        self.write_register(0x10d4, dneg)
        self.write_double_register(0x10d5, pw_h)
        self.write_register(0x10d7, enable)
        self.write_register(0x10d8, polarity << 1)
        self.write_register(0x10d9, idle_val << 2)
        self.write_register(0x10da, nb_pulses)
        self.write_double_register(0x10db, pw_l)
        self._illumination_trigger = illumination_trigger

    @property
    def sensor_temperature(self):
        '''Reads uncalibrated on-chip temperature sensor value and converts it to degrees Celcius.

        Returns
        -------
        float : 
            Temperature of sensor in degrees Celcius 
        '''   
        self.set_i2c_address('sensor')
        signal_level = self.read_double_register(0x3188) % 0x1000
        reset_level = self.read_double_register(0x318E) % 0x400
        context_observe_temp = self.context_observe
        self.context_observe = self.context_active
        gain = self.analog_gain
        self.context_observe = context_observe_temp
        if self.temperature_calibration == None:
            self._sensor_temperature = self.sensor_temperature_conversion(signal_level, reset_level, gain)
        else:
            self._sensor_temperature = self.temperature_calibration * self.sensor_temperature_conversion(signal_level, reset_level, gain)
        return self._sensor_temperature

    def sensor_temperature_conversion(self, signal, reset, gain):
        '''Converts temperature register value to degrees Celcius.

        Parameters
        ----------
        signal : int
            Temperature sensor signal value VPTAT

        reset : int
            Temperature sensor reset value VREF
        
        gain : int
            The analog gain of the sensor (1, 2 or 4)

        Returns
        -------
        float : 
            Temperature in degrees Celcius 
        ''' 
        lsb = 0.181 # mV/DN
        mvc = 1.63  # mV/degC
        v25 = 140   # mV @ 25degC
        tsens_sig = self.gray_to_dec(signal)
        tsens_rst = self.gray_to_dec(reset)
        tsens = (tsens_sig - tsens_rst) / gain
        temperature_degrees = ((tsens * lsb) - v25) / mvc + 25
        return temperature_degrees

    @property
    def pcb_temperature(self):
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

    def gray_to_dec(self, gray):
        '''Converts Gray encoded number to decimal number.

        Parameters
        ----------
        gray : int
            Gray encoded number

        Returns
        -------
        int : 
            Decoded number
        '''
        mask = gray
        while(mask):
            mask = mask >> 1
            gray ^= mask
        return gray

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

    @property
    def ulps(self):
        '''Get the MIPI ultra low power state.

        Returns
        -------
        list : 
            [0] : enable
            [1] : lane
        '''
        return self._ulps

    @ulps.setter
    def ulps(self, ulps):
        '''Set the MIPI ultra low power state.

        Parameters
        ----------
        ulps : list
            [0] : enable
                False : disable MIPI ULPS on selected lane
                True : enable MIPI ULPS on selected lane
            [1] : lane : str (default = 'BOTH')
                'CLOCK' : select clock lane for ULPS operation
                'DATA' : select data lanes for ULPS operation
                'BOTH' : select clock and data lanes for ULPS operation
        
        Raises
        ------
        ValueError
            When lane is not 'CLOCK' and not 'DATA' and not 'BOTH'
        '''
        [enable, lane] = ulps
        if lane == None:
            lane = 'BOTH'
        if (lane != 'CLOCK') and (lane != 'DATA') and (lane != 'BOTH'):
            raise ValueError(f'Wrong MIPI lane selected for MIPI operation, {lane} not valid.')

        self.set_i2c_address('sensor')
        if (lane == 'CLOCK') or (lane == 'BOTH'):
            if enable:
                self.write_register(0x6014, 0x01)
            else:
                self.write_register(0x6014, 0x02)
                self.write_register(0x6014, 0x00)
        if (lane == 'DATA') or (lane == 'BOTH'):
            if enable:
                self.write_register(0x6015, 0x55)
            else:
                self.write_register(0x6015, 0xaa)
                self.write_register(0x6015, 0x00)
        self._ulps = [enable, lane]

    @property
    def bsp(self):
        '''Get black sun protection status.

        Returns
        -------
        bool :
            enable
        '''
        self.set_i2c_address('sensor')
        value = self.read_register(0x4006)
        if value == 0x08:
            self._bsp = 1
        elif value == 0x0f:
            self._bsp = 0
        return self._bsp

    @bsp.setter
    def bsp(self, enable):
        '''Configures black sun protection.

        Parameters
        ----------
        enable : bool
            True : enable BSP
            False : disable BSP
        '''
        self.set_i2c_address('sensor')
        if enable:
            self.write_register(0x4006, 0x08)
        else:
            self.write_register(0x4006, 0x0f)
        self._bsp = enable

    @property
    def mipi_speed(self):
        '''Get the programmed MIPI speed.

        Returns
        -------
        int :
            MIPI D-PHY lane speed expressed in Mbit/s/lane
        '''
        return self._mipi_speed

    @mipi_speed.setter
    def mipi_speed(self, mipi_speed):
        '''Configures the MIPI speed. 
        
        Parameters
        ----------
        lane_speed : int
            MIPI D-PHY lane speed expressed in Mbit/s/lane. 100 and 80 do not work on the EVK.
        '''
        self.set_i2c_address('sensor')
        self.stop_img_capture()
        self.write_register(0x6006, 0x00)
        reg_list = [0x5004, 0x5086, 0x5087, 0x5088, 0x5090, 0x5091, 0x5092, 0x5093, 0x5094, 0x5095, 0x5096, 0x5097, 0x5098,
                    0x5004, 0x2066, 0x2067, 0x206E, 0x206F, 0x20AC, 0x20AD, 0x2076, 0x2077, 0x20B4, 0x20B5, 0x2078, 0x2079,
                    0x20B6, 0x20B7, 0x207A, 0x207B, 0x20B8, 0x20B9]
        value_sequence = {1500: [0x01, 0x02, 0x4E, 0x00, 0x00, 0x08, 0x14, 0x0F, 0x06, 0x32, 0x0E, 0x00, 0x11, 0x00, 0x6C,
                                 0x07, 0x7E, 0x06, 0x7E, 0x06, 0xC8, 0x00, 0xC8, 0x00, 0x1E, 0x04, 0x1E, 0x04, 0xD4, 0x04,
                                 0xD4, 0x04],
                          1400: [0x01, 0x02, 0x48, 0x00, 0x00, 0x07, 0x14, 0x0E, 0x06, 0x2F, 0x0E, 0x00, 0x10, 0x00, 0x00,
                                 0x08, 0x80, 0x07, 0x80, 0x07, 0x80, 0x04, 0x80, 0x04, 0x1E, 0x05, 0x1E, 0x05, 0xA0, 0x05,
                                 0xA0, 0x05], 
                          1300: [0x01, 0x02, 0x43, 0x00, 0x00, 0x07, 0x12, 0x0D, 0x05, 0x2C, 0x0D, 0x00, 0x0F, 0x00, 0x00,
                                 0x09, 0x80, 0x08, 0x80, 0x08, 0x00, 0x05, 0x00, 0x05, 0x5E, 0x05, 0x5E, 0x05, 0xE0, 0x05,
                                 0xE0, 0x05],
                          1200: [0x01, 0x02, 0x3E, 0x00, 0x00, 0x06, 0x11, 0x0D, 0x05, 0x28, 0x0C, 0x00, 0x0F, 0x00, 0x00,
                                 0x0A, 0x80, 0x09, 0x80, 0x09, 0x00, 0x05, 0x00, 0x05, 0x1E, 0x05, 0x1E, 0x05, 0xD4, 0x05,
                                 0xD4, 0x05], 
                          1100: [0x01, 0x02, 0x39, 0x00, 0x00, 0x06, 0x0F, 0x0C, 0x04, 0x25, 0x0B, 0x00, 0x0E, 0x00, 0x00,
                                 0x0B, 0x80, 0x0A, 0x80, 0x0A, 0x00, 0x06, 0x00, 0x06, 0x1E, 0x06, 0x1E, 0x06, 0xD4, 0x06,
                                 0xD4, 0x06], 
                          1000: [0x01, 0x02, 0x34, 0x00, 0x00, 0x05, 0x0E, 0x0B, 0x04, 0x22, 0x0B, 0x00, 0x0D, 0x00, 0x00,
                                 0x0C, 0x80, 0x0B, 0x80, 0x0B, 0x00, 0x06, 0x00, 0x06, 0x1E, 0x06, 0x1E, 0x06, 0xD4, 0x06,
                                 0xD4, 0x06], 
                          900: [0x01, 0x02, 0x2E, 0x00, 0x00, 0x05, 0x0D, 0x0A, 0x03, 0x1F, 0x0A, 0x00, 0x0C, 0x00, 0x00,
                                0x0D, 0x80, 0x0C, 0x80, 0x0C, 0x00, 0x07, 0x00, 0x07, 0x1E, 0x07, 0x1E, 0x07, 0xD4, 0x07,
                                0xD4, 0x07], 
                          800: [0x01, 0x02, 0x53, 0x00, 0x02, 0x09, 0x17, 0x10, 0x07, 0x35, 0x0F, 0x01, 0x18, 0x00, 0x00,
                                0x10, 0x80, 0x0E, 0x80, 0x0E, 0x00, 0x09, 0x00, 0x09, 0x1E, 0x09, 0x1E, 0x09, 0xD4, 0x09,
                                0xD4, 0x09], 
                          700: [0x01, 0x02, 0x48, 0x00, 0x02, 0x08, 0x14, 0x0F, 0x06, 0x2F, 0x0E, 0x01, 0x16, 0x00, 0x00,
                                0x14, 0x80, 0x13, 0x80, 0x13, 0x00, 0x11, 0x00, 0x11, 0x1E, 0x11, 0x1E, 0x11, 0xD4, 0x11,
                                0xD4, 0x11], 
                          600: [0x01, 0x02, 0x7D, 0x00, 0x04, 0x0E, 0x23, 0x17, 0x0A, 0x50, 0x15, 0x03, 0x2B, 0x00, 0x00,
                                0x18, 0x00, 0x16, 0x00, 0x16, 0x00, 0x12, 0x00, 0x12, 0x1E, 0x12, 0x1E, 0x12, 0xD4, 0x12,
                                0xD4, 0x12], 
                          500: [0x01, 0x02, 0x68, 0x00, 0x04, 0x0C, 0x1D, 0x14, 0x09, 0x42, 0x12, 0x03, 0x28, 0x00, 0x00,
                                0x28, 0x00, 0x20, 0x00, 0x20, 0x00, 0x1A, 0x00, 0x1A, 0x1E, 0x1A, 0x1E, 0x1A, 0xD4, 0x1A,
                                0xD4, 0x1A], 
                          400: [0x01, 0x02, 0x53, 0x00, 0x04, 0x0A, 0x18, 0x11, 0x07, 0x35, 0x0F, 0x03, 0x25, 0x00, 0x00,
                                0x30, 0x00, 0x28, 0x00, 0x28, 0x00, 0x22, 0x00, 0x22, 0x1E, 0x22, 0x1E, 0x22, 0xD4, 0x22,
                                0xD4, 0x22], 
                          300: [0x01, 0x02, 0x7D, 0x00, 0x06, 0x11, 0x25, 0x19, 0x0A, 0x50, 0x15, 0x07, 0x45, 0x00, 0x00,
                                0x40, 0x00, 0x30, 0x00, 0x30, 0x00, 0x24, 0x00, 0x24, 0x1E, 0x24, 0x1E, 0x24, 0xD4, 0x24,
                                0xD4, 0x24],
                          200: [0x01, 0x02, 0x53, 0x00, 0x06, 0x0C, 0x1B, 0x13, 0x07, 0x35, 0x0F, 0x07, 0x3F, 0x00, 0x00,
                                0x40, 0x00, 0x38, 0x00, 0x38, 0x00, 0x30, 0x00, 0x30, 0x1E, 0x34, 0x1E, 0x34, 0xD4, 0x34,
                                0xD4, 0x34],
                          100: [0x01, 0x02, 0x53, 0x00, 0x08, 0x10, 0x21, 0x17, 0x07, 0x35, 0x0F, 0x0F, 0x73, 0x00, 0x00,
                                0x50, 0x00, 0x4C, 0x00, 0x4C, 0x00, 0x44, 0x00, 0x44, 0x1E, 0x44, 0x1E, 0x44, 0xD4, 0x44,
                                0xD4, 0x44],
                          80: [0x01, 0x02, 0x42, 0x00, 0x08, 0x0E, 0x1D, 0x15, 0x05, 0x2B, 0x0D, 0x0F, 0x71, 0x00, 0x00,
                               0x60, 0x00, 0x58, 0x00, 0x58, 0xC8, 0x50, 0xC8, 0x50, 0x1E, 0x54, 0x1E, 0x54, 0xD4, 0x54,
                               0xD4, 0x54]}
        for i in range(0, len(reg_list)):
            self.write_register(reg_list[i], value_sequence[mipi_speed][i])
        
        self.write_register(0x6006, 0x01)
        new_row_length = np.ceil(self.row_length * self.mipi_speed / mipi_speed)
        self.row_length = new_row_length 
        self.start_img_capture(self.master_exp_ctrl_mode)
        self._mipi_speed = mipi_speed

    def set_uc_timing_triggers(self, t_exp_us, fps, cont=True, nb_pins=2):
        '''Configures the slave mode external triggers applied by the microcontroller.

        Parameters
        ----------
        t_exp_us : float
            The exposure time for the sensor
        
        fps : float
            The frame rate for the sensor
        
        cont : bool (default = True)
            True : multiple triggers
            False : only 1 trigger
        
        nb_pins : int (default = 2)
            1 : single pin mode (REQ_EXP starts readout)
            2 : dual pin mode (REQ_FRAME starts readout)
        '''
        if self.imager.getUcFirmware() >= 8:
            self.set_i2c_address('uC')
            self.write_register(17, 0) # Disable triggers
            if cont:
                self.write_register(22, 0) # Multiple triggers
            else:
                self.write_register(22, 1) # only 1 trigger      
            if nb_pins == 2:
                self.write_register(23, 0) # Dual pin mode
                reg_exp = int(t_exp_us / 99.8643)
                self.write_register(18, (reg_exp >> 8)) # [15:8] exp time
                self.write_register(19, (reg_exp & 0xff)) # [7:0] exp time
                reg_frame = int((1e6 / fps) / 1007.327)
                self.write_register(20, (reg_frame >> 8)) # [15:8] frame time
                self.write_register(21, (reg_frame & 0xff)) # [7:0] frame time
            elif nb_pins == 1:
                self.write_register(23, 1) # Single pin mode
                reg_exp_high = int(t_exp_us / 1007.327)
                self.write_register(24, (reg_exp_high >> 8)) # [15:8] exp time high
                self.write_register(25, (reg_exp_high & 0xff)) # [7:0] exp time high
                reg_exp_low = int(((1e6 / fps) - (reg_exp_high * 1007.327)) / 1007.327)
                self.write_register(26, (reg_exp_low >> 8)) # [15:8] exp time low
                self.write_register(27, (reg_exp_low & 0xff)) # [7:0] exp time low
            else:
                raise NotImplementedError(f'Amount of pins {nb_pins} is not implemented')
            self.write_register(17, 1) # Enable triggers
        
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
        '''Write lower 8 bits of value to given address and upper 8 bits to address + 1.
        
        Parameters
        ----------
        address : int
            Address of register

        value : int
            Value to write
        '''
        self.write_register(address, value % 0x100)
        self.write_register(address + 1, value >> 8)

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
        return (self.read_register(address + 1) << 8) + self.read_register(address)

    def read_all_registers(self, ic='sensor', dtype='int'):
        ''' Return all register adresses with their current values

        Returns:
            dict: {regaddress : regvalues}
        '''
        self.set_i2c_address(ic)
        d = OrderedDict()
        if dtype == 'int':
            for i in range(0, 0x6067):
                d[i] = self.read_register(i) 
        elif dtype == 'hex':
            for i in range(0, 0x6067):
                d[hex(i)] = hex(self.read_register(i))
        return d
    
    def set_analog_gain(self, gain): #Should be removed, still in abstract class
        self.analog_gain = gain

    def set_digital_gain(self, gain): #Should be removed, still in abstract class
        self.digital_gain = gain

    def set_exposure_us(self, time_us): #Should be removed, still in abstract class
        self.exposure_us = time_us
