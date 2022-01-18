
def controlInit():
    controlParams = {
        "name": "Blacksun",
        "comment": "black sun protection",
        "type": "checkbutton",
        "onvalue": 1,
        "offvalue": 0,
        "refresh": 1,
        "default": "on",
        "unit": "on/off",

    }
    return controlParams

def controlGet(main_app, sreg):

    # Get the driver access
    sreg.set(bool(main_app.sensor.bsp))
    print('bsp get called')

    return 0

def controlSet(main_app, sreg):

    main_app.sensor.set_bsp(bool(sreg.get()))
    print('bsp set called')
    main_app.imager.doWidgetUpdate()

    return 0

def execCmd():
    print('executed')
