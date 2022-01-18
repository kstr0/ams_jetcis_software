def controlInit():
    # Time conversion factor in seconds
    row_length = 0x130
    f_clk_in = 38.4e6
    time_conversion = row_length / f_clk_in

    # Exposure max
    fps = 30
    vsize = 1400
    vblank = int(int(f_clk_in/row_length/fps) - vsize)
    fot_length = 986
    exposure_length_max = int(((row_length * (vsize + vblank) - fot_length) / f_clk_in) / time_conversion)

    # Parameters are in ms
    controlParams = {
        "name": "Exposure time",
        "comment": "Press enter after entering a value.",
        "type": "spinbox",
        "min": 0.0,
        "max": exposure_length_max * time_conversion * 1000,
        "default": 1263 * time_conversion * 1000,
        "step": 1,
        "unit": "ms",
    }
    return controlParams


def controlGet(main_app, spinbox, variable, event=None):
    global len_eoi, f_clk_in

    # Driver access
    imager = main_app.imager
    imager.disablePrint()

    # I2C address and length (addr=16bit, val=8bit)
    imager.setSensorI2C(0x54)
    imager.type(1)

    # Time conversion factor in seconds
    row_length = imager.read(0x102c) * (2 ** 8) + imager.read(0x102b)
    time_conversion = row_length / f_clk_in

    # Exposure time
    exposure_length = imager.read(0x100d) * (2 ** 8) + imager.read(0x100c)
    exposure_time = exposure_length * time_conversion * 1000

    # FOT
    fot_length = len_eoi

    # Update the max boundary value
    vsize = (imager.read(0x1088) % (2 ** 3)) * (2 ** 8) + imager.read(0x1087)
    vblank = imager.read(0x1013) * (2 ** 8) + imager.read(0x1012)
    exposure_length_max = int(((row_length * (vsize + vblank) - fot_length) / f_clk_in) / time_conversion)
    exposure_time_max = exposure_length_max * time_conversion * 1000
    spinbox["to"] = exposure_time_max

    # Set the variable
    if exposure_time > exposure_time_max:
        exposure_length = exposure_length_max

        # Split value
        high = exposure_length // (2 ** 8)
        low = exposure_length % (2 ** 8)

        # Write to registers
        imager.write(0x100c, low)
        imager.write(0x100d, high)

        variable.set("{:.3f}".format(exposure_time_max))
    else:
        variable.set("{:.3f}".format(exposure_time))


def controlSet(main_app, value, event=None):
    global f_clk_in

    # Driver access
    imager = main_app.imager

    # I2C address and length (addr=16bit, val=8bit)
    imager.disablePrint()
    imager.setSensorI2C(0x54)
    imager.type(1)

    # Entry value
    try:
        value = float(value.get())
    except:
        value = 0.0

    # Given exposure time to the exposure length
    row_length = imager.read(0x102c) * (2 ** 8) + imager.read(0x102b)
    time_conversion = row_length / f_clk_in
    exposure_length = round(value / time_conversion / 1000)

    # Split value
    high = exposure_length // (2 ** 8)
    low = exposure_length % (2 ** 8)

    # Write to registers
    imager.enablePrint()
    imager.write(0x100c, low)
    imager.write(0x100d, high)

    # Remove cursor/focus
    main_app.statusArea.focus()

    # Updates the status of all Widgets
    imager.doWidgetUpdate()


def validate(spinbox, number=None):
    # Only allow numbers between from and to
    if number is None:
        number = spinbox.get()
    if number == "":
        return True
    try:
        if float(spinbox.cget("from")) <= float(number) <= float(spinbox.cget("to")):
            return True
    except ValueError:
        pass
    return False


def execCmd():
    print('executed')