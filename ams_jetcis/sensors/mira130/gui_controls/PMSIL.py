
def controlInit():
    controlParams = {
        "name": "PMSIL",
        "comment": "enable 940nm led",
        "type": "checkbutton",
        "onvalue": 1,
        "offvalue": 0,
        "default": "off",
        "unit": "on/off",

    }
    return controlParams

def controlGet(main_app, sreg):
    imager = main_app.imager
    if imager.sensori2c==0x32:
        
        # Get the driver access
        imager = main_app.imager

        # Read register and convert to 8 bit
        imager.setSensorI2C(0x30)
        imager.type(0) # Reg=8bit, val=8bit
        on=imager.read(6)

        imager.setSensorI2C(imager.sensori2c)
        imager.type(1) # default 
        
        if on==9:
            result = 1
        else:
            result = 0

        sreg.set(result)
        return result
    else:
            # Driver access
        imager = main_app.imager

        # I2C address LED and length (addr=8bit, val=8bit)
        imager.setSensorI2C(0x53)
        imager.type(0)

        # General purpose reg
        status = imager.read(0x10)

        # I2C address sensor and length (addr=16bit, val=8bit)
        imager.setSensorI2C(imager.sensori2c)
        imager.type(1)

        if status == 3:
            result = 1
        else:
            result = 0

        sreg.set(result)
        return result


def controlSet(main_app, variable):
    imager = main_app.imager
    sensor = main_app.sensor
    if sensor.sensori2c==0x32:
        # Get the driver access
        imager = main_app.imager

        # Get checkbutton value
        value = int(variable.get())

        # Change bit 3
        if (value == 1):
            imager.setSensorI2C(0x30)
            imager.type(0) # Reg=8bit, val=8bit
            imager.write(1,0xFE)
            imager.write(2,0xFE)
            imager.write(3,0x00)
            imager.write(6,9)
            imager.write(9,3)
            imager.setSensorI2C(0x32)
            imager.type(1) # default 
        else:
            imager.setSensorI2C(0x30)
            imager.type(0) # Reg=8bit, val=8bit
            imager.write(1,0xFE)
            imager.write(2,0xFE)
            imager.write(3,0x00)
            imager.write(6,1)
            imager.write(9,3)
            imager.setSensorI2C(imager.sensori2c)
            imager.type(1) # default 
    else:
            # Get the driver access

        imager = main_app.imager

        # Get checkbutton value
        value = int(variable.get())
        print('i2c 30 illum')
        # Change bit 3
        if (value == 1):
            print('i2c 30 illum - enable')
            # I2C address LED and length (addr=8bit, val=8bit)
            imager.setSensorI2C(0x53)
            imager.type(0)

            # Flash mode, current, timeout
            imager.write(0x10, 0x00)
            imager.write(0xb0, 0x07)
            imager.write(0xc0, 0x05)

            # I2C address sensor and length (addr=16bit, val=8bit)
            imager.setSensorI2C(imager.sensori2c)
            imager.type(1)

            # Enable trigger
            imager.write(0x10d7, 0x01)

        else:
            print('i2c 30 illum - disable')
            # I2C address LED and length (addr=8bit, val=8bit)
            imager.setSensorI2C(0x53)
            imager.type(0)

            # Turn off LED
            imager.write(0x10, 0x08)

            # I2C address sensor and length (addr=16bit, val=8bit)
            imager.setSensorI2C(imager.sensori2c)
            imager.type(1)

            # Disable trigger
            imager.write(0x10d7, 0x00)



def execCmd():
    print('executed')
