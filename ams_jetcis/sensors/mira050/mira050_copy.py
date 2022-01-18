import time
from ams_jetcis.sensors.sensor import Sensor
import modes
# from ams_jetcis.sensors.mira050.config_files import config_800_600_10b_mira050_normal_gain1_patch, config_800_600_10b_mira050_normal_gain2_patch, config_800_600_10b_mira050_normal_gain4_patch


class Mira050(Sensor):
    """
    Implementation of Sensor class for Mira050.
    big endian register access. --> largest byte in lowest address
    """

    def __init__(self, imagertools) -> None:
        super().__init__(imagertools)
        self.name = 'Mira050'
        self.bpp = 10
        self.width = 600
        self.height = 800
        self.widthDMA = 608
        self.heightDMA = 800
        self.bpp = 10
        self.fps = 30
        self.dtMode = 0
        self.sensor_i2c = 54
        self.sensor_type = 1
        self.bmode = '10bit'
        self.dgain = 1
        self.again = 1
        self.bsp = 1
        self._mirror = 0
        self.exposure = 1000
        self.pcorrection = 1
        self.blevel = 50
        self._state = {'analog gain': self.again,
                       'digital gain': self.dgain,
                       'bit mode': self.bmode,
                       'black sun protection': self.bsp,
                       'exposure [us]': self.exposure,
                       'pixel corrections': self.pcorrections,
                       'mirror': self._mirror,
                       'rows': self.width,
                       'cols': self.cols,
                       'name': self.name}

        # set the imager format
        self.imager.setformat(self.bpp, self.width,
                              self.height, self.widthDMA, self.heightDMA, True)
        
        # set starting state
        self.init_state()


    def init_sensor(self, bit_mode='10bit', analog_gain=1):
        """ 
        supported bit modes: '10bit', '12bit', '10bithighspeed'
        supported analog gains: 1 2 4
        """

        if not isinstance(analog_gain, int):
            analog_gain = int(analog_gain)

        if bit_mode == '12bit':
            self.bpp = 12
            if analog_gain == 1:
                modes.config_800_600_12b_mira050_gain1_patch()
            elif analog_gain == 2:
                modes.config_800_600_12b_mira050_gain2_patch()
            elif analog_gain == 4:
                modes.config_800_600_12b_mira050_gain4_patch()
            else:
                raise NotImplementedError('this mode is not implemented')
            self.dtMode = 0
        elif bit_mode == '10bit':
            self.dtMode = 2
            self.bpp = 10
            if analog_gain == 1:
                modes.config_800_600_10b_mira050_gain1_patch()
            elif analog_gain == 2:
                modes.config_800_600_10b_mira050_gain2_patch()
            elif analog_gain == 4:
                modes.config_800_600_10b_mira050_gain4_patch()
            else:
                raise NotImplementedError('this mode is not implemented')
        elif bit_mode == '10bithighspeed':
            self.dtMode = 2
            self.bpp = 10
            if analog_gain == 1:
                modes.config_800_600_10b_highspeed_mira050_gain1_patch()
            elif analog_gain == 2:
                modes.config_800_600_10b_highspeed_mira050_gain2_patch()
            elif analog_gain == 4:
                modes.config_800_600_10b_highspeed_mira050_gain4_patch()
            else:
                raise NotImplementedError('this mode is not implemented')
        else:
            raise NotImplementedError('this mode is not implemented')

        self.again = analog_gain
        self.bmode = bit_mode

    @property
    def state(self):
        """
        get the state
        """

        return self._state

    @state.setter
    def state(self, vals):
        """
        """
        old_vals = self.state.copy()
        
        # set analog gain and bit mode
        if vals['analog gain'] != old_vals['analog gain'] or\
            vals['bit mode'] != old_vals['bit mode']:
            self.init_sensor(vals['bit mode'], vals['analog gain'])

        # set black sun protection
        if vals['black sun protection'] != old_vals['black sun protection']:
            self.bsp = vals['black sun protection']
        
        # set pixel corrections
        if vals['pixel correction'] != old_vals['pixel correction']:
            self.pixel_corection = vals['pixel correction']
        
        # set digital gain
        if vals['digital gain'] != old_vals['digital gain']:
            self.digital_gain = vals['digital gain']

        # set mirror
        if vals['mirror'] != old_vals['mirror']:
            self.mirror = vals['mirror']

        # set exposure
        if vals['exposure'] != old_vals['exposure']:
            self.exposure_us = vals['exposure']


        # update state dict
        self.state = vals
        
        return self

    def init_state(self):
        """
        set initial state upon startup
        """

        self.init_sensor(vals['bit mode'], vals['analog gain'])
        self.bsp = vals['black sun protection']
        self.pixel_corection = vals['pixel correction']
        self.digital_gain = vals['digital gain']
        self.mirror = vals['mirror']
        self.exposure_us = vals['exposure']

        return self

    @property
    def bit_mode(self):
        """
        """    

        return self.bmode

    @bit_mode.setter
    def bit_mode(self, mode):
        """
        """

        # run sensor init to set new sensor gain
        self.init_sensor(mode, self.again)
        self.bmode = mode

        return self


    @property
    def pixel_correction(self):
        """
        """

        return self.pcorrection

    @pixel_correction.setter
    def pixel_correction(self, value=True):
        """
        """

        # values
        on = value
        mode = 0
        high = 2
        low = 2
        highmode = 0

        # set corrections
        self.imager.setSensorI2C(0x36)
        self.imager.type(1)
        self.imager.write(0xE000,0) # banksel
        self.imager.write(0x0057,on) # defectON
        self.imager.write(0x0058,mode) # mode
        self.imager.write(0x0059,high) # highlimit
        self.imager.write(0x005A,low) # low limit
        self.imager.write(0x005B,highmode) # high mode

        self.pcorrection = value

        return self
    
    def black_calibration(self):
        """
        Set offsetclipping reg to 4500 in 12b gain4. 
        The result is the otp calib value
        """
        self.init_sensor(bit_mode='12bit', analog_gain=4)
        self.set_exposure_us(100)
        self.imager.setSensorI2C(0x36)
        self.imager.type(1)
        self.imager.write(0xe000,0)
        self.imager.write(0x0193,0x11)
        self.imager.write(0x0194,0x94)


    @property
    def black_level(self):
        """
        """

        return self.b_level

    @black_level.setter
    def black_level(self, target=50):
        # self.imager.setSensorI2C(0x36)
        # self.imager.type(1)
        # self.imager.write(0xe000,0)
        # self.imager.write(0x0193,0)
        # self.imager.write(0x0194,0)
        # return
        
        LUT = {'10bit': {1:440, 2:692, 4:1600},
               '10bithighspeed': {1:580, 2:860, 4:1700},
               '12bit': {1:1700, 2:2708, 4:4500}}

        calibration_value = 778 #from OTP
        TARGETED_AVG_DARK_VALUE = target
        # The non-scaled calibration value is assumed to be for 12-bit mode,
        # analog gain x4 (= scale factor of 1)
        # The scale factor increases for lower bit modes and lower gains
        scale_factor = 2**(12-self.bpp) * (4/self.again)
        scaled_calibration_value = round(
            (calibration_value)/scale_factor  - TARGETED_AVG_DARK_VALUE )
        offset_clip = int(scaled_calibration_value + LUT[self.bmode][self.again])
        print(f'offset clip is {offset_clip}')
        self.imager.setSensorI2C(0x36)
        self.imager.type(1)
        self.imager.write(0xe000, 0)
        self.imager.write(0x0193, offset_clip >> 8 & 255)
        self.imager.write(0x0194, offset_clip & 255)

        self.blevel = target

        return self
        
    @property
    def bsp(self):
        """
        """

        return self._bsp

    @bsp.setter
    def bsp(self, value=True):
        """black sun protect"""
        # Change bit 3
        self.bsp = value
        imager = self.imager
        if value:
            imager.setSensorI2C(0x36)
            imager.type(1)
            imager.write(0xe004, 0)
            imager.write(0xe000, 0)
            imager.write(0x1b5, 1)
        else:
            imager.setSensorI2C(0x36)
            imager.type(1)
            imager.write(0xe004, 0)
            imager.write(0xe000, 0)
            imager.write(0x1b5, 0)
        
        self._bsp = value

        return self


    @property
    def mirror(self):
        """
        """

        return self._mirror

    @mirror.setter
    def mirror(self, value=False):
        # Get the driver access

        # Change bit 3
        if value:
            self.imager.setSensorI2C(0x36)
            self.imager.write(0xe004, 0)
            self.imager.write(0xe000, 1)
            self.imager.write(0xe030, 1)
        else:
            self.imager.setSensorI2C(0x36)
            self.imager.write(0xe004, 0)
            self.imager.write(0xe000, 1)
            self.imager.write(0xe030, 0)
        
        self._mirror = value

        return self

    @property
    def analog_gain(self):
        """
        """

        return self.again

    @analog_gain.setter
    def analog_gain(self, gain):
        """
        """
        
        # run init sequence to set the analog gain
        self.init_sensor(self.bmode, gain)

        self.again = gain
        super().set_analog_gain(gain)

        return self


    @property
    def digital_gain(self):
        """
        """

        return self.dgain

    @digital_gain.setter
    def digital_gain(self, gain):
        """
        """

        self.imager.setSensorI2C(self.sensor_i2c)
        self.imager.type(self.sensor_type)

        gain = int(gain*16-1)
        self.dgain = float((gain+1)/16)
        
        # Get the driver access
        self.imager.setSensorI2C(0x36)
        self.imager.type(1)
        self.imager.write(0xe004,  0)
        self.imager.write(0xe000,  1)
        self.imager.write(0x0024, gain)
        
        return super().set_digital_gain(gain)


    @property
    def exposure_us(self):
        """
        """

        return self.exposure

    @exposure_us.setter
    def exposure_us(self, time_us):
        """
        """

        self.imager.setSensorI2C(self.sensor_i2c)
        self.imager.type(self.sensor_type)

        value = int(time_us)

        # Split value
        b3 = value >> 24 & 255
        b2 = value >> 16 & 255
        b1 = value >> 8 & 255
        b0 = value & 255

        self.imager.write(0xe004,  0)
        self.imager.write(0xe000,  1)
        self.imager.write(0x000E, b3)
        self.imager.write(0x000F, b2)
        self.imager.write(0x0010, b1)
        self.imager.write(0x0011, b0)

        self.exposure = time_us

        return self

    def write_register(self, address, value):
        return super().write_register(address, value)

    def read_register(self, address):
        return super().read_register(address)


    def check_sensor(self):
        """
        check if sensor is present. Return 0 if detected.
        """
        # checksensor
        self.imager.setSensorI2C(0x36)
        self.imager.type(1)
        self.imager.write(0xE000, 0)
        self.imager.write(0xE004, 0)
        # Read ID 0x3=?, 0x4=?

        val = self.imager.read(0x11b)

        print(f'version is {val}')
        if val == 33:
            print('mira050 detected')
            self.imager.setSensorI2C(0x2d)
            self.imager.type(0)  # Reg=8bit, val=8bit
            # led seq -- use this to turn on leds. abc0000- 1110000 for all leds
            self.imager.write(0x61, 0b110000)
            return 0
        else:
            self.imager.setSensorI2C(0x2d)
            self.imager.type(0)  # Reg=8bit, val=8bit
            # led seq -- use this to turn on leds. abc0000- 1110000 for all leds
            self.imager.write(0x61, 0b1010000)
            return 1

    def reset_sensor(self):
        self.imager.setSensorI2C(0x2d)
        self.imager.type(0)  # Reg=8bit, val=8bit

        #### Disable master switch ####
        self.imager.write(0x62, 0x00)

        # Set all voltages to 0

        # DCDC1=0V
        self.imager.write(0x05, 0x00)
        # DCDC4=0V
        self.imager.write(0x0E, 0x0)
        # LDO1=0V VDDLO_PLL
        self.imager.write(0x11, 0x0)
        # LDO2=0.0V
        self.imager.write(0x14, 0x00)
        # LDO3=0.0V
        self.imager.write(0x17, 0x00)
        # LDO4=0V
        self.imager.write(0x1A, 0x00)
        # LDO5=0.0V
        self.imager.write(0x1C, 0x00)
        # LDO6=0.0V
        self.imager.write(0x1D, 0x00)
        # LDO7=0V
        self.imager.write(0x1E, 0x0)
        # LDO8=0.0V
        self.imager.write(0x1F, 0x00)
        # Disable LDO9 Lock
        self.imager.write(0x24, 0x48)
        # LDO9=0V VDDHI
        self.imager.write(0x20, 0x00)
        # LDO10=0V VDDLO_ANA
        self.imager.write(0x21, 0x0)

        #### Enable master switch ####
        time.sleep(50e-4)
        self.imager.write(0x62, 0x0D)  # enable master switch
        time.sleep(50e-4)

        # start PMIC
        # Keep LDOs always on
        self.imager.write(0x27, 0xFF)
        self.imager.write(0x28, 0xFF)
        self.imager.write(0x29, 0x00)
        self.imager.write(0x2A, 0x00)
        self.imager.write(0x2B, 0x00)

        # Unused LDO off
        time.sleep(50e-4)
        # set GPIO1=0
        self.imager.write(0x41, 0x04)
        # DCDC2=0.0V SPARE_PWR1
        self.imager.write(0x01, 0x00)
        self.imager.write(0x08, 0x00)
        # DCDC3=0V SPARE_PWR1
        self.imager.write(0x02, 0x00)
        self.imager.write(0x0B, 0x00)
        # LDO2=0.0V
        self.imager.write(0x14, 0x00)
        # LDO3=0.0V
        self.imager.write(0x17, 0x00)
        # LDO5=0.0V
        self.imager.write(0x1C, 0x00)
        # LDO6=0.0V
        self.imager.write(0x1D, 0x00)
        # LDO8=0.0V
        self.imager.write(0x1F, 0x00)

        self.imager.write(0x42, 4)


        # Enable 1.80V
        time.sleep(50e-4)
        # DCDC1=1.8V VINLDO1p8 >=1P8
        self.imager.write(0x00, 0x00)
        self.imager.write(0x04, 0x34)
        self.imager.write(0x06, 0xBF)
        self.imager.write(0x05, 0xB4)
        # DCDC4=1.8V VDDIO
        self.imager.write(0x03, 0x00)
        self.imager.write(0x0D, 0x34)
        self.imager.write(0x0F, 0xBF)
        self.imager.write(0x0E, 0xB4)

        # Enable 2.85V
        time.sleep(50e-4)
        # LDO4=2.85V VDDHI alternativ
        self.imager.write(0x1A, 0b10111000)
        # Disable LDO9 Lock
        self.imager.write(0x24, 0x48)
        # LDO9=2.85V VDDHI
        self.imager.read(0x20)
        self.imager.write(0x20, 0xb9)  # b9
        self.imager.read(0x20)

        # VPIXH on cob = vdd25A on interposer = LDO4 on pmic
        # VPIXH should connect to VDD28 on pcb, or enable 4th supply
        self.imager.read(0x19)
        self.imager.write(0x19, 0b00111000)  # b9
        self.imager.read(0x19)

        # Enable 1.2V
        time.sleep(700e-4)
        # LDO1=1.2V VDDLO_PLL
        self.imager.write(0x12, 0x16)
        self.imager.write(0x10, 0x16)
        self.imager.write(0x11, 0b10010000)
        # LDO7=1.2V VDDLO_DIG
        self.imager.write(0x1E, 0b10010000)
        # LDO10=1.2V VDDLO_ANA
        self.imager.write(0x21, 0b10010000)



        # Enable green LED
        time.sleep(50e-4)
        self.imager.write(0x43, 0x40)  # leda
        self.imager.write(0x44, 0x40)  # ledb
        self.imager.write(0x45, 0x40)  # ledc

        self.imager.write(0x47, 0x02)  # leda ctrl1
        self.imager.write(0x4F, 0x02)  # ledb ctrl1
        self.imager.write(0x57, 0x02)  # ledc ctrl1

        self.imager.write(0x4D, 0x01)  # leda ctrl1
        self.imager.write(0x55, 0x10)  # ledb ctrl7
        self.imager.write(0x5D, 0x10)  # ledc ctrl7
        # led seq -- use this to turn on leds. abc0000- 1110000 for all leds
        self.imager.write(0x61, 0b10000)

        time.sleep(2)
        # uC, set atb and jtag high
        self.imager.setSensorI2C(0x0A)
        self.imager.type(0)
        self.imager.write(11, 0b11001111)
        self.imager.write(15, 0b00110000)
        self.imager.write(6, 1)

        time.sleep(1)

        # Init sensor
        self.imager.setSensorI2C(0x36)
        self.imager.type(1)  # reg=16bit, val=8bit
        # Set input clock speed to 24MHz
        # self.imager.setmclk(24000000)
        self.imager.setDelay(0)
        # Reset sensor
        time.sleep(0.02)

        # Reset sensor
        self.imager.reset(2) #keep in reset
        self.imager.wait(100)
        time.sleep(0.01)
        self.imager.reset(3) #leave reset
        self.imager.wait(500)
        time.sleep(0.1)

        # Read ID 0x3=?, 0x4=?

        val = self.imager.read(0x11b)