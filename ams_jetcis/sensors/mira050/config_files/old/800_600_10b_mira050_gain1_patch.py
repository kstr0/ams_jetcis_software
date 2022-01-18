# Mira050 config
"""
Improve noise:
Vddpix and vddana short
Turn off vdd ana LDO
Change vddpix to 2.15V
"""
def getSensorInfo(imager):
    controlParams = {
        "width" : 600,
        "height" : 800,
        "widthDISP" : 600,
        "heightDISP" : 800,
        "widthDMA" : 608,
        "heightDMA" : 800,
        "bpp" : 12,
        "fps" : 30,
        "dtMode" : 0
    }
    return controlParams


def resetSensor(imager):
    #### PMIC I2C config ####
    imager.setSensorI2C(0x2d)
    imager.type(0)  # Reg=8bit, val=8bit

    #### Disable master switch ####
    imager.write(0x62, 0x00)

    # Set all voltages to 0

    # DCDC1=0V
    imager.write(0x05, 0x00)
    # DCDC4=0V
    imager.write(0x0E, 0x0)
    # LDO1=0V VDDLO_PLL
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
    # LDO9=0V VDDHI
    imager.write(0x20, 0x00)
    # LDO10=0V VDDLO_ANA
    imager.write(0x21, 0x0)

    #### Enable master switch ####
    time.sleep(50e-6)
    imager.write(0x62, 0x0D)  # enable master switch
    time.sleep(50e-6)

    # start PMIC
    # Keep LDOs always on
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
    # LDO2=0.0V
    imager.write(0x14, 0x00)
    # LDO3=0.0V
    imager.write(0x17, 0x00)
    # LDO5=0.0V
    imager.write(0x1C, 0x00)
    # LDO6=0.0V
    imager.write(0x1D, 0x00)
    # LDO8=0.0V
    imager.write(0x1F, 0x00)

    imager.write(0x42, 4)

    ## Enable 2.85V
    time.sleep(50e-6)
    # LDO4=2.85V VDDHI alternativ
    imager.write(0x1A, 0b10111000)
    # Disable LDO9 Lock
    imager.write(0x24, 0x48)
    # LDO9=2.85V VDDHI
    imager.read(0x20)
    imager.write(0x20, 0xb9)#b9
    imager.read(0x20)
    print('hier')
    #VPIXH on cob = vdd25A on interposer = LDO4 on pmic 
    #VPIXH should connect to VDD28 on pcb, or enable 4th supply
    imager.read(0x19)
    imager.write(0x19, 0b00111000)#b9
    imager.read(0x19)

    ## Enable 1.2V
    time.sleep(700e-6)
    # LDO1=1.2V VDDLO_PLL
    imager.write(0x12, 0x16)
    imager.write(0x10, 0x16)
    imager.write(0x11, 0b10010000)
    # LDO7=1.2V VDDLO_DIG
    imager.write(0x1E, 0b10010000)
    # LDO10=1.2V VDDLO_ANA
    imager.write(0x21, 0b10010000) 


    ## Enable 1.80V
    time.sleep(50e-6)
    # DCDC1=1.8V VINLDO1p8 >=1P8
    imager.write(0x00, 0x00)
    imager.write(0x04, 0x34)
    imager.write(0x06, 0xBF)
    imager.write(0x05, 0xB4)
    # DCDC4=1.8V VDDIO
    imager.write(0x03, 0x00)
    imager.write(0x0D, 0x34)
    imager.write(0x0F, 0xBF)
    imager.write(0x0E, 0xB4)


    ## Enable green LED
    time.sleep(50e-6)
    imager.write(0x43, 0x40) #leda
    imager.write(0x44, 0x40) #ledb
    imager.write(0x45, 0x40) #ledc

    imager.write(0x47, 0x02) #leda ctrl1
    imager.write(0x4F, 0x02) #ledb ctrl1
    imager.write(0x57, 0x02) #ledc ctrl1


    imager.write(0x4D, 0x01) #leda ctrl1
    imager.write(0x55, 0x10) #ledb ctrl7
    imager.write(0x5D, 0x10)#ledc ctrl7
    imager.write(0x61, 0b10000) #led seq -- use this to turn on leds. abc0000- 1110000 for all leds
    
    time.sleep(2)
    # uC, set atb and jtag high
    imager.setSensorI2C(0x0A)
    imager.type(0)
    imager.write(11,0b11001111)
    imager.write(15,0b00110000)
    imager.write(6,1)

    time.sleep(1)

    # Init sensor
    imager.setSensorI2C(0x36)
    imager.type(1) # reg=16bit, val=8bit
    # Set input clock speed to 24MHz
    #imager.setmclk(24000000)
    imager.setDelay(0)
    # Reset sensor
    time.sleep(0.02)
    
        # Reset sensor
    imager.reset(2) #keep in reset
    imager.wait(100)
    imager.reset(3) #leave reset
    imager.wait(2000) 
    imager.wait(2000)

    #checksensor 
    imager.setSensorI2C(0x36)
    imager.type(1)
    imager.write(0xE000,0)
    imager.write(0xE004,0)
    # Read ID 0x3=?, 0x4=?
    
    val=imager.read(0x11b)

    print(f'version is {val}')
    if val==33:
        print('mira050 detected')
        imager.setSensorI2C(0x2d)
        imager.type(0)  # Reg=8bit, val=8bit
        imager.write(0x61, 0b110000) #led seq -- use this to turn on leds. abc0000- 1110000 for all leds
    else:
        imager.setSensorI2C(0x2d)
        imager.type(0)  # Reg=8bit, val=8bit
        imager.write(0x61, 0b1010000) #led seq -- use this to turn on leds. abc0000- 1110000 for all leds
       

def checkSensor(imager):

    #checksensor 
    imager.setSensorI2C(0x36)
    imager.type(1)
    imager.write(0xE000,0)
    imager.write(0xE004,0)
    # Read ID 0x3=?, 0x4=?
    
    val=imager.read(0x11b)

    print(f'version is {val}')
    if val==33:
        print('mira050 detected')
        imager.setSensorI2C(0x2d)
        imager.type(0)  # Reg=8bit, val=8bit
        imager.write(0x61, 0b110000) #led seq -- use this to turn on leds. abc0000- 1110000 for all leds
    else:
        imager.setSensorI2C(0x2d)
        imager.type(0)  # Reg=8bit, val=8bit
        imager.write(0x61, 0b1010000) #led seq -- use this to turn on leds. abc0000- 1110000 for all leds
       

def initSensor(imager):
    imager.setSensorI2C(0x36)
    imager.type(1)
    import os
    print(f'cwd is {os.getcwd()}')
    print(f'file is {__file__}')

    fname = "../../Mira050/config_files/12-bit mode_gain_1_lowVpatch.txt"
    try:
        with open(fname, "r") as file:
            eobj = compile(file.read(), fname, "exec")
            exec(eobj, globals())
    except:
        print("ERROR: unable to execute init script")

    return 0
