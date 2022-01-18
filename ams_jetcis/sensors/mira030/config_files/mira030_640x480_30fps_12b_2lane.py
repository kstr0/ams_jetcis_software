# Version 1 (04/01/2021)

def getSensorInfo(imager):
    controlParams = {
        "width" : 640,
        "height" : 480,
        "widthDISP" : 640*0.3,
        "heightDISP" : 480*0.3,
        "widthDMA" : 640,
        "heightDMA" : 480,
        "bpp" : 12,
        "fps" : 30,
        "dtMode" : 0
    }
    return controlParams


def resetSensor(imager):
    imager.setSensorI2C(0x2d)
    imager.type(0)  # Reg=8bit, val=8bit

    # Disable master switch
    imager.write(0x62, 0x00)

    # Rewrite default LDO voltage registers
    imager.setSensorI2C(0x2d)
    imager.type(0) # Reg=8bit, val=8bit

    # DCDC1=0V
    imager.write(0x05, 0x00)
    # DCDC4=0V
    imager.write(0x0E, 0x0)
    # LDO1=0V 
    imager.write(0x11, 0x0)
    # LDO2=0.0V
    imager.write(0x14, 0x00)
    # LDO3=0.0V
    imager.write(0x17, 0x00)
    # LDO4=0V  
    imager.write(0x1A, 0x00)
    # LDO5=0.0V
    imager.write(0x1C, 0x00)
    # LDO6=0.0V
    imager.write(0x1D, 0x00)
    # LDO7=0V 
    imager.write(0x1E, 0x0)
    # LDO8=0.0V
    imager.write(0x1F, 0x00)
    # Disable LDO9 Lock
    imager.write(0x24, 0x48)
    # LDO9=2.8V AVDD 
    imager.write(0x20, 0x00)
    # LDO10=1.5V DVDD
    imager.write(0x21, 0x0)

    # Enable master switch
    time.sleep(50e-6)
    imager.write(0x62, 0x0D)  # enable master switch
    time.sleep(50e-6)

    # Keep LDOs always on
    time.sleep(50e-3)
    try:
        imager.read(0x20)
    except:
        pass
    imager.write(0x27, 0xFF)
    imager.write(0x28, 0xFF)
    imager.write(0x29, 0x00)
    imager.write(0x2A, 0x00)
    imager.write(0x2B, 0x00)

    ## Unused LDO off
    time.sleep(50e-6)
    # set GPIO1=0
    imager.write(0x41, 0x04)
    # DCDC2=0.0V SPARE_PWR1
    imager.write(0x01, 0x00)
    imager.write(0x08, 0x00)
    # DCDC3=0V SPARE_PWR1
    imager.write(0x02, 0x00)
    imager.write(0x0B, 0x00)
    # LDO1=0
    imager.write(0x11, 0x00)
    # LDO2=0.0V
    imager.write(0x14, 0x00)
    # LDO3=0.0V
    imager.write(0x17, 0x00)
    # LDO4=0V
    imager.write(0x1A, 0x00)
    # LDO5=0.0V
    imager.write(0x1C, 0x00)
    # LDO6=0.0V
    imager.write(0x1D, 0x00)
    # LDO7=0.0V
    imager.write(0x1E, 0x00)	
    # LDO8=0.0V
    imager.write(0x1F, 0x00)

    ## Enable 2.85V
    time.sleep(50e-6)

    # Disable LDO9 Lock
    imager.write(0x24, 0x48)
    # LDO9=2.8V AVDD
    imager.read(0x20)
    imager.write(0x20, 0xB8)
    imager.read(0x20)

    ## Enable 1.5V
    time.sleep(700e-6)
    # LDO10=1.5V VDDLO_ANA
    imager.write(0x21, 0x9C)

    ## Enable 1.80V
    time.sleep(50e-6)
    # DCDC1=1.8V VINLDO1p8 >=1P8
    imager.write(0x00, 0x00)
    imager.write(0x04, 0x34)
    imager.write(0x06, 0xBF)
    imager.write(0x05, 0xB4)
    # DCDC4=1.8V  (DOVDD, VDDIO) 
    imager.write(0x03, 0x00)
    imager.write(0x0D, 0x34)
    imager.write(0x0F, 0xBF)
    imager.write(0x0E, 0xB4)

    ## Enable CLK_IN
    # Enable GPIO2 for mclk XTALL
    time.sleep(50e-6)
    imager.write(0x42, 5)

    ## Enable green LED
    time.sleep(50e-6)
    imager.write(0x45, 0x40)
    imager.write(0x57, 0x02)
    imager.write(0x5D, 0x10)
    imager.write(0x61, 0x10)

    # I2C address LED and length (addr=8bit, val=8bit)
    imager.setSensorI2C(0x53)
    imager.type(0)
    # Turn off LED driver
    imager.write(0x10, 0x08)

    # init sensor
    imager.setSensorI2C(0x30)
    imager.type(1) # reg=16bit, val=8bit
    # set input clock speed to 27MHz
    imager.setmclk(24000000)
    imager.setDelay(0)
    # and reset sensor
    imager.reset(1)
    imager.wait(2000)

def checkSensor(imager):
    imager.setSensorI2C(0x30)
    imager.type(1)
    # read ID 3107=0, 3108=31
    imager.read(0x3107)
    imager.read(0x3108)

def initSensor(imager):
    imager.setSensorI2C(0x30)
    imager.type(1)
    # read ID 3107=0, 3108=31
    imager.read(0x3107)
    imager.read(0x3108)
    imager.write(0x0103, 0x01)
    imager.write(0x0100, 0x00)
    imager.write(0x36e9, 0x80)
    imager.write(0x36f9, 0x80)
    imager.write(0x3001, 0x00)
    imager.write(0x3000, 0x00)
    imager.write(0x300f, 0x0f)
    imager.write(0x3018, 0x33)
    imager.write(0x3019, 0xfc)
    imager.write(0x301c, 0x78)
    imager.write(0x301f, 0x10)
    imager.write(0x3031, 0x0c)
    imager.write(0x3037, 0x40)
    imager.write(0x303f, 0x01)
    imager.write(0x320c, 0x04)
    imager.write(0x320d, 0xb0)
    imager.write(0x320e, 0x07)
    imager.write(0x320f, 0xd0)
    imager.write(0x3220, 0x10)
    imager.write(0x3221, 0x60)
    imager.write(0x3250, 0xc0)
    imager.write(0x3251, 0x02)
    imager.write(0x3252, 0x02)
    imager.write(0x3253, 0xa6)
    imager.write(0x3254, 0x02)
    imager.write(0x3255, 0x07)
    imager.write(0x3304, 0x48)
    imager.write(0x3306, 0x38)
    imager.write(0x3309, 0x68)
    imager.write(0x330b, 0xe0)
    imager.write(0x330c, 0x18)
    imager.write(0x330f, 0x20)
    imager.write(0x3310, 0x10)
    imager.write(0x3314, 0x1e)
    imager.write(0x3315, 0x38)
    imager.write(0x3316, 0x40)
    imager.write(0x3317, 0x10)
    imager.write(0x3329, 0x34)
    imager.write(0x332d, 0x34)
    imager.write(0x332f, 0x38)
    imager.write(0x3335, 0x3c)
    imager.write(0x3344, 0x3c)
    imager.write(0x335b, 0x80)
    imager.write(0x335f, 0x80)
    imager.write(0x3366, 0x06)
    imager.write(0x3385, 0x31)
    imager.write(0x3387, 0x51)
    imager.write(0x3389, 0x01)
    imager.write(0x33b1, 0x03)
    imager.write(0x33b2, 0x06)
    imager.write(0x3621, 0xa4)
    imager.write(0x3622, 0x05)
    imager.write(0x3624, 0x47)
    imager.write(0x3630, 0x46)
    imager.write(0x3631, 0x48)
    imager.write(0x3633, 0x52)
    imager.write(0x3635, 0x18)
    imager.write(0x3636, 0x25)
    imager.write(0x3637, 0x89)
    imager.write(0x3638, 0x0f)
    imager.write(0x3639, 0x08)
    imager.write(0x363a, 0x00)
    imager.write(0x363b, 0x48)
    imager.write(0x363c, 0x06)
    imager.write(0x363d, 0x00)
    imager.write(0x363e, 0xf8)
    imager.write(0x3640, 0x00)
    imager.write(0x3641, 0x01)
    imager.write(0x36ea, 0x34)
    imager.write(0x36eb, 0x0f)
    imager.write(0x36ec, 0x1f)
    imager.write(0x36ed, 0x33)
    imager.write(0x36fa, 0x3a)
    imager.write(0x36fb, 0x00)
    imager.write(0x36fc, 0x01)
    imager.write(0x36fd, 0x03)
    imager.write(0x3908, 0x91)
    imager.write(0x3d08, 0x01)
    imager.write(0x3e01, 0x14)
    imager.write(0x3e02, 0x80)
    imager.write(0x3e06, 0x0c)
    imager.write(0x4500, 0x59)
    imager.write(0x4501, 0xc4)
    imager.write(0x4603, 0x00)
    imager.write(0x4809, 0x01)
    imager.write(0x4837, 0x38)
    imager.write(0x5011, 0x00)
    imager.write(0x36e9, 0x20)
    imager.write(0x36f9, 0x00)
    imager.write(0x0100, 0x01)
    imager.write(0x4418, 0x08)
    imager.write(0x4419, 0x8e)
    #imager.write(0x3314, 0x1e) [gain<2]
    #imager.write(0x3317, 0x10)
    #imager.write(0x3314, 0x4f) [4>gain>=2]
    #imager.write(0x3317, 0x0f)
    #imager.write(0x3314, 0x4f) [gain>=4]
    #imager.write(0x3317, 0x0f)
    return 0
