
def controlInit():
    controlParams = {
        "name": "Defect correction",
        "comment": "Defect pixel correction",
        "type": "checkbutton",
        "onvalue": 1,
        "offvalue": 0,
        "refresh": 1,
        "default": "on",
        "unit": "on/off",

    }
    return controlParams

def controlGet(main_app, sreg):

    sreg.set(bool(main_app.sensor.pixel_correction))
    print('defect_get called')

    return 0

def get_defect_correction(imager) -> int:

    # readout amount of defects
    imager.setSensorI2C(0x36)
    imager.type(1)
    imager.write(0xE000,0) # high mode
    imager.write(0x012E,1) #DEFECT_PIXEL_CNT_HOLD
    amount1 = imager.read(0x012B,0) #DEFECT_PIXEL_CNT high byte, big endian
    amount2 = imager.read(0x012C,0) #DEFECT_PIXEL_CNT
    amount3 = imager.read(0x012D,0) #DEFECT_PIXEL_CNT
    imager.write(0x012E,0) #DEFECT_PIXEL_CNT_HOLD
    return amount3+2**8*amount2+2**16*amount1

def controlSet(main_app, sreg):
    main_app.sensor.set_pixel_correction(bool(sreg.get()))
    print('defect_set called')
    return 0


def execCmd():
    print('executed')
