def controlInit():
    '''
    Initial widget parameters in ms
    '''

    controlParams = {
        "name" : "Exposure time",
        "comment" : "Press enter after entering a value.",
        "type" : "spinbox",
        "min": 50.0,
        "max": 1000000,
        "default": 100,
        "refresh": 1,
        "step": 100,
        "unit" : "us",
    }
    return controlParams

def controlGet(main_app, spinbox, variable, event=None):
    '''
    Get the register value and set the widget related to exposure time
    '''
    # Get the driver access
    exp = main_app.sensor.exposure_us
    variable.set("{:.3f}".format(exp))

    #imager.disablePrint()
    # imager.setSensorI2C(0x36)
    # imager.type(1)

    # Calculate the pixel clock period in ms

    return 0


def controlSet(main_app, sreg, event=None):
    '''
    Set the register value based on widget input related to exposure time
    '''
    print(f'sreg is {sreg}')
    main_app.sensor.set_exposure_us(sreg.get())
    # # Get the driver access
    # imager = main_app.imager
    # imager.disablePrint()
    # imager.setSensorI2C(0x36)
    # imager.type(1)

    # # Get the entry value
    # try:
    #     value = int(sreg.get())
    # except:
    #     value = 0

    # # Split value
    # b3 = value >> 24 & 255
    # b2 = value >> 16 & 255
    # b1 = value >> 8  & 255
    # b0 = value       & 255
    
    # # Write to registers
    # imager.enablePrint()

    # imager.write(0xe004,  0)
    # imager.write(0xe000,  1)
    # imager.write(0x000E, b3)
    # imager.write(0x000F, b2)
    # imager.write(0x0010, b1)
    # imager.write(0x0011, b0)
    # # Remove cursor/focus
    # main_app.statusArea.focus()

    # Updates the status of all Widgets
    main_app.imager.doWidgetUpdate()
    return 0

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
