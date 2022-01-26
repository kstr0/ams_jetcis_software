#
# This is a very simple example, showing how to script the JetCIS application framework
#

# Step1:    The driver_accass package must be included. It allows to have access to the camera driver and control
#           all attached I2C devices like PMICs, LED drivers or microcontroller. Please make sure., that the kernel
#           and devicetree fit to the selected image sensor
import driver_access

# Step2:    Include also other used packages
#
import time
import cv2
import os

# Step3:    Include helpful functions here. In this case a function is used to enable or disable the testpattern of
#           the CGSS130. This is taken from a cgss130 widget.
def controlSet(imager, onoff):
    # Get checkbutton value
    # Read register and convert to 8 bit
    current_address_value = imager.read(0x4501)
    current_address_value_bin = format(current_address_value, '08b')
    # Change bit 3
    if (onoff == False):
        write_value = current_address_value_bin[:4] + '0' + current_address_value_bin[5:]
    else:
        write_value = current_address_value_bin[:4] + '1' + current_address_value_bin[5:]
    # Write to register
    imager.write(0x4501, int(write_value, 2))



# Step4:    The driver_access class has to be used
#           The initialization has three parameters:
#               Param1 = callback function for outputs (could be piped in GUI frameworks or files
#               Param2 = Videoport (either 0 for /dev/video0 or 1 for /dev/video1)
#               Param3 = an instance of the connection to the SyncServer, which is useful in certain stereo scenarios.
#                        use "None" in doubt
#
#           setSystype defines the used hardware platform. Actually "Nano" and "TX2" are supported.
imager = driver_access.imagerTools(print, 0, None)
imager.setSystype("Nano")

# Step3:    First important thing is to initialize the sensor. This could be done either by directly by using the
#           driver_access i2c commands or by using an already existing init script
#           This example loads an init script:
#               - The fullres.py is loaded and - by using the compile command - integrated in the actual code
#               - After this, all functions from fullres.py could be executed
#               - getSensorInfo loads a structure into sensorInfo describing all important resolution informations
#               - resetSensor resets the sensor
#               - initSensor configures the sensor
fname = "../../cgss130-10bpp2lanes/fullres.py"
try:
    with open(fname, "r") as file:
        eobj = compile(file.read(), fname, "exec")
        exec(eobj, globals())
except:
    print("ERROR: unable to execute init script")
sensorInfo = getSensorInfo(imager)
resetSensor(imager)
initSensor(imager)

# Step 4:   The last step of this example creates one image as tiff file, switches to testpattern, waits a second
#           and creates a second image. This repeats 5 times before the program ends
testpattern = False
imager.setformat(sensorInfo["bpp"], sensorInfo["width"], sensorInfo["height"], sensorInfo["widthDMA"], sensorInfo["heightDMA"], True)
for lp in range(0,10):
    print("{} cycle:".format(lp))
    imager.saveRaw("~/test{}.raw".format(lp))
    iface = "/usr/bin/gst-launch-1.0 "
    iface += "nvarguscamerasrc num-buffers=1 sensor-id=0 wbmode=0 tnr-mode=0 tnr-strength=0.5 ee-mode=0 ee-strength=0.5 sensor-mode=0"
    iface += " saturation=0.0 !"
    iface += " \"video/x-raw(memory:NVMM),width=(int){},height=(int){},format=(string)NV12,framerate=(fraction){}/1\" !".format(
        sensorInfo["width"], sensorInfo["height"], sensorInfo["fps"])
    iface += " nvvidconv ! video/x-raw ! filesink location=test{}.tif".format(lp)
    print(iface)
    os.system(iface)
    time.sleep(1)
    testpattern = not testpattern
    controlSet(imager, testpattern)
