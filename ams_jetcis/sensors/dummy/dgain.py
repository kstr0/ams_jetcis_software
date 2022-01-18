
def controlInit():
    controlParams = {
        "name" : "DGAIN",
        "comment" : "Digital gain",
        "type" : "list",
        "min" : 1.0,
        "max" : 16.0,
        "default" : 4.0,
        "list" : (1.0, 2.0, 4.0, 8.0, 16.0),
        "unit" : "multiplier",
    }
    return controlParams

def controlGet():
    return 1.0

def controlSet(value):
    return value



