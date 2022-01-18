
def controlInit():
    controlParams = {
        "name" : "HDR level",
        "comment" : "Sets the level of the kneepoint",
        "type" : "slider",
        "nb_widgets": 1,
        "min" : - ((2 ** 8) - 1),
        "max" : (2 ** 8) - 1,
        "default" : 0.0,
        "step" : 1.0,
        "unit" : "voltage",
        "auto" : False,
        "refresh" : True,
    }
    return controlParams


def controlGet(main_app, s):
    # Get the driver access
    imager = main_app.imager

    # Read register and convert to 8 bit
    value = imager.read(0x3220)
    value_bin = format(value, '08b')

    # Select bit 6
    bit6 = int(value_bin[1])

    if (bit6 == 0):
        s["state"] = "disabled"
        s["bg"] = "#C7CCCF"
    else:
        s["state"] = "normal"
        s["bg"] = "#FD5000"

        # Read the registers
        v_step = imager.read(0x4416)
        dir_reg_v = imager.read(0x4417)

        if (dir_reg_v == 0):
            hdr_v_gui = v_step
        else:
            hdr_v_gui = -v_step

        s.set(hdr_v_gui)


def controlSet(main_app, sreg, event=None):
    # Get slider value
    input = float(sreg.get())

    # Get the driver access
    imager = main_app.imager

    if (input >= 0):
        imager.write(0x4416, abs(input))
        imager.write(0x4417, 0)
    else:
        imager.write(0x4416, abs(input))
        imager.write(0x4417, 1)

    # Updates the status of all Widgets
    imager.doWidgetUpdate()

def execCmd():
    print('executed')
