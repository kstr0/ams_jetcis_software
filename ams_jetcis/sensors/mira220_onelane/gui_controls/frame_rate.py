def controlInit():
    controlParams = {
        "name": "Frame rate",
        "comment": "Press enter after entering a value.",
        "type": "spinbox",
        "min": 1.0,
        "max": 90.0,
        "default": 30.0,
        "step": 1.0,
        "unit": "fps",
    }
    return controlParams


def controlGet(main_app, spinbox, variable, event=None):
    global len_eoi, f_clk_in

    # Get the driver access
    imager = main_app.imager
    imager.disablePrint()

    # I2C address and length (addr=16bit, val=8bit)
    imager.setSensorI2C(0x54)
    imager.type(1)

    # Actual fps
    row_length = imager.read(0x102c) * (2 ** 8) + imager.read(0x102b)
    vsize = (imager.read(0x1088) % (2 ** 3)) * (2 ** 8) + imager.read(0x1087)
    vblank = imager.read(0x1013) * (2 ** 8) + imager.read(0x1012)
    fps_actual = f_clk_in / (row_length * (vsize + vblank))

    # Update the min boundary value
    vblank_max = 0xffff
    fps_min = f_clk_in / (row_length * (vsize + vblank_max))
    spinbox["from_"] = fps_min

    # Update the max boundary value
    fot_length = len_eoi
    blvl_im_to_rd = imager.read(0x100a) * (2 ** 8) + imager.read(0x1009)
    glbl_rd_pause = imager.read(0x1007) * (2 ** 8) + imager.read(0x1006)
    vblank_min = int(fot_length / row_length) + 1 + blvl_im_to_rd + glbl_rd_pause
    fps_max = f_clk_in / (row_length * (vsize + vblank_min))
    spinbox["to"] = fps_max

    # Set the variable
    if fps_actual > fps_max:
        # Split value
        high = vblank_min // (2 ** 8)
        low = vblank_min % (2 ** 8)

        # Write to registers
        imager.write(0x1012, low)
        imager.write(0x1013, high)

        variable.set("{:.2f}".format(fps_max))

    elif fps_actual < fps_min:
        # Split value
        high = vblank_max // (2 ** 8)
        low = vblank_max % (2 ** 8)

        # Write to registers
        imager.write(0x1012, low)
        imager.write(0x1013, high)

        variable.set("{:.2f}".format(fps_min))

    else:
        variable.set("{:.2f}".format(fps_actual))


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
        fps = float(value.get())
    except:
        fps = 0.0

    # Vertical blanking
    row_length = imager.read(0x102c) * (2 ** 8) + imager.read(0x102b)
    vsize = (imager.read(0x1088) % (2 ** 3)) * (2 ** 8) + imager.read(0x1087)
    vblank = int(int(f_clk_in / row_length / fps) - vsize)

    # Split value
    high = vblank // (2 ** 8)
    low = vblank % (2 ** 8)

    # Write to registers
    imager.enablePrint()
    imager.write(0x1012, low)
    imager.write(0x1013, high)

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