import time
def controlInit():
    '''
    Initial widget parameters in ms
    '''

    controlParams = {
        "name" : "Frame length",
        "comment" : "Press enter after entering a value.",
        "type" : "spinbox",
        "min": 1.0,
        "max": 910208,
        "default": 21694,
        "refresh": 1,
        "step": 1000,
        "unit" : "us",
    }
    return controlParams


def controlGet(main_app, s):
    # Get the driver access
    imager = main_app.imager
    imager.setSensorI2C(imager.sensori2c)

    # Read the registers
    high = imager.read(0x320e)
    low = imager.read(0x320f)

    # GUI new value
    value = high * (2 ** 8) + low

    # Calculate the pixel clock period in ms
    fps_original = main_app.sensor_fps
    frame_length_original = 2400
    line_length_original = 1500
    Tpclk = (10 ** 6) / (fps_original * frame_length_original * line_length_original)

    # Get the line length
    line_length_atm = imager.read(0x320c) * (2 ** 8) + imager.read(0x320d)

    # Update label
    result = value * Tpclk * line_length_atm

    # Set the variable
    s.set(result)

    return result

def controlSet(main_app, sreg, event=None):
    # Get slider value
    value = int(float(sreg.get()))

    # Get the driver access
    imager = main_app.imager
    imager.setSensorI2C(imager.sensori2c)

    # Calculate the pixel clock period in ms
    fps_original = main_app.sensor_fps
    frame_length_original = 2400
    line_length_original = 1500
    Tpclk = (10 ** 3) / (fps_original * frame_length_original * line_length_original)

    # Get the line length
    line_length_atm = imager.read(0x320c) * (2 ** 8) + imager.read(0x320d)

    # Get new frame length
    frame_length_new = int(value / (Tpclk * line_length_atm))

    # Split value
    high = frame_length_new // (2**8)
    low = frame_length_new % (2**8)

    # Write to registers
    imager.write(0x320e, high)
    imager.write(0x320f, low)

    # Updates the status of all Widgets
    imager.doWidgetUpdate()

def execCmd():
    print('executed')



