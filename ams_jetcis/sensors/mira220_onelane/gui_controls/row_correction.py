def controlInit():
    controlParams = {
        "name": "Row correction",
        "comment": "row noise",
        "type": "checkbutton",
        "onvalue": 1,
        "offvalue": 0,
        "default": "off",
        "unit": "on/off",
    }
    return controlParams

def controlGet(main_app, sreg):
    # Get the driver access
    imager = main_app.imager

    # I2C address and length (addr=16bit, val=8bit)
    imager.setSensorI2C(0x54)
    imager.type(1)

    # Read register and convert to 8 bit
    value = imager.read(0x204b)

    sreg.set(value % 2)

    return value % 2


def controlSet(main_app, variable):
    # Get checkbutton value
    value = int(variable.get())

    # Get the driver access
    imager = main_app.imager

    # I2C address and length (addr=16bit, val=8bit)
    imager.disablePrint()
    imager.setSensorI2C(0x54)
    imager.type(1)
    imager.enablePrint()

    # Write
    if (value == 0):
        imager.write(0x204b, 0)
    else:
        imager.write(0x204b, 7)


def execCmd():
    print('executed')