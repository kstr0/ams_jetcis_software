def controlInit():
    controlParams = {
        "name": "Defect correction",
        "comment": "Choose a replacement method",
        "type": "optionmenu",
        "nb_widgets": 3,
        "default_1": "Off",
        "option_list_1": ["Off", "Kernel", "Line"],
        "default_2": "Median",
        "option_list_2": ["Median", "Mean", "Min", "Max"],
        "default_3": "Mode 0",
        "option_list_3": ["Mode 0", "Mode 1"],
        "unit": "method",
    }
    return controlParams


def controlGet_1(main_app, omvar):
    gui_text = main_app.sensor.dpc[0]
    omvar.set(gui_text)
    return gui_text


def controlSet_1(main_app, variable, event=None):
    value = variable.get()
    main_app.sensor.dpc = [value, None, None, None, None]


def controlGet_2(main_app, omvar):
    gui_text = main_app.sensor.dpc[1]
    omvar.set(gui_text)
    return gui_text


def controlSet_2(main_app, variable, event=None):
    value = variable.get()
    main_app.sensor.dpc = [None, value, None, None, None]


def controlGet_3(main_app, omvar):
    gui_text = main_app.sensor.dpc[4]
    omvar.set(gui_text)
    return gui_text


def controlSet_3(main_app, variable, event=None):
    value = variable.get()
    main_app.sensor.dpc = [None, None, None, None, int(value[-1])] 


def execCmd():
    print('executed')