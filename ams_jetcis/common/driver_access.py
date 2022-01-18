import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject  # , Gtk
import time
import threading
import subprocess
import os
import shutil
import re
import cv2
from . import fast_ioctl
import numpy as np
from PIL import Image
from ams_jetcis.common.kernel import Kernel_DTB_manager
# gi.require_version('Gtk', '3.0')


class ImagerTools:

    def __init__(self, printfun=None, port=0, rootPW="jetcis"):
        self.rootPW = rootPW
        self.fname = "/dev/video{}".format(port)
        self.port = port
        self.pw = None
        self.pr = printfun or self.printfun
        self.print = False
        self.pr("Open card:")
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
        self.systype = "Nano"
        self.WidgetUpdate = False
        self.sp = False
        self.sensori2c = 0
        self.kernel_dtb_manager = Kernel_DTB_manager(self.pr)

    def printfun(self, text):
        print(text)

    def setSensorI2C(self, id):
        self.id = id

    def setSystype(self, type):
        self.systype = type

    def write(self, addr, reg, devid=0):
        if(devid == 0):
            devid = self.id
        i2c = fast_ioctl.fastIOCTL(self.pr)
        # execute real write
        try:
            i2c.execI2C(addr, devid, self.dtype, reg, 0, self.port)
        except:
            self.pr("Error: Unable to write to I2C register {}".format(addr))
            return 1
        if(self.delay > 0):
            self.wait(self.delay)
        if self.print == True:
            self.pr(
                "-> Write reg={}, addr={} done".format(hex(int(reg)), hex(int(addr))))
            if(self.readback > 0):
                regread = i2c.execI2C(addr, devid, self.dtype, 0, 1)
                if(regread != reg):
                    self.pr(
                        "-> Error: Addr={}, Write={}, Read={}".format(addr, reg, regread))
        i2c.close()
#        self.unlockI2C()
        return 0

    def read(self, addr, devid=0):
        if(devid == 0):
            devid = self.id
        i2c = fast_ioctl.fastIOCTL(self.pr)
        # execute a real read
        try:
            reg = i2c.execI2C(addr, devid, self.dtype, 0, 1, self.port, print_en=self.print)
        except:
            if self.print == True:
                self.pr("Error: Unable to read from I2C register {}".format(addr))
            return -1
        if(self.delay > 0):
            self.wait(self.delay)
        if self.print == True:
            self.pr(
                "-> Read reg={}, addr={} done".format(hex(int(reg)), hex(int(addr))))
        i2c.close()
#        self.unlockI2C()
        return int(reg)

    def disablePrint(self):
        self.print = False

    def enablePrint(self):
        self.print = True

    def type(self, type):
        self.dtype = type
        return 0

    def wait(self, msec):
        time.sleep(msec/1000.0)

    def setDelay(self, delay):
        self.delay = delay

    def setReadback(self, rb):
        self.readback = int(rb)

    def reset(self, value):
        result = os.popen(f"/usr/bin/v4l2-ctl -d {self.fname} --set-ctrl=rst_sensor={value}")
        if value == 2:
            self.pr(f"Reset sensor low") 
        elif value == 3:
            self.pr(f"Reset sensor high ")
        else:
            self.pr(f"Reset sensor {value}")
        return 0

    def setmclk(self, rate):
        self.pr("Set mclk to {}Hz".format(rate))
        return 0

    # 0 UC id and revision

    def getUcId(self):
        """
        0x11 = dsPIC33EP32GP503
        """
        self.setSensorI2C(0x0A)
        self.type(0)
        try:
            brev = int(self.read(0x0))
            brev = hex(brev)
        except:
            brev = "0"
        return brev

    # 1 uc Firmware
    def getUcFirmware(self):
        self.setSensorI2C(0x0A)
        self.type(0)
        try:
            brev = int(self.read(0x1))
        except:
            brev = 0
        return brev

    # 2 sensor id
    def getUcDump(self):
        self.setSensorI2C(0x0A)
        self.type(0)
        for reg in range(0,20):
            print(f'uC reg {reg} : value {int(self.read(reg))} \n')

    def getSensorID(self):
        """
        values chosen based on the hardware resistor codes, which can be read out with the pic.
        1 = mira050
        2 = mira220
        3 = mira030
        4 = mira130
        lsb is ID2
        """
        id_lut = {1 : 'mira050',
        2 : 'mira220',
        3 : 'mira030',
        4 : 'mira130',
        -1: 'unknown'}

        self.setSensorI2C(0x0A)
        self.type(0)
        if self.getUcFirmware()>5:
            id = self.read(2)
        else:
            try:
                REG_BUF13 = int(self.read(13))
                REG_BUF14 = int(self.read(14))
                print(f'reg13 {REG_BUF13} reg14 {REG_BUF14}')
                type = ((REG_BUF14 & 0b1) <<2) + ((REG_BUF14 & 0b10)) + ((REG_BUF14 & 0b100 )>>2)
                id = ((REG_BUF13 & 0b1)) + ((REG_BUF14 & 0b1000000)>>5) + ((REG_BUF14 & 0b10000000 )>>5)
            except:
                id = -1
            try:
                id = id_lut[id]
            except KeyError:
                id = -1
                self.pr('key unknown id')
        print(f'id is {id}')

        return id
    
  # 3 sensor type
    def getSensorType(self):
        """
        values chosen based on the hardware resistor codes, which can be read out with the pic.
        0b001=csp
        0b010=cob
        0b110=socket
        
        """
        type_lut = {1:'csp',
        2:'cob',
        6:'socket',
        -1: 'unknown'}

        self.setSensorI2C(0x0A)
        self.type(0)
        if self.getUcFirmware()>5:
            type = self.read(3)
        else:
            try:
                REG_BUF13 = int(self.read(13))
                REG_BUF14 = int(self.read(14))

                type = ((REG_BUF14 & 0b1) <<2) + ((REG_BUF14 & 0b10)) + ((REG_BUF14 & 0b100 )>>2)
                id = ((REG_BUF13 & 0b1)) + ((REG_BUF14 & 0b1000000)>>5) + ((REG_BUF14 & 0b10000000 )>>5)
            except:
                type = -1
        try:
            type = type_lut[type]
        except KeyError as e:
            type = 'unknown'
            self.pr(f'key unknown type {e}')
        print(f'type is {type}')
        return type


  

    def getBoardRevision(self):
        """
        NOT IMPLEMENTED
        [7:4]=type, [3:0]= revision
        0x00 undefined
        0x11 mira050 CSP v1
        0x21 mira220 CSP v1
        0x22 mira220 CSP v2 with upgraded capacitors
        0x31 mira030 CSP v1
        0x41 mira130 CSP - undocumented
        0x51 interposer v1
        """
        self.setSensorI2C(0x0A)
        self.type(0)
        try:
            btype = int(self.read(0x03))
            if(btype == 0x11):
                btype = "0x11(mira050,CSP)"
            elif(btype == 0x21):
                btype = "0x21(mira220v1,CSP)"
            elif(btype == 0x22):
                btype = "0x22(mira220v2,CSP)"
            elif(btype == 0x31):
                btype = "0x31(mira130,CSP)"
            elif(btype == 0x51):
                btype = "0x31(interposerv1,COB)"
            else:
                btype = "{}(unknown)".format(hex(btype))
        except:
            btype = "00(undefined)"
        return btype

    def getBoardSerialNo(self):
        self.setSensorI2C(0x0A)
        self.type(0)
        try:
            for lp in range(7, 11):
                val[lp-7] = hex(int(self.read(lp)))
            sno = "{}-{}-{}-{}".format(val[0], val[1], val[2], val[3])
        except:
            sno = "??-??-??-??"
        return sno

    def getBoardTemp(self):
        result = os.popen(
            "cat /sys/class/thermal/thermal_zone0/temp".format(self.fname))
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
        self.format = "--set-fmt-video=width={},height={},pixelformat={}".format(
            wdma, hdma, format)
        # print(f'############### format is {self.format} ##################')
        self.w = width
        self.h = height
        self.bufw = wdma
        self.bufh = hdma
        self.v4l2 = v4l2
        
    def clearArgus(self):
        # We have to get the PID of NVARGUS
        time.sleep(1)
        sp = os.popen(
            "echo {} | sudo -S lsof -w {}".format(self.rootPW, self.fname))
        result = sp.read()
        sp.close()
        print(result)
        for line in result.splitlines():
            ll = line.split()
            if (ll[0] == "COMMAND"):
                pass
            elif (ll[0] == "python3"):
                fid = re.split(r"u", ll[3])
                fid = int(fid[0])
                os.close(fid)
            else:
                pid = int(ll[1])
                fid = re.split(r"u", ll[3])
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
                result = os.popen(
                    "echo {} | sudo -S /usr/bin/gdb -x /tmp/gdb.cmd -p {}".format(self.rootPW, pid))
                print(result)
                print(result.read())
                print("done")
        time.sleep(1)
        
    def saveTiff(self, dir_fname, count=1, save=True):
        '''See documentation of grab_images and save_images
        '''
        imgs = self.grab_images(count)
        if save:
            self.save_images(imgs, dir_fname)
        return imgs
        
    def grab_images(self, count=1):
        '''Capture images using v4l2.

        Parameters
        ----------
        count : int
            Number of frames to grab
            
        Returns
        -------
        np.array : 
            list of images
        '''

        sp = subprocess.Popen(["/usr/bin/v4l2-ctl", "-d",
                               self.fname,
                               self.format,
                               "--set-ctrl",
                               "bypass_mode=0",
                               "--stream-mmap",
                               f"--stream-count={count}", 
                               "--stream-to=/tmp/record.raw"], 
                              stdin=subprocess.PIPE)
        sp.wait()

        # Copy raw from RAM to return variable. Remove stuffing data and extract single frames
        if self.bpp > 8:
            dt = np.uint16
        else:
            dt = np.uint8
        sp.wait()

        img = np.fromfile("/tmp/record.raw", dtype=dt)
        img = img.reshape(count, self.bufh, self.bufw)[::, 0:self.h, 0:self.w]

        sp = subprocess.Popen(["/bin/rm", "/tmp/record.raw"])
        sp.wait()

        return img

    def save_images(self, imgs, dir_fname):
        '''Save images tiff files.

        Parameters
        ----------
        imgs : np.array
            List of images

        dir_fname : str
            The image directory/filename where to save the images
        '''
        dir_path = os.path.dirname(dir_fname)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        if self.bpp>8:
            for fno in range(0, imgs.shape[0]):
                Image.fromarray(imgs[fno] << (16-self.bpp)).save(f'{dir_fname}_{fno}.tiff')
        else:
            for fno in range(0, imgs.shape[0]):
                Image.fromarray(imgs[fno] ).save(f'{dir_fname}_{fno}.tiff')
        
    def saveRaw(self, fname, count=1):
        '''Depreciated code
        '''
        fname = str(fname).split(".")
        if (count == 1):
            cnt = 10
        else:
            cnt = count
        sp = subprocess.Popen(["/usr/bin/v4l2-ctl", "-d", self.fname, self.format, "--set-ctrl", "bypass_mode=0",
                               "--stream-mmap", "--stream-count={}".format(cnt), "--stream-to=/tmp/record.raw"])
#        sp.terminate()
        sp.wait()
        # time.sleep(2)
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
            sp = subprocess.Popen(["/bin/dd", "if=/tmp/record.raw", "of=/tmp/record_tmp.raw",
                                   "bs={}".format(w*bpp), "count={}".format(h), "skip={}".format(h*fno)])
            sp.wait()
            # cut out data
            img = np.fromfile("/run/record_tmp.raw", dtype=dt)
            try:
                img = img.reshape(h, w)
                img = img[0:self.h, 0:self.w]
                f = "{}_{}.raw".format(fname[0], fno)
                img.tofile(f)
#                self.pr("Cutting no={} to={}".format(fno, f))
            except:
                pass  # not enough image data
            sp = subprocess.Popen(["/bin/rm", "/tmp/record_tmp.raw"])
            sp.wait()
        sp = subprocess.Popen(["/bin/rm", "/tmp/record.raw"])
        sp.wait()

    def saveJpeg(self, fname):
        '''Depreciated code
        '''
        result = False
        while(not result):
            (result, frame) = self.csg1k_getframe()
        if(result):
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
            result, encimg = cv2.imencode('.jpg', frame, encode_param)
            if result is False:
                self.pr(
                    "Error: Can not save current image because of a jpg encoding problem")
            else:
                try:
                    f = open(fname, "w")
                    f.write(encimg)
                    f.close()
                except:
                    self.pr("Error: Unable to write Jpeg file to disk")
        else:
            self.pr("Error: Unable to store frame")

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

    def ina260Check(self):
        self.disablePrint()
        result = False
        self.type(2)
        pwr = self.read(0xFE, 0x45)
        if (pwr == 0x5449):
            result = True
            pwr = self.read(0x03, 0x45)
            pwr = float(pwr) / 100.0
        else:
            result = False
            pwr = 0
        return (result, pwr)

    # important: gstCmd contains a valig Gstreamer Pipeline string
    #            The sink must have the property name=sink1
    def initISP(self, w, h, fps, id, mode, callback):
        Gst.init(None)
        self.gstpipe = Gst.Pipeline.new("Capture")
        self.src = Gst.ElementFactory.make("nvarguscamerasrc", "src")
        self.src.set_property("sensor-id", id)
        self.src.set_property("wbmode", 0)
        self.src.set_property("sensor-mode", mode)
        caps1 = Gst.ElementFactory.make("capsfilter", "caps1")
        txt = "video/x-raw(memory:NVMM), width=(int){}, height=(int){}, format=(string)NV12, framerate=(fraction){}/1".format(
            w, h, fps)
        txt = Gst.Caps.from_string(txt)
        caps1.set_property("caps", txt)
        self.filter1 = Gst.ElementFactory.make("nvvidconv", "filter1")
        self.caps2 = Gst.ElementFactory.make("capsfilter", "caps2")
        txt = "video/x-raw, width={}, height={}, format=(string)RGBA".format(
            w, h)
        txt = Gst.Caps.from_string(txt)
        self.caps2.set_property("caps", txt)
        self.sink = Gst.ElementFactory.make("appsink", "sink")
        self.sink.set_property("max-buffers", 5)
        self.sink.set_property("drop", True)
        self.gstpipe.add(self.src)
        self.gstpipe.add(caps1)
        self.gstpipe.add(self.filter1)
        self.gstpipe.add(self.caps2)
        self.gstpipe.add(self.sink)
        self.src.link(caps1)
        caps1.link(self.filter1)
        self.filter1.link(self.caps2)
        self.caps2.link(self.sink)

        # connect LiveUpdate callback
        bus = self.gstpipe.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        bus.connect("message", self.liveMessage)
        #        bus.connect("sync-message::element", self.liveView)
        self.sink.set_property("emit-signals", True)
        handler_id = self.sink.connect("new-sample", callback)
        # Finally start the stream
        self.gstpipe.set_state(Gst.State.PLAYING)

    def liveMessage(self, bus, message):
        t = message.type
        if (t == Gst.MessageType.EOS):
            self.gstpipe.set_state(Gst.State.NULL)
            self.gstpipe = None
            self.statusAddLine(
                "Error: Gstreamer pipe is broken (.EOS) and must be restarted")
        elif (t == Gst.MessageType.ERROR):
            self.gstpipe.set_state(Gst.State.NULL)
            self.gstpipe = None
            self.statusAddLine(
                "Error: Gstreamer pipe is broken (.ERROR) and must be restarted")
