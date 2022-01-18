def controlInit():
    controlParams = {
        "name": "Read order",
        "comment": "read order",
        "type": "two_checkbuttons",
        "cb1_label_text": "Mirror:",
        "cb1_onvalue": 1,
        "cb1_offvalue": 0,
        "cb1_default": "off",
        "cb1_xpad": (0, 0),
        "cb2_label_text": "Flip:",
        "cb2_onvalue": 1,
        "cb2_offvalue": 0,
        "cb2_default": "off",
        "cb2_xpad": (0, 77),
        "unit": "on/off",
    }
    return controlParams

def controlGetCb1(imager, sreg):
    # I2C address and length (addr=16bit, val=8bit)
    imager.setSensorI2C(0x54)
    imager.type(1)

    # Read register
    value = imager.read(0x209C)

    sreg.set(value)

    return value

def controlGetCb2(imager, sreg):
    # I2C address and length (addr=16bit, val=8bit)
    imager.setSensorI2C(0x54)
    imager.type(1)

    # Read register
    value = imager.read(0x1095)

    sreg.set(value)

    return value

def controlSetCb1(imager, variable):
    # I2C address and length (addr=16bit, val=8bit)
    imager.disablePrint()
    imager.setSensorI2C(0x54)
    imager.type(1)
    imager.enablePrint()

    # Get checkbutton value
    value = int(variable.get())

    # Write to register
    if (value == 0):
        imager.write(0x209C, 0)
    else:
        imager.write(0x209C, 1)


def controlSetCb2(imager, variable):
    # I2C address and length (addr=16bit, val=8bit)
    imager.disablePrint()
    imager.setSensorI2C(0x54)
    imager.type(1)
    imager.enablePrint()

    # Get checkbutton value
    value = int(variable.get())

    # Write to register
    if (value == 0):
        imager.write(0x1095, 0)
    else:
        imager.write(0x1095, 1)


def execCmd():
    print('executed')