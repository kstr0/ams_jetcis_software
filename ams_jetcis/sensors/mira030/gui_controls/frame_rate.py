def controlInit():
    '''
    Initial widget parameters
    '''
    controlParams = {
        "name" : "Frame rate",
        "comment" : "Changes the frame length.",
        "type" : "slider",
        "nb_widgets": 1,
        "min" : 1,
        "max" : 80,
        "default" : 30,
        "step" : 1,
        "unit" : "fps",
        "auto": False,
        "refresh": True,
    }
    return controlParams

def controlGet(main_app, s):
    '''Get the register value and set the widget related to frame rate.
    '''
    result = main_app.sensor.fps
    s.set(result)
    main_app.sensor_fps = round(result, 3)
    main_app.sensorInfo["fps"] = round(result, 3)
    return result

def controlSet(main_app, sreg, event=None):
    '''Set the register value based on widget input related to frame rate.
    '''
    main_app.sensor.fps = float(sreg.get())
    # Updates the status of all Widgets
    main_app.imager.doWidgetUpdate()

def execCmd():
    print('executed')

