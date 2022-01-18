def controlInit():
    controlParams = {
        "name": "Frame rate",
        "comment": "Press enter after entering a value.",
        "type": "spinbox",
        "min": 1.0,
        "max": 90.0,
        "default": 30.0,
        "step": 1.0,
        "unit": "fps",
    }
    return controlParams


def controlGet(main_app, spinbox, variable, event=None):
    fps_observe = main_app.sensor.fps

    context_observe_temp = main_app.sensor.context_observe
    main_app.sensor.context_observe = main_app.sensor.context_active
    fps_actual = main_app.sensor.fps
    main_app.sensor.context_observe = context_observe_temp

    # Update the min/max boundary value
    [fps_min, fps_max, _, _] = main_app.sensor.get_fps_limit()
    spinbox["from_"] = fps_min  
    spinbox["to"] = fps_max

    variable.set("{:.4f}".format(fps_observe))

    main_app.sensor_fps = round(fps_actual, 3)
    main_app.sensorInfo["fps"] = round(fps_actual, 3)


def controlSet(main_app, value, event=None):
    # Entry value
    try:
        fps = float(value.get())
    except:
        fps = 1.0

    # Set fps
    main_app.sensor.fps = fps
    
    # Remove cursor/focus
    main_app.statusArea.focus()

    # Updates the status of all Widgets
    main_app.imager.doWidgetUpdate()


def validate(spinbox, number=None):
    # Only allow numbers between from and to
    if number is None:
        number = spinbox.get()
    if number == "":
        return True
    try:
        if float(spinbox.cget("from")) <= float(number) <= float(spinbox.cget("to")):
            return True
    except ValueError:
        pass
    return False


def execCmd():
    print('executed')
