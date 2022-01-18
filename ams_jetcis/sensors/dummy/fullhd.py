

def initPrint(printFunc):
    printFunc("INFO: sensor resolution script executed")
    global csg
    import driver_access
    csg = driver_access.csg1kTools(printFunc)

def getSensorInfo(csg):
    controlParams = {
        "width" : 1920,
        "height" : 1080,
        "widthDMA" : 1920,
        "heightDMA" : 1080,
        "bpp" : 8
    }
    return controlParams

def resetSensor(csg):
    pass

def checkSensor(csg):
    pass

def initSensor(csg):
    # init sensor
    pass
