def controlInit():
    controlParams = {
        "name": "Region of interest",
        "comment": "ROI",
        "type": "optionmenu",
        "nb_widgets": 1,
        "default_1": "1600x1400",
        "option_list_1": ["1600x1400", "1280x1120", "640x480"],
        "unit": "w x h",
    }
    return controlParams


def controlGet_1(main_app, omvar):
    [w, h, _, _] = main_app.sensor.roi
    omvar.set(f'{w}x{h}')
    return f'{w}x{h}'


def controlSet_1(main_app, variable, event=None):
    # Get option menu value
    value = variable.get()

    if main_app.sensor.context_active == main_app.sensor.context_observe:

        # Stop live image
        if (main_app.streaming == True):
            main_app.streaming = False
            main_app.stopLive()

        main_app.sensor.roi = [int(value.split('x')[0]), int(value.split('x')[1]), None, None]

        main_app.sensorInfo = main_app.sensor.get_sensor_info()
        main_app.sensor_mode = main_app.sensor.dtMode
        main_app.sensor_w = main_app.sensor.width
        main_app.sensor_h = main_app.sensor.height
        main_app.w = main_app.sensor.width# * 0.3
        main_app.h = main_app.sensor.height# * 0.3
        main_app.sensor_wdma = main_app.sensor.widthDMA
        main_app.sensor_hdma = main_app.sensor.heightDMA

        # Start live image
        main_app.startLive()
    
    else:
        main_app.sensor.roi = [int(value.split('x')[0]), int(value.split('x')[1]), None, None]


def execCmd():
    print('executed')
