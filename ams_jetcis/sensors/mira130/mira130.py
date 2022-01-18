import time

from ams_jetcis.sensors.sensor import Sensor
from ams_jetcis.sensors.mira130.config_files import fullres


class Mira130(Sensor):
    """
    Implementation of Sensor class for Mira130.
    """

    def __init__(self, imagertools) -> None:
        self.name = 'Mira130'
        self.bpp = 10
        self.width = 1080
        self.height = 1280
        self.widthDMA = 1088
        self.heightDMA = 1280
        self.bpp = 10
        self.fps = 30
        self.digital_gain = 1 #NOT dB also not used at the moment
        self.analog_gain = 1 #NOT dB
        self.dtMode = 0
        self.sensori2c = 0x30
        self.busy = 0
        self.frametime = 21.694
        self.frame_length = 2400
        self.line_length = 1500
        self.exposure_length_max = (self.frame_length - 8) * 16
        self.Tpclk = (10 ** 6) / (self.fps * self.frame_length * self.line_length)
        self.step = (1 / 16) * self.line_length * self.Tpclk
        self.hdr = False
        self.hdr_exposure_us = 100
        self.exposure_us = 1000
        # Table dB values
        self.ana_table_db = [0.00, 0.27, 0.53, 0.78, 1.02, 1.26, 1.49, 1.72, 1.94, 2.15, 2.36, 2.57, 2.77, 2.96, 3.15, 3.34, 3.52,
                        3.70, 3.88, 4.05, 4.22, 4.38, 4.54, 4.70, 4.86, 5.01, 5.17, 5.43, 5.69, 5.94, 6.19, 6.43, 6.66, 6.88,
                        7.10, 7.32, 7.53, 7.73, 7.93, 8.13, 8.32, 8.50, 8.69, 8.87, 9.04, 9.21, 9.38, 9.55, 9.71, 9.87, 10.03,
                        10.18, 10.33, 10.48, 10.63, 10.77, 10.91, 11.05, 11.19, 11.45, 11.71, 11.96, 12.21, 12.45, 12.68, 12.90,
                        13.12, 13.34, 13.55, 13.75, 13.95, 14.15, 14.34, 14.53, 14.71, 14.89, 15.06, 15.23, 15.40, 15.57, 15.73,
                        15.89, 16.05, 16.20, 16.35, 16.50, 16.65, 16.79, 16.93, 17.07, 17.21, 17.47, 17.73, 17.99, 18.23, 18.47,
                        18.70, 18.93, 19.14, 19.36, 19.57, 19.77, 19.97, 20.17, 20.36, 20.55, 20.73, 20.91, 21.08, 21.26, 21.42,
                        21.59, 21.75, 21.91, 22.07, 22.22, 22.37, 22.52, 22.67, 22.81, 22.95, 23.09, 23.23, 23.49, 23.75, 24.01,
                        24.25, 24.49, 24.72, 24.95, 25.17, 25.38, 25.59, 25.79, 25.99, 26.19, 26.38, 26.57, 26.75, 26.93, 27.10,
                        27.28, 27.44, 27.61, 27.77, 27.93, 28.09, 28.24, 28.39, 28.54, 28.69, 28.83, 28.97, 29.11]

        # Table dB values
        self.dig_table_db = [0.00, 0.27, 0.53, 0.78, 1.02, 1.26, 1.49, 1.72, 1.94, 2.15, 2.36, 2.57, 2.77, 2.96, 3.15, 3.34, 3.52,
                        3.70, 3.88, 4.05, 4.22, 4.38, 4.54, 4.70, 4.86, 5.01, 5.17, 5.31, 5.46, 5.60, 5.74, 5.88, 6.02, 6.29,
                        6.55, 6.80, 7.04, 7.28, 7.51, 7.74, 7.96, 8.17, 8.38, 8.59, 8.79, 8.98, 9.17, 9.36, 9.54, 9.72, 9.90,
                        10.07, 10.24, 10.40, 10.57, 10.72, 10.88, 11.04, 11.19, 11.33, 11.48, 11.62, 11.77, 11.9, 12.04, 12.31,
                        12.57, 12.82, 13.06, 13.30, 13.53, 13.76, 13.98, 14.19, 14.40, 14.61, 14.81, 15.00, 15.19, 15.38, 15.56,
                        15.74, 15.92, 16.09, 16.26, 16.42, 16.59, 16.75, 16.9, 17.06, 17.21, 17.36, 17.50, 17.64, 17.79, 17.93,
                        18.06, 18.33, 18.59, 18.84, 19.08, 19.32, 19.55, 19.78, 20.00, 20.21, 20.42, 20.63, 20.83, 21.02, 21.21,
                        21.40, 21.58, 21.76, 21.94, 22.11, 22.28, 22.44, 22.61, 22.77, 22.92, 23.08, 23.23, 23.38, 23.52, 23.67,
                        23.81, 23.95, 24.08, 24.35, 24.61, 24.86, 25.11, 25.34, 25.58, 25.80, 26.02, 26.24, 26.44, 26.65, 26.85,
                        27.04, 27.23, 27.42, 27.60, 27.78, 27.96, 28.13, 28.30, 28.46, 28.63, 28.79, 28.94, 29.10, 29.25, 29.40,
                        29.54, 29.69, 29.83, 29.97]


        super().__init__(imagertools)

    def reset_sensor(self):
        # start PMIC
        self.imager.setSensorI2C(0x2d)
        self.imager.type(0)  # Reg=8bit, val=8bit
        # set GPIO1=0
        self.imager.write(0x41, 0x04)
        # DCDC1=1.2V
        self.imager.write(0x00, 0x00)
        self.imager.write(0x04, 0x28)
        self.imager.write(0x06, 0x7F)
        self.imager.write(0x05, 0xA8)
        # DCDC2=0.0V
        self.imager.write(0x08, 0x00)
        # DCDC3=2.8V
        self.imager.write(0x02, 0x00)
        self.imager.write(0x0A, 0x2E)
        self.imager.write(0x0C, 0xFF)
        self.imager.write(0x0B, 0xAE)
        # DCDC4=1.8V
        self.imager.write(0x03, 0x00)
        self.imager.write(0x0D, 0x34)
        self.imager.write(0x0F, 0xBF)
        self.imager.write(0x0E, 0xB4)
        # LDO1=0.0V
        self.imager.write(0x11, 0x00)
        # LDO2=0.0V
        self.imager.write(0x14, 0x00)
        # LDO3=0.0V
        self.imager.write(0x17, 0x00)
        # LDO4=2.5V
        self.imager.write(0x1B, 0x32)
        self.imager.write(0x19, 0x32)
        self.imager.write(0x1A, 0xB2)
        # LDO5=0.0V
        self.imager.write(0x1C, 0x00)
        # LDO6=0.0V
        self.imager.write(0x1D, 0x00)
        # LDO7=0.0V
        self.imager.write(0x1E, 0x00)
        # LDO8=0.0V
        self.imager.write(0x1F, 0x00)
        # LDO9=0.0V
        self.imager.write(0x20, 0x00)
        # LDO10=0.0V
        self.imager.write(0x21, 0x00)
        # Enable master switch
        self.imager.write(0x62, 0x0D)
        # Keep LDOs always on
        self.imager.write(0x27, 0xFF)
        self.imager.write(0x28, 0xFF)
        self.imager.write(0x29, 0x00)
        self.imager.write(0x2A, 0x00)
        self.imager.write(0x2B, 0x00)
        # Enable green LED
        self.imager.write(0x44, 0x40)
        self.imager.write(0x4F, 0x02)
        self.imager.write(0x55, 0x10)
        self.imager.write(0x61, 0x20)
        # init sensor
        self.imager.setSensorI2C(0x30)
        self.imager.type(1)  # reg=16bit, val=8bit
        # set input clock speed to 27MHz
        self.imager.setmclk(24000000)
        self.imager.setDelay(0)
        # and reset sensor
        # Reset sensor
        self.imager.reset(2) #keep in reset
        self.imager.wait(100)
        time.sleep(0.01)
        self.imager.reset(3) #leave reset
        self.imager.wait(500)
        time.sleep(0.01)
        print('reset done')

        # uncomment to enable LED
        # LED DRIVER of PMIC config AS3648
        # imager.setSensorI2C(0x30)
        # imager.type(0) # Reg=8bit, val=8bit
        # imager.write(1,0xFE)
        # imager.write(2,0xFE)
        # imager.write(3,0x00)
        # imager.write(6,9)
        # imager.write(9,3)

    def check_sensor(self):
        """
        Check if sensor is connected.
        either 30 or 32 as i2c address. 
        The newest boards have 0x30
        """
        print('checking sensor')
        det=0
        self.imager.setSensorI2C(0x32)
        self.imager.type(1)  # reg=16bit, val=8bit

        # read ID 3107=1, 3108=32
        if self.imager.read(0x3107)>1 or self.imager.read(0x3108)>1:
            self.sensori2c = 0x32
            print('Mira130 i2c is 0x32')
            det= 1

        else:
            self.imager.setSensorI2C(0x30)
            self.imager.type(1)
            self.sensori2c = 0x30

            if self.imager.read(0x3107)>1 or self.imager.read(0x3108)>1:
                self.sensori2c = 0x30
                print('Mira130 i2c is 0x30')
                det= 1
            else:
                self.sensori2c = 0x0

                print('mira130 not detected')

        if det == 1:
            print('mira130 detected')
            self.imager.setSensorI2C(0x2d)
            self.imager.type(0)  # Reg=8bit, val=8bit
            # led seq -- use this to turn on leds. abc0000- 1110000 for all leds
            self.imager.write(0x61, 0b110000)
            return 0
        else:
            print('mira130 not detected')
            self.imager.setSensorI2C(0x2d)
            self.imager.type(0)  # Reg=8bit, val=8bit
            # led seq -- use this to turn on leds. abc0000- 1110000 for all leds
            self.imager.write(0x61, 0b1010000)
            return 1


    def disable_illuminator(self):
	    # I2C address LED and length (addr=8bit, val=8bit)
        self.imager.setSensorI2C(0x53)
        self.imager.type(0)

        # Turn off LED
        self.imager.write(0x10, 0x08)

        # I2C address sensor and length (addr=16bit, val=8bit)
        self.imager.setSensorI2C(self.sensori2c)
        self.imager.type(1)

        # Disable trigger
        self.imager.write(0x10d7, 0x00)
        # def check_sensor(self):
        #     """
        #     check if sensor is present. Return 0 if detected.
        #     """
        #     self.imager.setSensorI2C(0x32)
        #     self.imager.type(1)
        #     # read ID 3107=1, 3108=32
        #     val = self.imager.read(0x3107)
        #     print(val)

        #     val = self.imager.read(0x3108)
        #     print(val)
        #     print(f'version is {val}')
        #     if val == 1:
        #         print('mira130 detected')
        #         self.imager.setSensorI2C(0x2d)
        #         self.imager.type(0)  # Reg=8bit, val=8bit
        #         # led seq -- use this to turn on leds. abc0000- 1110000 for all leds
        #         self.imager.write(0x61, 0b110000)
        #         return 0
        #     else:
        #         print('mira130 not detected')
        #         self.imager.setSensorI2C(0x2d)
        #         self.imager.type(0)  # Reg=8bit, val=8bit
        #         # led seq -- use this to turn on leds. abc0000- 1110000 for all leds
        #         self.imager.write(0x61, 0b1010000)
        #         return 1

    def init_sensor(self, bit_mode='10bit', fps=30, w=1080, h=1280, nb_lanes=2, analog_gain=1):
        """
        supported bit modes: '10bit', 
        supported framreate : 30,
        supprted resolution: '1080x1280'
        """
        if nb_lanes == 2:
            if (w == 1080) and (h == 1280) and (bit_mode == '10bit'):
                self.width = 1080
                self.height = 1280
                self.widthDMA = 1088
                self.heightDMA = 1280
                self.bpp = 10
                self._init_fullres_30fps()
                self.set_exposure_us(1000)
            else:
                raise NotImplementedError('Requested {w}x{h} roi with {bit_mode} is not implemented')

            self.fps = 30
            self.set_analog_gain(analog_gain)
            self.disable_illuminator()
            self.imager.setformat(self.bpp, self.width, self.height, self.widthDMA, self.heightDMA, True)
        else:
            raise NotImplementedError(f'Requested {nb_lanes} data lanes are not implemented.') 

    def _init_fullres_30fps(self):
        self.imager.setSensorI2C(self.sensori2c)
        self.imager.type(1)
        # read ID 3107=1, 3108=32
        self.imager.read(0x3107)
        self.imager.read(0x3108)
        self.imager.wait(100)
        self.imager.setSensorI2C(self.sensori2c)
        self.imager.type(1)
        self.imager.write(0x0103, 0x01)
        self.imager.write(0x0100, 0x00)
        self.imager.write(0x36e9, 0x80)
        self.imager.write(0x36f9, 0x80)
        self.imager.write(0x3018, 0x32)  # 2lanes
        self.imager.write(0x3019, 0x0c)
        self.imager.write(0x301a, 0xb4)
        self.imager.write(0x3031, 0x0a)  # RAW10
        self.imager.write(0x3032, 0x60)
        self.imager.write(0x3038, 0x44)
        self.imager.write(0x3207, 0x17)
        self.imager.write(0x320c, 0x05)
        self.imager.write(0x320d, 0xdc)
        self.imager.write(0x320e, 0x09)
        self.imager.write(0x320f, 0x60)
        self.imager.write(0x3250, 0xcc)
        self.imager.write(0x3251, 0x02)
        self.imager.write(0x3252, 0x09)
        self.imager.write(0x3253, 0x5b)
        self.imager.write(0x3254, 0x05)
        self.imager.write(0x3255, 0x3b)
        self.imager.write(0x3306, 0x78)
        self.imager.write(0x330a, 0x00)
        self.imager.write(0x330b, 0xc8)
        self.imager.write(0x330f, 0x24)
        self.imager.write(0x3314, 0x80)
        self.imager.write(0x3315, 0x40)
        self.imager.write(0x3317, 0xf0)
        self.imager.write(0x331f, 0x12)
        self.imager.write(0x3364, 0x00)
        self.imager.write(0x3385, 0x41)
        self.imager.write(0x3387, 0x41)
        self.imager.write(0x3389, 0x09)
        self.imager.write(0x33ab, 0x00)
        self.imager.write(0x33ac, 0x00)
        self.imager.write(0x33b1, 0x03)
        self.imager.write(0x33b2, 0x12)
        self.imager.write(0x33f8, 0x02)
        self.imager.write(0x33fa, 0x01)
        self.imager.write(0x3409, 0x08)
        self.imager.write(0x34f0, 0xc0)
        self.imager.write(0x34f1, 0x20)
        self.imager.write(0x34f2, 0x03)
        self.imager.write(0x3622, 0xf5)
        self.imager.write(0x3630, 0x5c)
        self.imager.write(0x3631, 0x80)
        self.imager.write(0x3632, 0xc8)
        self.imager.write(0x3633, 0x32)
        self.imager.write(0x3638, 0x2a)
        self.imager.write(0x3639, 0x07)
        self.imager.write(0x363b, 0x48)
        self.imager.write(0x363c, 0x83)
        self.imager.write(0x363d, 0x10)
        self.imager.write(0x36ea, 0x38)
        self.imager.write(0x36fa, 0x25)
        self.imager.write(0x36fb, 0x05)
        self.imager.write(0x36fd, 0x04)
        self.imager.write(0x3900, 0x11)
        self.imager.write(0x3901, 0x05)
        self.imager.write(0x3902, 0xc5)
        self.imager.write(0x3904, 0x04)
        self.imager.write(0x3908, 0x91)
        self.imager.write(0x391e, 0x00)
        self.imager.write(0x3e01, 0x53)
        self.imager.write(0x3e02, 0xe0)
        self.imager.write(0x3e09, 0x20)
        self.imager.write(0x3e0e, 0xd2)
        self.imager.write(0x3e14, 0xb0)
        self.imager.write(0x3e1e, 0x7c)
        self.imager.write(0x3e26, 0x20)
        self.imager.write(0x4418, 0x38)
        self.imager.write(0x4503, 0x10)
        self.imager.write(0x4837, 0x21)
        self.imager.write(0x5000, 0x0e)
        self.imager.write(0x540c, 0x51)
        self.imager.write(0x550f, 0x38)
        self.imager.write(0x5780, 0x67)
        self.imager.write(0x5784, 0x10)
        self.imager.write(0x5785, 0x06)
        self.imager.write(0x5787, 0x02)
        self.imager.write(0x5788, 0x00)
        self.imager.write(0x5789, 0x00)
        self.imager.write(0x578a, 0x02)
        self.imager.write(0x578b, 0x00)
        self.imager.write(0x578c, 0x00)
        self.imager.write(0x5790, 0x00)
        self.imager.write(0x5791, 0x00)
        self.imager.write(0x5792, 0x00)
        self.imager.write(0x5793, 0x00)
        self.imager.write(0x5794, 0x00)
        self.imager.write(0x5795, 0x00)
        self.imager.write(0x5799, 0x04)
        # //fsync output enable
        self.imager.write(0x300a, 0x64)
        self.imager.write(0x3032, 0xa0)
        self.imager.write(0x3217, 0x09)
        self.imager.write(0x3218, 0x5a)  # //vts - 6
        # //PLL set
        self.imager.write(0x36e9, 0x20)
        self.imager.write(0x36f9, 0x24)
        self.imager.write(0x0100, 0x01)
        return(0)

    def set_exposure_us(self, time_us):
        """set exposure in us"""
            # Get the entry value
        self.exposure_us=time_us
        try:
            value = float(time_us) 
        except:
            value = 0.0

        # Calculate the pixel clock period in ms
        fps_original = self.fps
        frame_length_original = self.frame_length
        line_length_original = self.line_length
        Tpclk = (10 ** 6) / (fps_original * frame_length_original * line_length_original)
        # Calculate the given exposure time to the exposure length
        self.imager.disablePrint()
        # line_length_new = self.imager.read(0x320c) * (2 ** 8) + self.imager.read(0x320d)
        # line_time_new = line_length_new * Tpclk
        self.line_time = self.line_length * self.Tpclk
        exposure_length = round(16 * value / self.line_time)
        frame_length_new = self.imager.read(0x320e) * (2 ** 8) + self.imager.read(0x320f)
        if exposure_length > (frame_length_new - 8) * 16:
            exposure_length = (frame_length_new - 8) * 16

        # Split value
        high = exposure_length // (2 ** 16) + int(format(self.imager.read(0x3e00), '08b')[0:4], 2) * (2**4)
        middle_temp = exposure_length % (2 ** 16)
        middle = middle_temp // (2 ** 8)
        low = middle_temp % (2 ** 8)

        # Write to registers
        self.imager.enablePrint()
        self.imager.write(0x3e00, high)
        self.imager.write(0x3e01, middle)
        self.imager.write(0x3e02, low)
        
    def get_exposure_us(self):
        """get exposure in us"""
        return self.exposure_us
                # TBD

    def set_hdr(self, enabled=True, hdr_exposure_us=100):
        self.hdr = enabled
        self.hdr_exposure_us = hdr_exposure_us


        # Read register and convert to 8 bit
        current_address_value = self.imager.read(0x3220)
        current_address_value_bin = format(current_address_value, '08b')

        # Change bit 6
        if (enabled == 0):
            write_value = current_address_value_bin[:1] + '0' + current_address_value_bin[2:]
        else:
            write_value = current_address_value_bin[:1] + '1' + current_address_value_bin[2:]

        # Write to register
        self.imager.write(0x3220, int(write_value, 2))

        # set hdr exposure
        self.line_time = self.line_length * self.Tpclk
        exposure_length = round(16 * self.hdr_exposure_us / self.line_time)
        high = exposure_length // (2**8)
        low = exposure_length % (2**8)

        # Write to registers
        self.imager.write(0x3e31, high)
        self.imager.write(0x3e32, low)

    
    def get_hdr(self):
        return (self.hdr,self.hdr_exposure_us)

    def set_analog_gain(self, gain):
        self.imager.setSensorI2C(self.sensori2c)
        self.imager.type(1)
        self.analog_gain=gain
        """set analog gain"""
        gain2 = gain * 0x20
        gain_coarse = gain2//256
        gain_fine = gain2 % 256
        self.imager.write(0x3e03, 0x3)
        self.imager.write(0x3e08, gain_coarse)
        self.imager.write(0x3e09, gain_fine)
        # HDR regs
        self.imager.write(0x3e12, gain_coarse)
        self.imager.write(0x3e13, gain_fine)

    def get_analog_gain(self):
        self.imager.setSensorI2C(self.sensori2c)
        self.imager.type(1)
        return self.analog_gain

    def get_analog_gain_from_registers(self):
        self.imager.setSensorI2C(self.sensori2c)
        self.imager.type(1)
        mode = self.imager.read(0x3e03)
        if mode != 3:
            raise NotImplementedError(
                'this mode is not supported. please set 0x3e03 to 0x3')
        gain_coarse = self.imager.read(0x3e08)
        gain_fine = self.imager.read(0x3e09)
        gain = (gain_coarse * 256 + gain_fine) / 0x20
        self.analog_gain = gain
        return gain
        
    def set_digital_gain(self, gain):
        return ValueError('not implememted')

    def get_digital_gain(self, gain):
        return self.digital_gain


    def write_register(self, address, value):
        return super().write_register(address, value)

    def read_register(self, address):
        return super().read_register(address)
