def controlInit():
    '''
    Initial widget parameters
    '''
    controlParams = {
        "name": "BLC",
        "comment": "Black level control target",
        "type": "slider",
        "nb_widgets": 1,
        "min": 0.0,
        "max": (1<<13) - 1,
        "default": 1.0,
        "step": 32,
        "unit": "target",
        "auto": False,
        "refresh": True,
    }
    return controlParams


def controlGet(main_app, s):
    '''
    Get the register value and set the widget related to BLC target
    '''
    ana_gain_gui = main_app.sensor.blc[2]
    s.set(ana_gain_gui)
    return ana_gain_gui


def controlSet(main_app, sreg, event=None):
    '''
    Set the register value based on widget input related to BLC target
    '''
    main_app.sensor.blc = [None, None, int(sreg.get())]
    main_app.imager.doWidgetUpdate()


def execCmd():
    print('executed')

