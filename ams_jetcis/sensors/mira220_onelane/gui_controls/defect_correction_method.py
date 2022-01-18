def controlInit():
    controlParams = {
        "name": "Defect correction",
        "comment": "Choose a replacement method",
        "type": "optionmenu",
        "nb_widgets": 3,
        "default_1": "Off",
        "option_list_1": ["Off", "Kernel", "Line"],
        "default_2": "Median",
        "option_list_2": ["Median", "Mean", "Minimum", "Maximum"],
        "default_3": "Mode 0",
        "option_list_3": ["Mode 0", "Mode 1"],
        "unit": "method",
    }
    return controlParams


def controlGet_1(main_app, omvar):
    # Get the driver access
    imager = main_app.imager

    # I2C address and length (addr=16bit, val=8bit)
    imager.setSensorI2C(0x54)
    imager.type(1)

    # Read register
    value = imager.read(0x24dc) % (2 ** 2)

    # Translate
    if (value == 0) or (value == 2):
        gui_text = "Off"
    elif value == 1:
        gui_text = "Kernel"
    elif value == 3:
        gui_text = "Line"
    else:
        imager.pr("ERROR: Wrong input")

    # Set variable
    omvar.set(gui_text)

    return gui_text


def controlSet_1(main_app, variable, event=None):
    # Get checkbutton value
    value = variable.get()

    # Get the driver access
    imager = main_app.imager

    # I2C address and length (addr=16bit, val=8bit)
    imager.disablePrint()
    imager.setSensorI2C(0x54)
    imager.type(1)

    # Read register and convert to 8 bit
    reg_b = format(imager.read(0x24dc), '08b')
    imager.enablePrint()

    # Write register
    if value == "Off":
        imager.write(0x24dc, int(reg_b[:6] + '00', 2))
    elif value == "Kernel":
        imager.write(0x24dc, int(reg_b[:6] + '01', 2))
    elif value == "Line":
        imager.write(0x24dc, int(reg_b[:6] + '11', 2))
    else:
        imager.pr("ERROR: Wrong input")


def controlGet_2(main_app, omvar):
    # Get the driver access
    imager = main_app.imager

    # I2C address and length (addr=16bit, val=8bit)
    imager.setSensorI2C(0x54)
    imager.type(1)

    # Read register
    value = imager.read(0x24dc)
    value = (value // (2 ** 4)) % (2 ** 2)

    # Translate
    if value == 0:
        gui_text = "Median"
    elif value == 1:
        gui_text = "Mean"
    elif value == 2:
        gui_text = "Minimum"
    elif value == 3:
        gui_text = "Maximum"
    else:
        imager.pr("ERROR: Wrong input")

    # Set variable
    omvar.set(gui_text)

    return gui_text


def controlSet_2(main_app, variable, event=None):
    # Get checkbutton value
    value = variable.get()

    # Get the driver access
    imager = main_app.imager

    # I2C address and length (addr=16bit, val=8bit)
    imager.disablePrint()
    imager.setSensorI2C(0x54)
    imager.type(1)

    # Read register and convert to 8 bit
    reg_b = format(imager.read(0x24dc), '08b')
    imager.enablePrint()

    # Write register
    if value == "Median":
        imager.write(0x24dc, int(reg_b[:2] + '00' + reg_b[4:], 2))
    elif value == "Mean":
        imager.write(0x24dc, int(reg_b[:2] + '01' + reg_b[4:], 2))
    elif value == "Minimum":
        imager.write(0x24dc, int(reg_b[:2] + '10' + reg_b[4:], 2))
    elif value == "Maximum":
        imager.write(0x24dc, int(reg_b[:2] + '11' + reg_b[4:], 2))
    else:
        imager.pr("ERROR: Wrong input")


def controlGet_3(main_app, omvar):
    # Get the driver access
    imager = main_app.imager

    # I2C address and length (addr=16bit, val=8bit)
    imager.setSensorI2C(0x54)
    imager.type(1)

    # Read register
    value = imager.read(0x24df) % 2

    # Translate
    if value == 0:
        gui_text = "Mode 0"
    elif value == 1:
        gui_text = "Mode 1"
    else:
        imager.pr("ERROR: Wrong input")

    # Set variable
    omvar.set(gui_text)

    return gui_text


def controlSet_3(main_app, variable, event=None):
    # Get checkbutton value
    value = variable.get()

    # Get the driver access
    imager = main_app.imager

    # I2C address and length (addr=16bit, val=8bit)
    imager.disablePrint()
    imager.setSensorI2C(0x54)
    imager.type(1)

    # Read register and convert to 8 bit
    reg_b = format(imager.read(0x24df), '08b')
    imager.enablePrint()

    # Write register
    if value == "Mode 0":
        imager.write(0x24df, int(reg_b[:7] + '0', 2))
    elif value == "Mode 1":
        imager.write(0x24df, int(reg_b[:7] + '1', 2))
    else:
        imager.pr("ERROR: Wrong input")


def execCmd():
    print('executed')