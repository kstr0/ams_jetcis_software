
def controlInit():
    controlParams = {
        "name" : "Modes",
        "comment" : "ASpecial sensor modes",
        "type" : "list",
        "min" : 1.0,
        "max" : 32.0,
        "default" : "HDR",
        "list" : ("SDR", "HDR", "HDR-DLO"),
        "unit" : "",
    }
    return controlParams

def controlGet():
    return 1.0

def controlSet(value):
    return value

