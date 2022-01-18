def controlInit():
    '''
    Initial widget parameters
    '''
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


def controlGetCb1(imager, sreg):
    '''
    Get the register value and set the widget related to mirror
    '''
    # Read register
    imager.disablePrint()
    imager.setSensorI2C(0x30)
    imager.type(1)
    read_value = imager.read(0x3221)
    imager.enablePrint()
    
    # Select bit [2:1]
    if ExtractBits(read_value, 2, 1) == 0:
        value = 0
    else:
        value = 1

    sreg.set(value)
    return value


def controlGetCb2(imager, sreg):
    '''
    Get the register value and set the widget related to flip
    '''
    # Read register
    imager.disablePrint()
    imager.setSensorI2C(0x30)
    imager.type(1)
    read_value = imager.read(0x3221)
    imager.enablePrint()

    # Select bit [6:5]
    if ExtractBits(read_value, 2, 5) == 0:
        value = 0
    else:
        value = 1

    sreg.set(value)
    return value


def controlSetCb1(imager, variable):
    '''
    Set the register value based on widget input related to mirror
    '''
    # Get checkbutton value
    value = int(variable.get())

    # Read register
    imager.disablePrint()
    imager.setSensorI2C(0x30)
    imager.type(1)
    read_reg_value = imager.read(0x3221)
    imager.enablePrint()

    # Change bit [2:1]
    if value == 0:
        write_value = ReplaceBits(read_reg_value, 0b00, 2, 1)
    else:
        write_value = ReplaceBits(read_reg_value, 0b11, 2, 1)
    
    # Write to register
    imager.write(0x3221, write_value)


def controlSetCb2(imager, variable):
    '''
    Set the register value based on widget input related to flip
    '''
    # Get checkbutton value
    value = int(variable.get())

    # Read register
    imager.disablePrint()
    imager.setSensorI2C(0x30)
    imager.type(1)
    read_reg_value = imager.read(0x3221)
    imager.enablePrint()

    # Change bit [6:5]
    if (value == 0):
        write_value = ReplaceBits(read_reg_value, 0b00, 2, 5)
    else:
        write_value = ReplaceBits(read_reg_value, 0b11, 2, 5)
    
    # Write to register
    imager.write(0x3221, write_value)

 
def ExtractBits(number, k, p): 
    '''
    Extract k bits from p position and return an integer
    E.g. [2:0] -> k=3; p=0
    '''  
    return (((1 << k) - 1) & (number >> p))


def ReplaceBits(number, replacement, k, p):
    '''
    Replace k bits from p position with the replacement integer
    '''
    high = ExtractBits(number, 8-k-p, k+p)
    low = ExtractBits(number, p, 0)
    return (high << (k+p)) + (replacement << p) + low


def execCmd():
    print('executed')