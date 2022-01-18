def controlInit():
    controlParams = {
        "name": "Bit depth",
        "comment": "Bit depth",
        "type": "optionmenu",
        "nb_widgets": 1,
        "default_1": "10bit",
        "option_list_1": ["12bit", "10bit", "10bithighspeed"],
        "unit": "per pixel",
    }
    return controlParams


def controlGet_1(main_app, omvar):
    # Get the driver access
    sensor = main_app.sensor

    omvar.set(sensor.bit_mode)

    # return gui_text


def controlSet_1(main_app, variable, event=None):
    # global dtMode_to_cfg, cfg_to_dtMode
    
    # # Get option menu value
    bit_mode = variable.get()

    # # Get the driver access
    sensor = main_app.sensor


    # Stop live image
    if (main_app.streaming == True):
        main_app.streaming = False
        main_app.stopLive()


    # cfg = dtMode_to_cfg[main_app.sensor_mode]
    sensor.cold_start()
    sensor.init_sensor(bit_mode=bit_mode, analog_gain=1)

    main_app.bpp = sensor.bpp
    main_app.sensorInfo = sensor.get_sensor_info()
    main_app.sensor_mode = sensor.dtMode


    # Start live image
    main_app.startLive()
    main_app.imager.doWidgetUpdate()

    return 0


def execCmd():
    print('executed')
