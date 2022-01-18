def controlInit():
    controlParams = {
        "name": "Context switching",
        "comment": "Choose a context",
        "type": "optionmenu",
        "nb_widgets": 2,
        "default_1": "A",
        "option_list_1": ["A", "B"],
        "default_2": "A",
        "option_list_2": ["A", "B"],
        "unit": "observe / active",
    }
    return controlParams


def controlGet_1(main_app, omvar):
    gui_text = main_app.sensor.context_observe
    omvar.set(gui_text)
    return gui_text


def controlSet_1(main_app, variable, event=None):
    value = variable.get()
    main_app.sensor.context_observe = value
    main_app.imager.doWidgetUpdate()


def controlGet_2(main_app, omvar):
    gui_text = main_app.sensor.context_active
    omvar.set(gui_text)
    return gui_text


def controlSet_2(main_app, variable, event=None):
    value = variable.get()

    sensor = main_app.sensor

    active_context = sensor.context_active
    if value != active_context: # Context switch
        context_observe_temp = main_app.sensor.context_observe
        main_app.sensor.context_observe = active_context
        [w_old, h_old, _, _] = sensor.roi
        main_app.sensor.context_observe = value
        [w, h, _, _] = sensor.roi
        main_app.sensor.context_observe = context_observe_temp
        if (w != w_old) or (h != h_old): # Change in roi
            if (main_app.streaming == True): # Stop live image
                main_app.streaming = False
                main_app.stopLive()
            sensor.context_active = value
            main_app.sensor_mode = sensor.dtMode
            main_app.sensor_w = sensor.width
            main_app.sensor_h = sensor.height
            main_app.w = sensor.width * 0.3
            main_app.h = sensor.height * 0.3
            main_app.sensor_wdma = sensor.widthDMA
            main_app.sensor_hdma = sensor.heightDMA
            main_app.sensorInfo["width"] = main_app.sensor_w
            main_app.sensorInfo["height"] = main_app.sensor_h
            main_app.sensorInfo["widthDISP"] = main_app.w
            main_app.sensorInfo["heightDISP"] = main_app.h
            main_app.sensorInfo["widthDMA"] = main_app.sensor_wdma
            main_app.sensorInfo["heightDMA"] = main_app.sensor_hdma
            main_app.startLive() # Start live image
        else:
            sensor.context_active = value


def execCmd():
    print('executed')