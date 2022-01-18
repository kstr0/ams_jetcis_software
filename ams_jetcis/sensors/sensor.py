from abc import ABC, abstractmethod


class Sensor(ABC):
    """
    Abstract class describing sensor functions to be implemented.
    Class should be used together with an imager object. 
    """

    def __init__(self, imagertools) -> None:
        self.imager = imagertools
        self.imager.wrong_dtb = self.imager.kernel_dtb_manager.check_current_sensor(self.name)
        if self.imager.wrong_dtb:
            self.imager.kernel_dtb_manager.load_kernel_and_dtb(self.name)
            raise SystemError('### Wrong dtb/driver loaded. A wizard loaded the correct one. Now you should reboot. ### \n')

    def check_current_sensor(self, sensor_name):
        ret = self.imager.kernel_dtb_manager.check_current_sensor(sensor_name)
        return ret

    def cold_start(self):
        """reset, check and init sensor with error handling"""
        self.reset_sensor()
        attempts = 0
        while self.check_sensor():
            attempts = attempts + 1
            self.reset_sensor()
            if attempts>=2:
                raise IOError(f'sensor not detected after {attempts} attempts')
                exit('ending program')  
                return 1
        return 0        

    def get_sensor_info(self):
        controlParams = {
            "width" : self.width,
            "height" : self.height,
            "widthDISP" : self.width ,
            "heightDISP" : self.height,
            "widthDMA" :  self.widthDMA,
            "heightDMA" : self.heightDMA,
            "bpp" : self.bpp,
            "fps" : self.fps,
            "dtMode" : self.dtMode,
        }
        return controlParams

    @abstractmethod
    def reset_sensor(self, *args, **kwargs):
        """reset routine for sensor."""
        pass

    @abstractmethod
    def check_sensor(self, *args, **kwargs):
        """CHECK sensor, return 0 when detected, return 1 when not."""
        pass
    @abstractmethod
    def init_sensor(self, *args, **kwargs):
        """init routine for sensor."""
        pass
    @abstractmethod
    def set_exposure_us(self, *args, **kwargs):
        """exposure in us"""
        pass

    @abstractmethod
    def set_analog_gain(self, *args, **kwargs):
        pass

    @abstractmethod
    def set_digital_gain(self, *args, **kwargs):
        return 0

    @abstractmethod
    def write_register(self, *args, **kwargs):
        pass

    @abstractmethod
    def read_register(self, *args, **kwargs):
        pass
