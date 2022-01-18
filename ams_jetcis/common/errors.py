class Mira050ConfigError(Exception):
    """Exception raised for errors in the input salary.

    Attributes:
        salary -- input salary which caused the error
        message -- explanation of the error
    """

    def __init__(self, bit_mode, analog_gain, message="Invalid arguments"):
        self.bit_mode = bit_mode
        self.analog_gain = analog_gain
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'You used bit mode: {self.bit_mode} and analog gain: {self.analog_gain} -> {self.message}'


