def controlInit():
    controlParams = {
        "name": "Test image",
        "comment": "test image",
        "type": "optionmenu",
        "nb_widgets": 1,
        "default_1": "Off",
        "option_list_1": ["Off", "Vertical", "Diagonal", "Walking 1", "Walking 0"],
        "unit": "pattern",
    }
    return controlParams


def controlGet_1(main_app, omvar):
    gui_text = main_app.sensor.test_image
    omvar.set(gui_text)
    return gui_text


def controlSet_1(main_app, variable, event=None):
    main_app.sensor.test_image = variable.get()


def execCmd():
    print('executed')