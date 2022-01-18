def controlInit():
    # Time conversion factor in seconds
    row_length = 0x12c
    f_clk_in = 38.4e6
    time_conversion = row_length / f_clk_in

    # Exposure max
    fps = 30
    vsize = 1400
    vblank = int(int(f_clk_in/row_length/fps) - vsize)
    fot_length = 1928
    exposure_length_max = int(((row_length * (vsize + vblank) - fot_length) / f_clk_in) / time_conversion)

    # Parameters are in ms
    controlParams = {
        "name": "Exposure time",
        "comment": "Press enter after entering a value.",
        "type": "spinbox",
        "min": 0.0,
        "max": exposure_length_max * time_conversion * 1000,
        "default": 0x7e * time_conversion * 1000,
        "step": 1,
        "unit": "ms",
    }
    return controlParams


def controlGet(main_app, spinbox, variable, event=None):
    exposure_time = main_app.sensor.exposure_us

    # Update the min/max boundary value
    [exposure_time_max, _] = main_app.sensor.get_exposure_limit()
    spinbox["to"] = exposure_time_max / 1e3
    variable.set("{:.4f}".format(exposure_time / 1e3))


def controlSet(main_app, value, event=None):
    # Entry value
    try:
        value = float(value.get())
    except:
        value = 0.0

    # Set exposure
    main_app.sensor.exposure_us = value * 1e3

    # Remove cursor/focus
    main_app.statusArea.focus()

    # Updates the status of all Widgets
    main_app.imager.doWidgetUpdate()


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