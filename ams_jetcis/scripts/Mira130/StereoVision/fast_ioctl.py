import subprocess
import time
import fcntl
import os
import v4l2

class fastIOCTL:

    def __init__(self, printFunc):
        self.fname = "/dev/video0"
        self.pr = printFunc
        try:
            self.f = os.open(self.fname, os.O_RDWR)
        except:
            self.pr("ERROR: Unable to open driver")
        cp = v4l2.v4l2_capability()
        fcntl.ioctl(self.f, v4l2.VIDIOC_QUERYCAP, cp)
        self.card = cp.card

    def close(self):
        os.close(self.f)
        return (0)


    def execI2C(self, addr, devid, dtype, value,rw, mux=0):
        try:
            # Set addr register to dummy values
            ctrl = (v4l2.v4l2_ext_control * 1)()
            ctrl[0].id = 0x00980900 + 0x1108 # TEGRA_CAMERA_USER_TEST5
            ctrl[0].value = 0x00FFFFFF
            ctrl[0].value64 = 0x00FFFFFF
            ctrls = v4l2.v4l2_ext_controls(v4l2.V4L2_CTRL_CLASS_USER, len(ctrl))
            ctrls.controls = ctrl
            fcntl.ioctl(self.f, v4l2.VIDIOC_S_EXT_CTRLS, ctrls)
            # execute an access
            ctrl = (v4l2.v4l2_ext_control * 1)()
            ctrl[0].id = 0x00980900 + 0x110A # TEGRA_CAMERA_USER_TEST6
            ctrl[0].value = 0x00FFFFFF
            ctrl[0].value64 = 0x00FFFFFF
            ctrls = v4l2.v4l2_ext_controls(v4l2.V4L2_CTRL_CLASS_USER, len(ctrl))
            ctrls.controls = ctrl
            fcntl.ioctl(self.f, v4l2.VIDIOC_S_EXT_CTRLS, ctrls)
            # now set the address register correctly
            val = (int(dtype) << 24) + (int(devid) << 16) + int(addr)
            ctrl = (v4l2.v4l2_ext_control * 1)()
            ctrl[0].id = 0x00980900 + 0x1108 # TEGRA_CAMERA_USER_TEST5
            ctrl[0].value = val
            ctrl[0].value64 = val
            ctrls = v4l2.v4l2_ext_controls(v4l2.V4L2_CTRL_CLASS_USER, len(ctrl))
            ctrls.controls = ctrl
            fcntl.ioctl(self.f, v4l2.VIDIOC_S_EXT_CTRLS, ctrls)
            # and execute the access
            ctrl = (v4l2.v4l2_ext_control * 1)()
            ctrl[0].id = 0x00980900 + 0x110A # TEGRA_CAMERA_USER_TEST6
            ctrls = v4l2.v4l2_ext_controls(v4l2.V4L2_CTRL_CLASS_USER, len(ctrl))
            ctrls.controls = ctrl
            if (rw > 0):
                rw = 1
                value = 0
            # read register or write it
            val = (mux << 26) + (1<<24) + (int(rw) << 16) + int(value)
            ctrl[0].value = val
            ctrl[0].value64 = val
            fcntl.ioctl(self.f, v4l2.VIDIOC_S_EXT_CTRLS, ctrls)
            if (rw > 0):
                fcntl.ioctl(self.f, v4l2.VIDIOC_G_EXT_CTRLS, ctrls)
                fcntl.ioctl(self.f, v4l2.VIDIOC_G_EXT_CTRLS, ctrls)
                reg = ctrl[0].value
            else:
                reg = value
        except:
            txt = "ERROR: I2C access error to DEVID={},ADDR={},TYPE={},VALUE={},RW={}".format(devid, addr, dtype, value,rw)
            self.pr(txt)
            raise IOError(txt)
        return int(reg)

