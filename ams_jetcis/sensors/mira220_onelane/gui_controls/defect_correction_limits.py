def controlInit():
    controlParams = {
        "name": "Defect correction limits",
        "comment": "Choose a replacement limit",
        "type": "slider",
        "nb_widgets": 2,
        "min_1": 0.0,
        "max_1": 15.0,
        "default_1": 0.0,
        "step_1": 1.0,
        "min_2": 0.0,
        "max_2": 15.0,
        "default_2": 0.0,
        "step_2": 1.0,
        "unit": "Low/High",
        "auto": False,
        "refresh": True,
    }
    return controlParams


def controlGet_1(main_app, s):
    # Driver access
    imager = main_app.imager

    # I2C address and length (addr=16bit, val=8bit)
    imager.setSensorI2C(0x54)
    imager.type(1)

    # GUI new value
    value = imager.read(0x24dd)

    s.set(value)

    return value


def controlSet_1(main_app, sreg, event=None):
    # Get slider value
    input = float(sreg.get())

    # Get the driver access
    imager = main_app.imager

    # I2C address and length (addr=16bit, val=8bit)
    imager.disablePrint()
    imager.setSensorI2C(0x54)
    imager.type(1)

    # Write value to sensor
    imager.enablePrint()
    imager.write(0x24dd, input)

    # Updates the status of all Widgets
    imager.doWidgetUpdate()


def controlGet_2(main_app, s):
    # Driver access
    imager = main_app.imager

    # I2C address and length (addr=16bit, val=8bit)
    imager.setSensorI2C(0x54)
    imager.type(1)

    # GUI new value
    value = imager.read(0x24de)

    s.set(value)

    return value


def controlSet_2(main_app, sreg, event=None):
    # Get slider value
    input = float(sreg.get())

    # Get the driver access
    imager = main_app.imager

    # I2C address and length (addr=16bit, val=8bit)
    imager.disablePrint()
    imager.setSensorI2C(0x54)
    imager.type(1)

    # Write value to sensor
    imager.enablePrint()
    imager.write(0x24de, input)

    # Updates the status of all Widgets
    imager.doWidgetUpdate()


def execCmd():
    print('executed')
