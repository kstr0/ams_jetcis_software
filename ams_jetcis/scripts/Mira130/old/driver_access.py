import time
import threading
import subprocess
import os
import shutil
import re
import cv2
import fast_ioctl
import numpy as np
from PIL import Image

class ImagerTools:

    def __init__(self, printFunc, port, cli=None):
        self.fname = "/dev/video{}".format(port)
        self.port = port
        self.cli = cli
        self.pr = printFunc
        self.print = True
        self.pr("INFO: Open card:\n")
        result = os.popen("/usr/bin/v4l2-ctl -d {} -D".format(self.fname))
        self.delay = 0
        self.readback = 0
        self.format = ""
        self.fbuf = []
        self.newbuf = []
        self.actBuffer = 0
        self.numBuffer = 3
        self.bpp = 8
        self.streamactive = False
        self.statusCb = None
        self.dispfps = "FPS display: ???"
        self.sync0ms = 0
        self.sync1ms = 0
        self.id = 0x32
        self.toggle = 0
        self.dtype = 0
        self.systype = "Unknown"
        self.WidgetUpdate = False
        self.sp = False

    def setSensorI2C(self, id):
        self.id = id

    def setSystype(self, type):
        self.systype = type


    def write(self, addr, reg, devid=0):
        if(devid == 0):
            devid = self.id
        i2c = fast_ioctl.fastIOCTL(self.pr)
        # execute real write
        i2c.execI2C(addr, devid, self.dtype,reg, 0, self.port)
        if(self.delay > 0):
            self.wait(self.delay)
        if self.print == True:
            self.pr("-> Write reg={}, addr={} done".format(hex(int(reg)), hex(int(addr))))
        if(self.readback > 0):
            regread = i2c.execI2C(addr, devid, self.dtype, 0, 1)
            if(regread != reg):
                self.pr("-> ERROR: Addr={}, Write={}, Read={}".format(addr, reg, regread))
        i2c.close()
#        self.unlockI2C()
        return 0

    def read(self, addr, devid=0):
        if(devid == 0):
            devid = self.id
        i2c = fast_ioctl.fastIOCTL(self.pr)
        # execute a real read
        reg = i2c.execI2C(addr, devid, self.dtype, 0, 1, self.port)
        if(self.delay > 0):
            self.wait(self.delay)
        if self.print == True:
            self.pr("-> Read reg={}, addr={} done".format(hex(int(reg)), hex(int(addr))))
        i2c.close()
#        self.unlockI2C()
        return int(reg)


    def disablePrint(self):
        self.print = False

    def enablePrint(self):
        self.print = True

    def type(self, type):
        self.pr("-> type = {} done".format(type))
        self.dtype = type
        return 0


    def wait(self, msec):
        time.sleep(msec/1000.0)

    def setDelay(self,delay):
        self.delay = delay

    def setReadback(self, rb):
        self.readback = int(rb)

    def reset(self, onoff):
        value = 0x00000000
        result = os.popen("/usr/bin/v4l2-ctl -d {} --set-ctrl=rst_sensor=0".format(self.fname))
        value = 0x00000001
        result = os.popen("/usr/bin/v4l2-ctl -d {} --set-ctrl=rst_sensor=1".format(self.fname))
        if(self.delay > 0):
            self.sensor_wait(self.delay)
        self.pr("INFO: Reset sensor")
        return 0

    def setmclk(self, rate):
        self.pr("INFO: set mclk to {}Hz".format(rate))
        return 0

    def getBoardType(self):
        self.setSensorI2C(0x0A)
        self.type(0)
        try:
            btype = int(self.read(0x03))
            if(btype == 1):
                btype = "01(mira220,CSP)"
            elif(btype == 2):
                btype = "02(mira100,CSP)"
            elif(btype == 3):
                btype = "03(mira130,CSP)"
            else:
                btype = "{}(unknown)".format(hex(btype))
        except:
            btype = "00(mira130,CSP)"
        return btype

    def getBoardRevision(self):
        self.setSensorI2C(0x0A)
        self.type(0)
        try:
            brev = int(self.read(0x04))
            brev = hex(brev)
        except:
            brev = "01"
        return brev

    def getBoardSerialNo(self):
        self.setSensorI2C(0x0A)
        self.type(0)
        try:
            for lp in range(7,11):
                val[lp-7] = hex(int(self.read(lp)))
            sno = "{}-{}-{}-{}".format(val[0], val[1], val[2], val[3])
        except:
            sno = "??-??-??-??"
        return sno

    def getBoardTemp(self):
        result = os.popen("cat /sys/class/thermal/thermal_zone0/temp".format(self.fname))
        result = float(result.read()) / 1000.0
        return result

    def setformat(self, bpp, width, height, wdma, hdma, v4l2):
        if (bpp == 12):
            format = "RG12"
            self.bpp = 12
        elif (bpp == 10):
            format = "RG10"
            self.bpp = 10
        else:
            format = "RGGB"
            self.bpp = 8
        self.format = "--set-fmt-video=width={},height={},pixelformat={}".format(width, height, format)
        self.w = width
        self.h = height
        self.bufw = wdma
        self.bufh = hdma
        self.v4l2 = v4l2



    def saveRaw(self, fname, count=1):
        fname = str(fname).split(".")
        if (count == 1):
            cnt = 1
        else:
            cnt = count
        if(os.getuid() != 0):
            print('no root')
            return(0)
        self.clearArgus()
        sp = subprocess.Popen(["/usr/bin/v4l2-ctl", "-d", self.fname, self.format, "--set-ctrl", "bypass_mode=0", "--stream-mmap", "--stream-count={}".format(cnt), "--stream-to=/run/record.raw"])
#        sp.terminate()
        sp.wait()
        #time.sleep(2)
        # finally copy raw from RAM to final location. remove stuffing data and extract single frames
        for fno in range(0, cnt):
            w = self.bufw
            h = self.bufh
            if (self.bpp > 8):
                bpp = 2
                dt = np.uint16
            else:
                bpp = 1
                dt = np.uint8
            sp = subprocess.Popen(["/bin/dd", "if=/run/record.raw", "of=/run/record_tmp.raw", "bs={}".format(w*bpp), "count={}".format(h), "skip={}".format(h*fno)])
            sp.wait()
            # cut out data
            img = np.fromfile("/run/record_tmp.raw", dtype=dt)
            print('am here')
            #try:
            w_new=self.w+8
            img = img.reshape(self.bufh,self.bufw)
            img = img[0:self.h, 0:self.w]
            f = "{}_{}.raw".format(fname[0], fno)
            print(f)
            img.tofile(f)
#                self.pr("cutting no={} to={}".format(fno, f))
            #except:
            #    pass # not enough image data
            #sp = subprocess.Popen(["/bin/rm", "/run/record_tmp.raw"])
            #sp.wait()
        #sp = subprocess.Popen(["/bin/rm", "/run/record.raw"])
        #sp.wait() 


    def saveTiff_Usermode(self, fname, count=1):
        fname = str(fname).split(".")
        cnt = count
        #if(os.getuid() != 0):
        #    print('no root')
        #    return(0)
        #self.clearArgus()
        sp = subprocess.Popen(["/usr/bin/v4l2-ctl", "-d", self.fname, self.format, "--set-ctrl", "bypass_mode=0", "--stream-mmap", "--stream-count={}".format(cnt), "--stream-to=record.raw"])
#        sp.terminate()
        sp.wait()
        #time.sleep(2)
        # finally copy raw from RAM to final location. remove stuffing data and extract single frames
        w = self.bufw
        h = self.bufh
        if (self.bpp > 8):
            bpp = 2
            dt = np.uint16
        else:
            bpp = 1
            dt = np.uint8
        sp.wait()
        # cut out data
        img = np.fromfile("record.raw", dtype=dt)
#            try:
        w_new=self.w+8

        img=img.reshape(cnt,self.bufh,self.bufw)
        img=img[::,0:self.h,0:self.w]*(16-self.bpp)**2 #scale to 16 bit tiff
        for fno in range(0, cnt):
            f = "{}_{}.tiff".format(fname[0], fno)
            Image.fromarray(img[fno]).save(f)

#           except:
#              pass # not enough image data

        sp = subprocess.Popen(["/bin/rm", "record.raw"])
        sp.wait() 
        return 0

    def Capture_Raw(self):
        cnt = 1
        #if(os.getuid() != 0):
        #    print('no root')
        #    return(0)
        #self.clearArgus()
        sp = subprocess.Popen(["/usr/bin/v4l2-ctl", "-d", self.fname, self.format, "--set-ctrl", "bypass_mode=0", "--stream-mmap", "--stream-count={}".format(cnt), "--stream-to=record.raw"])
#        sp.terminate()
        sp.wait()
        #time.sleep(2)
        # finally copy raw from RAM to final location. remove stuffing data and extract single frames
        w = self.bufw
        h = self.bufh
        if (self.bpp > 8):
            bpp = 2
            dt = np.uint16
        else:
            bpp = 1
            dt = np.uint8
        sp.wait()
        # cut out data
        img = np.fromfile("record.raw", dtype=dt)
#            try:
        w_new=self.w+8

        img=img.reshape(self.bufh,self.bufw)
        img=img[0:self.h,0:self.w]


#           except:
#              pass # not enough image data

        sp = subprocess.Popen(["/bin/rm", "record.raw"])
        sp.wait() 
        return img

    def clearArgus(self):
        if(os.getuid() != 0):
            return(0)
        # We have to get the PID of NVARGUS
        sp = os.popen("lsof -w {}".format(self.fname))
        result = sp.read()
        sp.close()
        print(result)
        ll = result.split()
        if(len(ll) >= 13):
            print(ll)
            pid = int(ll[10])
            fid = re.split(r"u", ll[12])
            fid = int(fid[0])
            print("PID={}, FID={}".format(pid, fid))
            # We can now use gdb to close /dev/video0 on argus
            f = open("/tmp/gdb.cmd", "w")
            f.write("print \"EXEC started\"\n")
            f.write("set $dummy_fd = open(\"/dev/null\", 0x200000)\n")
            f.write("p dup2($dummy_fd, {})\n".format(fid))
            f.write("p close($dummy_fd)\n")
            f.write("detach\n")
            f.write("print \"EXEC done\"\n")
            f.write("quit\n")
            f.close()
            print("Adjust filehandle")
            result = os.popen("/usr/bin/gdb -x /tmp/gdb.cmd -p {}".format(pid))
            print(result)
            print(result.read())
            print("done")
        time.sleep(0.5)





    def saveJpeg(self, fname):
        result = False
        while(not result):
            (result, frame) = self.sensor_getframe()
        if(result):
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
            result, encimg = cv2.imencode('.jpg', frame, encode_param)
            if result is False:
                self.pr("ERROR: can not save current image because of a jpg encoding problem")
            else:
                try:
                    f = open(fname, "w")
                    f.write(encimg);
                    f.close()
                except:
                    self.pr("ERROR: unable to write Jpeg file to disk")
        else:
            self.pr("ERROR: unable to store frame")


    def doWidgetUpdate(self):
        self.WidgetUpdate = True

    def WidgetUpdatePending(self):
        if(self.WidgetUpdate == True):
            self.WidgetUpdate = False
            return True
        else:
            return False


    def initStatusCallback(self, cb):
        self.statusCb = cb

    def startstream(self):
        # prepare ring buffer structures and delete old ones if they already exist
        self.fbuf = []
        self.newbuf = []
        for lp in range(self.numBuffer):
            self.fbuf.append(b"")
            self.newbuf.append(False)
        self.actBuffer = 0
        # create threads
        self.streamactive = True
        pass




    def stopstream(self):
        self.streamactive = False
