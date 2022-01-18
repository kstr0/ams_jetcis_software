def controlInit():
    controlParams = {
        "name": "Analog gain",
        "comment": "analog gain",
        "type": "slider",
        "nb_widgets": 1,
        "min": 1.0,
        "max": 4.0,
        "default": 1.0,
        "step": 1.0,
        "unit": "x",
        "auto": False,
        "refresh": True,
    }
    return controlParams


# Table values
ana_table = [1, 2, 4]


def controlGet(main_app, s):
    # Driver access
    imager = main_app.imager

    # I2C address and length (addr=16bit, val=8bit)
    imager.setSensorI2C(0x54)
    imager.type(1)

    # Read the registers
    gain_value_read = imager.read(0x400A)

    # GUI new value
    ana_gain_gui = 8 / gain_value_read

    s.set(ana_gain_gui)

    return ana_gain_gui


def controlSet(main_app, sreg, event=None):
    global otp_gain_trims

    # Get slider value
    input = float(sreg.get())

    # Map input to discrete value
    mapped_input = min(ana_table, key=lambda x: abs(x - input))

    # Get the driver access
    imager = main_app.imager

    # I2C address and length (addr=16bit, val=8bit)
    imager.disablePrint()
    imager.setSensorI2C(0x54)
    imager.type(1)
    imager.enablePrint()

    # Write values to sensor
    if len(otp_gain_trims) == 0:
        if mapped_input == 1:
            imager.write(0x400A, 0x08)
            imager.write(0x402A, 0x63)
        elif mapped_input == 2:
            imager.write(0x400A, 0x04)
            imager.write(0x402A, 0x5F)
        elif mapped_input == 4:
            imager.write(0x400A, 0x02)
            imager.write(0x402A, 0x5E)
        else:
            # Print error in StatusArea
            imager.pr("ERROR: Only x1, x2, x4 is supported")
            imager.write(0x400A, 0x08)
            imager.write(0x402A, 0x63) 
    else:
        if mapped_input == 1:
            imager.write(0x400A, 0x08)
            imager.write(0x4009, otp_gain_trims[0])
        elif mapped_input == 2:
            imager.write(0x400A, 0x04)
            imager.write(0x4009, otp_gain_trims[1])
        elif mapped_input == 4:
            imager.write(0x400A, 0x02)
            imager.write(0x4009, otp_gain_trims[2])
        else:
            # Print error in StatusArea
            imager.pr("ERROR: Only x1, x2, x4 or x8 is supported")
            imager.write(0x400A, 0x08)
            imager.write(0x4009, otp_gain_trims[0])

    # Set GUI variable to mapped input
    sreg.set(mapped_input)

    # Updates the status of all Widgets
    imager.doWidgetUpdate()


def execCmd():
    print('executed')
