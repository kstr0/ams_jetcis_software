def controlInit():
    controlParams = {
        "name": "Row correction",
        "comment": "row noise",
        "type": "checkbutton",
        "onvalue": 1,
        "offvalue": 0,
        "default": "off",
        "unit": "on / off",
    }
    return controlParams

def controlGet(main_app, sreg):
    value = main_app.sensor.rnc[0]
    sreg.set(value)
    return value


def controlSet(main_app, variable):
    main_app.sensor.rnc = [int(variable.get()), None]


def execCmd():
    print('executed')