def controlInit():
    controlParams = {
        "name": "Defect correction limits",
        "comment": "Choose a replacement limit",
        "type": "slider",
        "nb_widgets": 2,
        "min_1": 0.0,
        "max_1": 15.0,
        "default_1": 0.0,
        "step_1": 1.0,
        "min_2": 0.0,
        "max_2": 15.0,
        "default_2": 0.0,
        "step_2": 1.0,
        "unit": "low / high",
        "auto": False,
        "refresh": True,
    }
    return controlParams


def controlGet_1(main_app, s):
    value = main_app.sensor.dpc[2]
    s.set(value)
    return value


def controlSet_1(main_app, sreg, event=None):
    main_app.sensor.dpc = [None, None, float(sreg.get()), None, None]

    # Updates the status of all Widgets
    main_app.imager.doWidgetUpdate()


def controlGet_2(main_app, s):
    value = main_app.sensor.dpc[3]
    s.set(value)
    return value


def controlSet_2(main_app, sreg, event=None):
    main_app.sensor.dpc = [None, None, None, float(sreg.get()), None]

    # Updates the status of all Widgets
    main_app.imager.doWidgetUpdate()


def execCmd():
    print('executed')
