class AutoBrightness130():

    """
    class to do agc/aec
    """

    def __init__(self,imager):
        self.means = []
        self.gains = []
        self.exposures = []
        self.imager=imager

    def do_abc(imager, last_img, frame_time, means, exposures, gains):
        """
        auto gain and auto exposure.
        """
        new_gain = gains[-1]
        new_exposure = exposures[-1]

        means.append(last_img.mean())
        if means[-1] > 200:
            new_exposure = exposures[-1]-1000
            exposures.append(new_exposure)

        elif means[-1] < 140:
            new_exposure = exposures[-1]+1000
            if new_exposure > frame_time:
                new_exposure = frame_time

        if len(exposures) > 10 and len(exposures) % 10 == 0:
            if np.mean(exposures[-10:]) > 0.9*frame_time:
                new_gain = gains[-1]+1
            if np.mean(exposures[-10:]) < 0.5*frame_time:
                new_gain = gains[-1]-1
                if new_gain < 0:
                    new_gain = 0

        exposures.append(new_exposure)
        gains.append(new_gain)
        set_gain(imager, new_gain)
        set_exposure(imager, new_exposure)

        return 0

    def get_max_exposure(imager):
        frame_length = imager.read(0x320e) * 256 + imager.read(0x320f)
        max_value = (frame_length - 8) * 16
        return max_value



    def set_gain(imager, input):

        # Map input to discrete value
        mapped_input = min(ana_table_db, key=lambda x: abs(x - input))

        if input >= 29.0:
            mapped_input = 29.11

        # Get index of discrete value
        mapped_input_index = ana_table_db.index(mapped_input)

        # Taking the gap into account
        if (mapped_input_index > 25):
            mapped_input_index = mapped_input_index + 6

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

    def set_exposure(imager,value):
        value = int(value)
        frame_length = imager.read(0x320e) * 256 + imager.read(0x320f)
        max_value = (frame_length - 8) * 16


        if value > max_value:
            value = max_value

        high = value // (2**16)
        middle_temp = value % (2**16)
        middle = middle_temp // (2**8)
        low = middle_temp % (2**8)

        imager.write(0x3e00, high)
        imager.write(0x3e01, middle)
        imager.write(0x3e02, low)
        return again
