
def controlInit():
    controlParams = {
        "name": "Read order",
        "comment": "read order",
        "type": "two_checkbuttons",
        "cb1_label_text": "Mirror:",
        "cb1_onvalue": 1,
        "cb1_offvalue": 0,
        "cb1_default": "off",
        "cb1_xpad": (0, 0),
        "cb2_label_text": "Flip:",
        "cb2_onvalue": 1,
        "cb2_offvalue": 0,
        "cb2_default": "off",
        "cb2_xpad": (0, 77),
        "unit": "on/off",
    }
    return controlParams

def controlGetCb1(main_app, sreg):
    imager = main_app.imager
    # Read register and convert to 8 bit
    value = imager.read(0x3221)
    value_bin = format(value, '08b')

    # Select bit [2:1]
    if value_bin[5:7] == '00':
        value = 0
    else:
        value = 1

    sreg.set(value)
    return value

def controlGetCb2(main_app, sreg):
    imager = main_app.imager
    # Read register and convert to 8 bit
    value = imager.read(0x3221)
    value_bin = format(value, '08b')

    # Select bit [6:5]
    if value_bin[1:3] == '00':
        value = 0
    else:
        value = 1

    sreg.set(value)
    return value

def controlSetCb1(main_app, variable):
    imager = main_app.imager
    # Get checkbutton value
    value = int(variable.get())

    # Read register and convert to 8 bit
    imager.disablePrint()
    current_address_value = imager.read(0x3221)
    imager.enablePrint()
    current_address_value_bin = format(current_address_value, '08b')

    # Change bit [2:1]
    if (value == 0):
        write_value = current_address_value_bin[0:5] + '00' + current_address_value_bin[7]
    else:
        write_value = current_address_value_bin[0:5] + '11' + current_address_value_bin[7]

    # Write to register
    imager.write(0x3221, int(write_value, 2))

def controlSetCb2(main_app, variable):
    imager = main_app.imager
    # Get checkbutton value
    value = int(variable.get())

    # Read register and convert to 8 bit
    imager.disablePrint()
    current_address_value = imager.read(0x3221)
    imager.enablePrint()
    current_address_value_bin = format(current_address_value, '08b')

    # Change bit [6:5]
    if (value == 0):
        write_value = current_address_value_bin[0] + '00' + current_address_value_bin[3:8]
    else:
        write_value = current_address_value_bin[0] + '11' + current_address_value_bin[3:8]

    # Write to register
    imager.write(0x3221, int(write_value, 2))

def execCmd():
    print('executed')