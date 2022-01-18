def controlInit():
    '''
    Initial widget parameters
    '''
    controlParams = {
        "name": "Read order",
        "comment": "read order",
        "type": "two_checkbuttons",
        "cb1_label_text": "Mirror:",
        "cb1_onvalue": 1,
        "cb1_offvalue": 0,
        "cb1_default": "off",
        "cb1_xpad": (0, 0),
        "cb2_label_text": "Flip:",
        "cb2_onvalue": 1,
        "cb2_offvalue": 0,
        "cb2_default": "off",
        "cb2_xpad": (0, 77),
        "unit": "on / off",
    }
    return controlParams


def controlGetCb1(main_app, sreg):
    '''
    Get the register value and set the widget related to mirror
    '''
    value = main_app.sensor.hflip
    sreg.set(value)
    return value


def controlGetCb2(main_app, sreg):
    '''
    Get the register value and set the widget related to flip
    '''
    value = main_app.sensor.vflip
    sreg.set(value)
    return value


def controlSetCb1(main_app, variable):
    '''
    Set the register value based on widget input related to mirror
    '''
    main_app.sensor.hflip = int(variable.get())


def controlSetCb2(main_app, variable):
    '''
    Set the register value based on widget input related to flip
    '''
    main_app.sensor.vflip = int(variable.get())


def execCmd():
    print('executed')