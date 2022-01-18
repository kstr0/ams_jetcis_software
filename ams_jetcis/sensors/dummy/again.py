
def controlInit():
    controlParams = {
        "name" : "AGAIN",
        "comment" : "Analog gain",
        "type" : "slider",
        "min" : 1.0,
        "max" : 32.0,
        "default" : 2.0,
        "step" : 0.5,
        "unit" : "dB",
    }
    return controlParams

def controlGet():
    return 1.0

def controlSet(value):
    return value

