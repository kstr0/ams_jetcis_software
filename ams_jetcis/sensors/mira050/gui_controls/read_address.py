def controlInit():
    '''
    Initial widget parameters
    '''
    controlParams = {
        "name" : "Read address",
        "comment" : "read address",
        "type" : "text_entry_read",
        "buttontext": "Get",
        "unit" : "hex",
    }
    return controlParams


def controlSet(imager, entryvar, statusArea, event=None):
    '''
    Show the register value in the status area based on the given address
    '''
    # I2C address and length (addr=16bit, val=8bit)
    imager.disablePrint()
    imager.setSensorI2C(0x36)
    imager.type(1)
    imager.enablePrint()

    # Add hexadecimal prefix
    entry_string = "0x" + str(entryvar.get())

    # Check on wrong inputs
    if len(entry_string) > 6:
        imager.pr("ERROR: Address input is too long (should not contain 16'h)")
    elif len(entry_string) < 3:
        imager.pr("ERROR: Address input is empty")
    else:
        try:
            # Convert hexadecimal to decimal and read register
            entry_dec = int(entry_string, base=16)
            output_dec = imager.read(entry_dec)
            imager.enablePrint()

            # Print result in StatusArea
            address_string = entry_string[2:]
            address_string = "0" * (4 - len(address_string)) + address_string
            value_string = hex(output_dec)[2:]
            value_string = "0" * (2 - len(value_string)) + value_string
            imager.pr("Address 16'h" + address_string + " contains 8'h" + value_string)
        except ValueError:
            # Print error in StatusArea when entry contains non hexadecimal symbols
            imager.pr("ERROR: Wrong address")

    # Remove cursor/focus
    statusArea.focus()
    imager.disablePrint()


def execCmd():
    print('executed')


def disableShortcuts(master, event=None):
    '''
    Disable shortcut keys that can be present in the hexadecimal numeral system
    '''
    master.unbind("f")
    master.unbind("b")


def enableShortcuts(master, toggleFullscreen, toggleBurst, event=None):
    '''
    Enable shortcut keys that can be present in the hexadecimal numeral system
    '''
    master.bind("f", toggleFullscreen)
    master.bind("b", toggleBurst)
