def controlInit():
    '''
    Initial widget parameters in ms
    '''
    frame_length = 0x07d0
    line_length = 0x04b0
    fps = 30
    exposure_length_max = (frame_length - 6) * 16
    Tpclk = (1e3) / (fps * frame_length * line_length)
    step = (1 / 16) * line_length * Tpclk

    controlParams = {
        "name" : "Exposure time",
        "comment" : "Press enter after entering a value.",
        "type" : "spinbox",
        "min": 0.0,
        "max": exposure_length_max * step,
        "default": 512 * step,
        "step": 1,
        "unit" : "ms",
    }
    return controlParams

def controlGet(main_app, spinbox, variable, event=None):
    '''
    Get the register value and set the widget related to exposure time
    '''
    exposure_time = main_app.sensor.exposure_us
    [exposure_length_max, step] = main_app.sensor.get_exposure_limit()

    spinbox["to"] = exposure_length_max * step / 1e3

    variable.set("{:.3f}".format(exposure_time / 1e3))


def controlSet(main_app, value, event=None):
    '''
    Set the register value based on widget input related to exposure time
    '''
    try:
        value = float(value.get())
    except:
        value = 0.0

    main_app.sensor.exposure_us = 1e3 * value
    
    # Remove cursor/focus
    main_app.statusArea.focus()

    # Updates the status of all Widgets
    main_app.imager.doWidgetUpdate()


def validate(spinbox, number=None):
    '''
    Validate the input of the wiget. Only allow numbers between from and to.
    '''
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
