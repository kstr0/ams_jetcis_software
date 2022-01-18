def controlInit():
    controlParams = {
        "name": "Illumination",
        "comment": "Enable 940nm LED",
        "type": "checkbutton",
        "onvalue": 1,
        "offvalue": 0,
        "default": "off",
        "unit": "on / off",
    }
    return controlParams


def controlGet(main_app, sreg):
    sreg.set(main_app.sensor.illum)
    return 0


def controlSet(main_app, variable):
    """
            
        Parameters
        ----------
        led_driver : list
            [0] : enable the flash mode if 1
            [1] : Desired current level in mA (80, 150, 220, 280, 350, 410, 470, 530, 590, 650, 710, 770, 830, 890, 950 or 1010)
            [2] : Time-out time in ms (60, 125, 250, 375, 500, 625, 750 or 1100)
    """
    value = int(variable.get())
    main_app.sensor.led_driver = [value, 950, 125]
    main_app.sensor.illum_trig(value)


def execCmd():
    print('executed')
