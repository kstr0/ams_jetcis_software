def controlInit():
    controlParams = {
        "name": "Illumination",
        "comment": "Enable 940nm LED",
        "type": "checkbutton",
        "onvalue": 1,
        "offvalue": 0,
        "default": "off",
        "unit": "on/off",
    }
    return controlParams


def controlGet(main_app, sreg):
    # Driver access
    imager = main_app.imager

    # I2C address LED and length (addr=8bit, val=8bit)
    imager.setSensorI2C(0x53)
    imager.type(0)

    # General purpose reg
    status = imager.read(0x10)

    # I2C address sensor and length (addr=16bit, val=8bit)
    imager.setSensorI2C(0x54)
    imager.type(1)

    if status == 3:
        result = 1
    else:
        result = 0

    sreg.set(result)
    return result


def controlSet(main_app, variable):
    # Get the driver access
    imager = main_app.imager

    # Get checkbutton value
    value = int(variable.get())

    # Change bit 3
    if (value == 1):
        # I2C address LED and length (addr=8bit, val=8bit)
        imager.setSensorI2C(0x53)
        imager.type(0)

        # Flash mode, current, timeout
        imager.write(0x10, 0x00)
        imager.write(0xb0, 0x07)
        imager.write(0xc0, 0x05)

        # I2C address sensor and length (addr=16bit, val=8bit)
        imager.setSensorI2C(0x54)
        imager.type(1)

        # Enable trigger
        imager.write(0x10d7, 0x01)

    else:
        # I2C address LED and length (addr=8bit, val=8bit)
        imager.setSensorI2C(0x53)
        imager.type(0)

        # Turn off LED
        imager.write(0x10, 0x08)

        # I2C address sensor and length (addr=16bit, val=8bit)
        imager.setSensorI2C(0x54)
        imager.type(1)

        # Disable trigger
        imager.write(0x10d7, 0x00)


def execCmd():
    print('executed')
