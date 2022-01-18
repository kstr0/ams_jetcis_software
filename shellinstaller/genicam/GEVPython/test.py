#import faulthandler; faulthandler.enable()
import time
import numpy as np
import cv2
import os
print(os.environ["GENICAM_ROOT_V3_1"])

import GEVPython

print("Test started")
#print("VERSION={}".format(GEVPython.__version__))
GEVPython.setparams(320, 240, 8)
print(GEVPython.getparams())
GEVPython.setip("00:04:4b:e6:f7:5b")
print("UPLOAD IMAGE")
img = cv2.imread("testimg.png", 0)
print(img)
print(img.shape)
GEVPython.setimage(img)
print("RUN")
GEVPython.run(1)


a = 0
while(a < 60):
	time.sleep(1)
	a = a + 1
	print(a)
