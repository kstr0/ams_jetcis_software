import pathlib
import time
from typing import NamedTuple

from ams_jetcis.sensors.sensor import Sensor
from ams_jetcis.common.errors import Mira050ConfigError

# from ams_jetcis.sensors.mira050.config_files import config_800_600_10b_mira050_normal_gain1_patch, config_800_600_10b_mira050_normal_gain2_patch, config_800_600_10b_mira050_normal_gain4_patch

class AddressField(NamedTuple):
    addr: int
    mask: int
    shift: int

    def get_value(self, value):
        """Take in a byte that was read from the OTP and mask + shift it."""
        return (value & self.mask) << self.shift



class Mira050(Sensor):
    """
    Implementation of Sensor class for Mira050.
    big endian register access. --> largest byte in lowest address
    """

    def __init__(self, imagertools) -> None:
        self.name = 'Mira050'
        self.bpp = 10
        self.width = 600
        self.height = 800
        self.widthDMA = 608
        self.heightDMA = 800
        self.fps = 30
        self.dtMode = 0
        self.sensor_i2c = 54
        self.sensor_type = 1
        self.bit_mode = ''
        self._digital_gain = 1
        self._analog_gain = 1
        self.bsp = 1
        self.mirror = 0
        self._exposure_us = 1000
        self.pixel_correction = 1
        self.temp_cor=True
        self.temperature = None
        self.low_fpn=True
        self.illum = False
        self.clock = 38.4
        self._led_driver = [None, None, None]

        self.mode_table =  {
            '10bit': {
                1: r'10-bit mode_anagain1_60fps_exp0.1ms_continuous_clk_datarate_1200.txt', \
                2: r'10-bit mode_anagain2_60fps_exp0.1ms_continuous_clk_datarate_1200.txt', \
                4: r'10-bit mode_anagain4_60fps_exp0.1ms_continuous_clk_datarate_1200.txt'}, \
            '10bithighspeed': {
                1: r'10-bit high speed mode_anagain1_60fps_exp0.1ms_continuous_clk_datarate_1200.txt', \
                2: r'10-bit high speed mode_anagain2_60fps_exp0.1ms_continuous_clk_datarate_1200.txt', \
                4: r'10-bit high speed mode_anagain4_60fps_exp0.1ms_continuous_clk_datarate_1200.txt'},\
            '12bit': {
                1: r'12-bit mode_anagain1_60fps_exp0.1ms_continuous_clk_datarate_1200.txt', \
                2: r'12-bit mode_anagain2_60fps_exp0.1ms_continuous_clk_datarate_1200.txt', \
                4: r'12-bit mode_anagain4_60fps_exp0.1ms_continuous_clk_datarate_1200.txt'}
                }
 
        self.mode_table_low_fpn_24 =  {
            '8bit': {
                1: r'low_fpn/8-bit mode_anagain1_60fps_exp0.1ms_continuous_clk_datarate_1200_mclk_24.txt', \
                2: r'low_fpn/8-bit mode_anagain2_60fps_exp0.1ms_continuous_clk_datarate_1200_mclk_24.txt', \
                4: r'low_fpn/8-bit mode_anagain4_60fps_exp0.1ms_continuous_clk_datarate_1200_mclk_24.txt', \
                16: r'low_fpn/8-bit mode_anagain16_60fps_exp0.1ms_continuous_clk_datarate_1200_mclk_24.txt'}, \
            '10bit': {
                1: r'low_fpn/10-bit mode_anagain1_60fps_exp0.1ms_continuous_clk_datarate_1200_mclk_24.txt', \
                2: r'low_fpn/10-bit mode_anagain2_60fps_exp0.1ms_continuous_clk_datarate_1200_mclk_24.txt', \
                4: r'low_fpn/10-bit mode_anagain4_60fps_exp0.1ms_continuous_clk_datarate_1200_mclk_24.txt'}, \
            '10bithighspeed': {
                1: r'low_fpn/10-bit high speed mode_anagain1_60fps_exp0.1ms_continuous_clk_datarate_1200_mclk_24.txt', \
                2: r'low_fpn/10-bit high speed mode_anagain2_60fps_exp0.1ms_continuous_clk_datarate_1200_mclk_24.txt', \
                4: r'low_fpn/10-bit high speed mode_anagain4_60fps_exp0.1ms_continuous_clk_datarate_1200_mclk_24.txt'},\
            '12bit': {
                1: r'low_fpn/12-bit mode_anagain1_60fps_exp0.1ms_continuous_clk_datarate_1200_mclk_24.txt', \
                2: r'low_fpn/12-bit mode_anagain2_60fps_exp0.1ms_continuous_clk_datarate_1200_mclk_24.txt', \
                4: r'low_fpn/12-bit mode_anagain4_60fps_exp0.1ms_continuous_clk_datarate_1200_mclk_24.txt'}
                }
        self.mode_table_low_fpn_38 =  {
            '8bit': {
                1: r'low_fpn/8-bit mode_anagain1_60fps_exp0.1ms_continuous_clk_datarate_1200_mclk_38.txt', \
                2: r'low_fpn/8-bit mode_anagain2_60fps_exp0.1ms_continuous_clk_datarate_1200_mclk_38.txt', \
                4: r'low_fpn/8-bit mode_anagain4_60fps_exp0.1ms_continuous_clk_datarate_1200_mclk_38.txt'}, \
            '10bit': {
                1: r'low_fpn/10-bit mode_anagain1_60fps_exp0.1ms_continuous_clk_datarate_1200_mclk_38.txt', \
                2: r'low_fpn/10-bit mode_anagain2_60fps_exp0.1ms_continuous_clk_datarate_1200_mclk_38.txt', \
                4: r'low_fpn/10-bit mode_anagain4_60fps_exp0.1ms_continuous_clk_datarate_1200_mclk_38.txt'}, \
            '10bithighspeed': {
                1: r'low_fpn/10-bit high speed mode_anagain1_60fps_exp0.1ms_continuous_clk_datarate_1200_mclk_38.txt', \
                2: r'low_fpn/10-bit high speed mode_anagain2_60fps_exp0.1ms_continuous_clk_datarate_1200_mclk_38.txt', \
                4: r'low_fpn/10-bit high speed mode_anagain4_60fps_exp0.1ms_continuous_clk_datarate_1200_mclk_38.txt'},\
            '12bit': {
                1: r'low_fpn/12-bit mode_anagain1_60fps_exp0.1ms_continuous_clk_datarate_1200_mclk_38.txt', \
                2: r'low_fpn/12-bit mode_anagain2_60fps_exp0.1ms_continuous_clk_datarate_1200_mclk_38.txt', \
                4: r'low_fpn/12-bit mode_anagain4_60fps_exp0.1ms_continuous_clk_datarate_1200_mclk_38.txt'}
                }
        super().__init__(imagertools)


    def ina_present(self):
        self.imager.setSensorI2C(65)
        self.imager.type(2)  # reg=16bit, val=8bit
        print(self.imager.read(0xFF) )

        if (self.imager.read(0xFF)==0x3220): 
            self.imager.setSensorI2C(self.sensor_i2c)
            self.imager.type(self.sensor_type)  # reg=16bit, val=8bit
            print('ina detected, sensor board mira050 is used')
            return True
        else:   
            print('ina not detected, probably interposer')
            return False

    def illum_trig(self, value):
        self.illum=value
        self.imager.setSensorI2C(self.sensor_i2c)
        self.imager.type(self.sensor_type)  # reg=16bit, val=8bit
        self.imager.write(0xE004,0)
        self.imager.write(0xE000,1)
        temp=self.imager.read(0x001C)
        print(temp)
        self.imager.write(0x001C,int(value))
        temp=self.imager.read(0x001C)
        print(temp)
        self.imager.write(0x0019,19)
        print(self.imager.read(0x0016))

        # self.imager.write(0x0016,8) #no delay



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
        self.imager.setSensorI2C(0x53)
        self.imager.type(0)
        enable = 0 if (self.imager.read(0x10) % (2**4)) == 0x08 else 1
        current = ([80, 150, 220, 280] + list(range(350, 1020, 60)))[self.imager.read(0xb0) % (2**4)]
        timeout = ([60] + list(range(125, 760, 125)) + [1100])[self.imager.read(0xc0) % (2**3)]
        self._led_driver = [enable, current, timeout]
        self.imager.setSensorI2C(self.sensor_i2c)
        self.imager.type(self.sensor_type)  # reg=16bit, val=8bit
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
        self.imager.setSensorI2C(0x53)
        self.imager.type(0)
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
        self.imager.setSensorI2C(self.sensor_i2c)
        self.imager.type(self.sensor_type)  # reg=16bit, val=8bit

    def config_parser(self, fname):
        config_file_path = pathlib.Path(__file__).parent.absolute()/'config_files'/fname
        print(config_file_path)
        # fname = r"C:\TeamForge\jetcis_svn\jetcis\software\trunk\sw\ams_jetcis\sensors\mira050\config_files\12-bit mode_anagain1_60fps_exp0.1ms_continuous_clk_datarate1400.txt"
        reg_seq = []
        
        with open(config_file_path, "r") as f:
            for line in f:
                values = line.split()
                if values[0] == 'Write':
                    addr =  (int(values[3],16))
                    val =  (int(values[1],10))
                    reg_seq.append((addr, val))
                else:
                    pass

        self.reg_seq=reg_seq
        return reg_seq

    def init_from_config(self,reg_seq):
        imager = self.imager
        imager.setSensorI2C(self.sensor_i2c)
        imager.type(1)
        self.imager.write(0xE000, 0)
        time.sleep(0.01)
        self.imager.disablePrint()
        for addr,reg in reg_seq:
            imager.write(int(addr), int(reg))
        self.software_trigger()

    def software_trigger(self):
        self.imager.setSensorI2C(0x36)
        self.imager.type(1)
        self.imager.write(0xE000, 0)
        self.imager.write(0xE004, 0)
        self.imager.write(0x00A,1)
        self.imager.write(0x00A,0)


    def reset_sensor(self):
        # Reset sensor
        self.imager.reset(2) #keep in reset
        self.imager.wait(100)

        # uC, set atb and jtag high
        # according to old uC fw (svn rev41)
        # 12[3] ldo en
        # 11[4,5] atpg jtag
        # 11/12 i/o direction, 15/16 output high/low
        # uC, set atb and jtag high
        # WARNING this only works on interposer v2 if R307 is not populated. otherwise, invert the bit for ldo
        self.imager.setSensorI2C(0x0A)
        self.imager.type(0)
        self.imager.write(12, 0b11110111)
        self.imager.write(16, 0b11111111) #ldo en:0
        self.imager.write(11, 0b11001111)
        self.imager.write(15, 0b11111111)
        self.imager.write(6, 1) #write


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
        
        time.sleep(1)


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
        self.imager.write(0x42, 0x15)  # gpio2

        #self.imager.write(0x43, 0x40)  # leda
        #self.imager.write(0x44, 0x40)  # ledb
        self.imager.write(0x45, 0x40)  # ledc

        #self.imager.write(0x47, 0x02)  # leda ctrl1
        #self.imager.write(0x4F, 0x02)  # ledb ctrl1
        self.imager.write(0x57, 0x02)  # ledc ctrl1

        #self.imager.write(0x4D, 0x01)  # leda ctrl1
        #self.imager.write(0x55, 0x10)  # ledb ctrl7
        self.imager.write(0x5D, 0x10)  # ledc ctrl7
        # led seq -- use this to turn on leds. abc0000- 1110000 for all leds
        self.imager.write(0x61, 0b10000)


        # uC, set atb and jtag high and ldo_en
        self.imager.setSensorI2C(0x0A)
        self.imager.type(0)
        self.imager.write(12, 0b11110111)
        self.imager.write(16, 0b11110111) #ldo en:0
        self.imager.write(11, 0b11001111)
        self.imager.write(15, 0b11111111)
        self.imager.write(6, 1) #write


        time.sleep(0.01)
        self.imager.reset(3) #release in reset
        time.sleep(0.1)

    


        # Init sensor
        self.imager.setSensorI2C(0x36)
        self.imager.type(1)  # reg=16bit, val=8bit
        # Set input clock speed to 24MHz
        # self.imager.setmclk(24000000)
        self.imager.setDelay(0)
  
        # Read ID 0x3=?, 0x4=?

        val = self.imager.read(0x11b)



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

    def init_sensor(self, bit_mode='10bit', fps=30, w=600, h=800, nb_lanes=1, analog_gain=1):
        """ 
        supported bit modes: '10bit', '12bit', '10bithighspeed' '8bit'
        supported analog gains: 1 2 4
        """
        try: #do some checks
            assert(bit_mode in self.mode_table_low_fpn_24.keys())
            assert(analog_gain in self.mode_table_low_fpn_24[bit_mode].keys())
        except AssertionError:
            message = f"Supported modes: {self.mode_table_low_fpn_24.keys()} gains: {self.mode_table_low_fpn_38['10bit'].keys()}"
            raise Mira050ConfigError(bit_mode=bit_mode, analog_gain = analog_gain, message = message)
        
        type = self.imager.getSensorType()

        if bit_mode == '12bit' or bit_mode == '12bitlow_fpn':
            self.bpp=12
            self.dtMode = 0
        elif bit_mode =='8bit':
            self.bpp=8
            self.dtMode = 4
        else:
            self.bpp=10
            self.dtMode = 2
        
    
        if self.ina_present()==True:
            self.clock=24 #csp sensor board
        else:
            self.clock=38.4 #interposer with cob or csp
        if self.clock==24:
            self.init_from_config(self.config_parser(self.mode_table_low_fpn_24[bit_mode][analog_gain]))
        elif self.low_fpn and self.clock==38.4:
            self.init_from_config(self.config_parser(self.mode_table_low_fpn_38[bit_mode][analog_gain]))
        else:
            self.init_from_config(self.config_parser(self.mode_table[bit_mode][analog_gain]))

        self.bit_mode = bit_mode
        self.analog_gain= analog_gain
        self.set_bsp(self.bsp)
        self.set_pixel_correction(self.pixel_correction)
        self.set_digital_gain(self.digital_gain)
        self.set_mirror(self.mirror)
        self.set_exposure_us(self.exposure_us)
        self.width = 600
        self.height = 800
        self.widthDMA = 608
        self.heightDMA = 800
        if self.bpp==8:
            self.widthDMA = 640
        self.framerate = 60
        self.analog_gain = analog_gain
        self.set_black_level(temperature = self.temperature) #self.get_temperature())

        self.imager.setformat(self.bpp, self.width,
                              self.height, self.widthDMA, self.heightDMA, True)

    def set_pixel_correction(self,value = True):
            # readout amount of defects
        self.pixel_correction=value
        imager = self.imager
        on = value
        mode=0
        high=2
        low=2
        highmode=0
        imager.setSensorI2C(0x36)
        imager.type(1)
        imager.write(0xE000,0) # banksel
        imager.write(0x0057,on) # defectON
        imager.write(0x0058,mode) # mode
        imager.write(0x0059,high) # highlimit
        imager.write(0x005A,low) # low limit
        imager.write(0x005B,highmode) # high mode
    
    # def black_calibration(self):
    #     """
    #     Set offsetclipping reg to 4500 in 12b gain4. 
    #     The result is the otp calib value
    #     """
    #     self.init_sensor(bit_mode='12bit', analog_gain=4)
    #     self.set_exposure_us(100)
    #     self.imager.setSensorI2C(0x36)
    #     self.imager.type(1)
    #     self.imager.write(0xe000,0)
    #     self.imager.write(0x0193,0x11)
    #     self.imager.write(0x0194,0x94)


    def _get_data_from_otp(self, addr_field: AddressField) -> int:
        
        """
        placeholder for otp readout
        https://forge.ams.com/svn/repos/mira_xs_doc/trunk/engineering/Test%20Specification/51193_OTP_Register_Map.xlsx
        
        """
        reg = addr_field.addr

        self.imager.setSensorI2C(self.sensor_i2c)
        self.imager.type(self.sensor_type)
        self.imager.write(0xe000,0)
        self.imager.write(0x0066,0x0)
        self.imager.write(0x0067,reg)
        
        self.imager.write(0x0064,0x1)
        time.sleep(0.01)
        self.imager.write(0x0064,0x0)
        time.sleep(0.01)

        
        b3=self.imager.read(0x006C)
        b2=self.imager.read(0x006D)
        b1=self.imager.read(0x006E)
        b0=self.imager.read(0x006F)
        val=(b3<<24)+(b2<<16)+(b1<<8)+b0

        # print(f'OTP data reg {reg}: {bin(val)}')

        return addr_field.get_value(val)




    def get_wafer_id(self) -> str:
        """Get the die's wafer ID (i.e. find out to which wafer this sample
        belonged). The ID is returned as a string."""
        addr_fields = (
            AddressField(0x11, 0xFFFFFFFF, 0),
            AddressField(0x12, 0xFFFFFFFF, 0),
            AddressField(0x13, 0xFFFFFFFF, 0),
            AddressField(0x14, 0xFFFFFFFF, 0),
        )
        self.BYTES_PER_ADDR=4
        bytes_arr = b''
        for addr_field in addr_fields:
            otp_data = self._get_data_from_otp(addr_field)
            bytes_arr += otp_data.to_bytes(
                self.BYTES_PER_ADDR,
                byteorder='little'
            )
        # Character "ETX" (0x03) indicates the end of the wafer ID string
        wafer_id_bytes = bytes_arr.split(b'\x03')[0]
        print(f'id bytes: {wafer_id_bytes}')

        return wafer_id_bytes.decode('utf-8')

    def get_wafer_x_location(self) -> int:
        """Get the die's x-location on the wafer as a signed short (16-bit)."""
        self.BYTES_PER_ADDR=4
        addr_fields = (
            AddressField(0x15, 0x0000FFFF, 0),
        )
        bytes_arr = b''
        for addr_field in addr_fields:
            otp_data = self._get_data_from_otp(addr_field)
            bytes_arr += otp_data.to_bytes(
                self.BYTES_PER_ADDR,
                byteorder='little'
            )
        # Character "ETX" (0x03) indicates the end of the wafer ID string
        wafer_id_bytes = bytes_arr.split(b'\x03')[0]     
        return  int.from_bytes(wafer_id_bytes, byteorder='little', signed=True)



    def get_wafer_y_location(self) -> int:
        """Get the die's y-location on the wafer as a signed short (16-bit)."""
        self.BYTES_PER_ADDR=4
        addr_fields = (
            AddressField(0x16, 0x0000FFFF, 0),
        )
        bytes_arr = b''
        for addr_field in addr_fields:
            otp_data = self._get_data_from_otp(addr_field)
            bytes_arr += otp_data.to_bytes(
                self.BYTES_PER_ADDR,
                byteorder='little'
            )
        # Character "ETX" (0x03) indicates the end of the wafer ID string
        wafer_id_bytes = bytes_arr.split(b'\x03')[0]     
        return  int.from_bytes(wafer_id_bytes, byteorder='little', signed=True)


    def get_temp_wafer(self) -> int:
        """Chuck Setting [°C] for Sort #1 (16-bit) INT16."""
        # result = self._get_data_from_otp(AddressField(0x19, 0x0000FFFF, 0))
        self.BYTES_PER_ADDR=4
        addr_fields = (
            AddressField(0x19, 0x00000FFFF, 0),
        )
        bytes_arr = b''
        for addr_field in addr_fields:
            otp_data = self._get_data_from_otp(addr_field)
            bytes_arr += otp_data.to_bytes(
                self.BYTES_PER_ADDR,
                byteorder='little'
            )

        # Character "ETX" (0x03) indicates the end of the wafer ID string
        wafer_id_bytes = bytes_arr.split(b'\x03')[0]
        print(f'id bytes: {(wafer_id_bytes)}')
       
        return  int.from_bytes(wafer_id_bytes, byteorder='little', signed=False)

    def get_map_version(self) -> int:
        """Chuck Setting [°C] for Sort #1 (16-bit) INT16."""
        # result = self._get_data_from_otp(AddressField(0x19, 0x0000FFFF, 0))
        self.BYTES_PER_ADDR=4
        addr_fields = (
            AddressField(0x10, 0xFFFFFFFF, 0),
        )
        bytes_arr = b''
        for addr_field in addr_fields:
            otp_data = self._get_data_from_otp(addr_field)
            bytes_arr += otp_data.to_bytes(
                self.BYTES_PER_ADDR,
                byteorder='little'
            )
        # Character "ETX" (0x03) indicates the end of the wafer ID string
        wafer_id_bytes = bytes_arr.split(b'\x03')[0]     
        return  int.from_bytes(wafer_id_bytes, byteorder='little', signed=True)




    def set_black_level(self, target=128, temperature = None):
        """set black level, optionally provide temperature to do temp dependent calibration"""
        
        LUT = {'8bit': {1: 160, 2: 230, 4: 440, 16: 1700},
               '10bit': {1: 440, 2: 692, 4: 1140},
               '10bithighspeed': {1: 580, 2: 860, 4: 1700},
               '12bit': {1: 1700, 2: 2720, 4: 4500}}
        if self.bpp==10:
            target = target/4
        if self.bpp==8:
            target = target/16
        scale_factor = 2**(12-self.bpp) * (4/self.analog_gain)
        dn_per_degree = -2.64662 / scale_factor

        if temperature and self.temp_cor: #### and self.bit_mode=='12bit' and self.analog_gain==1:
            temp_delta = 25 - temperature
            black_level_adj = temp_delta*dn_per_degree
            print(f"Black level adjustment = {black_level_adj}DN")
            target = target + black_level_adj   
        if self.low_fpn:
            calibration_value = 2 #511 #should come from OTP, I set it to fixed for now
        else:
            calibration_value = 511
        TARGETED_AVG_DARK_VALUE = target
        # The non-scaled calibration value is assumed to be for 12-bit mode,
        # analog gain x4 (= scale factor of 1)
        # The scale factor increases for lower bit modes and lower gains
        scaled_calibration_value = round(
            (calibration_value)/scale_factor  - TARGETED_AVG_DARK_VALUE )
        offset_clip = int(scaled_calibration_value + LUT[self.bit_mode][self.analog_gain])
        print(f'Offset clip is {offset_clip}')
        print(f'Scale factor is {scale_factor}')
        print(f'Temperature is {temperature}')

        self.imager.setSensorI2C(self.sensor_i2c)
        self.imager.type(1)
        self.imager.write(0xe000, 0)
        self.imager.write(0x0193, offset_clip >> 8 & 255)
        self.imager.write(0x0194, offset_clip & 255)

                

    def set_bsp(self,value = True):
        """black sun protect"""
        # Change bit 3
        self.bsp = value
        imager = self.imager
        if (value == True):
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

    def set_mirror(self, value = False):
        # Get the driver access
        imager = self.imager
        self.mirror = value
        # Change bit 3
        if (value == 1):
            imager.setSensorI2C(0x36)
            imager.write(0xe004, 0)
            imager.write(0xe000, 1)
            imager.write(0xe030, 1)
        else:
            imager.setSensorI2C(0x36)
            imager.write(0xe004, 0)
            imager.write(0xe000, 1)
            imager.write(0xe030, 0)
    


    def get_temperature(self):
        # For 12-bit, Analog Gain x1
        if (self.bit_mode!='12bit' or self.analog_gain!=1):
            raise Exception('cannot measure temp in this mode. only in 12b  gain1')
        tsens_slope = 1.29
        tsens_offset = 400
        


        self.imager.setSensorI2C(0x36)
        self.imager.type(1)
        self.imager.write(0xE000, 0) # banksel
        
        self.imager.write(0x74, 1)
        raw_temp = self.imager.read(0x72)*256 + self.imager.read(0x73)
        self.imager.write(0x74, 0)

        # get offset
        adc_cyc_act1 = self.imager.read(0x018B)*256 + self.imager.read(0x018C)
        offset = 2* adc_cyc_act1
        # get calbirated temp
        raw_tsens_data = raw_temp - offset
        temp = (raw_tsens_data - tsens_offset) / tsens_slope
        return temp



    def set_exposure_us(self, time_us):
        self._exposure_us = time_us
        imager = self.imager
        imager.setSensorI2C(self.sensor_i2c)
        imager.type(self.sensor_type)

        value = int(time_us)

        # Split value
        b3 = value >> 24 & 255
        b2 = value >> 16 & 255
        b1 = value >> 8 & 255
        b0 = value & 255

        imager.write(0xe004,  0)
        imager.write(0xe000,  1)
        imager.write(0x000E, b3)
        imager.write(0x000F, b2)
        imager.write(0x0010, b1)
        imager.write(0x0011, b0)

    def set_analog_gain(self, gain):
        return super().set_analog_gain(gain)

    def set_digital_gain(self, gain):
        imager = self.imager
        imager.setSensorI2C(self.sensor_i2c)
        imager.type(self.sensor_type)

        gain = int(gain*16-1)
        self.digital_gain = float((gain+1)/16)
        # Get the driver access
        imager.setSensorI2C(0x36)
        imager.type(1)
        imager.write(0xe004,  0)
        imager.write(0xe000,  1)
        imager.write(0x0024,gain)
        return super().set_digital_gain(gain)

    def write_register(self, address, value):
        return super().write_register(address, value)

    def read_register(self, address):
        return super().read_register(address)


    def set_analog_gain(self, gain):
        return super().set_analog_gain(gain)

    def set_digital_gain(self, gain):
        imager = self.imager
        imager.setSensorI2C(self.sensor_i2c)
        imager.type(self.sensor_type)

        gain = int(gain*16-1)
        self.digital_gain = float((gain+1)/16)
        # Get the driver access
        imager.setSensorI2C(0x36)
        imager.type(1)
        imager.write(0xe004,  0)
        imager.write(0xe000,  1)
        imager.write(0x0024,gain)
        return super().set_digital_gain(gain)

    def write_register(self, address, value):
        return super().write_register(address, value)

    def read_register(self, address):
        return super().read_register(address)


#######setters and getters########
        # self.sensor_i2c = 54
        # self.sensor_type = 1
        # self.bit_mode = ''
        # self.digital_gain = 1
        # self.analog_gain = 1
        # self.bsp = 1
        # self.mirror = 0
        # self.exposure_us = 1000
        # self.pixel_correction = 1
        # self.temp_cor=True
        # self.temperature = None
        # self.low_fpn=True
        # self.illum = False
        # self.clock = 38.4

    @property
    def analog_gain(self):
        '''Get the programmed exposure time.

        Returns
        -------
        float : 
            exposure time in us
        '''
        print('property exposure called')
        return self._analog_gain    

    @analog_gain.setter
    def analog_gain(self, analog_gain):
        '''Set analog gain and related registers.

        Parameters
        ----------
        gain : int
            Analog gain (1, 2 or 4)
        '''
        print('setting again with setter')
        self.set_analog_gain(analog_gain)



    @property
    def digital_gain(self):
        '''Get the programmed exposure time.

        Returns
        -------
        float : 
            exposure time in us
        '''
        print('property exposure called')
        return self._digital_gain    

    @digital_gain.setter
    def digital_gain(self, digital_gain):
        '''Set analog gain and related registers.

        Parameters
        ----------
        gain : int
            Analog gain (1, 2 or 4)
        '''
        print('setting again with setter')
        self.set_digital_gain(digital_gain)


    @property
    def exposure_us(self):
        '''Get the programmed exposure time.

        Returns
        -------
        float : 
            exposure time in us
        '''
        print('property exposure called')
        return self._exposure_us    

    @exposure_us.setter
    def exposure_us(self, time_us):
        '''Set the exposure time in us in master mode.

        Parameters
        ----------
        exposure : float
            Exposure time of the sensor
        '''
        print('setting exposure with setter')
        self.set_exposure_us(time_us)
