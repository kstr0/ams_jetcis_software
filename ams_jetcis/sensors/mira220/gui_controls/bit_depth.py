def controlInit():
    controlParams = {
        "name": "Bit depth",
        "comment": "Bit depth",
        "type": "optionmenu",
        "nb_widgets": 1,
        "default_1": "12bit",
        "option_list_1": ["12bit", "10bit", "8bit"],
        "unit": "per pixel",
    }
    return controlParams


def controlGet_1(main_app, omvar):
    gui_text = f'{main_app.sensor.bpp}bit'
    omvar.set(gui_text)
    return gui_text


def controlSet_1(main_app, variable, event=None):  
    # Stop live image
    if (main_app.streaming == True):
        main_app.streaming = False
        main_app.stopLive()

    main_app.sensor.bpp = variable.get()

    main_app.sensor_mode = main_app.sensor.dtMode
    main_app.bpp = main_app.sensor._bpp
    # main_app.sensorInfo["bpp"] = main_app.sensor.bpp
    main_app.sensorInfo = main_app.sensor.get_sensor_info()

    # Start live image
    main_app.startLive()


def execCmd():
    print('executed')
