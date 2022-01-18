def controlInit():
    '''
    Initial widget parameters
    '''
    controlParams = {
        "name": "BLC",
        "comment": "Black level control mode",
        "type": "optionmenu",
        "nb_widgets": 2,
        "default_1": "Off",
        "option_list_1": ["Off", "Manual", "Auto"],
        "default_2": "1 channel",
        "option_list_2": ["1 channel", "4 channels", "8 channels"],
        "unit": "mode",
    }
    return controlParams


def controlGet_1(main_app, omvar):
    '''
    Get the register value and set the widget related to BLC enable mode
    '''
    gui_text = main_app.sensor.blc[0]
    omvar.set(gui_text)
    return gui_text


def controlSet_1(main_app, variable, event=None):
    '''
    Set the register value based on widget input related to BLC enable mode
    '''
    main_app.sensor.blc = [variable.get(), None, None]


def controlGet_2(main_app, omvar):
    '''
    Get the register value and set the widget related to BLC channels
    '''
    gui_text = main_app.sensor.blc[1]
    omvar.set(gui_text)
    return gui_text


def controlSet_2(main_app, variable, event=None):
    '''
    Set the register value based on widget input related to BLC channels
    '''
    main_app.sensor.blc = [None, variable.get(), None]


def execCmd():
    print('executed')

