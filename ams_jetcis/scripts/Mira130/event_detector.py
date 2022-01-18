# ==============================================================================
# Kevin Vancauwenbergh
# November 2019
# AMS
# ==============================================================================
# conda install py-opencv
# conda install numpy
# ==============================================================================
import cv2
import numpy as np
import time
import operator
import driver_access_new as driver_access
import time
import cv2
import os
import matplotlib.pyplot as plt
import gi
import fullres

# ==============================================================================
# Camera Parameters
# ==============================================================================
# Resolution of the simulating camera
camera_width = 540
camera_height = 640

# Frametime of the simulating camera in ms
camera_frame_time = 1000.0 / 30

# ==============================================================================
# Sensor Parameters
# ==============================================================================
# Resolution of the actual sensor
sensor_width = 540
sensor_height = 640

# Frametime as will be used in the actual sensor
sensor_frame_time = 1000.0 / 30

# ==============================================================================
# Algorithm Parameters
# ==============================================================================
# Number of tiles in each direction
tile_xcount = 5
tile_ycount = 4

# Subsampling step in each direction
tile_xsubs = 8
tile_ysubs = 8

# Binning factor in each direction
tile_xbin = 1
tile_ybin = 1

# Rate at which the current tileset is saved as the previous one
# e.g. if frame_step = 2, every other framed is copied over the previous
frame_step = 3
frame_counter = 0

# Containers for the tilesets
tileset = np.zeros((tile_ycount, tile_xcount))
tileset_prev = np.zeros_like(tileset)

#
virtual_supertiling_enabled = False

# Retain only the top bits
meaningful_msbs = 6

# ==============================================================================
# Helper functions
# ==============================================================================
mu_time = lambda: int(round(time.time() * 1000000))  # Current time in microsecs
mi_time = lambda: int(round(time.time() * 1000))  # Current time in millisecs


def draw_label(img, text, pos, color=(0, 255, 255)):
    font_face = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.5

    thickness = -1  # (filled)
    margin = 2

    txt_size = cv2.getTextSize(text, font_face, scale, thickness)

    end_x = pos[0] + txt_size[0][0] + margin
    end_y = pos[1] - txt_size[0][1] - margin

    # cv2.rectangle(img, pos, (end_x, end_y), bg_color, thickness)
    cv2.putText(img, text, pos, font_face, scale, color, 1, cv2.LINE_AA)


def crop(img, bounding):
    start = tuple(map(lambda a, da: a // 2 - da // 2, img.shape, bounding))
    end = tuple(map(operator.add, start, bounding))
    slices = tuple(map(slice, start, end))
    return img[slices]


def chop_lsbs(frame, meaningful_msbs):
    # @@ for now assuming 8 bit operation
    bw = 8
    bwdelta = bw - meaningful_msbs
    return (frame >> bwdelta) << bwdelta


def apply_binning(frame, xbin, ybin):
    return cv2.resize(frame, dsize=(frame.shape[0] // ybin, frame.shape[1] // xbin), interpolation=cv2.INTER_NEAREST)
    # @@ doesnt work
    new_shape = (frame.shape[0] // ybin, frame.shape[1] // xbin)

    shape = (new_shape[0], frame.shape[0] // new_shape[0],
             new_shape[1], frame.shape[1] // new_shape[1])
    return frame.reshape(shape).mean(-1).mean(1)


def apply_subsampling(frame, xsubs, ysubs):
    return frame[::ysubs, ::xsubs]


# ==============================================================================
# Algorithm functions
# ==============================================================================
def extract_profiles():
    # TODO
    row_profile = []
    col_profile = []
    return row_profile, col_profile


def extract_tiles(frame, tile_xcount, tile_ycount):
    xsize = (frame.shape[1]) // tile_xcount
    ysize = (frame.shape[0]) // tile_ycount
    tilesize = xsize * ysize

    tileset = np.zeros((tile_ycount, tile_xcount))

    for y in range(tile_ycount):
        for x in range(tile_xcount):
            tileset[y, x] = frame[y * ysize:(y + 1) * ysize - 1, \
                            x * xsize:(x + 1) * xsize - 1].mean()

    return tileset


def judge_tiles(tileset, treshold_percemtage):
    judgement = np.zeros_like(tileset)

    for y in range(tileset.shape[0]):
        for x in range(tileset.shape[1]):
            val = tileset[y][x]

    return judgement


# ==============================================================================
# Viewing functionality
# ==============================================================================
# def draw_tiles(tile_count_x, tile_count_y, highlight_tiles)


# ==============================================================================
# Main script
# ==============================================================================
# Create the window and connect to the webcam
# cv2.namedWindow("camera")
# cv2.namedWindow("sensor")
# cv2.namedWindow("settings")

imager = driver_access.ImagerTools(print, 0, None)
imager.setSystype("Nano")
sensorInfo = fullres.getSensorInfo(imager)
fullres.resetSensor(imager)
fullres.initSensor(imager)
testpattern = False
imager.setformat(sensorInfo["bpp"], sensorInfo["width"], sensorInfo["height"], sensorInfo["widthDMA"], sensorInfo["heightDMA"], True)
port=0
tnr=0
ee=0
sensor_mode=0
dgain="1 1"

sensor_w=1080
sensor_h=1280
sensor_wdma=1152
sensor_hdma=1280
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
imager.setformat(bpp, sensor_w, sensor_h, sensor_wdma, sensor_hdma, v4l2)
# imager.startstream()
#os.system(iface)
time.sleep(1)

# while(vc.isOpened()):
#     ret, frame = cap.read()

#     cvimage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
#     new=cv2.resize(cvimage,(1080,1280))
#     cv2.imshow('frame1',new)
#     if cv2.waitKey(10) & 0xFF == ord('q'):
#         break


cv2.namedWindow("concat")

# Set the required resoluion
# vc.set(cv2.CAP_PROP_FRAME_WIDTH, int(camera_width))
# vc.set(cv2.CAP_PROP_FRAME_HEIGHT, int(camera_height))


# Add some trackbars
def nothing():
    pass


cv2.createTrackbar("tile_xcount", "settings", 1, sensor_width, nothing)
cv2.createTrackbar("tile_ycount", "settings", 1, sensor_height, nothing)
cv2.createTrackbar("tile_xsubs", "settings", 1, sensor_width, nothing)
cv2.createTrackbar("tile_ysubs", "settings", 1, sensor_height, nothing)
cv2.createTrackbar("tile_xbin", "settings", 1, sensor_width, nothing)
cv2.createTrackbar("tile_ybin", "settings", 1, sensor_height, nothing)

# Enter the eternal frame acquisition loop
last_frame_t = mu_time()
frame_count = 0

dump_cntr = 0

while vc.isOpened():
    # Extract settings
    hul = cv2.getTrackbarPos("Max", "settings")
    huh = cv2.getTrackbarPos("Min", "settings")

    # Acquire a frame from the camera
    rval, frame = vc.read()
    cvimage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)

    # Upon acquisition of a frame, first flatten to a monochrome sensor
    frame = cv2.cvtColor(cvimage, cv2.COLOR_RGBA2GRAY)

    # Crop the frame to the actual sensor resolution
    frame = crop(frame, (sensor_height, sensor_width))

    #
    frame = chop_lsbs(frame, meaningful_msbs)

    #
    # dataset = apply_binning(frame, tile_xbin, tile_ybin)
    dataset = apply_subsampling(frame, tile_xsubs, tile_ysubs)

    #
    dataset_view = cv2.resize(dataset, dsize=(sensor_width, sensor_height), interpolation=cv2.INTER_NEAREST)

    #
    tileset = extract_tiles(dataset, tile_xcount, tile_ycount)

    # Back to RGB so we can do colored anotations
    frame_view = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
    frame_view = cv2.resize(
        frame_view,
        dsize=(int(1.0 * sensor_width), int(1.0 * sensor_height)),
        interpolation=cv2.INTER_NEAREST
    )

    dataset_view = cv2.cvtColor(dataset_view, cv2.COLOR_GRAY2RGB)

    # Do it
    motion_detected = False

    for y in range(tile_ycount):
        for x in range(tile_xcount):
            val = tileset[y, x]
            prevval = tileset_prev[y, x]

            xsize = (frame_view.shape[1]) // tile_xcount
            ysize = (frame_view.shape[0]) // tile_ycount

            # Print the current mean value
            # draw_label(frame_view, str(int(tileset[y, x])), (int(xsize*(x+0.25)), int(ysize*(y+0.25))))
            # draw_label(dataset_view, str(int(tileset[y, x])), (int(xsize*(x+0.25)), int(ysize*(y+0.25))))

            #
            tile_width = xsize
            tile_height = ysize

            treshold = 5
            delta = abs(tileset[y, x] - tileset_prev[y, x])

            if (delta > (tileset[y, x] / treshold)):
                color = (0, 0, 255)
                border = 5
                motion_detected = True
            else:
                color = (0, 255, 255)
                border = 1

            cv2.rectangle(
                frame_view,
                (x * tile_width, y * tile_height),
                (x * tile_width + tile_width - 1, y * tile_height + tile_height - 1),
                color,
                border
            )

            cv2.rectangle(
                dataset_view,
                (x * tile_width, y * tile_height),
                (x * tile_width + tile_width - 1, y * tile_height + tile_height - 1),
                color,
                border
            )

    print(frame_count, frame_step, motion_detected)
    if (frame_count == frame_step):
        print(motion_detected)


        def rotate_left(frame):
            return frame.transpose()


        # cv2.imwrite("C:\\Users\\kvnc\\svnwa\\cis_common_digital\\trunk\software\\MotionDetector\\dump\\{}.pgm".format(
            # dump_cntr), \
                    # rotate_left(dataset), (cv2.IMWRITE_PXM_BINARY, 0))

        if (motion_detected):
            # cv2.imwrite(
            #     # "C:\\Users\\kvnc\\svnwa\\cis_common_digital\\trunk\software\\MotionDetector\\dump\\r{}d.png".format(
            #         dump_cntr), \
            #     dataset_view)
            print(">> sir yes sir")
        # else:
        #     cv2.imwrite(
        #         # "C:\\Users\\kvnc\\svnwa\\cis_common_digital\\trunk\software\\MotionDetector\\dump\\r{}.png".format(
        #         #     dump_cntr), \
        #         # dataset_view)

        dump_cntr += 1
        frame_count = 0
        tileset_prev = np.array(tileset, copy=True)
    else:
        frame_count += 1

    # Show it
    # cv2.imshow("camera", frame_view)
    # cv2.imshow("sensor", dataset_view)
    # cv2.imshow("settings", np.zeros((400, 300)))

    concat = np.concatenate((dataset_view, frame_view), axis=1)
    cv2.imshow("concat", concat)

    # Framerate is 24 fps
    # key = cv2.waitKey(int(1000.0 / 2.0))
    if cv2.waitKey(10) & 0xFF == ord('q'):
        
        cv2.destroyAllWindows()
        break
