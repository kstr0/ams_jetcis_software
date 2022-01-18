import numpy as np


def controlInit():
    controlParams = {
        "name": "Analog gain",
        "comment": "analog gain",
        "type": "slider",
        "nb_widgets": 1,
        "min": 0.00,
        "max": 29.11,
        "default": 1.0,
        "step": 0.01,
        "unit": "dB",
        "auto": False,
        "refresh": True,
    }
    return controlParams


# Table dB values
ana_table_db = [0.00, 0.27, 0.53, 0.78, 1.02, 1.26, 1.49, 1.72, 1.94, 2.15, 2.36, 2.57, 2.77, 2.96, 3.15, 3.34, 3.52,
                3.70, 3.88, 4.05, 4.22, 4.38, 4.54, 4.70, 4.86, 5.01, 5.17, 5.43, 5.69, 5.94, 6.19, 6.43, 6.66, 6.88,
                7.10, 7.32, 7.53, 7.73, 7.93, 8.13, 8.32, 8.50, 8.69, 8.87, 9.04, 9.21, 9.38, 9.55, 9.71, 9.87, 10.03,
                10.18, 10.33, 10.48, 10.63, 10.77, 10.91, 11.05, 11.19, 11.45, 11.71, 11.96, 12.21, 12.45, 12.68, 12.90,
                13.12, 13.34, 13.55, 13.75, 13.95, 14.15, 14.34, 14.53, 14.71, 14.89, 15.06, 15.23, 15.40, 15.57, 15.73,
                15.89, 16.05, 16.20, 16.35, 16.50, 16.65, 16.79, 16.93, 17.07, 17.21, 17.47, 17.73, 17.99, 18.23, 18.47,
                18.70, 18.93, 19.14, 19.36, 19.57, 19.77, 19.97, 20.17, 20.36, 20.55, 20.73, 20.91, 21.08, 21.26, 21.42,
                21.59, 21.75, 21.91, 22.07, 22.22, 22.37, 22.52, 22.67, 22.81, 22.95, 23.09, 23.23, 23.49, 23.75, 24.01,
                24.25, 24.49, 24.72, 24.95, 25.17, 25.38, 25.59, 25.79, 25.99, 26.19, 26.38, 26.57, 26.75, 26.93, 27.10,
                27.28, 27.44, 27.61, 27.77, 27.93, 28.09, 28.24, 28.39, 28.54, 28.69, 28.83, 28.97, 29.11]


def controlGet(main_app, s):
    # Get the driver access
    imager = main_app.imager
    imager.setSensorI2C(imager.sensori2c)
    # Read the registers
    coarse_value_read = imager.read(0x3e08)
    fine_value_read = imager.read(0x3e09)

    # Coarse gain
    if coarse_value_read == 3:
        coarse_reg = 0
    else:
        coarse_reg = int(np.log2(coarse_value_read - 31)) - 1

    # Fine gain
    fine_reg = fine_value_read - 32

    # Taking the gap into account
    if (coarse_reg > 0) or (fine_reg > 25):
        fine_reg = fine_reg - 6

    # GUI new value
    ana_gain_index = 32 * coarse_reg + fine_reg
    ana_gain_gui = ana_table_db[ana_gain_index]

    s.set(ana_gain_gui)

    return ana_gain_gui


def controlSet(main_app, sreg, event=None):
    imager = main_app.imager
    imager.setSensorI2C(imager.sensori2c)
    # Get slider value
    input = float(sreg.get())

    # Map input to discrete value
    mapped_input = min(ana_table_db, key=lambda x: abs(x - input))

    if input >= 29.0:
        mapped_input = 29.11

    # Get index of discrete value
    mapped_input_index = ana_table_db.index(mapped_input)

    # Taking the gap into account
    if (mapped_input_index > 25):
        mapped_input_index = mapped_input_index + 6

    # Get the driver access
    imager = main_app.imager

    # Coarse gain
    coarse_input = mapped_input_index // 32
    if coarse_input > 0:
        coarse_value = 2 ** (coarse_input + 1) + 31
    else:
        coarse_value = 3
    imager.write(0x3e08, coarse_value)

    # Fine gain
    fine_input = mapped_input_index % 32 + 1
    fine_value = fine_input + 31
    imager.write(0x3e09, fine_value)

    # Set GUI variable to mapped input
    sreg.set(mapped_input)

    # Updates the status of all Widgets
    imager.doWidgetUpdate()


def execCmd():
    print('executed')
