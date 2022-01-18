
def controlInit():
    controlParams = {
        "name": "HDR exposure time",
        "comment": "HDR. 0 = max HDR, higher value lowers the effect.",
        "type": "checkbutton_and_slider",
        "onvalue": 1,
        "offvalue": 0,
        "checkbutton_default": "off",
        "min": 0.0,
        "max": 10000,
        "slider_default": 100.0,
        "step": 100,
        "slider_default_state": "disabled",
        "unit": "us",
        "auto" : True,
        "refresh" : False,
    }
    return controlParams

def controlGetCheckbutton(main_app, sreg):
    # Get the driver access
    # imager = main_app.imager
    # imager.setSensorI2C(imager.sensori2c)

    # # Read register and convert to 8 bit
    # value = imager.read(0x3220)
    # value_bin = format(value, '08b')

    # # Select bit 6
    # bit6 = int(value_bin[1])

    sreg.set(main_app.sensor.hdr)
    # # return bit6
    # main_app.sensor.set_hdr(value,main_app.sensor.hdr_exposure_us)


def controlGetSlider(main_app, sreg):
    # Get the driver access
    # imager = main_app.imager
    # imager.setSensorI2C(imager.sensori2c)

    # # Read the registers
    # high = imager.read(0x3e31)
    # low = imager.read(0x3e32)

    # # GUI new value
    # value = high * (2 ** 8) + low

    # # Calculate the pixel clock period
    # fps_original = main_app.sensor_fps
    # frame_length_original = 2400
    # line_length_original = 1500
    # Tpclk = (10 ** 3) / (fps_original * frame_length_original * line_length_original)

    # # Calculate the exposure time
    # line_length_new = imager.read(0x320c) * (2 ** 8) + imager.read(0x320d)
    # hdr_exposure_time = value * (1 / 16) * line_length_new * Tpclk

    # Update label
    sreg.set(main_app.sensor.hdr_exposure_us)


def controlSetCheckbutton(main_app, sreg):
    # Get checkbutton value
    value = int(sreg.get())

    # Get the driver access
    imager = main_app.imager

    # # Read register and convert to 8 bit
    # current_address_value = imager.read(0x3220)
    # current_address_value_bin = format(current_address_value, '08b')

    # # Change bit 6
    # if (value == 0):
    #     write_value = current_address_value_bin[:1] + '0' + current_address_value_bin[2:]
    # else:
    #     write_value = current_address_value_bin[:1] + '1' + current_address_value_bin[2:]

    # # Write to register
    # imager.write(0x3220, int(write_value, 2))
    main_app.sensor.set_hdr(value,main_app.sensor.hdr_exposure_us)
    imager.doWidgetUpdate()

def controlSetSlider(main_app, variable, event=None):
    value = int(variable.get())

    # Get the driver access
    sensor = main_app.sensor
    sensor.set_hdr(sensor.hdr, hdr_exposure_us = value)
    # # Split value
    # high = value // (2**8)
    # low = value % (2**8)

    # # Write to registers
    # imager.write(0x3e31, high)
    # imager.write(0x3e32, low)

    #imager.doWidgetUpdate()

def execCmd():
    print('executed')
