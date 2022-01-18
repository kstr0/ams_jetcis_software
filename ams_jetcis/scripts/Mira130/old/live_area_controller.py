import cv2
import os
import logging
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.path import Path
import matplotlib.patches as patches
import numpy as np
import tkinter
from datetime import datetime
import subprocess
import signal
import time


class LiveAreaController:
    logger = logging.getLogger('root')
    last_image = None
    last_frame = None
    video_mode = True

    def __init__(self, master, path, rawburst):
        self.master = master
        self.path = path
        self.recording = False
        self.rawburst = rawburst

    def set_hw(self, imager):
        self.csg = imager


    def set_play_pause_param(self, play_pause_button, pause_image, play_image, tooltip):
        self.play_pause_button = play_pause_button
        self.pause_image = pause_image
        self.play_image = play_image
        self.play_pause_tooltip = tooltip

    def set_play_pause_menu(self, menu):
        self.menu = menu


    def is_video_mode(self):
        return self.video_mode


    def save_video_callback(self, event=None):
        if (self.recording == False):
            now = datetime.now()
            date_time = now.strftime("record_%m-%d-%Y_%H%M%S.avi")
            self.path = os.path.expanduser(str(self.path))
            self.path = os.path.abspath(self.path)
            path = (self.path.encode("ascii","ignore"))
            try:
                path = tkinter.filedialog.askdirectory(initialdir=self.path)
            except:
                self.logger.error(str(e))
                return
            if (not path):
                return
            try:
                self.master.statusAddLine("INFO: Saving Live video (H.264) started.")
                # Change Record button to blinking and disable all other SAVE button
                # activate gstreamer pipeline
                self.master.stopLive()
#                self.csg.clearArgus()
                self.recording = True
                fname = path+"/"+date_time
                ispdigitalgainrange=\"{}\" !".format(dgain)
                cmd = "exec /usr/bin/gst-launch-1.0 nvarguscamerasrc sensor-id={} wbmode=0 ispdigitalgainrange='1 1' sensor-mode=0 saturation=0 !  'video/x-raw(memory:NVMM),width=(int){},height=(int){},format=(string)NV12,framerate=(fraction)30/1' ! nvv4l2h264enc ! h264parse ! avimux ! filesink location={}".format(self.master.port, self.master.sensor_w, self.master.sensor_h, fname)
#                cmd = "/bin/bash record.sh"
#                cmd = cmd.split()
                self.sp = subprocess.Popen(cmd, shell=True)
#                self.master.startLive(record=False)
                self.master.button_save264.config(image=self.master.img_save264stop)
                self.master.button_save264.image = self.master.img_save264stop
            except:
                raise
                pass
        else:
            self.recording = False
            # Stop recording pipeline
#            os.kill(self.sp.pid, signal.SIGUSR2)
            # As gst-launch is not stopping correctly, we have to kill the process to free argus
#            gp = subprocess.Popen(["/bin/ps", "-C", "gst-launch-1.0", "--no-headers"], stdout=subprocess.PIPE)
#            gp.wait()
#            out, err = gp.communicate()
#            out = out.split()
#            pid = int(out[0])
#            print("Killing {}".format(pid))
#            gp = subprocess.Popen(["/usr/bin/killall", "gst-launch-1.0"])
#            gp.wait()
#            time.sleep(1)
            self.sp.terminate()
            self.sp.wait(2.0)
#            gp = subprocess.Popen(["/bin/systemctl", "restart", "nvargus-daemon"])
#            gp.wait()
#            self.csg.clearArgus()
            time.sleep(2)
            #            self.master.stopLive()
            # deactivate button blinking and enable all other buttons
            self.master.button_save264.config(image=self.master.img_save264)
            self.master.button_save264.image = self.master.img_save264
            self.master.statusAddLine("INFO: Saving Live video (H.264) stopped.")
            self.master.startLive(record=False)

    def save_raw_callback(self, event=None):
        now = datetime.now()
        date_time_raw = now.strftime("recording_%m-%d-%Y_%H%M%S.raw")
        self.path = os.path.expanduser(str(self.path))
        self.path = os.path.abspath(self.path)
        path = (self.path.encode("ascii","ignore"))
        try:
            path = tkinter.filedialog.askdirectory(initialdir=self.path)
        except:
            self.logger.error(str(e))
            return
        if (not path):
            return

        try:
            self.master.statusAddLine("INFO: Saving Raw video")
            self.master.stopLive()
            self.csg.saveRaw(path+"/"+date_time_raw, count=self.rawburst)
            self.master.statusAddLine("INFO: Restart Live Pipeline")
            self.master.startLive()
        except:
            raise
            pass



    def save_image_callback(self, event=None):

        now = datetime.now()
        date_time = now.strftime("image_%m-%d-%Y_%H%M%S.jpg")
        date_time_tif = now.strftime("image_%m-%d-%Y_%H%M%S.tif")
        date_time_raw = now.strftime("image_%m-%d-%Y_%H%M%S.raw")
        self.path = os.path.expanduser(str(self.path))
        self.path = os.path.abspath(self.path)
        path = (self.path.encode("ascii","ignore"))
        try:
            path = tkinter.filedialog.askdirectory(initialdir=self.path)
        except:
            self.logger.error(str(e))
            return
        if (not path):
            return
        try:
            cv2.imwrite(path+"/"+date_time_tif, self.master.last_image)
#            self.master.statusAddLine("INFO: Saving Raw file")
#            self.master.stopLive()
#            self.csg.saveRaw(path+"/"+date_time_raw)
#            self.master.statusAddLine("INFO: Restart Live Pipeline")
#            self.master.startLive()
        except:
            raise
            pass

    def play_pause_callback(self, event=None):
        if self.play_pause_button is None:
            self.logger.error("live_area_controller needs a play/pause button reference but its missing")
            return

        if self.video_mode is True:
            self.video_mode = False
            self.play_pause_button.config(image=self.play_image)
            self.play_pause_button.image = self.play_image
            self.menu.entryconfigure(0, label="Play")
            self.play_pause_tooltip.set_text("Play the live video stream (P)")
        else:
            self.play_pause_button.config(image=self.pause_image)
            self.play_pause_button.image = self.pause_image
            self.menu.entryconfigure(0, label="Pause")
            self.play_pause_tooltip.set_text("Pause the live video stream (P)")
            self.video_mode = True


