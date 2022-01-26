'''
Mira050 Event Detection Emulator

Dependencies:
$ pip install opencv-python
$ pip install numpy
$ pip install matplotlib

'''
import time
import numpy as np
import cv2
import matplotlib.pyplot as plt

import driver_access as driver_access
import sys
sys.path.append("/home/jetcis/JetCis/scripting/Mira050")

sys.path.append("/home/jetcis/JetCis/scripting/Mira050")

fname = "../../Mira050/config_files/800_600_12b_mira050_normal_gain1_patch.py"



class EventDetector:

    def __init__(self):

        # Constant parameters
        self.__tile_xcount = 4
        self.__tile_ycount = 5
        self.__tile_treshold = 0.25
        self.__tile_min_treshold = 0
        self.__min_flagged_tiles = 1
        self.__max_flagged_tiles = 19
        self.__tile_disable_mask = 0
        self.__tile_disable_mask2 = np.zeros(
            [self.__tile_xcount, self.__tile_ycount])

        self.exposure = 10
        self.__tile_width = 150
        self.__tile_height = 160
        self.__tile_xstart = 0
        self.__tile_ystart = 0
        self.__cpy_tiles_interval = 0
        self.__tile_dicard_nr_bits = 0
        self.__tile_xsubs = 8
        self.__tile_ysubs = 8
        self.__tile_xbin = 1
        self.__tile_ybin = 1
        self.__detect_flag = 0
        self.__last_detection = time.time()
        self.__detection_power = 3.5  # 1 fps without output
        self.__active_power = 15  # 12b 30fps
        self.__power_history = np.zeros(100)
        self.__last_power_update = time.time()

        # Internal cuisine
        self.__tileset_prev = np.zeros(
            (self.__tile_ycount, self.__tile_xcount))
        self.__deltaset_prev = np.zeros(
            (self.__tile_ycount, self.__tile_xcount))
        self.__detected = np.zeros(
            (self.__tile_ycount, self.__tile_xcount))
        self.__frame_counter = 0

    @ staticmethod
    def __assert_in_list(value, list, name):
        assert value in list, f"{name}={value} not in values {list}"
        return value

    def set_detection_threshold(self, value):
        if value == 0:
            self.set_tile_treshold(0.0625)
        elif value == 1:
            self.set_tile_treshold(0.125)
        elif value == 2:
            self.set_tile_treshold(0.25)
        elif value == 3:
            self.set_tile_treshold(0.5)
        else:
            print('invalid value from slider')

    def set_tile_treshold(self, value):
        self.__tile_treshold = self.__assert_in_list(
            value,
            [0.5, 0.25, 0.125, 0.0625],
            "TILE_TRESHOLD"
        )

    @property
    def power_history(self):
        return self.__power_history

    @property
    def get_detection_flag(self):
        return self.__detect_flag

    def set_tile_min_treshold(self, value):
        self.__tile_min_treshold = value

    def set_min_flagged_tiles(self, value):
        self.__min_flagged_tiles = value

    def set_max_flagged_tiles(self, value):
        self.__max_flagged_tiles = value


    def set_tile_disable_mask(self, value):
        self.__tile_disable_mask = value

    def set_tile_disable_mask2(self, value):
        self.__tile_disable_mask2 = value

    def set_tile_width(self, value):
        self.__tile_width = value

    def set_tile_height(self, value):
        self.__tile_height = value

    def set_tile_xstart(self, value):
        self.__tile_xstart = value

    def set_tile_ystart(self, value):
        self.__tile_ystart = value

    def set_cpy_tiles_interval(self, value):
        self.__cpy_tiles_interval = value

    def set_tile_dicard_nr_bits(self, value):
        self.__tile_dicard_nr_bits = value

    def set_tile_xsubs(self, value):
        self.__tile_xsubs = value

    def set_tile_ysubs(self, value):
        self.__tile_ysubs = value

    def set_tile_xbin(self, value):
        self.__tile_xbin = value

    def set_tile_ybin(self, value):
        self.__tile_ybin = value

    @staticmethod
    def draw_label(img=None, text='text', pos=[0,0], color=(255, 255, 255)):
        font_face = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.8

        thickness = 2  # (filled)
        margin = 2

        txt_size = cv2.getTextSize(text, font_face, scale, thickness)

        end_x = pos[0] + txt_size[0][0] + margin
        end_y = pos[1] - txt_size[0][1] - margin

        # cv2.rectangle(img, pos, (end_x, end_y), bg_color, thickness)
        cv2.putText(img, text, pos, font_face, scale,
                    color)

    @staticmethod
    def draw_label2(img, text, pos, color=(0, 255, 0)):
        font_face = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.8

        thickness = 2  # (filled)
        margin = 2

        txt_size = cv2.getTextSize(text, font_face, scale, thickness)

        end_x = pos[0] + txt_size[0][0] + margin
        end_y = pos[1] - txt_size[0][1] - margin

        # cv2.rectangle(img, pos, (end_x, end_y), bg_color, thickness)
        cv2.putText(img, text, pos, font_face, scale,
                    color, thickness, cv2.LINE_AA)

    @staticmethod
    def draw_label3(img, text, pos, color=(0, 0, 255)):
        font_face = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.8

        thickness = 2  # (filled)
        margin = 2

        txt_size = cv2.getTextSize(text, font_face, scale, thickness)

        end_x = pos[0] + txt_size[0][0] + margin
        end_y = pos[1] - txt_size[0][1] - margin

        # cv2.rectangle(img, pos, (end_x, end_y), bg_color, thickness)
        cv2.putText(img, text, pos, font_face, scale,
                    color, thickness, cv2.LINE_AA)

    def mouse_action(self, event, x, y, flags, param):
        width = self.__tile_width*self.__tile_xcount
        height = self.__tile_height*self.__tile_ycount
        xtile = int(np.floor(x/self.__tile_width))
        ytile = int(np.floor(y/self.__tile_height))
        # # Apply tiling masks
        # index = (self.__tile_ycount-y-1)*self.__tile_xcount+x
        # maskbit = (self.__tile_disable_mask >> index) & 0b1

        if event == cv2.EVENT_LBUTTONDOWN:
            self.__ix, self.__iy = x, y

            self.__tile_disable_mask2[ytile, xtile] = not(
                self.__tile_disable_mask2[ytile, xtile])

    def update_power(self, new):
        if time.time()-self.__last_power_update > 1:
            self.__power_history[:-1] = self.__power_history[1::]
            self.__power_history[-1] = new
            self.__last_power_update = time.time()

    def process_frame(self, frame):

        # Upon acquisition of a frame, first flatten to a monochrome sensor
        try:
            work_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        except:
            work_frame = np.array(frame)

        # Chop off bits
        work_frame = (
            work_frame >> self.__tile_dicard_nr_bits) << self.__tile_dicard_nr_bits

        # Crop out the tile region
        crop_frame = work_frame[self.__tile_ystart:self.__tile_ycount *
                                self.__tile_height, self.__tile_xstart:self.__tile_xcount*self.__tile_width]

        # Apply binning
        binned_frame = cv2.resize(crop_frame, dsize=(
            crop_frame.shape[0] // self.__tile_ybin, crop_frame.shape[1] // self.__tile_xbin), interpolation=cv2.INTER_NEAREST)

        # Apply subsampling
        work_frame = work_frame[::self.__tile_ysubs, ::self.__tile_ysubs]
        annotated_frame = work_frame
        # Prepare an annotatable frame in rgb space
        annotated_frame = cv2.resize(work_frame, dsize=(
            600, 800),  interpolation=cv2.INTER_NEAREST)
        annotated_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_GRAY2RGB)

        # Extract the tileset
        xsize = (crop_frame.shape[1]) // self.__tile_xcount
        ysize = (crop_frame.shape[0]) // self.__tile_ycount
        tileset = np.zeros((self.__tile_ycount, self.__tile_xcount))

        for y in range(self.__tile_ycount):
            for x in range(self.__tile_xcount):
                tileset[y, x] = crop_frame[y*ysize:(y+1)*ysize-1,
                                           x*xsize:(x+1)*xsize-1].mean()

        # Calculate the delta, if applicable
        if (self.__frame_counter == self.__cpy_tiles_interval):
            self.__frame_counter = 0
            deltaset = tileset - self.__tileset_prev

            self.__tileset_prev = tileset
            self.__deltaset_prev = deltaset

            self.__detected = np.zeros_like(tileset)

            for y in range(self.__tile_ycount):
                for x in range(self.__tile_xcount):
                    # Apply tresholding
                    if (self.__deltaset_prev[y, x] > (self.__tileset_prev[y, x] * self.__tile_treshold)):
                        self.__detected[y, x] = 1
                    else:
                        self.__detected[y, x] = 0

                    # Apply tiling masks
                    index = (self.__tile_ycount-y-1)*self.__tile_xcount+x
                    maskbit = (self.__tile_disable_mask >> index) & 0b1

                    if (self.__tile_disable_mask2[y, x]):
                        self.__detected[y, x] = 0

            # Apply min and max flagged tile rules
            summum = np.sum(np.sum(self.__detected))
            if (summum >= self.__min_flagged_tiles and summum <= self.__max_flagged_tiles):
                self.__detect_flag = 1
                self.__last_detection = time.time()
            elif (time.time() - self.__last_detection) > 5:
                self.__detect_flag = 0

        else:
            self.__frame_counter += 1

        # # motion detection
        # if np.all(self.__detected == 0) and (time.time()-self.__last_detection) > 5 and self.__detect_flag == 1:
        #     self.__detect_flag = 0

        # elif not(np.all(self.__detected == 0)) and self.__detect_flag == 0:
        #     self.__detect_flag = 1
        #     self.__last_detection = time.time()

        # elif not(np.all(self.__detected == 0)):
        #     self.__detect_flag = 1
        #     self.__last_detection = time.time()

        for y in range(self.__tile_ycount):
            for x in range(self.__tile_xcount):
                if self.__tile_disable_mask2[y, x]:
                    color = (0, 0, 0)
                    border = -1
                elif (self.__detected[y, x]):
                    color = (0, 0, 255)  # red
                    border = 5
                else:
                    color = (0, 255, 255)  # yellow
                    border = 1

                cv2.rectangle(
                    annotated_frame,
                    (self.__tile_xstart+x*self.__tile_width,
                     self.__tile_ystart+y*self.__tile_height),
                    (self.__tile_xstart+x*self.__tile_width+self.__tile_width-1,
                     self.__tile_ystart+y*self.__tile_height+self.__tile_height-1),
                    color,
                    border
                )

                cv2.rectangle(
                    annotated_frame,
                    (self.__tile_xstart+x*self.__tile_width,
                     self.__tile_ystart+y*self.__tile_height),
                    (self.__tile_xstart+x*self.__tile_width+self.__tile_width-1,
                     self.__tile_ystart+y*self.__tile_height+self.__tile_height-1),
                    color,
                    border
                )

        #         # Annotate the frame
        self.draw_label(annotated_frame,
                        f'Internal subsampled image', (20, 20))

        if self.__detect_flag:
            power = self.__active_power
            self.draw_label2(
                annotated_frame, 'Motion detected, image stream enabled!', (20, 100))

        else:
            power = self.__detection_power
            self.draw_label3(
                annotated_frame, 'No motion, image stream disabled', (20, 100))

        self.update_power(power)

        self.draw_label2(
            annotated_frame, f'Estimated power consumption: {power} mW', (20, 50))
        self.draw_label(annotated_frame,f'Click to mask tiles.',(20,610))
        self.draw_label(annotated_frame,f'Esc to exit.',(20,640))

        return annotated_frame


# OpenCV example
ed = EventDetector()

imager = driver_access.ImagerTools(print, 0, None)
imager.setSystype("Nano")
try:
    with open(fname, "r") as file:
        eobj = compile(file.read(), fname, "exec")
        exec(eobj, globals())
except:
    print("ERROR: unable to execute init script")
sensorInfo = getSensorInfo(imager)
resetSensor(imager)
initSensor(imager)
testpattern = False
imager.setformat(sensorInfo["bpp"], sensorInfo["width"], sensorInfo["height"], sensorInfo["widthDMA"], sensorInfo["heightDMA"], True)
port=0
tnr=0
ee=0
sensor_mode=0
dgain="1 1"

sensor_w=600
sensor_h=800
sensor_wdma=600
sensor_hdma=800
bpp=10
sensor_fps=30
v4l2=0
iface =  "nvarguscamerasrc sensor-id={} wbmode=0  tnr-mode={} tnr-strength=0.5 ee-mode={} ee-strength=0.5 sensor-mode={} ".format(port, tnr, ee, sensor_mode)
iface += "saturation=0.0 "
iface += "ispdigitalgainrange=\"{}\" !".format(dgain)
iface += " video/x-raw(memory:NVMM),width=(int){},height=(int){},format=(string)NV12,framerate=(fraction){}/1 !".format(sensor_w, sensor_h, sensor_fps)
#            if (record == False):
iface += " nvvidconv ! video/x-raw ! appsink"
print(iface)
vc = cv2.VideoCapture(iface)


def set_exposure(exposure_ms=10):
    # Exposure registers
    imager.setSensorI2C(0x36)
    imager.type(1)

    # Get the entry value

    value = int(exposure_ms)*1000

    # Split value
    b3 = value >> 24 & 255
    b2 = value >> 16 & 255
    b1 = value >> 8 & 255
    b0 = value & 255

    # Write to registers
    imager.enablePrint()

    imager.write(0xe004,  0)
    imager.write(0xe000,  1)
    imager.write(0x000E, b3)
    imager.write(0x000F, b2)
    imager.write(0x0010, b1)
    imager.write(0x0011, b0)



# vc = cv2.VideoCapture(0)

# vc.set(3, 600)
# vc.set(4, 800)


ed.set_cpy_tiles_interval(0)
ed.set_tile_treshold(0.125)


def on_change(num):
    print('change')


ed.set_tile_disable_mask(0b0000000000011111111)  # discard lowest line
ed.set_tile_disable_mask2(np.array(
    [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]))
# ed.set_tile_xstart(25)
# ed.set_tile_ystart(75)
# ed.set_tile_width(100)
# ed.set_tile_height(100)
cv2.namedWindow("Sensor output")
cv2.namedWindow("Internal algorithm")
cv2.setMouseCallback('Internal algorithm', ed.mouse_action)

cv2.createTrackbar('Threshold', "Internal algorithm",
                   1, 3, ed.set_detection_threshold)
cv2.createTrackbar('minTiles', "Internal algorithm",
                   1, 20, ed.set_min_flagged_tiles)
cv2.createTrackbar('maxTiles', "Internal algorithm",
                   19, 20, ed.set_max_flagged_tiles)
cv2.createTrackbar('ExposureTime_ms', "Internal algorithm",
                   10, 100, set_exposure)

plt.ion()
fig = plt.figure('Power')
ax = fig.add_subplot(111)
x = np.linspace(0, 99, 100)
line1, = ax.plot(x, ed.power_history, 'b-')
ax.set_ylim(0, 50)
ax.set_title('power consumption (mW)')
framecounter = 0

while (vc.isOpened()):
    rval, frame = vc.read()
    framecounter += 1
    # frame = cv2.resize(frame, dsize=(600, 800))
    frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

    if framecounter % 20 ==0 or ed.get_detection_flag==1:
        t = time.time()

        result = ed.process_frame(frame)
        t2 = time.time()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cv2.imshow("Internal algorithm", result)

        if ed.get_detection_flag == 1:
            ed.draw_label(img=frame, text=f'Sensor output', pos=(20, 40))
            ed.draw_label(img=frame, text=f'Running at 30 fps', pos= (20, 110))
            cv2.imshow("Sensor output", frame)

        else:
            frame = frame*0
            ed.draw_label(img=frame, text=f'No motion, output disabled.', pos=(20, 40))
            ed.draw_label(img=frame, text=f'Running at 1 fps', pos=(20, 110))
            cv2.imshow("Sensor output", frame)

    line1.set_ydata(ed.power_history)



    key = cv2.waitKey(20)
    fig.canvas.draw()
    if key == 27:  # hit escape for exit
        break
    fig.canvas.flush_events()
