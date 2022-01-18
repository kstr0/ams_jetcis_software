#import faulthandler; faulthandler.enable()
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
fps = 30
while(a < (30 *fps)):
	time.sleep(1.0 / fps)
	img = img + int(a)
#	GEVPython.setimage(img)
	a = a + 1
	if((a % fps) == 0):
		print(a)
