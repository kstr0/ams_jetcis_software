
def controlInit():
    controlParams = {
        "name": "HDR calibration",
        "comment": "HDR calibration",
        "type": "two_checkbuttons",
        "cb1_label_text": "HDRC:",
        "cb1_onvalue": 0,
        "cb1_offvalue": 1,
        "cb1_default": "on",
        "cb1_xpad": (0, 0),
        "cb2_label_text": "HDR point read:",
        "cb2_onvalue": 1,
        "cb2_offvalue": 0,
        "cb2_default": "off",
        "cb2_xpad": (0, 4),
        "unit": "on/off",
    }
    return controlParams

def controlGetCb1(imager):
    # Read register and convert to 8 bit
    value = imager.read(0x5001)
    value_bin = format(value, '08b')

    # Select bit 3
    bit3 = int(value_bin[4])

    return bit3

def controlGetCb2(imager):
    # Read register and convert to 8 bit
    value = imager.read(0x3222)
    value_bin = format(value, '08b')

    # Select bit [5:4]
    if value_bin[2:4] == '00':
        value = 0
    else:
        value = 1

    return value

def controlSetCb1(imager, variable):
    # Get checkbutton value
    value = int(variable.get())

    # Read register and convert to 8 bit
    imager.disablePrint()
    current_address_value = imager.read(0x5001)
    imager.enablePrint()
    current_address_value_bin = format(current_address_value, '08b')

    # Change bit 3
    if (value == 0):
        write_value = current_address_value_bin[0:4] + '0' + current_address_value_bin[5:8]
    else:
        write_value = current_address_value_bin[0:4] + '1' + current_address_value_bin[5:8]

    # Write to register
    imager.write(0x5001, int(write_value, 2))

def controlSetCb2(imager, variable):
    # Get checkbutton value
    value = int(variable.get())

    # Read register and convert to 8 bit
    imager.disablePrint()
    current_address_value = imager.read(0x3222)
    imager.enablePrint()
    current_address_value_bin = format(current_address_value, '08b')

    # Change bit [5:4]
    if (value == 0):
        write_value = current_address_value_bin[0:2] + '00' + current_address_value_bin[4:8]
    else:
        write_value = current_address_value_bin[0:2] + '11' + current_address_value_bin[4:8]

    # Write to register
    imager.write(0x3222, int(write_value, 2))

def execCmd():
    print('executed')