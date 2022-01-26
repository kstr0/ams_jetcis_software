import ams_jetcis
from ams_jetcis.sensors.sensor import Sensor
from ams_jetcis.sensors.mira220.mira220 import Mira220
from ams_jetcis.sensors.mira130.mira130 import Mira130
from ams_jetcis.sensors.mira050.mira050 import Mira050
from ams_jetcis.sensors.mira030.mira030 import Mira030
from ams_jetcis.common.driver_access import ImagerTools

imagertools = ImagerTools(printfun=None, port=0, rootPW = 'jetcis')
sensor = Mira050(imagertools)
sensor.exposure_us=sensor.exposure_us
sensor.analog_gain=sensor.analog_gain