# Mira050 config

def getSensorInfo(imager):
    controlParams = {
        "width" : 600,
        "height" : 800,
        "widthDISP" : 600,
        "heightDISP" : 800,
        "widthDMA" : 608,
        "heightDMA" : 800,
        "bpp" : 10,
        "fps" : 90,
        "dtMode" : 2
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
    imager.write(0x1A, 0x00)
    # Disable LDO9 Lock
    imager.write(0x24, 0x48)
    # LDO9=2.85V VDDHI
    imager.read(0x20)
    imager.write(0x20, 0xB9)
    imager.read(0x20)

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
    imager.write(0xE000, 0)
    imager.write(0xE1E4, 0)
    imager.write(0xE1E5, 19)
    imager.write(0xE1E2, 23)
    imager.write(0xE1E3, 136)
    imager.write(0xE1E6, 0)
    imager.write(0xE1E7, 202)
    imager.write(0xE16C, 1)
    imager.write(0xE16B, 1)
    imager.write(0xE16D, 50)
    imager.write(0xE31F, 0)
    imager.write(0xE320, 10)
    imager.write(0xE321, 4)
    imager.write(0xE322, 131)
    imager.write(0xE1A2, 0)
    imager.write(0xE1A3, 1)
    imager.write(0xE1A4, 4)
    imager.write(0xE1A5, 122)
    imager.write(0xE19E, 0)
    imager.write(0xE19F, 0)
    imager.write(0xE1A6, 0)
    imager.write(0xE1A7, 152)
    imager.write(0xE1A8, 5)
    imager.write(0xE1A9, 17)
    imager.write(0xE1A0, 0)
    imager.write(0xE1A1, 76)
    imager.write(0xE1B0, 0)
    imager.write(0xE1B1, 95)
    imager.write(0xE16E, 44)
    imager.write(0xE16F, 0)
    imager.write(0xE170, 0)
    imager.write(0xE171, 134)
    imager.write(0xE172, 0)
    imager.write(0xE173, 0)
    imager.write(0xE174, 0)
    imager.write(0xE175, 0)
    imager.write(0xE176, 0)
    imager.write(0xE177, 0)
    imager.write(0xE178, 0)
    imager.write(0xE179, 0)
    imager.write(0xE17A, 0)
    imager.write(0xE17B, 0)
    imager.write(0xE17C, 0)
    imager.write(0xE17D, 0)
    imager.write(0xE208, 1)
    imager.write(0xE209, 240)
    imager.write(0xE20A, 3)
    imager.write(0xE20B, 77)
    imager.write(0xE20C, 2)
    imager.write(0xE20D, 16)
    imager.write(0xE20E, 3)
    imager.write(0xE20F, 1)
    imager.write(0xE210, 0)
    imager.write(0xE211, 19)
    imager.write(0xE212, 0)
    imager.write(0xE213, 3)
    imager.write(0xE214, 3)
    imager.write(0xE215, 239)
    imager.write(0xE216, 3)
    imager.write(0xE217, 243)
    imager.write(0xE218, 3)
    imager.write(0xE219, 244)
    imager.write(0xE21A, 0)
    imager.write(0xE21B, 33)
    imager.write(0xE21C, 0)
    imager.write(0xE21D, 2)
    imager.write(0xE21E, 1)
    imager.write(0xE21F, 242)
    imager.write(0xE220, 3)
    imager.write(0xE221, 113)
    imager.write(0xE222, 0)
    imager.write(0xE223, 33)
    imager.write(0xE224, 3)
    imager.write(0xE225, 240)
    imager.write(0xE226, 3)
    imager.write(0xE227, 241)
    imager.write(0xE228, 3)
    imager.write(0xE229, 242)
    imager.write(0xE22A, 3)
    imager.write(0xE22B, 245)
    imager.write(0xE22C, 3)
    imager.write(0xE22D, 246)
    imager.write(0xE22E, 0)
    imager.write(0xE22F, 33)
    imager.write(0xE230, 0)
    imager.write(0xE231, 2)
    imager.write(0xE232, 1)
    imager.write(0xE233, 242)
    imager.write(0xE234, 3)
    imager.write(0xE235, 117)
    imager.write(0xE236, 3)
    imager.write(0xE237, 255)
    imager.write(0xE238, 3)
    imager.write(0xE239, 49)
    imager.write(0xE23A, 1)
    imager.write(0xE23B, 240)
    imager.write(0xE23C, 3)
    imager.write(0xE23D, 135)
    imager.write(0xE23E, 0)
    imager.write(0xE23F, 10)
    imager.write(0xE240, 0)
    imager.write(0xE241, 11)
    imager.write(0xE242, 1)
    imager.write(0xE243, 249)
    imager.write(0xE244, 3)
    imager.write(0xE245, 13)
    imager.write(0xE246, 0)
    imager.write(0xE247, 7)
    imager.write(0xE248, 3)
    imager.write(0xE249, 239)
    imager.write(0xE24A, 3)
    imager.write(0xE24B, 243)
    imager.write(0xE24C, 3)
    imager.write(0xE24D, 244)
    imager.write(0xE24E, 3)
    imager.write(0xE24F, 0)
    imager.write(0xE250, 0)
    imager.write(0xE251, 7)
    imager.write(0xE252, 0)
    imager.write(0xE253, 12)
    imager.write(0xE254, 1)
    imager.write(0xE255, 241)
    imager.write(0xE256, 3)
    imager.write(0xE257, 67)
    imager.write(0xE258, 1)
    imager.write(0xE259, 248)
    imager.write(0xE25A, 3)
    imager.write(0xE25B, 16)
    imager.write(0xE25C, 0)
    imager.write(0xE25D, 7)
    imager.write(0xE25E, 3)
    imager.write(0xE25F, 240)
    imager.write(0xE260, 3)
    imager.write(0xE261, 241)
    imager.write(0xE262, 3)
    imager.write(0xE263, 242)
    imager.write(0xE264, 3)
    imager.write(0xE265, 245)
    imager.write(0xE266, 3)
    imager.write(0xE267, 246)
    imager.write(0xE268, 3)
    imager.write(0xE269, 0)
    imager.write(0xE26A, 2)
    imager.write(0xE26B, 135)
    imager.write(0xE26C, 0)
    imager.write(0xE26D, 1)
    imager.write(0xE26E, 3)
    imager.write(0xE26F, 255)
    imager.write(0xE270, 3)
    imager.write(0xE271, 49)
    imager.write(0xE272, 3)
    imager.write(0xE273, 167)
    imager.write(0xE274, 0)
    imager.write(0xE275, 10)
    imager.write(0xE276, 0)
    imager.write(0xE277, 11)
    imager.write(0xE278, 1)
    imager.write(0xE279, 249)
    imager.write(0xE27A, 3)
    imager.write(0xE27B, 13)
    imager.write(0xE27C, 0)
    imager.write(0xE27D, 7)
    imager.write(0xE27E, 3)
    imager.write(0xE27F, 239)
    imager.write(0xE280, 3)
    imager.write(0xE281, 243)
    imager.write(0xE282, 3)
    imager.write(0xE283, 244)
    imager.write(0xE284, 3)
    imager.write(0xE285, 0)
    imager.write(0xE286, 0)
    imager.write(0xE287, 23)
    imager.write(0xE288, 3)
    imager.write(0xE289, 148)
    imager.write(0xE28A, 0)
    imager.write(0xE28B, 7)
    imager.write(0xE28C, 3)
    imager.write(0xE28D, 240)
    imager.write(0xE28E, 3)
    imager.write(0xE28F, 241)
    imager.write(0xE290, 3)
    imager.write(0xE291, 242)
    imager.write(0xE292, 3)
    imager.write(0xE293, 245)
    imager.write(0xE294, 3)
    imager.write(0xE295, 246)
    imager.write(0xE296, 3)
    imager.write(0xE297, 0)
    imager.write(0xE298, 0)
    imager.write(0xE299, 7)
    imager.write(0xE29A, 3)
    imager.write(0xE29B, 0)
    imager.write(0xE29C, 3)
    imager.write(0xE29D, 255)
    imager.write(0xE29E, 3)
    imager.write(0xE29F, 0)
    imager.write(0xE2A0, 3)
    imager.write(0xE2A1, 255)
    imager.write(0xE2A2, 2)
    imager.write(0xE2A3, 135)
    imager.write(0xE2A4, 3)
    imager.write(0xE2A5, 2)
    imager.write(0xE2A6, 0)
    imager.write(0xE2A7, 22)
    imager.write(0xE2A8, 0)
    imager.write(0xE2A9, 51)
    imager.write(0xE2AA, 0)
    imager.write(0xE2AB, 4)
    imager.write(0xE2AC, 0)
    imager.write(0xE2AD, 17)
    imager.write(0xE2AE, 3)
    imager.write(0xE2AF, 9)
    imager.write(0xE2B0, 0)
    imager.write(0xE2B1, 2)
    imager.write(0xE2B2, 0)
    imager.write(0xE2B3, 32)
    imager.write(0xE2B4, 0)
    imager.write(0xE2B5, 181)
    imager.write(0xE2B6, 0)
    imager.write(0xE2B7, 229)
    imager.write(0xE2B8, 0)
    imager.write(0xE2B9, 18)
    imager.write(0xE2BA, 0)
    imager.write(0xE2BB, 71)
    imager.write(0xE2BC, 0)
    imager.write(0xE2BD, 39)
    imager.write(0xE2BE, 0)
    imager.write(0xE2BF, 181)
    imager.write(0xE2C0, 0)
    imager.write(0xE2C1, 229)
    imager.write(0xE2C2, 0)
    imager.write(0xE2C3, 0)
    imager.write(0xE2C4, 0)
    imager.write(0xE2C5, 4)
    imager.write(0xE2C6, 0)
    imager.write(0xE2C7, 67)
    imager.write(0xE2C8, 0)
    imager.write(0xE2C9, 1)
    imager.write(0xE2CA, 0)
    imager.write(0xE2CB, 39)
    imager.write(0xE2CC, 0)
    imager.write(0xE2CD, 8)
    imager.write(0xE2CE, 3)
    imager.write(0xE2CF, 255)
    imager.write(0xE2D0, 1)
    imager.write(0xE2D1, 248)
    imager.write(0xE2D2, 3)
    imager.write(0xE2D3, 28)
    imager.write(0xE2D4, 0)
    imager.write(0xE2D5, 23)
    imager.write(0xE2D6, 0)
    imager.write(0xE2D7, 8)
    imager.write(0xE2D8, 3)
    imager.write(0xE2D9, 255)
    imager.write(0xE2DA, 0)
    imager.write(0xE2DB, 56)
    imager.write(0xE2DC, 0)
    imager.write(0xE2DD, 23)
    imager.write(0xE2DE, 0)
    imager.write(0xE2DF, 8)
    imager.write(0xE2E0, 3)
    imager.write(0xE2E1, 255)
    imager.write(0xE2E2, 3)
    imager.write(0xE2E3, 255)
    imager.write(0xE2E4, 3)
    imager.write(0xE2E5, 255)
    imager.write(0xE2E6, 3)
    imager.write(0xE2E7, 255)
    imager.write(0xE2E8, 3)
    imager.write(0xE2E9, 255)
    imager.write(0xE2EA, 3)
    imager.write(0xE2EB, 255)
    imager.write(0xE2EC, 3)
    imager.write(0xE2ED, 255)
    imager.write(0xE2EE, 3)
    imager.write(0xE2EF, 255)
    imager.write(0xE2F0, 3)
    imager.write(0xE2F1, 255)
    imager.write(0xE2F2, 3)
    imager.write(0xE2F3, 255)
    imager.write(0xE2F4, 3)
    imager.write(0xE2F5, 255)
    imager.write(0xE2F6, 3)
    imager.write(0xE2F7, 255)
    imager.write(0xE2F8, 3)
    imager.write(0xE2F9, 255)
    imager.write(0xE2FA, 3)
    imager.write(0xE2FB, 255)
    imager.write(0xE2FC, 3)
    imager.write(0xE2FD, 255)
    imager.write(0xE2FE, 3)
    imager.write(0xE2FF, 255)
    imager.write(0xE300, 3)
    imager.write(0xE301, 255)
    imager.write(0xE302, 3)
    imager.write(0xE303, 255)
    imager.write(0xE1E9, 0)
    imager.write(0xE1E8, 24)
    imager.write(0xE1EA, 75)
    imager.write(0xE1EB, 77)
    imager.write(0xE1EC, 100)
    imager.write(0xE1ED, 105)
    imager.write(0x01EE, 10)
    imager.write(0x01EF, 140)
    imager.write(0x01F8, 15)
    imager.write(0x01D8, 1)
    imager.write(0x01DA, 1)
    imager.write(0x01DC, 1)
    imager.write(0x01DE, 1)
    imager.write(0x0189, 1)
    imager.write(0x01B7, 1)
    imager.write(0x01C1, 14)
    imager.write(0x01C2, 255)
    imager.write(0x01C3, 255)
    imager.write(0x01C9, 7)
    imager.write(0x01CC, 0)
    imager.write(0x01B8, 1)
    imager.write(0x01BA, 59)
    imager.write(0x0071, 1)
    imager.write(0x01B4, 1)
    imager.write(0x01B5, 1)
    imager.write(0x01F1, 1)
    imager.write(0x01F4, 1)
    imager.write(0x01F5, 1)
    imager.write(0x0314, 1)
    imager.write(0x0315, 1)
    imager.write(0x0316, 1)
    imager.write(0x0207, 0)
    imager.write(0x4207, 2)
    imager.write(0x2207, 2)
    imager.write(0x01AC, 0)
    imager.write(0x01AD, 95)
    imager.write(0x209D, 0)
    imager.write(0x0063, 1)
    imager.write(0x01F0, 13)
    imager.write(0x00D0, 2)
    imager.write(0x01F7, 15)
    imager.write(0x0309, 23)
    imager.write(0x030A, 19)
    imager.write(0x030B, 20)
    imager.write(0x030C, 27)
    imager.write(0x030E, 21)
    imager.write(0x030D, 21)
    imager.write(0x0310, 15)
    imager.write(0xE016, 0)
    imager.write(0xE017, 30)
    imager.write(0x2000, 0)
    imager.write(0x207C, 0)
    imager.write(0xE000, 0)
    imager.write(0x2077, 0)
    imager.write(0x2076, 142)
    imager.write(0x00CE, 2)
    imager.write(0x0070, 9)
    imager.write(0x016D, 50)
    imager.write(0x20C6, 0)
    imager.write(0x20C7, 0)
    imager.write(0x20C8, 1)
    imager.write(0x20C9, 0)
    imager.write(0x20CA, 0)
    imager.write(0x20CB, 1)
    imager.write(0x2075, 0)
    imager.write(0x2000, 0)
    imager.write(0x207C, 1)
    imager.write(0xE000, 0)
    imager.write(0x001E, 0)
    imager.write(0xE000, 0)
    imager.write(0x207E, 0)
    imager.write(0x207F, 0)
    imager.write(0x2080, 0)
    imager.write(0x2081, 3)
    imager.write(0x2082, 0)
    imager.write(0x2083, 2)
    imager.write(0x0090, 1)
    imager.write(0x2097, 0)
    imager.write(0x01B2, 0)
    imager.write(0x01B3, 100)
    imager.write(0xE000, 0)
    imager.write(0x0011, 3)
    imager.write(0x011D, 0)
    imager.write(0xE000, 0)
    imager.write(0x0012, 0)
    imager.write(0x0013, 38)
    imager.write(0x015A, 0)
    imager.write(0x015B, 27)
    imager.write(0x015C, 0)
    imager.write(0x015D, 27)
    imager.write(0x015E, 0)
    imager.write(0x015F, 27)
    imager.write(0x0162, 0)
    imager.write(0x0163, 6)
    imager.write(0x0164, 4)
    imager.write(0x0165, 88)
    imager.write(0x0166, 4)
    imager.write(0x0167, 88)
    imager.write(0xE000, 0)
    imager.write(0x005C, 0)
    imager.write(0x005D, 0)
    imager.write(0xE000, 0)
    imager.write(0x01BB, 200)
    imager.write(0x01BC, 192)
    imager.write(0x01F3, 2)
    imager.write(0x016E, 174)
    imager.write(0x0172, 0)
    imager.write(0x0173, 0)
    imager.write(0x016F, 255)
    imager.write(0x0170, 255)
    imager.write(0x0171, 174)
    imager.write(0x0174, 0)
    imager.write(0x0175, 0)
    imager.write(0x018B, 0)
    imager.write(0x018C, 178)
    imager.write(0x018D, 0)
    imager.write(0x018E, 152)
    imager.write(0x018F, 2)
    imager.write(0x0190, 178)
    imager.write(0x0193, 1)
    imager.write(0x0194, 100)
    imager.write(0xE1A2, 1)
    imager.write(0xE1A3, 172)
    imager.write(0xE31F, 1)
    imager.write(0xE320, 181)
    imager.write(0xE1A6, 2)
    imager.write(0xE1A7, 67)
    imager.write(0xE000, 0)
    imager.write(0xE009, 1)
    imager.write(0x212F, 1)
    imager.write(0x2130, 1)
    imager.write(0x2131, 1)
    imager.write(0x2132, 1)
    imager.write(0x2133, 1)
    imager.write(0x2134, 1)
    imager.write(0x2135, 1)
    imager.write(0xE0E1, 1)
    imager.write(0x018A, 1)
    imager.write(0x00E0, 1)
    imager.write(0xE004, 0)
    imager.write(0xE000, 1)
    imager.write(0xE02C, 0)
    imager.write(0xE02D, 0)
    imager.write(0xE02E, 2)
    imager.write(0xE02F, 87)
    imager.write(0xE030, 0)
    imager.write(0xE025, 0)
    imager.write(0xE02A, 0)
    imager.write(0x2029, 70)
    imager.write(0x0034, 1)
    imager.write(0x0035, 44)
    imager.write(0xE004, 0)
    imager.write(0x001E, 0)
    imager.write(0x001F, 1)
    imager.write(0x002B, 0)
    imager.write(0xE004, 0)
    imager.write(0x000E, 0)
    imager.write(0x000F, 0)
    imager.write(0x0010, 19)
    imager.write(0x0011, 136)
    imager.write(0x0012, 0)
    imager.write(0x0013, 0)
    imager.write(0x0014, 0)
    imager.write(0x0015, 0)
    imager.write(0xE004, 0)
    imager.write(0x0032, 6)
    imager.write(0x0033, 103)
    imager.write(0xE004, 0)
    imager.write(0x0007, 6)
    imager.write(0x0008, 0)
    imager.write(0x0009, 0)
    imager.write(0x000A, 65)
    imager.write(0x000B, 25)
    imager.write(0xE004, 0)
    imager.write(0x0024, 15)
    imager.write(0xE004, 0)
    imager.write(0x0031, 0)
    imager.write(0xE004, 0)
    imager.write(0x0026, 0)
    imager.write(0xE004, 0)
    imager.write(0x001C, 0)
    imager.write(0x0019, 0)
    imager.write(0x001A, 7)
    imager.write(0x001B, 83)
    imager.write(0x0016, 8)
    imager.write(0x0017, 0)
    imager.write(0x0018, 0)
    imager.write(0xE004, 0)
    imager.write(0x001D, 0)
    imager.write(0xE004, 0)
    imager.write(0xE000, 1)
    imager.write(0x001E, 0)
    imager.write(0x001F, 1)
    imager.write(0x002B, 0)
    imager.write(0xE004, 1)
    imager.write(0x001E, 0)
    imager.write(0x001F, 1)
    imager.write(0x002B, 0)
    imager.write(0xE000, 0)
    imager.write(0x001F, 0)
    imager.write(0x0020, 0)
    imager.write(0x0023, 0)
    imager.write(0x0024, 3)
    imager.write(0x0025, 32)
    imager.write(0x0026, 0)
    imager.write(0x0027, 8)
    imager.write(0x0028, 0)
    imager.write(0x0029, 0)
    imager.write(0x002A, 0)
    imager.write(0x002B, 0)
    imager.write(0x002C, 0)
    imager.write(0x002D, 0)
    imager.write(0x002E, 0)
    imager.write(0x002F, 0)
    imager.write(0x0030, 0)
    imager.write(0x0031, 0)
    imager.write(0x0032, 0)
    imager.write(0x0033, 0)
    imager.write(0x0034, 0)
    imager.write(0x0035, 0)
    imager.write(0x0036, 0)
    imager.write(0x0037, 0)
    imager.write(0x0038, 0)
    imager.write(0x0039, 0)
    imager.write(0x003A, 0)
    imager.write(0x003B, 0)
    imager.write(0x003C, 0)
    imager.write(0x003D, 0)
    imager.write(0x003E, 0)
    imager.write(0x003F, 0)
    imager.write(0x0040, 0)
    imager.write(0x0041, 0)
    imager.write(0x0042, 0)
    imager.write(0x0043, 0)
    imager.write(0x0044, 0)
    imager.write(0x0045, 0)
    imager.write(0x0046, 0)
    imager.write(0x0047, 0)
    imager.write(0x0048, 0)
    imager.write(0x0049, 0)
    imager.write(0x004A, 0)
    imager.write(0x004B, 0)
    imager.write(0x004C, 0)
    imager.write(0x004D, 0)
    imager.write(0x004E, 0)
    imager.write(0x004F, 0)
    imager.write(0x0050, 0)
    imager.write(0x0051, 0)
    imager.write(0x0052, 0)
    imager.write(0x0053, 0)
    imager.write(0x0054, 0)
    imager.write(0x0055, 0)
    imager.write(0xE000, 0)
    imager.write(0xE1FA, 1)
    imager.write(0xE000, 0)
    imager.write(0x0066, 0)
    imager.write(0x0067, 100)
    imager.write(0x0064, 1)
    imager.write(0x0064, 0)
    imager.write(0x0000, 0)
    imager.write(0x0065, 0)
    imager.write(0x0000, 0)
    imager.write(0x006C, 0)
    imager.write(0x006D, 30)
    imager.write(0x006E, 116)
    imager.write(0x006F, 251)
    imager.write(0xE000, 0)
    imager.write(0x01D9, 1)
    imager.write(0x00EB, 13)
    imager.write(0x01DB, 1)
    imager.write(0x00EC, 17)
    imager.write(0x01DD, 1)
    imager.write(0x00ED, 6)
    imager.write(0x01DF, 1)
    imager.write(0x00EE, 2)
    imager.write(0x20A0, 1)
    imager.write(0x209F, 4)
    imager.write(0x20BD, 1)
    imager.write(0x20BC, 0)
    imager.write(0xE000, 0)
    imager.write(0xE1B5, 0)
    imager.write(0xE000, 0)
    imager.write(0xE1BE, 152)
    imager.write(0xE000, 0)
    imager.write(0xE1BF, 60)
    imager.write(0xE000, 0)
    imager.write(0xE1C0, 115)
    imager.write(0xE000, 0)
    imager.write(0xE0F0, 1)
    imager.write(0xE000, 0)
    imager.write(0xE0EF, 5)
    imager.write(0xE000, 0)
    imager.write(0xE0F2, 1)
    imager.write(0xE000, 0)
    imager.write(0xE0F1, 15)
    imager.write(0xE000, 0)
    imager.write(0xE000, 1)
    imager.write(0xE004, 0)
    imager.write(0xE000, 1)
    imager.write(0xE004, 1)

    return 0
