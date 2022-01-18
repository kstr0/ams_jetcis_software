#!/usr/bin/python3
import sys
sys.path.append("..")

import driver_access
import gi
import time
gi.require_version('Gst', '1.0')
gi.require_version('Gtk', '3.0')
gi.require_version('GstVideo', '1.0')
from gi.repository import Gst, GObject, Gtk
import os
import numpy as np

import argparse

parser = argparse.ArgumentParser(description='Headless Runner Script for Genicam Streaming.')
parser.add_argument("--path", "-p", default="../Mira030/config_files/mira030_640x480_30fps_10b_2lane.py",
                    help="The Path to the Sensor Config. Default: ../Mira030/config_files/mira030_640x480_30fps_10b_2lane.py")
args = parser.parse_args()

try:
    os.putenv("GENICAM_ROOT_V3_1", "/opt/pleora/ebus_sdk/linux-aarch64-arm/lib/genicam")
    import GEVPython
except:
    print("Info: GEV/Genicam not available")

class HeadlessRunner:
    """ Standalone headless runner class for GEV Streaming. Only requires path to sensor config during init. """
    def __init__(self, path):
        self.path = path
        self.port = 0
        self.device = 0
        self.rootPW = "nano"
        self.imager = driver_access.ImagerTools(print, self.device, None)
        self.imager.setSystype("Nano")
        self.ethIP = os.popen("ifconfig eth0 | grep ether | awk '{print $2}'").read().strip()
        Gst.init(None)
        self.startSensor()


    def startSensor(self):
        fname = self.path
        try:
            with open(fname, "r") as file:
                eobj = compile(file.read(), fname, "exec")
                exec(eobj, globals())
        except:
            print("ERROR: unable to execute init script")
        sensorInfo = getSensorInfo(self.imager)
        resetSensor(self.imager)
        initSensor(self.imager)

        self.sensorInfo = getSensorInfo(self.imager)
        self.sensor_w = int(self.sensorInfo["width"])
        self.sensor_h = int(self.sensorInfo["height"])
        self.sensor_wdma = int(self.sensorInfo["widthDMA"])
        self.sensor_hdma = int(self.sensorInfo["heightDMA"])
        self.w = int(self.sensorInfo["widthDISP"])
        self.h = int(self.sensorInfo["heightDISP"])
        self.sensor_fps = int(self.sensorInfo["fps"])
        self.sensor_mode = int(self.sensorInfo["dtMode"])
        self.bpp = self.sensorInfo["bpp"]

        self.imager.setformat(sensorInfo["bpp"], sensorInfo["width"], sensorInfo["height"], sensorInfo["widthDMA"],
                         sensorInfo["heightDMA"], True)

    def startGEV(self):
        # Create new live pipeline
        self.gstpipe = Gst.Pipeline.new("Live")
        if(int(self.sensorInfo["bpp"]) == 8):
            fmt = "bggr8"
        elif(int(self.sensorInfo["bpp"]) == 10):
            fmt = "bggr10"
        else:
            fmt = "bggr12"
        self.src = Gst.ElementFactory.make("v4l2src", "src")
        caps1 = Gst.ElementFactory.make("capsfilter", "caps1")
        txt = "video/x-bayer, width=(int){}, height=(int){}, format=(string){}, framerate=(fraction){}/1".format(self.sensor_w, self.sensor_h, fmt, self.sensor_fps)
        txt = Gst.Caps.from_string(txt)
        caps1.set_property("caps", txt)
        self.sink = Gst.ElementFactory.make("appsink", "sink")
        self.sink.set_property("emit-signals", True)
        self.sink.set_property("enable-last-sample", True)
        self.gstpipe.add(self.src)
        self.gstpipe.add(caps1)
        self.gstpipe.add(self.sink)
        self.src.link(caps1)
        caps1.link(self.sink)
        # connect LiveUpdate callback
        bus = self.gstpipe.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        #bus.connect("message", self.liveMessage)
        #bus.connect("sync-message::element", self.liveView)
        self.sink.connect("new-sample", self.getImageGEV)
        self.v4l2 = False
        self.capt = False
        #self.root.config(cursor="")
        self.imager.setformat(self.bpp, self.sensor_w, self.sensor_h, self.sensor_wdma, self.sensor_hdma, self.v4l2)
        # Do a raw save to get it up and running
        #self.imager.clearArgus()
        self.imager.saveTiff("/dev/null", count=1)
        #self.root.after(2000, self.doWidgetAutoUpdate)
        #self.imager.doWidgetUpdate()
        # Finally start the stream
        self.gstpipe.set_state(Gst.State.PLAYING)
        #self.root.after(200, self.liveUpdate)
        # And start also the GEV / Genicam interface
        GEVPython.setparams(self.sensor_w, self.sensor_h, self.bpp)
        GEVPython.setip(self.ethIP)
        GEVPython.run(1)

    def getImageGEV(self, sink):
            sample = self.sink.emit("pull-sample")
            caps = sample.get_caps()
            # Extract the width and height info from the sample's caps
            height = caps.get_structure(0).get_value("height")
            width = caps.get_structure(0).get_value("width")
            # Get the actual data
            buffer = sample.get_buffer()
            # Get read access to the buffer data
            success, map_info = buffer.map(Gst.MapFlags.READ)
            if not success:
                raise RuntimeError("Could not map buffer data!")

            if (self.bpp == 8):
                self.cvimage = np.ndarray(shape=(height, width), dtype=np.uint8, buffer=map_info.data)
            else:
                shift = 16 - self.bpp
                self.cvimage = np.left_shift(np.ndarray(shape=(height, width), dtype=np.uint16, buffer=map_info.data),
                                             shift)
            # send image also to GEV Genicam interface
            # Clean up the buffer mapping


            GEVPython.setimage(self.cvimage)
            buffer.unmap(map_info)
            return False

    def stopGEV(self):
        self.GEVrun = False
        GEVPython.run(0)
        result = self.gstpipe.set_state(Gst.State.PAUSED)
        if (result == Gst.StateChangeReturn.ASYNC):
            self.statusAddLine("INFO: Async change in stoplive")
        self.gstpipe.get_state(10)
        result = self.gstpipe.set_state(Gst.State.READY)
        if (result == Gst.StateChangeReturn.ASYNC):
            self.statusAddLine("INFO: Async change in stoplive")
        self.gstpipe.get_state(10)
        result = self.gstpipe.set_state(Gst.State.NULL)
        if (result == Gst.StateChangeReturn.ASYNC):
            self.statusAddLine("INFO: Async change in stoplive")
        self.gstpipe.get_state(10)
        self.gstpipe.unref()
        del self.gstpipe

def main():
    try:
        runner = HeadlessRunner(args.path)
        runner.startGEV()
        while True:
            time.sleep(60)
    except KeyboardInterrupt as e:
        print("Stopping GEV streaming.")
        runner.stopGEV()
        exit(0)
        raise(e)
    except BaseException as e:
        print("Stopping GEV streaming.")
        runner.stopGEV()
        exit(1)
        raise(e)


if __name__ == "__main__":
    main()