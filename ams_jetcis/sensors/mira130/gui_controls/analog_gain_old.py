import time
def controlInit():
    '''
    Initial widget parameters in ms
    '''

    controlParams = {
        "name" : "analog gain",
        "comment" : "Press enter after entering a value.",
        "type" : "spinbox",
        "min": 1.0,
        "max": 30,
        "default": 1,
        "refresh": 1,
        "step": 0.0625,
        "unit" : "linear",
    }
    return controlParams

def controlGet(main_app, spinbox, variable, event=None):
    '''
    Get the register value and set the widget related to exposure time
    '''
    variable.set("{:.4f}".format(main_app.sensor.analog_gain))

    return 0


def controlSet(main_app, sreg, event=None):
    '''
    Set the register value based on widget input related to exposure time
    '''

    main_app.sensor.set_analog_gain(float(sreg.get()))
    main_app.imager.doWidgetUpdate()

    # Set GUI variable to mapped input
    #sreg.set(gain)

    # Updates the status of all Widgets
    #imager.doWidgetUpdate()



def validate(spinbox, number=None):
    '''
    Validate the input of the wiget. Only allow numbers between from and to.
    '''
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
