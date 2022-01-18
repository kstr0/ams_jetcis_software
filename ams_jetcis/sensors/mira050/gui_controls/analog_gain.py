def controlInit():
    controlParams = {
        "name": "Analog gain",
        "comment": "Analog gain",
        "type": "optionmenu",
        "nb_widgets": 1,
        "default_1": 1,
        "option_list_1": [1,2,4],
        "unit": "per pixel",
    }
    return controlParams


def controlGet_1(main_app, omvar):
    # Get the driver access
    omvar.set(main_app.sensor.analog_gain)
    return 0


def controlSet_1(main_app, variable, event=None):
   
    # # Get option menu value
    analog_gain = int(variable.get())
    # # Get the driver access
    main_app.sensor.init_sensor(bit_mode=main_app.sensor.bit_mode, analog_gain=analog_gain)

    main_app.imager.doWidgetUpdate()

    return 0

