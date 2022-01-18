import numpy as np


def controlInit():
    controlParams = {
        "name" : "Digital gain",
        "comment" : "digital gain",
        "type" : "slider",
        "nb_widgets": 1,
        "min" : 0.00,
        "max" : 29.97,
        "default" : 0.0,
        "step" : 0.01,
        "unit" : "dB",
        "auto" : False,
        "refresh" : True,
    }
    return controlParams


# Table dB values
dig_table_db = [0.00, 0.27, 0.53, 0.78, 1.02, 1.26, 1.49, 1.72, 1.94, 2.15, 2.36, 2.57, 2.77, 2.96, 3.15, 3.34, 3.52,
                3.70, 3.88, 4.05, 4.22, 4.38, 4.54, 4.70, 4.86, 5.01, 5.17, 5.31, 5.46, 5.60, 5.74, 5.88, 6.02, 6.29,
                6.55, 6.80, 7.04, 7.28, 7.51, 7.74, 7.96, 8.17, 8.38, 8.59, 8.79, 8.98, 9.17, 9.36, 9.54, 9.72, 9.90,
                10.07, 10.24, 10.40, 10.57, 10.72, 10.88, 11.04, 11.19, 11.33, 11.48, 11.62, 11.77, 11.9, 12.04, 12.31,
                12.57, 12.82, 13.06, 13.30, 13.53, 13.76, 13.98, 14.19, 14.40, 14.61, 14.81, 15.00, 15.19, 15.38, 15.56,
                15.74, 15.92, 16.09, 16.26, 16.42, 16.59, 16.75, 16.9, 17.06, 17.21, 17.36, 17.50, 17.64, 17.79, 17.93,
                18.06, 18.33, 18.59, 18.84, 19.08, 19.32, 19.55, 19.78, 20.00, 20.21, 20.42, 20.63, 20.83, 21.02, 21.21,
                21.40, 21.58, 21.76, 21.94, 22.11, 22.28, 22.44, 22.61, 22.77, 22.92, 23.08, 23.23, 23.38, 23.52, 23.67,
                23.81, 23.95, 24.08, 24.35, 24.61, 24.86, 25.11, 25.34, 25.58, 25.80, 26.02, 26.24, 26.44, 26.65, 26.85,
                27.04, 27.23, 27.42, 27.60, 27.78, 27.96, 28.13, 28.30, 28.46, 28.63, 28.79, 28.94, 29.10, 29.25, 29.40,
                29.54, 29.69, 29.83, 29.97]


def controlGet(main_app, s):
    # Get the driver access
    imager = main_app.imager

    # Read the registers
    coarse_value_read = imager.read(0x3e06)
    fine_value_read = imager.read(0x3e07)

    # Coarse gain
    coarse_reg = int(np.log2(coarse_value_read + 1))

    # Fine gain
    fine_reg = int((fine_value_read - 128) / 4)

    # GUI new value
    dig_gain_index = 32 * coarse_reg + fine_reg
    dig_gain_gui = dig_table_db[dig_gain_index]

    s.set(dig_gain_gui)
    return dig_gain_gui

def controlSet(main_app, sreg, event=None):
    # Get slider value
    input = float(sreg.get())

    # Map input to discrete value
    mapped_input = min(dig_table_db, key=lambda x: abs(x - input))

    # Get index of discrete value
    mapped_input_index = dig_table_db.index(mapped_input)

    # Get the driver access
    imager = main_app.imager

    # Coarse gain
    coarse_input = mapped_input_index // 32
    coarse_value = 2 ** int(coarse_input) - 1
    imager.write(0x3e06, coarse_value)

    # Fine gain
    fine_input = mapped_input_index % 32
    fine_value = 128 + 4 * fine_input
    imager.write(0x3e07, fine_value)

    # Set GUI variable to mapped input
    sreg.set(mapped_input)

    # Updates the status of all Widgets
    imager.doWidgetUpdate()

def execCmd():
    print('executed')
