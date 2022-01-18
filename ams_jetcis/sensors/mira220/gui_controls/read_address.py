def controlInit():
    controlParams = {
        "name" : "Read address",
        "comment" : "read address",
        "type" : "text_entry_read",
        "buttontext": "Get",
        "unit" : "hex",
    }
    return controlParams

def controlSet(imager, entryvar, statusArea, event=None):
    # I2C address and length (addr=16bit, val=8bit)
    imager.disablePrint()
    imager.setSensorI2C(0x54)
    imager.type(1)

    # Add hexadecimal prefix
    entry_string = str(entryvar.get())

    # Check on wrong inputs
    if len(entry_string) > 4:
        imager.pr("ERROR: Address input is too long (should not contain 0x)")
    elif len(entry_string) < 1:
        imager.pr("ERROR: Address input is empty")
    else:
        try:
            # Convert hexadecimal to decimal and read register
            entry_dec = int(entry_string, base=16)
            output_dec = imager.read(abs(entry_dec))
            imager.enablePrint()

            # Print result in StatusArea 
            address_string = "0" * (4 - len(entry_string)) + entry_string
            value_string = hex(output_dec)[2:]
            value_string = "0" * (2 - len(value_string)) + value_string
            imager.pr("Address 0x" + address_string + " contains 0x" + value_string)
        except ValueError:
            # Print error in StatusArea when entry contains non hexadecimal symbols
            imager.pr("ERROR: Wrong address")

    # Remove cursor/focus
    statusArea.focus()

def execCmd():
    print('executed')

def disableShortcuts(master, event=None):
    # Otherwise fullscreen will be enabled when writing an f
    master.unbind("f")
    master.unbind("b")

def enableShortcuts(master, toggleFullscreen, toggleBurst, event=None):
    # Bind again
    master.bind("f", toggleFullscreen)
    master.bind("b", toggleBurst)
