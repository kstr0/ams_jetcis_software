

def execCmd(imager):
    imager.setSensorI2C(imager.sensori2c)
    imager.type(1)
    imager.write(0x4501, 0x08)
    imager.write(0x5e00, 0x80)
    pass
