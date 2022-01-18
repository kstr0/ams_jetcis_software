def controlInit():


    # Parameters are in milliseconds
    controlParams = {
        "name" : "Exposure time",
        "comment" : "Press enter after entering a value.",
        "type" : "spinbox",
        "min": 0.0,
        "max": 20000,
        "default": 1000,
        "step": 100 ,
        "unit" : "us",
    }
    return controlParams

def controlGet(main_app, spinbox, variable, event=None):
    # Get the driver access
    imager = main_app.imager
    # imager.setSensorI2C(imager.sensori2c)
    variable.set("{:.4f}".format(main_app.sensor.exposure_us))
    # # Calculate the pixel clock period in ms
    # fps_original = main_app.sensor_fps
    # frame_length_original = 2400
    # line_length_original = 1500
    # Tpclk = (10 ** 3) / (fps_original * frame_length_original * line_length_original)

    # # Calculate the exposure time
    # line_length_new = imager.read(0x320c) * (2 ** 8) + imager.read(0x320d)
    # line_time_new = line_length_new * Tpclk
    # step = (1 / 16) * line_time_new
    # exposure_time = (int(format(imager.read(0x3e00), '08b')[-4:8], 2) * (2**16) + imager.read(0x3e01) * (2**8) + imager.read(0x3e02)) * step
    # print(f'exposure time is {exposure_time}')
    # # Update the max boundary value
    # frame_length_new = imager.read(0x320e) * (2 ** 8) + imager.read(0x320f)
    # exposure_time_max = ((frame_length_new - 8) * 16) * step
    # spinbox["to"] = exposure_time_max

    # # Update the step value
    # spinbox["increment"] = 1000 * step

    # # Set the variable
    # if exposure_time > exposure_time_max:
    #     exposure_length = (frame_length_new - 8) * 16

    #     # Split value
    #     high = exposure_length // (2 ** 16) + int(format(imager.read(0x3e00), '08b')[0:4], 2) * (2 ** 4)
    #     middle_temp = exposure_length % (2 ** 16)
    #     middle = middle_temp // (2 ** 8)
    #     low = middle_temp % (2 ** 8)

    #     # Write to registers
    #     imager.write(0x3e00, high)
    #     imager.write(0x3e01, middle)
    #     imager.write(0x3e02, low)

    #     variable.set("{:.3f}".format(exposure_time_max))
    # else:
    #     variable.set("{:.3f}".format(exposure_time))


def controlSet(main_app, value, event=None):
    # Get the driver access
    imager = main_app.imager
    imager.setSensorI2C(imager.sensori2c)

    # Get the entry value
    try:
        value = float(value.get())
    except:
        value = 0.0
    # value.set("{:.4f}".format(main_app.sensor.exposure_us))
    main_app.sensor.set_exposure_us(float(value))

    # # Calculate the pixel clock period in ms
    # fps_original = main_app.sensor_fps
    # frame_length_original = 2400
    # line_length_original = 1500
    # Tpclk = (10 ** 3) / (fps_original * frame_length_original * line_length_original)

    # # Calculate the given exposure time to the exposure length
    # imager.disablePrint()
    # line_length_new = imager.read(0x320c) * (2 ** 8) + imager.read(0x320d)
    # line_time_new = line_length_new * Tpclk
    # exposure_length = round(16 * value / line_time_new)
    # frame_length_new = imager.read(0x320e) * (2 ** 8) + imager.read(0x320f)
    # if exposure_length > (frame_length_new - 8) * 16:
    #     exposure_length = (frame_length_new - 8) * 16

    # # Split value
    # high = exposure_length // (2 ** 16) + int(format(imager.read(0x3e00), '08b')[0:4], 2) * (2**4)
    # middle_temp = exposure_length % (2 ** 16)
    # middle = middle_temp // (2 ** 8)
    # low = middle_temp % (2 ** 8)

    # # Write to registers
    # imager.enablePrint()
    # imager.write(0x3e00, high)
    # imager.write(0x3e01, middle)
    # imager.write(0x3e02, low)

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
