
def controlInit():
    controlParams = {
        "name": "Mirror",
        "comment": "Xmirror",
        "type": "checkbutton",
        "onvalue": 1,
        "refresh": 1,
        "offvalue": 0,
        "default": "off",
        "unit": "on/off",

    }
    return controlParams


def controlGet(main_app, sreg):

    # Get the driver access
    sreg.set(bool(main_app.sensor.mirror))
    print('mirror get called')

    return 0

def controlSet(main_app, sreg):

    main_app.sensor.set_mirror(bool(sreg.get()))
    print('mirror set called')
    main_app.imager.doWidgetUpdate()

    return 0







# def controlGet(main_app, sreg):

#     # Get the driver access
#     imager = main_app.imager

#     # Read register and convert to 8 bit
#     imager.setSensorI2C(0x36)
#     imager.type(1) # Reg=16bit, val=8bit
#     imager.write(0xe004,0)
#     imager.write(0xe000,1)
#     on=imager.read(0x4030) & 0x1

    
#     if on==1:
#         result = 1
#     else:
#         result = 0

#     sreg.set(result)
#     print('mirror_set called')

#     return result

# def controlSet(main_app, variable):

#     # Get the driver access
#     imager = main_app.imager
#     imager.disablePrint()
#     imager.setSensorI2C(0x36)
#     imager.type(1)
#     imager.enablePrint()

#     # Get checkbutton value
#     value = int(variable.get())

#     # Change bit 3
#     if (value == 1):
#         imager.setSensorI2C(0x36)
#         imager.write(0xe004, 0)
#         imager.write(0xe000, 1)
#         imager.write(0xe030, 1)
#     else:
#         imager.setSensorI2C(0x36)
#         imager.write(0xe004, 0)
#         imager.write(0xe000, 1)
#         imager.write(0xe030, 0)
#     main_app.imager.doWidgetUpdate()
#     imager.disablePrint()
#     print('mirror_set called')


def execCmd():
    print('executed')
