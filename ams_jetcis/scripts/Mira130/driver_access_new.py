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
import gi
gi.require_version('Gst', '1.0')
# gi.require_version('Gtk', '3.0')
from gi.repository import Gst, GObject#, Gtk

class ImagerTools:

    def __init__(self, printFunc, port, rootPW=""):
        self.rootPW = rootPW
        self.fname = "/dev/video{}".format(port)
        self.port = port
        self.pw = None
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
        try:
            i2c.execI2C(addr, devid, self.dtype, reg, 0, self.port)
        except:
            self.pr("ERROR: Unable to write to I2C register {}".format(addr))
            return 0
        if(self.delay > 0):
            self.wait(self.delay)
        if self.print == True:
            self.pr(
                "-> Write reg={}, addr={} done".format(hex(int(reg)), hex(int(addr))))
        if(self.readback > 0):
            regread = i2c.execI2C(addr, devid, self.dtype, 0, 1)
            if(regread != reg):
                self.pr(
                    "-> ERROR: Addr={}, Write={}, Read={}".format(addr, reg, regread))
        i2c.close()
#        self.unlockI2C()
        return 0

    def read(self, addr, devid=0):
        if(devid == 0):
            devid = self.id
        i2c = fast_ioctl.fastIOCTL(self.pr)
        # execute a real read
        try:
            reg = i2c.execI2C(addr, devid, self.dtype, 0, 1, self.port)
        except:
            self.pr("ERROR: Unable to read from I2C register {}".format(addr))
            return 0
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
        if self.print == True:
            self.pr("-> type = {} done".format(type))
        self.dtype = type
        return 0

    def wait(self, msec):
        time.sleep(msec/1000.0)

    def setDelay(self, delay):
        self.delay = delay

    def setReadback(self, rb):
        self.readback = int(rb)

    def reset(self, onoff):
        value = 0x00000000
        result = os.popen(
            "/usr/bin/v4l2-ctl -d {} --set-ctrl=rst_sensor=0".format(self.fname))
        value = 0x00000001
        result = os.popen(
            "/usr/bin/v4l2-ctl -d {} --set-ctrl=rst_sensor=1".format(self.fname))
        if(self.delay > 0):
            self.csg1k_wait(self.delay)
        self.pr("INFO: Reset sensor")
        return 0

    def setmclk(self, rate):
        self.pr("INFO: set mclk to {}Hz".format(rate))
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
            brev = hex(brev)
        except:
            brev = "0"
        return brev

    # 2 sensor type
    def getSensorType(self):
        """
        values chosen based on the hardware resistor codes, which can be read out with the pic.
        0b100=csp
        0b010=cob
        0b110=socket
        """
        self.setSensorI2C(0x0A)
        self.type(0)
        try:
            brev = int(self.read(0x04))
            brev = hex(brev)
        except:
            brev = "01"
        return brev

    # 3 Sensory id
    def getSensorID(self):
        """
        values chosen based on the hardware resistor codes, which can be read out with the pic.
        0 = undefined or mira130
        1 = mira050
        2 = mira220
        3 = mira030
        4 = mira130
        """
        self.setSensorI2C(0x0A)
        self.type(0)
        try:
            btype = int(self.read(0x03))
            if(btype == 1):
                btype = "02(mira220,CSP)"
            elif(btype == 2):
                btype = "03(mira030,CSP)"
            elif(btype == 3):
                btype = "01(mira050,CSP)"
            elif(btype == 4):
                btype = "04(mira050,CSP)"
            else:
                btype = "{}(unknown)".format(hex(btype))
        except:
            btype = "00(unknown,CSP)"
        return btype

        # 3 Sensory type
    def getBoardRevision(self):
        """

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
            width, height, format)
        self.w = width
        self.h = height
        self.bufw = wdma
        self.bufh = hdma
        self.v4l2 = v4l2

    def clearArgus(self):
        # We have to get the PID of NVARGUS
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
        time.sleep(0.5)

    def saveTiff(self, fname, count=1):
        fname = str(fname).split(".")
        cnt = count
        print(self.format)
        extra_columns_to_fit_buffer = self.w % 16
        extra_rows_to_fit_buffer = self.h % 16
        format = "--set-fmt-video=width={},height={},pixelformat={}".format(self.w + extra_columns_to_fit_buffer, self.h + extra_rows_to_fit_buffer, "RG" + str(self.bpp))
        print(format)
        sp = subprocess.Popen(["/usr/bin/v4l2-ctl", "-d", self.fname, format, "--set-ctrl", "bypass_mode=0",
                               "--stream-mmap", "--stream-count={}".format(cnt), "--stream-to=/tmp/record.raw"], stdin=subprocess.PIPE)

        sp.wait()
        print("hello")

        # finally copy raw from RAM to final location. remove stuffing data and extract single frames

        print("checking byte per pixel...")
        if (self.bpp > 8):
            bpp = 2
            dt = np.uint16
        else:
            bpp = 1
            dt = np.uint8
        print("checked byte per pixel: {}".format(bpp))

        if(fname[0] != "/dev/null"):
            # cut out data
            print("loading raw image...")
            img = np.fromfile("/tmp/record.raw", dtype=dt)
            print(img.shape)
            print(img)
            print("loaded raw image.")
            print("scaling raw image to tiff...")
            img = img.reshape(cnt, self.bufh + extra_rows_to_fit_buffer, self.w + extra_columns_to_fit_buffer)
            print("done reshaping, scaling now")
            img = img[::, 0:self.h, 0:self.w] * \
                2**(16-self.bpp)  # scale to 16 bit tiff
            print(img.shape)
            print("scaled raw image to tiff...")
            for fno in range(0, cnt):
                print("saving tiff...")
                f = "{}_{}.tiff".format(fname[0], fno)
                Image.fromarray(img[fno]).save(f)
                print("saved tiff.")
        print("cleaning up...")
        sp = subprocess.Popen(["/bin/rm", "/tmp/record.raw"])
        sp.wait()
        print("cleaned up.")

    def saveRaw(self, fname, count=1):
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
#                self.pr("cutting no={} to={}".format(fno, f))
            except:
                pass  # not enough image data
            sp = subprocess.Popen(["/bin/rm", "/tmp/record_tmp.raw"])
            sp.wait()
        sp = subprocess.Popen(["/bin/rm", "/tmp/record.raw"])
        sp.wait()

    def saveJpeg(self, fname):
        result = False
        while(not result):
            (result, frame) = self.csg1k_getframe()
        if(result):
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
            result, encimg = cv2.imencode('.jpg', frame, encode_param)
            if result is False:
                self.pr(
                    "ERROR: can not save current image because of a jpg encoding problem")
            else:
                try:
                    f = open(fname, "w")
                    f.write(encimg)
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
        self.enablePrint()
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
                "ERROR: Gstreamer pipe is broken (.EOS) and must be restarted")
        elif (t == Gst.MessageType.ERROR):
            self.gstpipe.set_state(Gst.State.NULL)
            self.gstpipe = None
            self.statusAddLine(
                "ERROR: Gstreamer pipe is broken (.ERROR) and must be restarted")
