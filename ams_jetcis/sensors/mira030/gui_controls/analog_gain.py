def controlInit():
    '''
    Initial widget parameters
    '''
    controlParams = {
        "name": "Analog gain",
        "comment": "analog gain",
        "type": "slider",
        "nb_widgets": 1,
        "min": 1.0,
        "max": 15.5,
        "default": 1.0,
        "step": 0.0005,
        "unit": "linear",
        "auto": False,
        "refresh": True,
    }
    return controlParams


def controlGet(main_app, s):
    '''
    Get the register value and set the widget related to analog gain
    '''
    ana_gain_gui = main_app.sensor.analog_gain
    s.set(ana_gain_gui)
    return ana_gain_gui


def controlSet(main_app, sreg, event=None):
    '''
    Set the register value based on widget input related to analog gain
    '''
    main_app.sensor.analog_gain = float(sreg.get())
    sreg.set(main_app.sensor._analog_gain)
    # Updates the status of all Widgets
    main_app.imager.doWidgetUpdate()


def execCmd():
    print('executed')

