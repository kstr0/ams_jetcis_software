def controlInit():
    controlParams = {
        "name": "Illumination",
        "comment": "Enable 940nm LED",
        "type": "checkbutton",
        "onvalue": 1,
        "offvalue": 0,
        "default": "off",
        "unit": "on / off",
    }
    return controlParams


def controlGet(main_app, sreg):
    [status, _, _] = main_app.sensor.led_driver
    sreg.set(status)
    return status


def controlSet(main_app, variable):
    value = int(variable.get())
    main_app.sensor.led_driver = [value, 530, 1100]
    main_app.sensor.illumination_trigger = [value, None, None, None, None, None, None]


def execCmd():
    print('executed')
