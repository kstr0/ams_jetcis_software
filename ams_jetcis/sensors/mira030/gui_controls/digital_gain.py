def controlInit():
    '''
    Initial widget parameters
    '''
    controlParams = {
        "name" : "Digital gain",
        "comment" : "digital gain",
        "type" : "slider",
        "nb_widgets": 1,
        "min" : 1.0,
        "max" : 7.75,
        "default" : 1.0,
        "step" : 0.0005,
        "unit" : "linear",
        "auto" : False,
        "refresh" : True,
    }
    return controlParams


def controlGet(main_app, s):
    '''
    Get the register value and set the widget related to digital gain
    '''
    dig_gain_gui = main_app.sensor.digital_gain
    s.set(dig_gain_gui)
    return dig_gain_gui


def controlSet(main_app, sreg, event=None):
    '''
    Set the register value based on widget input related to digital gain
    '''
    main_app.sensor.digital_gain = float(sreg.get())

    # Set GUI variable to mapped input
    sreg.set(main_app.sensor._digital_gain)

    # Updates the status of all Widgets
    main_app.imager.doWidgetUpdate()


def execCmd():
    print('executed')

