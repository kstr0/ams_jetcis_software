"""
Example below shows a videostream from left and right camera simultaneaously, using the HW accelerated pipeline. no root required to run this.
Auto exposure function included to show how to read/write registers..
author: Philippe.Baetens@ams.com
"""

import driver_access_new as driver_access
import time
import cv2
import os
import matplotlib.pyplot as plt
import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt
import fullres
import glob

def setup_iface():

    imager0 = driver_access.ImagerTools(print, 0, None)
    imager1 = driver_access.ImagerTools(print, 1, None)

    imager1.setSystype("Nano")
    imager0.setSystype("Nano")

    # Step3:    First important thing is to initialize the sensor. This could be done either by directly by using the
    #           driver_access i2c commands or by using an already existing init script
    #           This example loads an init script:
    #               - The fullres.py is loaded and - by using the compile command - integrated in the actual code
    #               - After this, all functions from fullres.py could be executed
    #               - getSensorInfo loads a structure into sensorInfo describing all important resolution informations
    #               - resetSensor resets the sensor
    #               - initSensor configures the sensor


    sensorInfo = fullres.getSensorInfo(imager1)
    fullres.resetSensor(imager1)
    fullres.initSensor(imager1)
    fullres.resetSensor(imager0)
    fullres.initSensor(imager0)

    # Step 4:   The last step of this example creates one image as tiff file, switches to testpattern, waits a second
    #           and creates a second image. This repeats 5 times before the program ends
    testpattern = False
    imager0.setformat(sensorInfo["bpp"], sensorInfo["width"], sensorInfo["height"], sensorInfo["widthDMA"], sensorInfo["heightDMA"], True)
    imager1.setformat(sensorInfo["bpp"], sensorInfo["width"], sensorInfo["height"], sensorInfo["widthDMA"], sensorInfo["heightDMA"], True)
        # imager.saveRaw("~/test{}.raw".format(lp))
        # iface = "/usr/bin/gst-launch-1.0 "
        # iface += "nvarguscamerasrc num-buffers=1 sensor-id=0 wbmode=0 tnr-mode=0 tnr-strength=0.5 ee-mode=0 ee-strength=0.5 sensor-mode=0"
        # iface += " saturation=0.0 !"
        # iface += " \"video/x-raw(memory:NVMM),width=(int){},height=(int){},format=(string)NV12,framerate=(fraction){}/1\" !".format(
        #     sensorInfo["width"], sensorInfo["height"], sensorInfo["fps"])
        # iface += " nvvidconv ! video/x-raw ! filesink location=test{}.raw".format(lp)
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
    iface=[0,0]
    for port in [0,1]:
        iface[port] =  "nvarguscamerasrc sensor-id={} wbmode=0  tnr-mode={} tnr-strength=0.5 ee-mode={} ee-strength=0.5 sensor-mode={} ".format(port, tnr, ee, sensor_mode)
        iface[port] += "saturation=0.0 "
        iface[port] += "ispdigitalgainrange=\"{}\" !".format(dgain)
        iface[port] += " video/x-raw(memory:NVMM),width=(int){},height=(int){},format=(string)NV12,framerate=(fraction){}/1 !".format(sensor_w, sensor_h, sensor_fps)
        #            if (record == False):
        iface[port] += " nvvidconv ! video/x-raw ! appsink"
        print(iface[port])

    return iface

def livestream(iface):
    cap0 = cv2.VideoCapture(iface[0])
    cap1 = cv2.VideoCapture(iface[1])            

    time.sleep(0.1)

    while(cap0.isOpened() and cap1.isOpened()):
        ret, right = cap0.read()
        ret, left = cap1.read()

        right = cv2.cvtColor(right, cv2.COLOR_BGR2RGBA)
        left = cv2.cvtColor(left, cv2.COLOR_BGR2RGBA) 

        cv2.imshow('right',right)
        cv2.imshow('left',left)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
                
    cap0.release()
    cap1.release()
    return 0



def depthstream(iface,stereofile='stereo.yml'):
    K1, D1, K2, D2, R, T, E, F, R1, R2, P1, P2, Q = load_stereo_coefficients(stereofile)  # Get cams params

    cap_right = cv2.VideoCapture(iface[0])
    cap_left = cv2.VideoCapture(iface[1])            


    if not cap_left.isOpened() and not cap_right.isOpened():  # If we can't get images from both sources, error
        print("Can't opened the streams!")
        sys.exit(-9)

    # # Change the resolution in need
    # cap_right.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # float
    # cap_right.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # float

    # cap_left.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # float
    # cap_left.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # float

    while True:  # Loop until 'q' pressed or stream ends
        # Grab&retreive for sync images
        if not (cap_left.grab() and cap_right.grab()):
            print("No more frames")
            break

        _, leftFrame = cap_left.retrieve()
        _, rightFrame = cap_right.retrieve()
        height, width = leftFrame.shape  # We will use the shape for remap

        # Undistortion and Rectification part!
        leftMapX, leftMapY = cv2.initUndistortRectifyMap(K1, D1, R1, P1, (width, height), cv2.CV_32FC1)
        left_rectified = cv2.remap(leftFrame, leftMapX, leftMapY, cv2.INTER_LINEAR, cv2.BORDER_CONSTANT)
        rightMapX, rightMapY = cv2.initUndistortRectifyMap(K2, D2, R2, P2, (width, height), cv2.CV_32FC1)
        right_rectified = cv2.remap(rightFrame, rightMapX, rightMapY, cv2.INTER_LINEAR, cv2.BORDER_CONSTANT)

        # We need grayscale for disparity map.
        gray_left = left_rectified #cv2.cvtColor(left_rectified, cv2.COLOR_BGR2GRAY)
        gray_right = right_rectified #cv2.cvtColor(right_rectified, cv2.COLOR_BGR2GRAY)
        x,y=left_rectified.shape
        left_rectified=cv2.resize(left_rectified,(int(y/2),int(x/2)))
        x,y=right_rectified.shape
        right_rectified=cv2.resize(right_rectified,(int(y/2),int(x/2)))

        old=time.time()
        disparity = depth_map(left_rectified, right_rectified)  # Get the disparity map
        
        #stereo = cv.StereoBM_create(numDisparities=16, blockSize=15)
        #disparity = stereo.compute(left_rectified,right_rectified)

        #disparity = stereoSGBM(left_rectified,right_rectified)
        print(f'fun took {time.time()-old}')
        # Show the images
        #cv2.imshow('left(R)', leftFrame)
        #cv2.imshow('right(R)', rightFrame)
        cv2.imshow('left(Rect)', left_rectified)
        cv2.imshow('right(Rect)', right_rectified)
        norm_image = cv2.normalize(disparity, None, alpha = 0, beta = 1, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_32F)

        cv2.imshow('dispar)', norm_image)


        if cv2.waitKey(10) & 0xFF == ord('q'):  # Get key to stop stream. Press q for exit
            break
  

    # Release the sources.
    cap_left.release()
    cap_right.release()
    cv2.destroyAllWindows()   


def depthstream_test(iface=None,stereofile='stereo.yml'):
    K1, D1, K2, D2, R, T, E, F, R1, R2, P1, P2, Q = load_stereo_coefficients(stereofile)  # Get cams params

    rightFrame = cv2.imread('calib/Right5.jpg')
    leftFrame  = cv2.imread('calib/Left5.jpg')           
   
    rightFrame = cv2.cvtColor(rightFrame,cv2.COLOR_BGR2GRAY)
    leftFrame = cv2.cvtColor(leftFrame,cv2.COLOR_BGR2GRAY)

    height, width = leftFrame.shape  # We will use the shape for remap

    # Undistortion and Rectification part!
    leftMapX, leftMapY = cv2.initUndistortRectifyMap(K1, D1, R1, P1, (width, height), cv2.CV_8UC1)
    left_rectified = cv2.remap(leftFrame, leftMapX, leftMapY, cv2.INTER_LINEAR, cv2.BORDER_CONSTANT)
    rightMapX, rightMapY = cv2.initUndistortRectifyMap(K2, D2, R2, P2, (width, height), cv2.CV_8UC1)
    right_rectified = cv2.remap(rightFrame, rightMapX, rightMapY, cv2.INTER_LINEAR, cv2.BORDER_CONSTANT)

    # We need grayscale for disparity map.
    gray_left = left_rectified #cv2.cvtColor(left_rectified, cv2.COLOR_BGR2GRAY)
    gray_right = right_rectified #cv2.cvtColor(right_rectified, cv2.COLOR_BGR2GRAY)

    disparity = depth_map(gray_left, gray_right)  # Get the disparity map
    
    # stereo = cv.StereoBM_create(numDisparities=16, blockSize=15)
    #disparity = stereoSGBM(left_rectified,right_rectified)

    # Show the images
    #cv2.imshow('left(R)', leftFrame)
    #cv2.imshow('right(R)', rightFrame)
    while True:
        cv2.imshow('left(Rect)', left_rectified)
        cv2.imshow('right(Rect)', right_rectified)
        norm_image = cv2.normalize(disparity, None, alpha = 0, beta = 1, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
        cv2.imshow('dispar)', norm_image)
        if cv2.waitKey(50) & 0xFF == ord('q'):  # Get key to stop stream. Press q for exit
            break



def stereoSGBM(left,right):
    # Set disparity parameters
    #Note: disparity range is tuned according to specific parameters obtained through trial and error. 
    win_size = 5
    min_disp = -1
    max_disp = 63 #min_disp * 9
    num_disp = max_disp - min_disp # Needs to be divisible by 16
    #Create Block matching object. 
    stereo = cv2.StereoSGBM_create(minDisparity= min_disp,
    numDisparities = num_disp,
    blockSize = 5,
    uniquenessRatio = 20,
    speckleWindowSize = 30,
    speckleRange = 3,
    disp12MaxDiff = 4,
    P1 = 8*3*win_size**2,#8*3*win_size**2,
    P2 =32*3*win_size**2) #32*3*win_size**2)
    #Compute disparity map
    print ("\nComputing the disparity  map...")
    disparity_map = stereo.compute(left, right)
    return disparity_map
    #Show disparity map before generating 3D cloud to verify that point cloud will be usable. 
    # plt.imshow(disparity_map,'gray')
    # plt.show()

def chessboard(iface):
    cap0 = cv2.VideoCapture(iface[0])
    cap1 = cv2.VideoCapture(iface[1])            

    time.sleep(0.1)
    i=0
    while(cap0.isOpened() and cap1.isOpened()):
        ret, right = cap0.read()
        ret, left = cap1.read()
        right = cv2.cvtColor(right, cv2.COLOR_BGR2RGBA)
        left = cv2.cvtColor(left, cv2.COLOR_BGR2RGBA)  
        cv2.imshow('right',right)
        cv2.imshow('left',left)


        key= cv2.waitKey(33)& 0xFF
        if key == ord('a'):
            print("save img")
            filename = f'calib/Left{i}.jpg'
            cv2.imwrite(filename, left) 
            filename = f'calib/Right{i}.jpg'
            cv2.imwrite(filename, right) 
            i=i+1
        if key == ord('q'):
            break
                
    cap0.release()
    cap1.release()
    return 0

def process_chessboard():
    # termination criteria
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    # prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
    objp = np.zeros((6*9,3), np.float32)
    objp[:,:2] = np.mgrid[0:9,0:6].T.reshape(-1,2)

    # Arrays to store object points and image points from all the images.
    objpoints = [] # 3d point in real world space
    imgpoints = [] # 2d points in image plane.


    images = glob.glob(f'calib/*.jpg')

    for fname in images:
        img = cv2.imread(fname)
        gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

        # Find the chess board corners
        ret, corners = cv2.findChessboardCorners(gray, (9,6),None)

        # If found, add object points, image points (after refining them)
        if ret == True:
            objpoints.append(objp)

            corners2 = cv2.cornerSubPix(gray,corners,(11,11),(-1,-1),criteria)
            imgpoints.append(corners2)

            # Draw and display the corners
            img = cv2.drawChessboardCorners(img, (9,6), corners2,ret)
            cv2.imshow('img',img)
            cv2.waitKey(500)

    cv2.destroyAllWindows()

    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1],None,None)

    img = cv2.imread(f'calib/Right6.jpg')
    h,  w = img.shape[:2]
    newcameramtx, roi=cv2.getOptimalNewCameraMatrix(mtx,dist,(w,h),1,(w,h))

    # undistort
    dst = cv2.undistort(img, mtx, dist, None, newcameramtx)

    # crop the image
    x,y,w,h = roi
    dst = dst[y:y+h, x:x+w]
    cv2.imwrite(f'calibresult.png',dst)
    mean_error = 0
    for i in range(len(objpoints)):
        imgpoints2, _ = cv2.projectPoints(objpoints[i], rvecs[i], tvecs[i], mtx, dist)
        error = cv2.norm(imgpoints[i],imgpoints2, cv2.NORM_L2)/len(imgpoints2)
        mean_error += error

    print (f"total error : ", mean_error/len(objpoints))

    #save parameters to disk
    np.save(f"calib/Original camera matrix", mtx)
    np.save(f"calib/Distortion coefficients", dist)
    np.save(f"calib/Optimal camera matrix", newcameramtx)

    # #open params
    # mtx = np.load("calib/Original camera matrix.npy")
    # dist = np.load("calib/Distortion coefficients.npy")
    # newcameramtx = np.load("calib/Optimal camera matrix.npy")


def save_coefficients(mtx, dist, path):
    """ Save the camera matrix and the distortion coefficients to given path/file. """
    cv_file = cv2.FileStorage(path, cv2.FILE_STORAGE_WRITE)
    cv_file.write("K", mtx)
    cv_file.write("D", dist)
    # note you *release* you don't close() a FileStorage object
    cv_file.release()


def save_stereo_coefficients(path, K1, D1, K2, D2, R, T, E, F, R1, R2, P1, P2, Q):
    """ Save the stereo coefficients to given path/file. """
    cv_file = cv2.FileStorage(path, cv2.FILE_STORAGE_WRITE)
    cv_file.write("K1", K1)
    cv_file.write("D1", D1)
    cv_file.write("K2", K2)
    cv_file.write("D2", D2)
    cv_file.write("R", R)
    cv_file.write("T", T)
    cv_file.write("E", E)
    cv_file.write("F", F)
    cv_file.write("R1", R1)
    cv_file.write("R2", R2)
    cv_file.write("P1", P1)
    cv_file.write("P2", P2)
    cv_file.write("Q", Q)
    cv_file.release()


def load_coefficients(path):
    """ Loads camera matrix and distortion coefficients. """
    # FILE_STORAGE_READ
    cv_file = cv2.FileStorage(path, cv2.FILE_STORAGE_READ)

    # note we also have to specify the type to retrieve other wise we only get a
    # FileNode object back instead of a matrix
    camera_matrix = cv_file.getNode("K").mat()
    dist_matrix = cv_file.getNode("D").mat()

    cv_file.release()
    return [camera_matrix, dist_matrix]


def load_stereo_coefficients(path):
    """ Loads stereo matrix coefficients. """
    # FILE_STORAGE_READ
    cv_file = cv2.FileStorage(path, cv2.FILE_STORAGE_READ)
    # note we also have to specify the type to retrieve other wise we only get a
    # FileNode object back instead of a matrix
    K1 = cv_file.getNode("K1").mat()
    D1 = cv_file.getNode("D1").mat()
    K2 = cv_file.getNode("K2").mat()
    D2 = cv_file.getNode("D2").mat()
    R = cv_file.getNode("R").mat()
    T = cv_file.getNode("T").mat()
    E = cv_file.getNode("E").mat()
    F = cv_file.getNode("F").mat()
    R1 = cv_file.getNode("R1").mat()
    R2 = cv_file.getNode("R2").mat()
    P1 = cv_file.getNode("P1").mat()
    P2 = cv_file.getNode("P2").mat()
    Q = cv_file.getNode("Q").mat()

    cv_file.release()
    return [K1, D1, K2, D2, R, T, E, F, R1, R2, P1, P2, Q]


# termination criteria
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)


def calibrate(dirpath='calib', prefix='', image_format='jpg', square_size=2.2, width=9, height=6):
    """ Apply camera calibration operation for images in the given directory path. """
    # prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(8,6,0)
    objp = np.zeros((height*width, 3), np.float32)
    objp[:, :2] = np.mgrid[0:width, 0:height].T.reshape(-1, 2)

    objp = objp * square_size  # Create real world coords. Use your metric.

    # Arrays to store object points and image points from all the images.
    objpoints = []  # 3d point in real world space
    imgpoints = []  # 2d points in image plane.

    # Directory path correction. Remove the last character if it is '/'
    if dirpath[-1:] == '/':
        dirpath = dirpath[:-1]

    # Get the images
    images = glob.glob(dirpath+'/' + prefix + '*.' + image_format)

    # Iterate through the pairs and find chessboard corners. Add them to arrays
    # If openCV can't find the corners in an image, we discard the image.
    i=0
    for fname in images:
        img = cv2.imread(fname)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Find the chess board corners
        ret, corners = cv2.findChessboardCorners(gray, (width, height), None)
        
        # If found, add object points, image points (after refining them)
        if ret:
            objpoints.append(objp)
            i=i+1
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            imgpoints.append(corners2)

            # Draw and display the corners
            # Show the image to see if pattern is found ! imshow function.
            img = cv2.drawChessboardCorners(img, (width, height), corners2, ret)
            cv2.imshow('img_chessboard',img)
            cv2.waitKey(100)
            filename = f'chessboard/board{i}.jpg'
            cv2.imwrite(filename, img) 

    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

    return [ret, mtx, dist, rvecs, tvecs]

def stereo_calibrate(left_file, right_file, left_dir='calib', left_prefix='Left', right_dir='calib', right_prefix='Right', image_format='jpg', save_file='stereo.yml', square_size=2.2, width=9, height=6):
    """ Stereo calibration and rectification """
    objp, leftp, rightp = load_image_points(left_dir, left_prefix, right_dir, right_prefix, image_format, square_size, width, height)

    K1, D1 = load_coefficients(left_file)
    K2, D2 = load_coefficients(right_file)

    flag = 0
    # flag |= cv2.CALIB_FIX_INTRINSIC
    flag |= cv2.CALIB_USE_INTRINSIC_GUESS
    ret, K1, D1, K2, D2, R, T, E, F = cv2.stereoCalibrate(objp, leftp, rightp, K1, D1, K2, D2, image_size)
    print("Stereo calibration rms: ", ret)
    R1, R2, P1, P2, Q, roi_left, roi_right = cv2.stereoRectify(K1, D1, K2, D2, image_size, R, T, flags=cv2.CALIB_ZERO_DISPARITY, alpha=-1)

    save_stereo_coefficients(save_file, K1, D1, K2, D2, R, T, E, F, R1, R2, P1, P2, Q)


def load_image_points(left_dir, left_prefix, right_dir, right_prefix, image_format, square_size, width=9, height=6):
    global image_size
    pattern_size = (width, height)  # Chessboard size!
    # prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(8,6,0)
    objp = np.zeros((height * width, 3), np.float32)
    objp[:, :2] = np.mgrid[0:width, 0:height].T.reshape(-1, 2)

    objp = objp * square_size  # Create real world coords. Use your metric.

    # Arrays to store object points and image points from all the images.
    objpoints = []  # 3d point in real world space
    left_imgpoints = []  # 2d points in image plane.
    right_imgpoints = []  # 2d points in image plane.

    # Left directory path correction. Remove the last character if it is '/'
    if left_dir[-1:] == '/':
        left_dir = left_dir[:-1]

    # Right directory path correction. Remove the last character if it is '/'
    if right_dir[-1:] == '/':
        right_dir = right_dir[:-1]

    # Get images for left and right directory. Since we use prefix and formats, both image set can be in the same dir.
    left_images = glob.glob(left_dir + '/' + left_prefix + '*.' + image_format)
    right_images = glob.glob(right_dir + '/' + right_prefix + '*.' + image_format)

    # Images should be perfect pairs. Otherwise all the calibration will be false.
    # Be sure that first cam and second cam images are correctly prefixed and numbers are ordered as pairs.
    # Sort will fix the globs to make sure.
    left_images.sort()
    right_images.sort()

    # Pairs should be same size. Otherwise we have sync problem.
    if len(left_images) != len(right_images):
        print("Numbers of left and right images are not equal. They should be pairs.")
        print("Left images count: ", len(left_images))
        print("Right images count: ", len(right_images))
        sys.exit(-1)

    pair_images = zip(left_images, right_images)  # Pair the images for single loop handling

    # Iterate through the pairs and find chessboard corners. Add them to arrays
    # If openCV can't find the corners in one image, we discard the pair.
    for left_im, right_im in pair_images:
        # Right Object Points
        right = cv2.imread(right_im)
        gray_right = cv2.cvtColor(right, cv2.COLOR_BGR2GRAY)

        # Find the chess board corners
        ret_right, corners_right = cv2.findChessboardCorners(gray_right, pattern_size,
                                                             cv2.CALIB_CB_ADAPTIVE_THRESH | cv2.CALIB_CB_FILTER_QUADS)

        # Left Object Points
        left = cv2.imread(left_im)
        gray_left = cv2.cvtColor(left, cv2.COLOR_BGR2GRAY)

        # Find the chess board corners
        ret_left, corners_left = cv2.findChessboardCorners(gray_left, pattern_size,
                                                           cv2.CALIB_CB_ADAPTIVE_THRESH | cv2.CALIB_CB_FILTER_QUADS)

        if ret_left and ret_right:  # If both image is okay. Otherwise we explain which pair has a problem and continue
            # Object points
            objpoints.append(objp)
            # Right points
            corners2_right = cv2.cornerSubPix(gray_right, corners_right, (5, 5), (-1, -1), criteria)
            right_imgpoints.append(corners2_right)
            # Left points
            corners2_left = cv2.cornerSubPix(gray_left, corners_left, (5, 5), (-1, -1), criteria)
            left_imgpoints.append(corners2_left)
        else:
            print("Chessboard couldn't detected. Image pair: ", left_im, " and ", right_im)
            continue

    image_size = gray_right.shape  # If you have no acceptable pair, you may have an error here.
    return [objpoints, left_imgpoints, right_imgpoints]


def depth_map(imgL, imgR):
    """ Depth map calculation. Works with SGBM and WLS. Need rectified images, returns depth map ( left to right disparity ) """
    # SGBM Parameters -----------------
    window_size = 3  # wsize default 3; 5; 7 for SGBM reduced size image; 15 for SGBM full size image (1300px and above); 5 Works nicely

    left_matcher = cv2.StereoSGBM_create(
        minDisparity=-1,
        numDisparities=5*16,  # max_disp has to be dividable by 16 f. E. HH 192, 256
        blockSize=window_size,
        P1=8 * 3 * window_size,
        # wsize default 3; 5; 7 for SGBM reduced size image; 15 for SGBM full size image (1300px and above); 5 Works nicely
        P2=32 * 3 * window_size,
        disp12MaxDiff=12,
        uniquenessRatio=10,
        speckleWindowSize=50,
        speckleRange=32,
        preFilterCap=63,
        mode=cv2.STEREO_SGBM_MODE_SGBM_3WAY
    )
    right_matcher = cv2.ximgproc.createRightMatcher(left_matcher)
    # FILTER Parameters
    lmbda = 80000
    sigma = 1.3
    visual_multiplier = 6

    wls_filter = cv2.ximgproc.createDisparityWLSFilter(matcher_left=left_matcher)
    wls_filter.setLambda(lmbda)

    wls_filter.setSigmaColor(sigma)
    displ = left_matcher.compute(imgL, imgR)  # .astype(np.float32)/16
    dispr = right_matcher.compute(imgR, imgL)  # .astype(np.float32)/16
    displ = np.int16(displ)
    dispr = np.int16(dispr)
    filteredImg = wls_filter.filter(displ, imgL, None, dispr)  # important to put "imgL" here!!!

    filteredImg = cv2.normalize(src=filteredImg, dst=filteredImg, beta=0, alpha=255, norm_type=cv2.NORM_MINMAX);
    filteredImg = np.uint8(filteredImg)

    return filteredImg


if __name__ == "__main__":
    iface=setup_iface()
    # livestream(iface)
    #chessboard(iface)
    #process_chessboard()
    
    # [ret, mtx, dist, rvecs, tvecs]=calibrate(prefix='Right')
    # save_coefficients(mtx, dist, 'singlecalibRight.yml')
    # print("Calibration is finished. RMS: ", ret)
    # [ret, mtx, dist, rvecs, tvecs]=calibrate(prefix='Left')
    # save_coefficients(mtx, dist, 'singlecalibLeft.yml')
    # print("Calibration is finished. RMS: ", ret)
    # stereo_calibrate(left_file='singlecalibLeft.yml', right_file='singlecalibRight.yml')
    
    depthstream(iface)
    #depthstream_test()

    pass