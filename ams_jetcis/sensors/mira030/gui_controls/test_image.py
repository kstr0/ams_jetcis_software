def controlInit():
    '''
    Initial widget parameters
    '''
    controlParams = {
        "name": "Test image",
        "comment": "test image",
        "type": "checkbutton",
        "onvalue": 1,
        "offvalue": 0,
        "default": "off",
        "unit": "on / off",
    }
    return controlParams


def controlGet(main_app, sreg):
    '''
    Get the register value and set the widget related to test image
    '''
    value = main_app.sensor.test_image
    sreg.set(value)
    return value


def controlSet(main_app, variable):
    '''
    Set the register value based on widget input related to test image
    '''
    main_app.sensor.test_image = int(variable.get())
    main_app.imager.doWidgetUpdate()


def execCmd():
    print('executed')

