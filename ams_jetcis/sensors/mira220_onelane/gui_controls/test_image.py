def controlInit():
    controlParams = {
        "name": "Test image",
        "comment": "test image",
        "type": "optionmenu",
        "nb_widgets": 1,
        "default_1": "Off",
        "option_list_1": ["Off", "Vertical", "Diagonal", "Walking 1", "Walking 0"],
        "unit": "pattern",
    }
    return controlParams

def controlGet_1(main_app, omvar):
    # Get the driver access
    imager = main_app.imager

    # I2C address and length (addr=16bit, val=8bit)
    imager.setSensorI2C(0x54)
    imager.type(1)

    # Read register
    value = imager.read(0x2091)

    # Translate
    if value == 0:
        gui_text = "Off"
    elif value == 1:
        gui_text = "Vertical"
    elif value == 17:
        gui_text = "Diagonal"
    elif value == 65:
        gui_text = "Walking 1"
    elif value == 81:
        gui_text = "Walking 0"
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
    imager.enablePrint()

    # Write register
    if value == "Off":
        imager.write(0x2091, 0)
    elif value == "Vertical":
        imager.write(0x2091, 1)
    elif value == "Diagonal":
        imager.write(0x2091, 17)
    elif value == "Walking 1":
        imager.write(0x2091, 65)
    elif value == "Walking 0":
        imager.write(0x2091, 81)
    else:
        imager.pr("ERROR: Wrong input")


def execCmd():
    print('executed')