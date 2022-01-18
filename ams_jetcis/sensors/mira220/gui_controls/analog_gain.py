def controlInit():
    controlParams = {
        "name": "Analog gain",
        "comment": "Analog gain",
        "type": "optionmenu",
        "nb_widgets": 1,
        "default_1": "1",
        "option_list_1": ["1", "2", "4"],
        "unit": "x",
    }
    return controlParams


def controlGet_1(main_app, omvar):
    ana_gain_gui = main_app.sensor.analog_gain
    omvar.set(str(ana_gain_gui))
    return ana_gain_gui


def controlSet_1(main_app, variable, event=None):
    main_app.sensor.analog_gain = int(variable.get())

    # Updates the status of all Widgets
    main_app.imager.doWidgetUpdate()


def execCmd():
    print('executed')
