"""
barcode scanning prototype demo
"""

# USAGE
# python barcode_scanner_video.py

# import the necessary packages
from imutils.video import VideoStream
from pyzbar import pyzbar
import argparse
import datetime
import imutils
import time
import cv2
import fullres
import driver_access
import numpy as np
from autobrightness import AutoBrightness130

exposures=[]

exposure = 21472
mean = 128
again=1

means=[140]
exposures=[21472]
gains=[0]
flag=False
framecount=0





def auto_exposure(mean,exposure,again):
    print(f"mean {mean} exp {exposure} gain {again}")

    if mean<140:
        exposure=exposure*1.2
        print(f'increasing exposure. new value is {exposure}')
        again=set_exposure(imager0,exposure,again)
    if mean>180:
        exposure=exposure*0.9
        print(f'decreasing exposure. new value is {exposure}')
        again=set_exposure(imager0,exposure,again)
    return exposure,again

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



def printfun(args):
    a=2
imager0 = driver_access.ImagerTools(printfun, 0, None)
imager0.setSystype("Nano")
sensorInfo = fullres.getSensorInfo(imager0)
fullres.resetSensor(imager0)
fullres.initSensor(imager0)
imager0.setformat(sensorInfo["bpp"], sensorInfo["width"], sensorInfo["height"], sensorInfo["widthDMA"], sensorInfo["heightDMA"], True)
port=0
tnr=0
ee=0
sensor_mode=0
dgain="1 1"

sensor_w=1080
sensor_h=1280
sensor_wdma=1088
sensor_hdma=1280
bpp=10
sensor_fps=30
v4l2=0
iface=[0,0]
port=0
iface[port] =  "nvarguscamerasrc sensor-id={} wbmode=0  tnr-mode={} tnr-strength=0.5 ee-mode={} ee-strength=0.5 sensor-mode={} ".format(port, tnr, ee, sensor_mode)
iface[port] += "saturation=0.0 "
iface[port] += "ispdigitalgainrange=\"{}\" !".format(dgain)
iface[port] += " video/x-raw(memory:NVMM),width=(int){},height=(int){},format=(string)NV12,framerate=(fraction){}/1 !".format(sensor_w, sensor_h, sensor_fps)
#            if (record == False):
iface[port] += " nvvidconv ! video/x-raw ! appsink"
cap0 = cv2.VideoCapture(iface[0])
imager0.setformat(bpp, sensor_w, sensor_h, sensor_wdma, sensor_hdma, v4l2)
imager0.startstream()
imager=imager0


# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-o", "--output", type=str, default="barcodes.csv",
    help="path to output CSV file containing barcodes")
args = vars(ap.parse_args())

# initialize the video stream and allow the camera sensor to warm up
print("[INFO] starting video stream...")
# vs = VideoStream(src=0).start()

# open the output CSV file for writing and initialize the set of
# barcodes found thus far
csv = open(args["output"], "w")
found = set()
frame_time=get_max_exposure(imager)
abc=AutoBrightness()
# loop over the frames from the video stream
while(cap0.isOpened()):  
    ret, frame = cap0.read()
    cvimage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
    frame=cv2.resize(cvimage,(1080,1280))
    # mean=frame.mean()
    #exposure,again=auto_exposure(mean,exposure,again)


    frame = imutils.resize(frame, width=400)


    text=f'press X to start detecting'
    cv2.putText(frame, text, (20,20),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    text=f'gain: {gains[-1]}'
    text=f'mean: {means[-1]}'
    cv2.putText(frame, text, (20,80),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
    text=f'gain: {gains[-1]}'
    cv2.putText(frame, text, (20,40),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
    text=f'exp: {exposures[-1]}'
    cv2.putText(frame, text, (20,60),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
    # grab the frame from the threaded video stream and resize it to
    # have a maximum width of 400 pixels

    if flag==True:
        # find the barcodes in the frame and decode each of the barcodes
        AutoBrightness.do_abc(imager,frame,frame_time,means,exposures,gains)

        barcodes = pyzbar.decode(frame)
        framecount = framecount + 1
    else:
        barcodes=[]
        framecount=0
    

    # loop over the detected barcodes
    for barcode in barcodes:
        # extract the bounding box location of the barcode and draw
        # the bounding box surrounding the barcode on the image
        (x, y, w, h) = barcode.rect
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

        # the barcode data is a bytes object so if we want to draw it
        # on our output image we need to convert it to a string first
        barcodeData = barcode.data.decode("utf-8")
        barcodeType = barcode.type

        # draw the barcode data and barcode type on the image
        text = "{} ({})".format(barcodeData, barcodeType)
        cv2.putText(frame, text, (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        # if the barcode text is currently not in our CSV file, write
        # the timestamp + barcode to disk and update the set
        if barcodeData not in found:
            csv.write("{},{}\n".format(datetime.datetime.now(),
                barcodeData))
            csv.flush()
            found.add(barcodeData)
        text=f'QR dectected after {framecount} frames'
        cv2.putText(frame, text, (20,100),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)

    # show the output frame
    cv2.imshow("Barcode Scanner", frame)
    if barcodes:
        key = cv2.waitKey(3000) & 0xFF
        flag=False
    else:
        key = cv2.waitKey(1) & 0xFF
 
    # if the `q` key was pressed, break from the loop
    if key == ord("q"):
        break
        # if the `q` key was pressed, break from the loop
    if key == ord("x"):
        flag=not(flag)

# close the output CSV file do a bit of cleanup
print("[INFO] cleaning up...")
csv.close()
cv2.destroyAllWindows()
imager0.stopstream()
cap0.release()
