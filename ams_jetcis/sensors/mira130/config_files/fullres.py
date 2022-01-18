# Version 2 provided by Philippe 11/02/2020

def getSensorInfo(imager):
    controlParams = {
        "width" : 1080,
        "height" : 1280,
        "widthDISP" : 1080*0.5,
        "heightDISP" : 1280*0.5,
        "widthDMA" : 1088,
        "heightDMA" : 1280,
        "bpp" : 10,
        "fps" : 30,
        "dtMode" : 0
    }
    return controlParams

def resetSensor(imager):
    # start PMIC
    imager.setSensorI2C(imager.sensori2c)
    imager.type(0) # Reg=8bit, val=8bit
    # set GPIO1=0
    imager.write(0x41, 0x04)
    # DCDC1=1.2V
    imager.write(0x00, 0x00)
    imager.write(0x04, 0x28)
    imager.write(0x06, 0x7F)
    imager.write(0x05, 0xA8)
    # DCDC2=0.0V
    imager.write(0x08, 0x00)
    # DCDC3=2.8V
    imager.write(0x02, 0x00)
    imager.write(0x0A, 0x2E)
    imager.write(0x0C, 0xFF)
    imager.write(0x0B, 0xAE)
    # DCDC4=1.8V
    imager.write(0x03, 0x00)
    imager.write(0x0D, 0x34)
    imager.write(0x0F, 0xBF)
    imager.write(0x0E, 0xB4)
    # LDO1=0.0V
    imager.write(0x11, 0x00)
    # LDO2=0.0V
    imager.write(0x14, 0x00)
    # LDO3=0.0V
    imager.write(0x17, 0x00)
    # LDO4=2.5V
    imager.write(0x1B, 0x32)
    imager.write(0x19, 0x32)
    imager.write(0x1A, 0xB2)
    # LDO5=0.0V
    imager.write(0x1C, 0x00)
    # LDO6=0.0V
    imager.write(0x1D, 0x00)
    # LDO7=0.0V
    imager.write(0x1E, 0x00)
    # LDO8=0.0V
    imager.write(0x1F, 0x00)
    # LDO9=0.0V
    imager.write(0x20, 0x00)
    # LDO10=0.0V
    imager.write(0x21, 0x00)
    # Enable master switch
    imager.write(0x62, 0x0D)
    # Keep LDOs always on
    imager.write(0x27, 0xFF)
    imager.write(0x28, 0xFF)
    imager.write(0x29, 0x00)
    imager.write(0x2A, 0x00)
    imager.write(0x2B, 0x00)
    # Enable green LED
    imager.write(0x44, 0x40)
    imager.write(0x4F, 0x02)
    imager.write(0x55, 0x10)
    imager.write(0x61, 0x20)
    # init sensor
    imager.setSensorI2C(imager.sensori2c)
    imager.type(1) # reg=16bit, val=8bit
    # set input clock speed to 27MHz
    imager.setmclk(24000000)
    imager.setDelay(0)
    # and reset sensor
    imager.reset(1)
    imager.wait(500)

    #uncomment to enable LED
    # LED DRIVER of PMIC config AS3648
    #imager.setSensorI2C(0x30)
    #imager.type(0) # Reg=8bit, val=8bit
    #imager.write(1,0xFE)
    #imager.write(2,0xFE)
    #imager.write(3,0x00)
    #imager.write(6,9)
    #imager.write(9,3)
    # I2C address LED and length (addr=8bit, val=8bit)
    imager.setSensorI2C(0x53)
    imager.type(0)

    # Turn off LED
    imager.write(0x10, 0x08)
    checkSensor(imager)

def checkSensor(imager):
    """
    Check if sensor is connected.
    either 30 or 32 as i2c address. 
    The newest boards have 0x30
    """
    imager.setSensorI2C(0x32)
    imager.type(1)
    # read ID 3107=1, 3108=32
    if imager.read(0x3107)>1 or imager.read(0x3108)>1:
        imager.sensori2c = 0x32
        print('Mira130 i2c is 0x32')

        return 0

    imager.setSensorI2C(0x30)
    imager.type(1)

    if imager.read(0x3107)>1 or imager.read(0x3108)>1:
        imager.sensori2c = 0x30
        print('Mira130 i2c is 0x30')

        return 0

    return 1
    

def initSensor(imager):
    imager.setSensorI2C(imager.sensori2c)
    imager.type(1)
    # read ID 3107=1, 3108=32
    imager.read(0x3107)
    imager.read(0x3108)
    imager.wait(100)
    imager.setSensorI2C(imager.sensori2c)
    imager.type(1)
    imager.write(0x0103,0x01)
    imager.write(0x0100,0x00)

#//PLL bypass
    imager.write(0x36e9,0x80)
    imager.write(0x36f9,0x80)

    imager.write(0x3018,0x32) # 2lanes
    imager.write(0x3019,0x0c)
    imager.write(0x301a,0xb4)
    imager.write(0x3031,0x0a) # RAW10
    imager.write(0x3032,0x60)
    imager.write(0x3038,0x44)
    imager.write(0x3207,0x17)
    imager.write(0x320c,0x05)
    imager.write(0x320d,0xdc)
    imager.write(0x320e,0x09)
    imager.write(0x320f,0x60)
    imager.write(0x3250,0xcc)
    imager.write(0x3251,0x02)
    imager.write(0x3252,0x09)
    imager.write(0x3253,0x5b)
    imager.write(0x3254,0x05)
    imager.write(0x3255,0x3b)
    imager.write(0x3306,0x78)
    imager.write(0x330a,0x00)
    imager.write(0x330b,0xc8)
    imager.write(0x330f,0x24)
    imager.write(0x3314,0x80)
    imager.write(0x3315,0x40)
    imager.write(0x3317,0xf0)
    imager.write(0x331f,0x12)
    imager.write(0x3364,0x00)
    imager.write(0x3385,0x41)
    imager.write(0x3387,0x41)
    imager.write(0x3389,0x09)
    imager.write(0x33ab,0x00)
    imager.write(0x33ac,0x00)
    imager.write(0x33b1,0x03)
    imager.write(0x33b2,0x12)
    imager.write(0x33f8,0x02)
    imager.write(0x33fa,0x01)
    imager.write(0x3409,0x08)
    imager.write(0x34f0,0xc0)
    imager.write(0x34f1,0x20)
    imager.write(0x34f2,0x03)
    imager.write(0x3622,0xf5)
    imager.write(0x3630,0x5c)
    imager.write(0x3631,0x80)
    imager.write(0x3632,0xc8)
    imager.write(0x3633,0x32)
    imager.write(0x3638,0x2a)
    imager.write(0x3639,0x07)
    imager.write(0x363b,0x48)
    imager.write(0x363c,0x83)
    imager.write(0x363d,0x10)
    imager.write(0x36ea,0x38)
    imager.write(0x36fa,0x25)
    imager.write(0x36fb,0x05)
    imager.write(0x36fd,0x04)
    imager.write(0x3900,0x11)
    imager.write(0x3901,0x05)
    imager.write(0x3902,0xc5)
    imager.write(0x3904,0x04)
    imager.write(0x3908,0x91)
    imager.write(0x391e,0x00)
    imager.write(0x3e01,0x53)
    imager.write(0x3e02,0xe0)
    imager.write(0x3e09,0x20)
    imager.write(0x3e0e,0xd2)
    imager.write(0x3e14,0xb0)
    imager.write(0x3e1e,0x7c)
    imager.write(0x3e26,0x20)
    imager.write(0x4418,0x38)
    imager.write(0x4503,0x10)
    imager.write(0x4837,0x21)
    imager.write(0x5000,0x0e)
    imager.write(0x540c,0x51)
    imager.write(0x550f,0x38)
    imager.write(0x5780,0x67)
    imager.write(0x5784,0x10)
    imager.write(0x5785,0x06)
    imager.write(0x5787,0x02)
    imager.write(0x5788,0x00)
    imager.write(0x5789,0x00)
    imager.write(0x578a,0x02)
    imager.write(0x578b,0x00)
    imager.write(0x578c,0x00)
    imager.write(0x5790,0x00)
    imager.write(0x5791,0x00)
    imager.write(0x5792,0x00)
    imager.write(0x5793,0x00)
    imager.write(0x5794,0x00)
    imager.write(0x5795,0x00)
    imager.write(0x5799,0x04)
    #//fsync output enable
    imager.write(0x300a,0x64)
    imager.write(0x3032,0xa0)
    imager.write(0x3217,0x09)
    imager.write(0x3218,0x5a) #//vts - 6
    #//PLL set
    imager.write(0x36e9,0x20)
    imager.write(0x36f9,0x24)
    imager.write(0x0100,0x01)
    return(0)

