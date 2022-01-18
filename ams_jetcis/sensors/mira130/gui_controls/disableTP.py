
def execCmd(imager):
    imager.setSensorI2C(imager.sensori2c)

    imager.type(1)
    imager.write(0x4501, 0x00)
    imager.write(0x5e00, 0x00)
    pass
