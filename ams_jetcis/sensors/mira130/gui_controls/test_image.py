
def controlInit():
    controlParams = {
        "name": "Test image",
        "comment": "test image",
        "type": "checkbutton",
        "onvalue": 1,
        "offvalue": 0,
        "default": "off",
        "unit": "on/off",
    }
    return controlParams

def controlGet(main_app, sreg):
    # Get the driver access
    imager = main_app.imager

    # Read register and convert to 8 bit
    value = imager.read(0x4501)
    value_bin = format(value, '08b')

    # Select bit 3
    bit3 = int(value_bin[4])
    sreg.set(bit3)

    return bit3

def controlSet(main_app, variable):
    # Get checkbutton value
    value = int(variable.get())

    # Get the driver access
    imager = main_app.imager

    # Read register and convert to 8 bit
    current_address_value = imager.read(0x4501)
    current_address_value_bin = format(current_address_value, '08b')

    # Change bit 3
    if (value == 0):
        write_value = current_address_value_bin[:4] + '0' + current_address_value_bin[5:]
    else:
        write_value = current_address_value_bin[:4] + '1' + current_address_value_bin[5:]

    # Write to register
    imager.write(0x4501, int(write_value, 2))
    imager.doWidgetUpdate()

def execCmd():
    print('executed')