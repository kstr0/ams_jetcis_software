import numpy as np


# Table values
ana_table = [1, 2, 4]

def setFrameRate(imager, input, event=None):
    # These can be set differently in the sensor config files!!!
    # check if the value matches if this function makes trouble
    f_clk_in = 38.4e6

    # I2C address and length (addr=16bit, val=8bit)
    imager.disablePrint()
    imager.setSensorI2C(0x54)
    imager.type(1)

    # Entry value
    try:
        fps = float(input)
    except:
        fps = 0.0

    # Vertical blanking
    row_length = imager.read(0x102c) * (2 ** 8) + imager.read(0x102b)
    vsize = (imager.read(0x1088) % (2 ** 3)) * (2 ** 8) + imager.read(0x1087)
    vblank = int(int(f_clk_in / row_length / fps) - vsize)

    # Split value
    high = vblank // (2 ** 8)
    low = vblank % (2 ** 8)

    # Write to registers
    imager.enablePrint()
    imager.write(0x1012, low)
    imager.write(0x1013, high)


def setExposureTime(imager, input, event=None):
    # These can be set differently in the sensor config files!!!
    # check if the value matches if this function makes trouble
    len_eoi = 0
    f_clk_in = 38.4e6

    imager.disablePrint()
    imager.setSensorI2C(0x54)
    imager.type(1)

    try:
        value = float(input)
    except:
        value = 0.0

    # Given exposure time to the exposure length
    row_length = imager.read(0x102c) * (2 ** 8) + imager.read(0x102b)
    time_conversion = row_length / f_clk_in
    exposure_length = round(value / time_conversion / 1000)

    # Split value
    high = exposure_length // (2 ** 8)
    low = exposure_length % (2 ** 8)

    # Write to registers
    imager.enablePrint()
    imager.write(0x100c, low)
    imager.write(0x100d, high)

def setAnalogGain(imager, input, event=None):
    '''
    Set the register value based on widget input related to digital gain
    '''

    # Get value
    input = float(input)

        # Map input to discrete value
    mapped_input = min(ana_table, key=lambda x: abs(x - input))

    # I2C address and length (addr=16bit, val=8bit)
    imager.disablePrint()
    imager.setSensorI2C(0x54)
    imager.type(1)
    imager.enablePrint()

    # Write values to sensor
    #if len(otp_gain_trims) == 0:
    try:
        if mapped_input == 1:
            imager.write(0x400A, 0x08)
            imager.write(0x402A, 0x63)
        elif mapped_input == 2:
            imager.write(0x400A, 0x04)
            imager.write(0x402A, 0x5F)
        elif mapped_input == 4:
            imager.write(0x400A, 0x02)
            imager.write(0x402A, 0x5E)
        else:
            # Print error in StatusArea
            imager.pr("ERROR: Only x1, x2, x4 is supported")
            imager.write(0x400A, 0x08)
            imager.write(0x402A, 0x63) 
    except:
        if mapped_input == 1:
            imager.write(0x400A, 0x08)
            imager.write(0x4009, otp_gain_trims[0])
        elif mapped_input == 2:
            imager.write(0x400A, 0x04)
            imager.write(0x4009, otp_gain_trims[1])
        elif mapped_input == 4:
            imager.write(0x400A, 0x02)
            imager.write(0x4009, otp_gain_trims[2])
        else:
            # Print error in StatusArea
            imager.pr("ERROR: Only x1, x2, x4 or x8 is supported")
            imager.write(0x400A, 0x08)
            imager.write(0x4009, otp_gain_trims[0])


def execCmd():
    print('executed')

