def controlInit():
    '''
    Initial widget parameters
    '''
    controlParams = {
        "name" : "Write address",
        "comment" : "write address",
        "type" : "text_entry_write",
        "buttontext": "Set",
        "unit" : "hex",
    }
    return controlParams


def controlSet(imager, entryvar_address, entryvar_value, statusArea, event=None):
    '''
    Write the given register value to the given address
    '''
    # I2C address and length (addr=16bit, val=8bit)
    imager.disablePrint()
    imager.setSensorI2C(0x30)
    imager.type(1)
    imager.enablePrint()

    # Add hexadecimal prefix
    entry_address_string = str(entryvar_address.get())
    entry_value_string = str(entryvar_value.get())

    # Check on wrong inputs
    if len(entry_address_string) > 4:
        imager.pr("ERROR: Address input is too long (should not contain 16'h")
    elif len(entry_address_string) < 1:
        imager.pr("ERROR: Address input is empty")
    elif len(entry_value_string) > 2:
        imager.pr("ERROR: Value input is too long (should not contain 8'h)")
    elif len(entry_value_string) < 1:
        imager.pr("ERROR: Value input is empty")
    else:
        try:
            # Convert hexadecimal to decimal and write register
            entry_address_dec = int(entry_address_string, base=16)
            entry_value_dec = int(entry_value_string, base=16)
            imager.write(abs(entry_address_dec), abs(entry_value_dec))

            # Print in StatusArea
            imager.pr("Write is executed")
        except ValueError:
            # Print error in StatusArea when entries contain non hexadecimal symbols
            imager.pr("ERROR: Wrong input")

    # Updates the status of all Widgets
    imager.doWidgetUpdate()

    # Remove cursor/focus
    statusArea.focus()


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
