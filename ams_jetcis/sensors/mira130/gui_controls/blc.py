
def controlInit():
    controlParams = {
        "name" : "BLC",
        "comment" : "blc",
        "type" : "checkbutton_and_slider",
        "onvalue": 1,
        "offvalue": 0,
        "checkbutton_default": "on",
        "min" : 0.0,
        "max" : 7.0,
        "slider_default" : 0.0,
        "step" : 1,
        "slider_default_state": "normal",
        "unit": "units",
    }
    return controlParams

def controlGetCheckbutton(main_app, sreg):
    # Get the driver access
    imager = main_app.imager

    # Read register and convert to 8 bit
    value = imager.read(0x3902)
    value_bin = format(value, '08b')

    # Select bit 6
    bit6 = int(value_bin[1])

    sreg.set(bit6)
    return bit6

def controlGetSlider(main_app, sreg):
    # Get the driver access
    imager = main_app.imager

    # Read register
    value = imager.read(0x391d)

    # Select bit [2:0]
    first_3_bits = value % (2 ** 3)

    # Update label
    sreg.set(first_3_bits)
    return first_3_bits

def controlSetCheckbutton(main_app, sreg):
    # Get the driver access
    imager = main_app.imager

    # Get checkbutton value
    value = int(sreg.get())

    # Read register and convert to 8 bit
    current_address_value = imager.read(0x3902)
    current_address_value_bin = format(current_address_value, '08b')

    # Change bit 6
    if (value == 0):
        write_value = current_address_value_bin[:1] + '0' + current_address_value_bin[2:]
        sreg.set(0)
    else:
        write_value = current_address_value_bin[:1] + '1' + current_address_value_bin[2:]
        sreg.set(1)

    # Write to register
    imager.write(0x3902, int(write_value, 2))

    # Updates the status of all Widgets
    imager.doWidgetUpdate()

def controlSetSlider(main_app, variable, event=None):
    value = int(variable.get())

    # Get the driver access
    imager = main_app.imager

    # Read register and select last 5 bits
    current_address_value = imager.read(0x391d)
    high = current_address_value // (2**3)

    # Write to register
    imager.write(0x391d, high * (2 ** 3) + value)

    # Updates the status of all Widgets
    imager.doWidgetUpdate()

def execCmd():
    print('executed')


