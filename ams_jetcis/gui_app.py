if __name__ == '__main__':
    print('Please run using the python module from the sw folder: $ python3 -m ams_jetcis')
    print('or run gui.sh in the parent folder')
    exit()

import tkinter
import tkinter.ttk
from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
from tkinter import simpledialog
from tkinter.ttk import *
from ttkbootstrap import Style
import configparser
import sys
import os
import traceback
import cv2
import time
import numpy as np
from PIL import ImageTk, Image
from functools import partial
import pandas as pd

from datetime import datetime
import subprocess
from xmlrpc.client import ServerProxy

from ams_jetcis.common.tooltip import CreateToolTip
from ams_jetcis.common import driver_access
from ams_jetcis.scripts.Mira050.fullres_mira050 import resetSensor

# ams imports
#sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))) #add parent folder to path
from ams_jetcis.common.driver_access import ImagerTools
from ams_jetcis.common.kernel import Kernel_DTB_manager
from ams_jetcis.sensors.mira050.mira050 import Mira050
from ams_jetcis.sensors.mira130.mira130 import Mira130
from ams_jetcis.sensors.mira220.mira220 import Mira220
from ams_jetcis.sensors.mira030.mira030 import Mira030
from ams_jetcis.sensors.sensor import Sensor

import gi
gi.require_version('Gst', '1.0')
gi.require_version('Gtk', '3.0')
gi.require_version('GstVideo', '1.0')
from gi.repository import Gst, GObject, Gtk
from gi.repository import GdkX11, GstVideo
import cairo
gi.require_foreign('cairo') 

try:
    os.putenv("GENICAM_ROOT_V3_1", "/opt/pleora/ebus_sdk/linux-aarch64-arm/lib/genicam")
    import GEVPython
except:
    print("GEV/Genicam not available")

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure

import locale
locale.setlocale(locale.LC_NUMERIC, 'en_US.UTF-8')

import requests
from bs4 import BeautifulSoup
from distutils.version import StrictVersion
import urllib

# Debugging only
#import pydevd_pycharm
#pydevd_pycharm.settrace('192.168.1.100', port=12345, stdoutToServer=True,
#                        stderrToServer=True)

class MainApp(tkinter.Frame):

    def __init__(self, master=None):
        # store master link
        self.root = master
        self.rootPW = 'jetcis'
        # Set screen size
        self.window_width = 1400
        self.window_height = 910
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.x_coordinate = int((self.screen_width/2) - (self.window_width/2))
        self.y_coordinate = int((self.screen_height/2) - (self.window_height/2))
        self.dpi_value = self.root.winfo_fpixels('1i')
        self.root.tk.call('tk', 'scaling', '-displayof', '.', self.dpi_value / 72.0) # still need to test this with 4k screen
        self.root.geometry(f"{self.window_width}x{self.window_height}+{self.x_coordinate}+{self.y_coordinate-40}")
        # self.root.geometry(f"{1400*self.screen_width//1920}x{910*self.screen_height//1080}")
        # Define important things
        self.pwrAvail = True
        self.streaming = False
        self.cap = None
        self.port = 0
        self.fullscreen = False
        self.systype = "Unknown"
        self.widgetList = list()
        self.widgetAutoUpdate = list()
        self.sensor_fps = 30
        self.videoDevice = tkinter.IntVar()
        self.videoDevice.set(0)
        self.imager = None
        self.temp = float(20.0)
        self.videoLocked = False
        self.run = True
        self.sensLoaded = False
        self.video_mode = True
        self.recording = False
        # Scaler data
        self.scale = 1.0
        self.factor = 0.5
        self.posx = 0.5
        self.posy = 0.5
        self.oldX = -1
        self.oldY = -1
        self.GEVactive = tkinter.BooleanVar()
        self.GEVactive.set(False)
        self.GEVrun = False
        # Load version info file
        self.version_info = configparser.ConfigParser()
        self.version_info.read("./version_info.cfg")
        # Load gui config file
        self.config = configparser.ConfigParser()
        self.config.read("./ams_jetcis/gui_config.cfg")
        try:
            self.version = str(self.version_info["SW"]["version"])
            print(f"Software version {self.version} loaded")
        except Exception as err:
            print(f"Error: {str(err)} no or wrong version_info.cfg present. Program will be terminated")
            sys.exit(0)
        # And check file path
        try:
            self.config["File"]["path"]
        except:
            self.config["File"]["path"] = "~/Pictures"
        try:
            self.config["File"]["logpath"]
        except:
            self.config["File"]["logpath"] = "~/Documents"
        try:
            self.config["GUI"]["useGEV"]
        except:
            self.config["GUI"]["useGEV"] = 0
        try:
            self.ethIP = os.popen("ifconfig eth0 | grep ether | awk '{print $2}'").read().strip()
        except:
            try:
                self.config["GUI"]["ethIP"]
            except:
                self.ethIP = "00:04:4b:e6:f7:5b"

        tkinter.Frame.__init__(self, master)
        self.pack(fill="both", expand=True)
        self.menuBar = tkinter.Menu(master)
        master.config(menu=self.menuBar)
        self.initMenuBar()
        self.master.resizable(True, True)
        self.initPopups()
        self.checkPlatform()
        self.initGUI()

        # Ask for Root Password
        self.rootPW = 'jetcis'

        # Start watchdog thread

        # Add keyboard functions
        self.master.bind("f", self.toggleFullscreen)
        self.master.bind("<Escape>", self.exitFullscreen)
        self.master.bind("q", self.endProgram)
        self.master.bind("s", self.save_image_callback)
        self.master.bind("r", self.save_video_callback) # H264: comment out if not used
        self.master.bind("b", self.save_raw_callback)
        self.master.bind("p", self.play_pause_callback)
        self.master.bind("o", self.openSensorConfig)
        # Iniialize Gstreamer framework
        Gst.init(None)

    def startSync(self):
        """
        depreciated code
        """
        print("SyncServer...")

        #####################
        # MAIN
        #####################
        try:
            self.serv = SyncServer.SyncServer()
            self.serv.serve()
        except:
            raise
            print("Success: SyncServer is already running.")
        print("SyncServer stopped.")


    def endProgram(self, event=None):
        self.run = False
        try:
            self.sync.join(2.0)
        except:
            pass # happens if SyncServer did not run
        try:
            if(self.cap is not None):
                self.cap.release()
                self.cap = None
        except:
            pass
        self.streaming = False
        time.sleep(1)
        sys.exit(0)

    def checkPlatform(self):
        if (os.path.exists("/sys/devices/50000000.host1x/546c0000.i2c/i2c-6")):
            self.systype = "Nano"
        elif (os.path.exists("/sys/devices/3180000.i2c/i2c-2")):
            self.systype = "TX2"
        else:
            self.systype = "Unknown"

    def checkPortAvail(self, port):
        sp = os.popen("echo {} | sudo -S lsof -w /dev/video{}".format(self.rootPW, int(port)))
        result = sp.read()
        sp.close()
        pid = os.getpid()
        # Device was opened by us
        if(result.find(str(pid)) >= 0):
            return True
        # Check if device is used by someone else
        try:
            result.index("python3")
            return False
        except ValueError:
            return True

    def initMenuBar(self):
        # File menu
        self.menuFile = tkinter.Menu(self.menuBar, tearoff=False)
        self.menuFile.add_command(label="Open Sensor Configuration", command=self.openSensorConfig, accelerator="O")
        self.menuFile.add_separator()
        self.menuFile.add_command(label="Save Settings", command=self.saveSettings)
        self.menuFile.add_separator()
        self.menuFile.add_command(label="Exit Program", command=self.endProgram, accelerator="Q")
        self.menuBar.add_cascade(label="File", menu=self.menuFile)
        # Edit Menu
        self.menuEdit = tkinter.Menu(self.menuBar, tearoff=False)
        self.menuEdit.add_command(label="Application Settings", command=self.editSettings)
        self.menuBar.add_cascade(label="Edit", menu=self.menuEdit)
        self.menuEdit.entryconfig(1, state=DISABLED)
        # Control Menu
        self.menuControl = tkinter.Menu(self.menuBar, tearoff=False)
        self.menuControl.add_command(label="Pause", command=self.play_pause_callback,
                                     accelerator="P")
        self.menuControl.add_command(label="Save Image", command=self.save_image_callback,
                                     accelerator="S")
        self.menuControl.add_command(label="Save Video (H.264)", command=self.save_video_callback,
                                     accelerator="R") # H264: Disable with , state=tkinter.DISABLED
        # self.menuControl.add_command(label="Save Burst (RAW)", command=self.save_raw_callback,
                                    #  accelerator="B")
        
        self.burst_submenu = tkinter.Menu(self.menuControl, tearoff=0)
        self.burst_submenu.add_command(label="Save Burst (RAW)", command=self.save_video_callback, accelerator="B")
        self.burst_submenu.add_command(label='Change the quantity', command=self.set_nb_raw_burst)
        self.nb_raw_burst = int(self.config["Record"]["rawburst"])
        self.menuControl.add_cascade(label='Burst', menu=self.burst_submenu)

        self.menuControl.add_command(label="Full Screen", command=self.toggleFullscreen, accelerator="F")
        self.menuControl.add_command(label="Register Dump", command=self.register_dump, state=tkinter.DISABLED)
        #print(GEVPython.getparams())
        if (int(self.config["GUI"]["useGEV"]) == 1):
            try:
                GEVPython.getparams()
                self.menuControl.add_checkbutton(label="Use GEV/Genicam streaming", onvalue=1, offvalue=0, variable=self.GEVactive)
            except:
                pass
        self.menuBar.add_cascade(label="Control", menu=self.menuControl)
        # Help Menu
        self.menuHelp = tkinter.Menu(self.menuBar, tearoff=False)
        self.menuHelp.add_command(label="Open Installed Documentation", command=self.showDocumentation)
        self.menuHelp.add_command(label="Open Online Documentation", command=self.showDocumentationOnline)
        self.menuHelp.add_separator()
        self.menuHelp.add_command(label="About", command=self.showAbout)
        self.menuHelp.add_command(label="Check For Updates", command=self.checkForUpdates)
        self.menuHelp.add_command(label="Changes", command=self.showChanges)
        self.menuHelp.add_command(label="License Agreement", command=self.showAgreement)
        self.menuBar.add_cascade(label="Help", menu=self.menuHelp)
        #self.menuHelp.entryconfig(1, state=DISABLED)

    def initPopups(self):
        # text area popup menu
        self.menuText = tkinter.Menu(self, tearoff=False)
        self.menuText.add_command(label="Clear", command=self.statusClear)
        self.menuText.add_command(label="Save", command=self.statusSave)

    def initGUI(self):
        ##############################
        # check kernel and SDK version
        ##############################
        p = subprocess.Popen(["uname", "-r"], stdout=subprocess.PIPE)
        version = str(p.stdout.read())
        if(not (re.search(r"4.9.140", version) or re.search(r"4.9.253", version))): # SDK 4.3
            messagebox.showinfo("ERROR",
                                  "Kernel Version({}) is not supported by the software".format(version))
            exit(1)
        
        ##################
        # Grid configure
        ##################
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=10)
        self.rowconfigure(2, weight=1)
        self.rowconfigure(3, weight=0)
        
        ##################
        # The ButtonArea
        ##################
        self.buttonArea = tkinter.Frame(self, bd=1, relief="raised")
        self.buttonArea.grid(row=0, column=0, columnspan=2, sticky="new")
        
        # Open config button
        self.img_openconfig = ImageTk.PhotoImage(Image.open("ams_jetcis/button_icons/open_camera.png").resize((32, 32), Image.ANTIALIAS))
        self.button_openconfig = tkinter.Button(self.buttonArea, image=self.img_openconfig, activebackground="#00ADFD",
                                                bg="#FDF6F1", highlightthickness = 0, bd=0, command=self.openSensorConfig)
        self.button_openconfig.grid(row=0, column=0, padx=(0,5))
        self.button_openconfig_ttp = CreateToolTip(self.button_openconfig, self.buttonArea,
                                                   "Open a sensor configuration file")

        # Play pause button
        self.img_pause = ImageTk.PhotoImage(Image.open("ams_jetcis/button_icons/pause_pipeline.png").resize((32, 32), Image.ANTIALIAS))
        self.img_play = ImageTk.PhotoImage(Image.open("ams_jetcis/button_icons/play_pipeline.png").resize((32, 32), Image.ANTIALIAS))
        self.button_playpause = tkinter.Button(self.buttonArea, image=self.img_pause, activebackground="#00ADFD",
                                               bg="#FDF6F1", highlightthickness = 0, bd=0, command=self.play_pause_callback)
        self.button_playpause_ttp = CreateToolTip(self.button_playpause, self.buttonArea,
                                                  "Pause the live video stream (P)")
        self.button_playpause.grid(row=0, column=1, padx=(0,5))
        
        # Save image button
        self.img_saveimage = ImageTk.PhotoImage(Image.open("ams_jetcis/button_icons/save_single_image.png").resize((32, 32), Image.ANTIALIAS))
        self.button_saveimage = tkinter.Button(self.buttonArea, image=self.img_saveimage, activebackground="#00ADFD",
                                               bg="#FDF6F1", highlightthickness = 0, bd=0, command=self.save_image_callback)
        self.button_saveimage.grid(row=0, column=2, padx=(0,5))
        self.button_saveimage_ttp = CreateToolTip(self.button_saveimage, self.buttonArea,
                                                  "Save the presented image as TIFF (S)")
        
        # Save burst button
        self.img_saveraw = ImageTk.PhotoImage(Image.open("ams_jetcis/button_icons/save_burst_image.png").resize((32, 32), Image.ANTIALIAS))
        self.button_saveimageraw = tkinter.Button(self.buttonArea, image=self.img_saveraw, activebackground="#00ADFD",
                                               bg="#FDF6F1", highlightthickness = 0, bd=0, command=self.save_raw_callback)
        self.button_saveimageraw.grid(row=0, column=3, padx=(0,5))
        self.button_saveimageraw_ttp = CreateToolTip(self.button_saveimageraw, self.buttonArea,
                                                  "Save the presented video as RAW burst (B)")

        # Save video button
        self.img_save264 = ImageTk.PhotoImage(Image.open("ams_jetcis/button_icons/videorecord_start.png").resize((32, 32), Image.ANTIALIAS))
        self.img_save264stop = ImageTk.PhotoImage(Image.open("ams_jetcis/button_icons/videorecord_stop.png").resize((32, 32), Image.ANTIALIAS))
        self.button_save264 = tkinter.Button(self.buttonArea, image=self.img_save264, activebackground="#00ADFD",
                                               bg="#FDF6F1", highlightthickness = 0, bd=0, command=self.save_video_callback) # H264 disable with , state=tkinter.DISABLED
        self.button_save264.grid(row=0, column=4, padx=(0,5))
        self.button_save264_ttp = CreateToolTip(self.button_save264, self.buttonArea,
                                                  "Save the presented video in H.264 (R)")

        # Fullscreen button
        self.img_fullscreen = ImageTk.PhotoImage(Image.open("ams_jetcis/button_icons/fullscreen.png").resize((32, 32), Image.ANTIALIAS))
        self.button_fullscreen = tkinter.Button(self.buttonArea, image=self.img_fullscreen, activebackground="#00ADFD",
                                                bg="#FDF6F1", highlightthickness = 0, bd=0, command=self.toggleFullscreen)
        self.button_fullscreen.grid(row=0, column=5, padx=(0,5))
        self.button_fullscreenm_ttp = CreateToolTip(self.button_fullscreen, self.buttonArea,
                                                    "Turn on full screen (F)")

        ###################
        # The BottomArea
        ###################
        # ams osram logo
        self.bottomArea = tkinter.ttk.Frame(self)
        self.bottomArea.grid(row=3, column=0, columnspan=2, sticky="sew")
        self.ams_logo_photo = ImageTk.PhotoImage(Image.open("./ams_jetcis/button_icons/logo.png").resize((200, 22), Image.ANTIALIAS))
        logo_label = tkinter.ttk.Label(self.bottomArea, image=self.ams_logo_photo)
        logo_label.pack(side="left")
        # /dev/video1 selection
        self.videorb2 = tkinter.ttk.Radiobutton(self.bottomArea)
        self.videorb2["text"] = "/dev/video1 "
        self.videorb2["value"] = 1
        self.videorb2["variable"] = self.videoDevice
        self.videorb2.pack(side="right")
        # /dev/video0 selection
        self.videorb1 = tkinter.ttk.Radiobutton(self.bottomArea)
        self.videorb1["text"] = "/dev/video0 "
        self.videorb1["value"] = 0
        self.videorb1["variable"] = self.videoDevice
        self.videorb1.pack(side="right")

        ##################
        # The LiveArea
        ##################
        self.liveArea = tkinter.LabelFrame(self)
        self.liveArea["text"] = "Image/Video"
        self.liveArea.grid(row=1, column=0, sticky="nesw")
        self.liveCanvas = tkinter.Canvas(self.liveArea, bg="#1D252D")
        self.liveCanvas.bind("<Button-1>", self.liveCanvasScroll)
        self.liveCanvas.bind("<B1-Motion>", self.liveCanvasScroll)
        self.liveCanvas.bind("<ButtonRelease-1>", self.liveCanvasScrollStop)
        self.liveCanvas.bind("<Button-4>", self.liveCanvasScaleUp)
        self.liveCanvas.bind("<Button-5>", self.liveCanvasScaleDown)
        self.liveCanvas.pack(expand=True, fill="both")

        ###################
        # The StatusArea
        ###################
        self.statusArea = tkinter.LabelFrame(self)
        self.statusArea["text"] = "Status"
        self.statusArea.grid(row=2, column=0, sticky="nesw")
        self.statusScroll = tkinter.Scrollbar(self.statusArea)
        self.statusScroll.pack(side="right", fill="y")
        self.statusText = tkinter.Text(self.statusArea, height=6)
        self.statusText.pack(side="left", fill="both", expand=True)
        self.statusScroll.config(command=self.statusText.yview)
        self.statusText.config(yscrollcommand=self.statusScroll.set)
        self.statusText.insert(tkinter.END, "Logging started\n")
        self.statusText.insert(tkinter.END, "Open sensor config to start\n")
        self.statusText.configure(state="disabled")
        self.statusText.bind("<Button-3>", self.TextPopup)

        ###################
        # The ControlArea
        ###################
        self.controlBook = Notebook(self)
        self.controlBook.grid(row=1, column=1, rowspan=2, sticky="nsew")
        # we need also a Sync Panel (not on Nano systems that do not have sync functionality)
        if(self.systype != "Nano"):
            self.syncArea = tkinter.Frame(self)
            self.controlBook.add(self.syncArea, text="Sync")
            lf = tkinter.LabelFrame(self.syncArea)
            lf["text"] = "Sync0 (in fps, 0=off)"
            lf.pack(side="top")
            self.sliderSync0 = tkinter.Scale(lf, length=200, orient=tkinter.HORIZONTAL, command=self.setSync0)
            self.sliderSync0["from"] = 0
            self.sliderSync0["to"] = 100
            self.sliderSync0["resolution"] = 1
            self.sliderSync0.set(0)
            self.sliderSync0.pack()
            if(os.getuid() == 0):
                lf = tkinter.LabelFrame(self.syncArea)
                lf["text"] = "Sync1 (in fps, 0=off)"
                lf.pack(side="top")
                self.sliderSync0 = tkinter.Scale(lf, length=200, orient=tkinter.HORIZONTAL, command=self.setSync1)
                self.sliderSync0["from"] = 0
                self.sliderSync0["to"] = 100
                self.sliderSync0["resolution"] = 1
                self.sliderSync0.set(0)
                self.sliderSync0.pack()
        # and a status area
        self.statArea = tkinter.Frame(self.controlBook)
        self.statArea.pack(side="top", fill='both', expand=True)
        self.controlBook.add(self.statArea, text=f'{"Status": ^7s}')
        # FPS Sensor
        self.actFPS = tkinter.ttk.Label(self.statArea)
        self.actFPS["text"] = "FPS sensor: ???"
        self.actFPS.pack(side="top", anchor="w")
        # Resolution
        self.Resdisp = tkinter.ttk.Label(self.statArea)
        self.Resdisp["text"] = "Resolution: ??? x ???"
        self.Resdisp.pack(side="top", anchor="w")
        # Bits per Pixel
        self.BPPdisp = tkinter.ttk.Label(self.statArea)
        self.BPPdisp["text"] = "Bits per Pixel: ???"
        self.BPPdisp.pack(side="top", anchor="w")
        # Sensor Name
        self.Namedisp = tkinter.ttk.Label(self.statArea)
        self.Namedisp["text"] = "Sensor Name: ???"
        self.Namedisp.pack(side="top", anchor="w")
        # Sensor I2C
        self.I2Cdisp = tkinter.ttk.Label(self.statArea)
        self.I2Cdisp["text"] = "Sensor I2C address: ???"
        self.I2Cdisp.pack(side="top", anchor="w")
        # Sensor Color
        self.Colordisp = tkinter.ttk.Label(self.statArea)
        self.Colordisp["text"] = "Sensor Color: ???"
        self.Colordisp.pack(side="top", anchor="w")
        # System Type
        self.Systypedisp = tkinter.ttk.Label(self.statArea)
        self.Systypedisp["text"] = "System Type: nVidia Jetson {}".format(self.systype)
        self.Systypedisp.pack(side="top", anchor="w")
        # System Temperature
        self.Systempdisp = tkinter.ttk.Label(self.statArea)
        self.Systempdisp["text"] = "System Temperature: {}°C".format(self.temp)
        self.Systempdisp.pack(side="top", anchor="w")
        # Video Pipe
        self.Pipedisp = tkinter.ttk.Label(self.statArea)
        self.Pipedisp["text"] = "Video Pipeline: ???"
        self.Pipedisp.pack(side="top", anchor="w")
        # Board Type
        self.Typedisp = tkinter.ttk.Label(self.statArea)
        self.Typedisp["text"] = "Board Type: ???"
        self.Typedisp.pack(side="top", anchor="w")
        # Board ID
        self.Iddisp = tkinter.ttk.Label(self.statArea)
        self.Iddisp["text"] = "Board ID: ???"
        self.Iddisp.pack(side="top", anchor="w")
        # Board Serial No.
        self.Serialdisp = tkinter.ttk.Label(self.statArea)
        self.Serialdisp["text"] = "Board Serial-No.: ??-??-??-??"
        self.Serialdisp.pack(side="top", anchor="w")
        # INA260 power sensor
        self.Powerdisp = tkinter.ttk.Label(self.statArea)
        self.Powerdisp["text"] = "Sensorboard power: ?.???W"
        self.Powerdisp.pack(side="top", anchor="w")
        
        ######################################
        # ISP controls
        ######################################
        self.ispArea = tkinter.Frame(self.controlBook)
        self.controlBook.add(self.ispArea, text=f'{"ISP": ^7s}')
        
        lf = tkinter.LabelFrame(self.ispArea)
        lf["text"] = "Rotation"
        lf.pack(side="top", anchor="w", fill=tkinter.X)
        self.rotList = ["No rotation", "90 degrees", "180 degrees", "270 degrees", "Horizontal flip", "Upper right diagonal flip", "Vertical flip", "Upper-left diagonal"]
        self.isprot = tkinter.StringVar()
        self.isprot.set(str(self.config["ISP"]["rot"]))
        self.rot = self.rotList.index(str(self.config["ISP"]["rot"]))
        self.ROTispArea = tkinter.ttk.OptionMenu(lf, self.isprot, str(self.config["ISP"]["rot"]),
                                                *self.rotList, command=self.setROT)
        self.ROTispArea.pack(side="top", anchor="w", fill=tkinter.X)
        
        lf = tkinter.LabelFrame(self.ispArea)
        lf["text"] = "Noise Reduction"
        lf.pack(side="top", anchor="w", fill=tkinter.X)
        self.tnrList = ["off", "fast"]
        self.isptnr = tkinter.StringVar()
        self.isptnr.set(str(self.config["ISP"]["tnr"]))
        self.TNRispArea = tkinter.ttk.OptionMenu(lf, self.isptnr, str(self.config["ISP"]["tnr"]),
                                                *self.tnrList, command=self.setTNR)
        self.TNRispArea.pack(side="top", anchor="w", fill=tkinter.X)
            
        self.isptnrstrength = tkinter.DoubleVar()
        self.isptnrstrength.set(float(self.config["ISP"]["tnr_strength"]))
        self.TNRSTRENGTHispArea = tkinter.Scale(lf, length=200, orient=tkinter.HORIZONTAL, variable=self.isptnrstrength,
                                                highlightthickness=0,troughcolor="#FECAB2")
        self.TNRSTRENGTHispArea.config(command=self.setTNRSTRENGTH)
        self.TNRSTRENGTHispArea["from_"] = -1
        self.TNRSTRENGTHispArea["to"] = 1
        self.TNRSTRENGTHispArea["resolution"] = 0.01
        self.TNRSTRENGTHispArea.set(float(self.config["ISP"]["tnr_strength"]))
        self.TNRSTRENGTHispArea.pack(side="left", anchor="w", fill='x', expand='yes', padx=(2, 6))
        self.TNRSTRENGTHentry = tkinter.ttk.Label(lf, textvariable=self.isptnrstrength, width=6)
        self.TNRSTRENGTHentry.pack(side='right')

        lf = tkinter.LabelFrame(self.ispArea)
        lf["text"] = "Edge Enhancement"
        lf.pack(side="top", anchor="w", fill=tkinter.X)
        self.eeList = ["off", "fast", "HQ"]
        self.ispee = tkinter.StringVar()
        self.ispee.set(str(self.config["ISP"]["ee"]))
        self.EEispArea = tkinter.ttk.OptionMenu(lf, self.ispee, str(self.config["ISP"]["ee"]),
                                                *self.eeList, command=self.setEE)
        self.EEispArea.pack(side="top", anchor="w", fill=tkinter.X)
        
        self.ispeestrength = tkinter.DoubleVar()
        self.ispeestrength.set(float(self.config["ISP"]["ee_strength"]))
        self.EESTRENGTHispArea = tkinter.Scale(lf, length=200, orient=tkinter.HORIZONTAL, variable=self.ispeestrength,
                                                highlightthickness=0,troughcolor="#FECAB2")
        self.EESTRENGTHispArea.config(command=self.setEESTRENGTH)
        self.EESTRENGTHispArea["from_"] = -1
        self.EESTRENGTHispArea["to"] = 1
        self.EESTRENGTHispArea["resolution"] = 0.01
        self.EESTRENGTHispArea.set(float(self.config["ISP"]["ee_strength"]))
        self.EESTRENGTHispArea.pack(side="left", anchor="w", fill='x', expand='yes', padx=(2, 6))
        self.EESTRENGTHentry = tkinter.ttk.Label(lf, textvariable=self.ispeestrength, width=6)
        self.EESTRENGTHentry.pack(side='right')

        lf = tkinter.LabelFrame(self.ispArea)
        lf["text"] = "Digital Gain (AGC)"
        lf.pack(side="top", anchor="w", fill=tkinter.X)
        self.dgainList = ["off", "on"]
        self.ispdgain = tkinter.StringVar()
        self.ispdgain.set(str(self.config["ISP"]["dgain"]))
        self.DGAINispArea = tkinter.ttk.OptionMenu(lf, self.ispdgain, str(self.config["ISP"]["dgain"]),
                                                    *self.dgainList, command=self.setDGAIN)
        self.DGAINispArea.pack(side="top", anchor="w", fill=tkinter.X)
        
        lf = tkinter.LabelFrame(self.ispArea)
        lf["text"] = "White balance"
        lf.pack(side="top", anchor="w", fill=tkinter.X)
        self.wbmodeList = ['off', 'auto', 'incandescent', 'fluorescent', 'warm-fluorescent', 'daylight', 'cloudy-daylight', 'twilight', 'shade', 'manual']
        self.ispwbmode = tkinter.StringVar()
        self.ispwbmode.set(str(self.config["ISP"]["wbmode"]))
        self.WBMODEispArea = tkinter.ttk.OptionMenu(lf, self.ispwbmode, str(self.config["ISP"]["wbmode"]), 
                                                    *self.wbmodeList, command=self.setWBMODE)
        self.WBMODEispArea.pack(side="top", anchor="w", fill=tkinter.X)

        lf = tkinter.LabelFrame(self.ispArea)
        lf["text"] = "Contrast"
        lf.pack(side="top", anchor="w", fill=tkinter.X)
        self.ispcontrast = tkinter.DoubleVar()
        self.ispcontrast.set(int(self.config["ISP"]["contrast"]))
        self.CONTRASTispArea = tkinter.Scale(lf, length=200, orient=tkinter.HORIZONTAL, variable=self.ispcontrast,
                                                highlightthickness=0,troughcolor="#FECAB2")
        self.CONTRASTispArea.config(command=self.setCONTRAST)
        self.CONTRASTispArea["from_"] = -1000
        self.CONTRASTispArea["to"] = 1000
        self.CONTRASTispArea["resolution"] = 10
        self.CONTRASTispArea.pack(side="left", anchor="w", fill='x', expand='yes', padx=(2, 6))
        self.CONTRASTentry = tkinter.ttk.Label(lf, textvariable=self.ispcontrast, width=6)
        self.CONTRASTentry.pack(side='right')

        lf = tkinter.LabelFrame(self.ispArea)
        lf["text"] = "Brightness"
        lf.pack(side="top", anchor="w", fill=tkinter.X)
        self.ispbrightness = tkinter.DoubleVar()
        self.ispbrightness.set(int(self.config["ISP"]["brightness"]))
        self.BRIGHTNESSispArea = tkinter.Scale(lf, length=200, orient=tkinter.HORIZONTAL, variable=self.ispbrightness,
                                                highlightthickness=0,troughcolor="#FECAB2")
        self.BRIGHTNESSispArea.config(command=self.setBRIGHTNESS)
        self.BRIGHTNESSispArea["from_"] = -1000
        self.BRIGHTNESSispArea["to"] = 1000
        self.BRIGHTNESSispArea["resolution"] = 10
        self.BRIGHTNESSispArea.pack(side="left", anchor="w", fill='x', expand='yes', padx=(2, 6))
        self.BRIGHTNESSentry = tkinter.ttk.Label(lf, textvariable=self.ispbrightness, width=6)
        self.BRIGHTNESSentry.pack(side='right')

        #######################
        # Tools area
        #######################
        self.toolsArea = ScrollFrame(self.controlBook)
        self.toolsArea.pack_propagate(False)
        self.controlBook.add(self.toolsArea, text=f'{"Tools": ^7s}')
                 
        # Histogram
        self.histframe = ToggledFrame(self.toolsArea.viewPort, self.pipelineOverlay, text='Histogram', relief="raised", borderwidth=1)
        self.histframe.pack(fill="x", side="top", anchor="w")
        f = Figure(figsize=(7,5), dpi=60)
        self.histplot = f.add_subplot(111)
        self.hplotdata, = self.histplot.plot([0,255], [0,0], "#FD5000")
        self.histplot.set_xlabel('Pixel value')
        self.histplot.set_ylabel('Occurrence')
        self.histplot.set_xlim(left=0, right=256)
        self.histplot.set_ylim(bottom=0.0, top=1.0)
        self.histplot.set_facecolor("#FDF6F1")
        self.histcanvas = FigureCanvasTkAgg(f, self.histframe.sub_frame)
        self.histcanvas.draw()
        toolbar = NavigationToolbar2TkAgg(self.histcanvas, self.histframe.sub_frame)
        toolbar.children["!button2"].pack_forget()
        toolbar.children["!button3"].pack_forget()
        toolbar.children["!button6"].pack_forget()
        self.histcanvas.get_tk_widget().pack(side="top", anchor="w")

        # Waveform horizontal
        self.waveframe_h = ToggledFrame(self.toolsArea.viewPort, self.pipelineOverlay, text='Horizontal waveform', relief="raised", borderwidth=1)
        self.waveframe_h.pack(fill="x", side="top", anchor="w")
        f = Figure(figsize=(7,5), dpi=60)
        self.waveplot_h = f.add_subplot(111)
        self.wplotdata_h, = self.waveplot_h.plot([0,255], [0,255], "#FD5000")
        self.waveplot_h.set_xlabel('X-Position')
        self.waveplot_h.set_ylabel('Pixel value')
        self.waveplot_h.set_xlim(left=0, right=256)
        self.waveplot_h.set_ylim(bottom=0.0, top=256)
        self.waveplot_h.set_facecolor("#FDF6F1")
        self.wavecanvas_h = FigureCanvasTkAgg(f, self.waveframe_h.sub_frame)
        self.wavecanvas_h.draw()
        toolbar = NavigationToolbar2TkAgg(self.wavecanvas_h, self.waveframe_h.sub_frame)
        toolbar.children["!button2"].pack_forget()
        toolbar.children["!button3"].pack_forget()
        toolbar.children["!button6"].pack_forget()
        self.wavecanvas_h.get_tk_widget().pack(side="top", anchor="w")
        
        # Waveform vertical
        self.waveframe_v = ToggledFrame(self.toolsArea.viewPort, self.pipelineOverlay, text='Vertical waveform', relief="raised", borderwidth=1)
        self.waveframe_v.pack(fill="x", side="top", anchor="w")
        f = Figure(figsize=(7,5), dpi=60)
        self.waveplot_v = f.add_subplot(111)
        self.wplotdata_v, = self.waveplot_v.plot([0,255], [0,255], "#FD5000")
        self.waveplot_v.set_xlabel('Pixel value')
        self.waveplot_v.set_ylabel('Y-Position')
        self.waveplot_v.set_xlim(left=0, right=256)
        self.waveplot_v.set_ylim(bottom=0, top=256)
        self.waveplot_v.set_facecolor("#FDF6F1")
        self.wavecanvas_v = FigureCanvasTkAgg(f, self.waveframe_v.sub_frame)
        self.wavecanvas_v.draw()
        toolbar = NavigationToolbar2TkAgg(self.wavecanvas_v, self.waveframe_v.sub_frame)
        toolbar.children["!button2"].pack_forget()
        toolbar.children["!button3"].pack_forget()
        toolbar.children["!button6"].pack_forget()
        self.wavecanvas_v.get_tk_widget().pack(side="top", anchor="w")

        # Column profile
        self.colprofileframe = ToggledFrame(self.toolsArea.viewPort, self.pipelineOverlay, text='Column profile', relief="raised", borderwidth=1)
        self.colprofileframe.pack(fill="x", side="top", anchor="w")
        f = Figure(figsize=(7,5), dpi=60)
        self.colprofileplot = f.add_subplot(111)
        self.cpplotdata, = self.colprofileplot.plot([0,255], [0,255], "#FD5000")
        self.colprofileplot.set_xlabel('X-Position')
        self.colprofileplot.set_ylabel('Profile value')
        self.colprofileplot.set_xlim(left=0, right=256)
        self.colprofileplot.set_ylim(bottom=0.0, top=256)
        self.colprofileplot.set_facecolor("#FDF6F1")
        self.colprofilecanvas = FigureCanvasTkAgg(f, self.colprofileframe.sub_frame)
        self.colprofilecanvas.draw()
        toolbar = NavigationToolbar2TkAgg(self.colprofilecanvas, self.colprofileframe.sub_frame)
        toolbar.children["!button2"].pack_forget()
        toolbar.children["!button3"].pack_forget()
        toolbar.children["!button6"].pack_forget()
        self.colprofilecanvas.get_tk_widget().pack(side="top", anchor="w")

        # Row profile
        self.rowprofileframe = ToggledFrame(self.toolsArea.viewPort, self.pipelineOverlay, text='Row profile', relief="raised", borderwidth=1)
        self.rowprofileframe.pack(fill="x", side="top", anchor="w")
        f = Figure(figsize=(7,5), dpi=60)
        self.rowprofileplot = f.add_subplot(111)
        self.rpplotdata, = self.rowprofileplot.plot([0,255], [0,255], "#FD5000")
        self.rowprofileplot.set_xlabel('Profile value')
        self.rowprofileplot.set_ylabel('Y-Position')
        self.rowprofileplot.set_xlim(left=0, right=256)
        self.rowprofileplot.set_ylim(bottom=0, top=256)
        self.rowprofileplot.set_facecolor("#FDF6F1")
        self.rowprofilecanvas = FigureCanvasTkAgg(f, self.rowprofileframe.sub_frame)
        self.rowprofilecanvas.draw()
        toolbar = NavigationToolbar2TkAgg(self.rowprofilecanvas, self.rowprofileframe.sub_frame)
        toolbar.children["!button2"].pack_forget()
        toolbar.children["!button3"].pack_forget()
        toolbar.children["!button6"].pack_forget()
        self.rowprofilecanvas.get_tk_widget().pack(side="top", anchor="w")

        #####################
        # Sensor controls
        #####################
        self.controlArea = tkinter.Frame(self.controlBook) # not added

        
    def videoSrcDisable(self):
        self.videorb1["state"] = "disabled"
        self.videorb2["state"] = "disabled"

    def videoSrcEnable(self):
        self.videorb1["state"] = "active"
        self.videorb2["state"] = "active"

    def videoSrcSet(self, port):
        self.videoDevice.set(int(port))

    def setROT(self, text):
        try:
            self.rot = self.rotList.index(self.isprot.get())
            self.stopLive() # cannot dynamically change when rotated 90 or 270 degrees because width and height are swapped. So restarting pipeline
            self.startLive()
        except:
            pass

    def setTNR(self, text):
        try:
            self.src.set_property("tnr-mode", self.tnrList.index(text))
        except AttributeError:
            pass
        except:
            raise
    
    def setTNRSTRENGTH(self, number):
        try:
            self.src.set_property("tnr-strength", float(number))
        except AttributeError:
            pass
        except:
            raise

    def setEE(self, text):
        try:
            self.src.set_property("ee-mode", self.eeList.index(text))
        except AttributeError:
            pass
        except:
            raise

    def setEESTRENGTH(self, number):
        try:
            self.src.set_property("ee-strength", float(number))
        except AttributeError:
            pass
        except:
            raise

    def setDGAIN(self, text):
        if (text == "off"):
            dgain = "1 1"
        else:
            dgain = "1 8"
        try:
            self.src.set_property("ispdigitalgainrange", dgain)
        except AttributeError:
            pass
        except:
            raise

    def setWBMODE(self, text):
        try:
            self.src.set_property("wbmode", self.wbmodeList.index(text))
        except AttributeError:
            pass
        except:
            raise
        
    def setCONTRAST(self, number):
        try:
            self.sink.set_property("contrast", int(number))
        except AttributeError:
            pass
        except:
            raise

    def setBRIGHTNESS(self, number):
        try:
            self.sink.set_property("brightness", int(number))
        except AttributeError:
            pass
        except:
            raise

    def TextPopup(self, event):
        try:
            self.menuText.tk_popup(event.x_root, event.y_root, 0)
        finally:
#            self.menuText.grab_release()
            pass

    def updateLiveDimensions(self):
#        self.liveCanvas.config(width=self.w, height=self.h)
#        self.liveCanvas.pack()
        pass

    def register_dump(self, event=None):     
        now = datetime.now()
        filename = now.strftime("regdump_%m-%d-%Y_%H%M%S.txt")
        self.path = os.path.expanduser(str(self.config["File"]["path"]))
        self.path = os.path.abspath(self.path)
        path = (self.path.encode("ascii","ignore"))
        try:
            path = tkinter.filedialog.askdirectory(initialdir=path)
        except:
            self.statusAddLine("Unable to open Path")
            return
        if (not path):
            self.statusAddLine("Unable to open Path")
            return

        self.statusAddLine("Creating register dump")
        self.imager.disablePrint()
        try:
            d = self.sensor.read_all_registers(dtype='hex')
            df = pd.DataFrame.from_dict(d, orient='index')
            with open(path + "/" + filename, 'w') as f:
                df.to_csv(f, header=False, index=True, mode='a')
            self.statusAddLine("Finished register dump")
        except:
            self.statusAddLine("Register dump not implemented")
        self.imager.enablePrint()
            

    def toggleFullscreen(self, event=None):
        if self.fullscreen == True:
            self.fullscreen = False        
            self.liveCanvas.config(width=500, height=280)
            self.master.attributes("-fullscreen", False)
            self.master.attributes('-zoomed', False)
            self.root.geometry(f"{self.window_width}x{self.window_height}+{self.x_coordinate}+{self.y_coordinate-40}")
            self.master.update()
            self.master.config(menu=self.menuBar)
            self.buttonArea.grid(row=0, column=0, columnspan=2, sticky="new")
            self.bottomArea.grid(row=3, column=0, columnspan=2, sticky="sew")
            self.liveArea.grid(row=1, column=0, sticky="nesw")
            self.statusArea.grid(row=2, column=0, sticky="nesw")
            self.controlBook.grid(row=1, column=1, rowspan=2, sticky="nsew")            
        else:
            self.fullscreen = True
            self.master.attributes("-fullscreen", True)
            self.master.config(menu="")
            self.buttonArea.grid_forget()
            self.controlBook.grid_forget()
            self.statusArea.grid_forget()
            self.bottomArea.grid_forget()
            self.liveCanvas.config(width=self.screen_width, height=self.screen_height)
        self.statusAddLine("Fullscreen toggled")

    def exitFullscreen(self, event=None):
        if self.fullscreen == True:
            self.toggleFullscreen(event)

    def play_pause_callback(self, event=None):
        if self.video_mode is True:
            self.video_mode = False
            self.button_saveimage.config(state="disabled")
            self.button_save264.config(state="disabled")
            self.button_saveimageraw.config(state="disabled")
            self.button_playpause.config(image=self.img_play)
            self.button_playpause.image = self.img_play
            self.menuControl.entryconfigure(0, label="Play")
            self.button_playpause_ttp.set_text("Play the live video stream (P)")
            self.gstpipe.set_state(Gst.State.PAUSED)
        else:
            self.button_playpause.config(image=self.img_pause)
            self.button_playpause.image = self.img_pause
            self.menuControl.entryconfigure(0, label="Pause")
            self.button_playpause_ttp.set_text("Pause the live video stream (P)")
            self.video_mode = True
            self.button_saveimage.config(state="normal")
            self.button_save264.config(state="normal")
            self.button_saveimageraw.config(state="normal")
            self.gstpipe.set_state(Gst.State.PLAYING)



    def save_raw_callback(self, event=None):
        self.button_saveimage.config(state="disabled")
        self.button_save264.config(state="disabled")
        self.button_playpause.config(state="disabled")
        now = datetime.now()
        date_time_raw = now.strftime("recording_%m-%d-%Y_%H%M%S")
        self.path = os.path.expanduser(str(self.config["File"]["path"]))
        self.path = os.path.abspath(self.path)
        path = (self.path.encode("ascii","ignore"))
        try:
            path = tkinter.filedialog.askdirectory(initialdir=path)
        except:
            self.statusAddLine("Unable to open Path")
            self.button_saveimage.config(state="normal")
            self.button_save264.config(state="normal")
            self.button_playpause.config(state="normal")
            return
        if (not path):
            self.statusAddLine("Unable to open Path")
            self.button_saveimage.config(state="normal")
            self.button_save264.config(state="normal")
            self.button_playpause.config(state="normal")
            return
        try:
            self.statusAddLine("Saving Raw video")
            self.stopLive()
            self.imager.clearArgus()
            self.imager.saveTiff(path+"/"+date_time_raw, count=self.nb_raw_burst)
            self.statusAddLine("Restart Live Pipeline")
            self.startLive()
        except:
            
            pass
        self.button_saveimage.config(state="normal")
        self.button_save264.config(state="normal")
        self.button_playpause.config(state="normal")

    def save_image_callback(self, event=None):
        self.button_saveimageraw.config(state="disabled")
        self.button_save264.config(state="disabled")
        self.button_playpause.config(state="disabled")
        now = datetime.now()
        date_time_raw = now.strftime("recording_%m-%d-%Y_%H%M%S")
        self.path = os.path.expanduser(str(self.config["File"]["path"]))
        self.path = os.path.abspath(self.path)
        path = (self.path.encode("ascii","ignore"))
        try:
            path = tkinter.filedialog.askdirectory(initialdir=path)
        except:
            self.statusAddLine("Unable to open Path")
            self.button_saveimageraw.config(state="normal")
            self.button_save264.config(state="normal")
            self.button_playpause.config(state="normal")
            return
        if (not path):
            self.statusAddLine("Unable to open Path")
            self.button_saveimageraw.config(state="normal")
            self.button_save264.config(state="normal")
            self.button_playpause.config(state="normal")
            return
        try:
            self.statusAddLine("Saving Raw video")
            self.stopLive()
            self.imager.clearArgus()
            try:
                self.imager.saveTiff(path+"/"+date_time_raw, count=1)
            except Exception as e:
                self.statusAddLine("Error: Failed saving Tiff")
                print( "<p>Error: %s</p>" % e )
                raise e

            self.statusAddLine("Restart Live Pipeline")
            self.startLive()
        except Exception as e:
            self.statusAddLine("Error: Failed saving image callback")
            e = sys.exc_info()[0]
            print( "<p>Error: %s</p>" % e )
            raise e
            
        self.button_saveimageraw.config(state="normal")
        self.button_save264.config(state="normal")
        self.button_playpause.config(state="normal")

    def save_video_callback(self, event=None):
        if (self.recording == False):
            self.button_saveimage.config(state="disabled")
            self.button_saveimageraw.config(state="disabled")
            self.button_playpause.config(state="disabled")
            self.recording = True
            now = datetime.now()
            date_time = now.strftime("record_%m-%d-%Y_%H%M%S.avi")
            self.path = os.path.expanduser(str(self.config["File"]["path"]))
            self.path = os.path.abspath(self.path)
            path = (self.path.encode("ascii", "ignore"))
            try:
                path = tkinter.filedialog.askdirectory(initialdir=path)
            except:
                self.statusAddLine("Error: Invalid path")
                self.button_save264.config(image=self.img_save264)
                self.button_save264.image = self.img_save264
                self.button_saveimage.config(state="normal")
                self.button_saveimageraw.config(state="normal")
                self.button_playpause.config(state="normal")
                return
            if (not path):
                self.statusAddLine("Error: Invalid path")
                self.button_save264.config(image=self.img_save264)
                self.button_save264.image = self.img_save264
                self.button_saveimage.config(state="normal")
                self.button_saveimageraw.config(state="normal")
                self.button_playpause.config(state="normal")
                return
            try:
                self.statusAddLine("Saving Live video (H.264) started")
                fname = path + "/" + date_time
                # Change Record button to blinking and disable all other SAVE button
                # activate gstreamer pipeline
                self.stopLive()
                self.startLive(record=True, fname=fname)
                self.button_save264.config(image=self.img_save264stop)
                self.button_save264.image = self.img_save264stop
            except:
                pass
        else:
            self.recording = False
            self.stopLive()
            self.statusAddLine("Saving Live video (H.264) stopped")
            time.sleep(0.5)
            # deactivate button blinking and enable all other buttons
            self.button_save264.config(image=self.img_save264)
            self.button_save264.image = self.img_save264
            self.button_saveimage.config(state="normal")
            self.button_saveimageraw.config(state="normal")
            self.button_playpause.config(state="normal")
            self.statusAddLine("Saving Live video (H.264) done")
            time.sleep(0.5)
            self.startLive(record=False)
            time.sleep(0.5)
            self.statusAddLine("Live pipeline restarted")


    def set_nb_raw_burst(self):
        number = simpledialog.askinteger("Input",
                                         "How much burst images do you want to set?",
                                         parent=self,
                                         minvalue=1, 
                                         maxvalue=100)
        if number != None:
            self.nb_raw_burst = number


    def updateHistPlot(self, xplot, yplot):
        self.hplotdata.set_xdata(xplot)
        self.hplotdata.set_ydata(yplot)
        self.histcanvas.draw()

    def updateWaveHPlot(self, hline):
        w, = hline.shape
        plotx = np.linspace(0, (w-1), w)
        self.waveplot_h.set_xlim(left=0, right=w)
        self.wplotdata_h.set_xdata(plotx)
        self.wplotdata_h.set_ydata(hline)
        self.wavecanvas_h.draw()

    def updateWaveVPlot(self, vline):
        h, = vline.shape
        plotx = np.linspace(0, (h-1), h)
        self.waveplot_v.set_ylim(bottom=0, top=h)
        self.wplotdata_v.set_xdata(vline)
        self.wplotdata_v.set_ydata(plotx)
        self.waveplot_v.invert_yaxis()
        self.wavecanvas_v.draw()

    def updateColprofilePlot(self, hline):
        w, = hline.shape
        plotx = np.linspace(0, (w-1), w)
        self.colprofileplot.set_xlim(left=0, right=w)
        self.cpplotdata.set_xdata(plotx)
        self.cpplotdata.set_ydata(hline)
        self.colprofilecanvas.draw()

    def updateRowprofilePlot(self, vline):
        h, = vline.shape
        ploty = np.linspace(0, (h-1), h)
        self.rowprofileplot.set_ylim(bottom=0, top=h)
        self.rpplotdata.set_xdata(vline)
        self.rpplotdata.set_ydata(ploty)
        self.rowprofileplot.invert_yaxis()
        self.rowprofilecanvas.draw()

    def liveStatUpdate(self, fps):
        self.actFPS["text"] = fps
        try:
            self.sensorConfig
            self.Pipedisp["text"] = "Video Pipeline: " + self.sensorConfig["Sensor"]["gstInterface"]
            self.Colordisp["text"] = "Sensor Color: " + "Mono"#self.sensorConfig["Sensor"]["gstPipe"]
            self.I2Cdisp["text"] = "Sensor I2C address: 0x" + self.sensorConfig["Sensor"]["i2cID"]
            self.Namedisp["text"] = "Sensor Name: " + self.sensorConfig["Description"]["Name"]
        except:
            pass
        try:
            self.sensorInfo
            self.Resdisp["text"] = "Resolution: {}px x {}px".format(int(self.sensorInfo["width"]), int(self.sensorInfo["height"]))
            self.BPPdisp["text"] = "Bits per Pixel: {}bpp".format(int(self.sensorInfo["bpp"]))
        except:
            pass
        # All microcontroller stuff
        if(self.imager != None):
            # Update all important controller settings
            self.Typedisp["text"] = "Board Type: {}".format(self.board_type)
            self.Iddisp["text"] = "Board Id: {}".format(self.board_id)
            self.Serialdisp["text"] = "Board Serial-No.: {}".format(self.serial_no)
        # Read also system temperature
        try:
            self.temp = self.imager.getBoardTemp()
        except:
            pass
        self.Systempdisp["text"] = "System Temperature: {}°C".format(self.temp)
        # self.update()

    def liveCanvasScaleDown(self, event):
        if(self.scale > 1.0):
            self.scale = self.scale / 1.25
            self.updateScaler()
        else:
            self.posx = 0.5
            self.posy = 0.5

    def liveCanvasScaleUp(self, event):
        if self.factor == 0.25:
            if self.w < 160:
                max_scale = 3
            else:
                max_scale = 4
        elif self.factor == 0.5:
            max_scale = 8
        elif self.factor == 1:
            max_scale = 10
        elif self.factor == 2:
            max_scale = 6
        elif self.factor == 4:
            max_scale = 1.6
        else:
            # if display width is custom, take the most conservative max
            max_scale = 1.6

        resize_factor = 1.25
        if self.scale * resize_factor < max_scale:
            self.scale = self.scale * resize_factor
            self.updateScaler()

    def liveCanvasScroll(self, event):
        if (self.oldX == -1):
            self.oldX = event.x
            self.oldY = event.y
            return
        if(not self.streaming):
            return

        # calculate scroll direction
        move_x = (self.oldX - event.x) / self.sensor_w
        move_y = (self.oldY - event.y) / self.sensor_h
        self.oldX = event.x
        self.oldY = event.y
        self.posx = self.posx + move_x
        self.posy = self.posy + move_y
        # security checks
        if(self.posx < 0.0):
            self.posx = 0.0
        if(self.posx > 1.0):
            self.posx = 1.0
        if(self.posy < 0.0):
            self.posy = 0.0
        if(self.posy > 1.0):
            self.posy = 1.0
        self.updateScaler()

    def liveCanvasScrollStop(self, event):
        self.oldX = -1
        self.oldY = -1

    def statusAddLine(self, txt):
        self.statusText.configure(state="normal")
        self.statusText.insert(tkinter.END, "{}\n".format(txt))
        self.statusText.configure(state="disabled")
        self.statusText.see(tkinter.END)
        self.root.update()

    def statusClear(self):
        self.statusText.configure(state="normal")
        self.statusText.delete('1.0', END)
        self.statusText.configure(state="disabled")
        self.statusText.see(tkinter.END)
        self.root.update()

    def statusSave(self):
        path = os.path.expanduser(str(self.config["File"]["logpath"]))
        path = os.path.abspath(path)
        path = str(path.encode("ascii","ignore"))
        try:
            path = filedialog.askdirectory(initialdir=path)
        except:
            self.logger.error(str(e))
            return
        now = datetime.now()
        fname = now.strftime("log_%m-%d-%Y_%H%M%S.txt")
        fname = path + "/" + fname
        fout = open(fname, "wt")
        self.statusText.configure(state="normal")
        textout = self.statusText.get("1.0", "end-1c")
        fout.write(textout)
        fout.close()
        self.statusText.configure(state="disabled")
        self.statusText.see(tkinter.END)
        # self.root.update()


    def openSensorConfig(self, event=None):
        self.dialog = ChoiceDialog(self, 'Sensor selection', items=['Mira030', 'Mira050', 'Mira130', 'Mira220'],
                                    text='Which sensor is plugged in?')
        self.statusAddLine(f'Selected sensor is  {self.dialog.selection}')
        if self.dialog.selection == None:
            return
        #the new way, TBD


        #the old way    
        # Parse the sensor configuration
        self.sensorConfig = configparser.ConfigParser()
        self.sensorConfig.read(f'./ams_jetcis/sensors/{(self.dialog.selection.split("_")[0]).lower()}/{self.dialog.selection}.sensor')
        try:
            name = str(self.sensorConfig["Description"]["Name"])
            self.statusAddLine("Loading sensor configuration ({})".format(name))
        except:
            self.statusAddLine("Error: No or wrong config.cfg. Program will be terminated")
            return
        # Check for available video device
        self.port = int(self.videoDevice.get())
        if (self.checkPortAvail(self.port) == False):
            messagebox.showinfo("ERROR",
                                    "Unable to open sensor interface /dev/video{}\nIt is already opened by another program instance".format(self.port))
            return
        # check video pipeline
        try:
            self.iface = int(self.sensorConfig["Sensor"]["gstInterface"])
            self.noGst = True
#            self.port = self.iface
        except ValueError:
            self.iface = str(self.sensorConfig["Sensor"]["gstInterface"])
            self.noGst = False
#            self.port = 0

        # Check if selected sensor is supported by actual kernel and device tree
        try:
            self.i2c = self.sensorConfig["Sensor"]["i2cID"]
            self.i2c = int(self.i2c,16)
            self.statusAddLine(f'sensor i2c is {self.i2c}')
        except:
            self.i2c = 0
            self.statusAddLine(f'sensor i2c is {self.i2c}')
        
        # Open v4l2 interface
        self.imager = driver_access.ImagerTools(self.statusAddLine, self.port, self.rootPW)
        self.imager.initStatusCallback(self.liveStatUpdate)
        self.imager.setSystype(self.systype)

        if(self.i2c != 0):
            detected = False
            # check device tree
            # try:
                # fin = open("/boot/sensor.conf", "r")
                # for line in fin:
                #     if(re.match(r"(.*){}(.*)".format(name), line)):
                #         self.statusAddLine("Device tree is okay")
                #         print("Device tree is okay")
                #         detected = True
                # self.imager.kernel_dtb_manager.check_current_sensor()
            # except:
                # self.statusAddLine("Error: Unable to check device tree")
                # print("Error: unable to check device tree")
            if self.imager.kernel_dtb_manager.check_current_sensor(self.dialog.selection):
                print('incorrect dtb')
                if(messagebox.askyesno("INFO","Need to load new device tree for this sensor. Press YES to proceed. (recommended)") != True):
                    return(0)
                
                # Adjust the kernel configuration
                if(self.systype == "Nano"):
                    self.imager.kernel_dtb_manager.load_kernel_and_dtb(self.dialog.selection)

                    # program the new dtb
                    self.statusAddLine("Reprogramming DTB and kernel image")
                    # os.system("echo {} | sudo -S cp {} /boot/dtbnano.dtb".format(self.rootPW, self.sensorConfig["Sensor"]["DevtreeImgNano"]))
                    # # and also program the new kernel
                    # self.statusAddLine("Reprogramming kernel image")
                    # os.system("echo {} | sudo -S cp {} /boot/Image".format(self.rootPW, self.sensorConfig["Sensor"]["KernelImgNano"]))
                    # # and also program the new isp_overrides
                    # self.statusAddLine("Reprogramming camera overrides isp")
                    # os.system("echo {} | sudo -S cp {} /var/nvidia/nvcam/settings/camera_overrides.isp".format(self.rootPW, self.sensorConfig["Sensor"]["camera_overrides"]))
                    # # Update the sensor configuration
                    # self.statusAddLine("Updating sensor configuration")
                    # os.system("echo \"{}\" > /tmp/sensor.conf".format(name))
                    # os.system("echo {} | sudo -S cp /tmp/sensor.conf /boot/sensor.conf".format(self.rootPW))
                    messagebox.showinfo("INFO","Done.\nPlease reboot the OS to reload the kernel.")
                    self.endProgram()
                elif(self.systype == "TX2"):
                    messagebox.showinfo("ERROR","nVidia TX2 is not supported by the actual JetCis Software")
                    self.endProgram()
                    # program the new dtb
#                    self.statusAddLine("Reprogramming DTB image")
#                    os.system("dd if={} of=/dev/mmcblk0p30".format(self.sensorConfig["Sensor"]["DevtreeImg"]))
#                    # and also program the new kernel
#                    self.statusAddLine("Reprogramming kernel image")
#                    os.system("dd if={} of=/dev/mmcblk0p28".format(self.sensorConfig["Sensor"]["KernelImg"]))
#                    # Update the sensor configuration
#                    self.statusAddLine("Updating sensor configuration")
#                    os.system("echo \"{}\" > /boot/sensor.conf".format(name))
#                    messagebox.showinfo("INFO","Done.\nPlease restart the Software.")
#                    self.endProgram()
#                else:
                    messagebox.showinfo("ERROR","Unsupported nVidia Platform.")
                    self.endProgram()
                return(0)

        self.initSensor(self.sensorConfig["Sensor"]["defFormat"])


        # enable register dump menu item
        self.menuControl.entryconfigure(6, state=tkinter.NORMAL)
        # read some important board info
        self.imager.disablePrint()
        self.board_type = self.imager.getSensorType()
        self.board_id = self.imager.getSensorID()
        self.serial_no = self.imager.getBoardSerialNo()
        self.imager.enablePrint()
        # Prepare Control panel
        self.controlArea.destroy()
        self.controlArea = tkinter.Frame(self.controlBook)  
        self.controlArea.pack_propagate(False)      
        self.controlBook.add(self.controlArea, text=f'{"Sensor": ^7s}')
        # Prepare Sensor Format
        self.controlLabel1 = tkinter.LabelFrame(self.controlArea)
        self.controlLabel1["text"] = "Sensor Format:"
        self.controlLabel1.pack(fill=tkinter.X)
        self.controlFormat = tkinter.StringVar()
        self.controlFormat.set(self.sensorConfig["Sensor"]["defFormat"])
        self.controlFormatList = list()
        for key in self.sensorConfig["Format"]:
            self.controlFormatList.append(key)
        self.controlFormatSelect = tkinter.ttk.OptionMenu(self.controlLabel1, self.controlFormat, self.sensorConfig["Sensor"]["defFormat"],
                                                         *self.controlFormatList, command=self.initSensor)
        self.controlFormatSelect.pack(side="left")
        # Prepare Sensor Controls
        self.controlLabel2 = tkinter.LabelFrame(self.controlArea)
        self.controlLabel2["text"] = "Control Elements:"  
        self.controlLabel2.pack(fill=tkinter.X)
        self.widgetList = list()
        for key in self.sensorConfig["Control"]:
            fname = str(self.sensorConfig["Control"][key])
            fname = os.getcwd() + "/" + fname
            try:
                with open(fname, "r") as file:
                    eobj = compile(file.read(),fname, "exec")
                    exec(eobj, globals())
            except Exception as e:
                print(f"{type(e).__name__} at line {e.__traceback__.tb_lineno} of {__file__}: {e}")

                self.statusAddLine("Error: Control file problem (not found or buggy {}".format(fname))
            controlParams = controlInit()
            l = tkinter.LabelFrame(self.controlLabel2) 
            l["text"] = controlParams["name"] + " ({})".format(controlParams["unit"])
            l.pack(fill=tkinter.X)

            if(controlParams["type"] == "slider"):
                nb_w = controlParams["nb_widgets"]
                for w_i in range(1, nb_w + 1):
                    if nb_w == 1:
                        w_i_str = ""
                    else:
                        w_i_str = "_" + str(w_i)
                    sreg = tkinter.DoubleVar()
                    sreg.set(controlParams["default" + w_i_str])
                    s = tkinter.Scale(l, length=200//nb_w, orient=tkinter.HORIZONTAL, variable=sreg, highlightthickness=0,
                                    troughcolor="#FECAB2")
                    s.config(command=partial(eval("controlSet" + w_i_str), self, sreg))
                    s["from_"] = controlParams["min" + w_i_str]
                    s["to"] = controlParams["max" + w_i_str]
                    s["resolution"] = controlParams["step" + w_i_str]
                    s.set(controlParams["default" + w_i_str])
                    s.grid(row=0, column=2 * w_i - 2, padx=(2, 6))

                    sentry = tkinter.ttk.Label(l, textvariable=sreg, width=6)
                    sentry.grid(row=0, column=2 * w_i - 1, padx=(0, 10))

                    if controlParams["comment"]:
                        CreateToolTip(s, s, controlParams["comment"])                    
                        widget = [controlParams, sreg, s, partial(eval("controlGet" + w_i_str), self, s)]                    
                        if (("refresh" in controlParams) and (controlParams["refresh"] == True)):                        
                            self.widgetList.append(widget)                    
                        if (("auto" in controlParams) and (controlParams["auto"] == True)):                        
                            self.widgetAutoUpdate.append(widget)
            
            elif(controlParams["type"] == "list"):
                sreg = tkinter.IntVar()
                sreg.set(controlParams["default"])
                s = tkinter.Spinbox(l)
                s["values"] = controlParams["list"]
                s["textvariable"] =sreg
                s.pack(fill=tkinter.X)
                if controlParams["comment"]:
                    CreateToolTip(s, s, controlParams["comment"])
                widget = [controlParams, sreg, s, controlGet]
                self.widgetList.append(widget)

            elif (controlParams["type"] == "spinbox"):
                sreg = tkinter.DoubleVar()
                sreg.set(controlParams["default"])
                s = tkinter.Spinbox(l, width=12, textvariable=sreg, format="%.4f", command=partial(controlSet, self, sreg), validate='all',
                                    fg='#FDF6F1', bg='#FD5000', buttonbackground='#FD5000', 
                                    buttondownrelief=tkinter.SUNKEN, buttonup=tkinter.GROOVE)
                s["to"] = controlParams["max"]
                s["from_"] = controlParams["min"]
                s["increment"] = controlParams["step"]
                s.config(wrap=False)
                s.config(validatecommand=(s.register(partial(validate, s)), "%P"))
                s.grid(row=0, column=0, padx=(5, 85))
                s.bind("<Return>", partial(controlSet, self, sreg))
                s.bind("<KP_Enter>", partial(controlSet, self, sreg))
                s.bind("<FocusOut>", partial(controlGet, self, s, sreg))
                if controlParams["comment"]:
                    CreateToolTip(s, s, controlParams["comment"])
                widget = [controlParams, sreg, s, partial(controlGet, self, s, sreg)]
                self.widgetList.append(widget)

            elif (controlParams["type"] == "checkbutton"):
                checkvar = tkinter.BooleanVar()
                cb = tkinter.ttk.Checkbutton(l, variable=checkvar, command=partial(controlSet, self, checkvar), style='Roundtoggle.Toolbutton')
                cb["onvalue"] = controlParams["onvalue"]
                cb["offvalue"] = controlParams["offvalue"]
                cb.grid(row=0, column=0, padx=(5, 174))
                if controlParams["default"] == "on":
                    checkvar.set(bool("onvalue"))
                if controlParams["comment"]:
                    CreateToolTip(cb, cb, controlParams["comment"])                
                widget = [controlParams, checkvar, cb, partial(controlGet, self, checkvar)]
                self.widgetList.append(widget)

            elif (controlParams["type"] == "text_entry_read"):
                address_label = Label(l, text="Address:")
                address_label.grid(row=0, column=0)

                entryvar = tkinter.StringVar()
                entrybox = tkinter.Entry(l, textvariable=entryvar)
                entrybox.grid(row=0, column=1)
                entrybox.bind("<FocusIn>", partial(disableShortcuts, self.master))
                entrybox.bind("<FocusOut>", partial(enableShortcuts, self.master, self.toggleFullscreen))
                entrybox.config(width=10)
                entrybox.bind("<KP_Enter>", partial(controlSet, self.imager, entryvar, self.statusArea))
                entrybox.bind("<Return>", partial(controlSet, self.imager, entryvar, self.statusArea))
                CreateToolTip(entrybox, entrybox, "Address, e.g. 3E01")
                entrybutton = tkinter.ttk.Button(l, command=partial(controlSet, self.imager, entryvar, self.statusArea))
                entrybutton["text"] = controlParams["buttontext"]
                if controlParams["comment"]:
                    CreateToolTip(entrybutton, entrybutton, controlParams["comment"])
                entrybutton.grid(row=0, column=2, padx=(5, 0))

            elif (controlParams["type"] == "text_entry_write"):
                address_label = Label(l, text="Address:")
                address_label.grid(row=0, column=0)

                entryvar_address = tkinter.StringVar()
                entrybox_address = tkinter.Entry(l, textvariable=entryvar_address)
                entrybox_address.grid(row=0, column=1)
                entrybox_address.bind("<FocusIn>", partial(disableShortcuts, self.master))
                entrybox_address.bind("<FocusOut>", partial(enableShortcuts, self.master, self.toggleFullscreen))
                entrybox_address.config(width=10)
                CreateToolTip(entrybox_address, entrybox_address, "Address, e.g. 3E01")
                value_label = Label(l, text="Value:")
                value_label.grid(row=1, column=0, sticky=W)

                entryvar_value = tkinter.StringVar()
                entrybox_value = tkinter.Entry(l, textvariable=entryvar_value)
                entrybox_value.grid(row=1, column=1)
                entrybox_value.bind("<FocusIn>", partial(disableShortcuts, self.master))
                entrybox_value.bind("<FocusOut>", partial(enableShortcuts, self.master, self.toggleFullscreen))
                entrybox_value.config(width=10)
                CreateToolTip(entrybox_value, entrybox_value, "Value, e.g. 3C")
                entrybutton = tkinter.ttk.Button(l, command=partial(controlSet, self.imager, entryvar_address, entryvar_value,
                                                                self.statusArea))
                entrybutton["text"] = controlParams["buttontext"]
                entrybutton.grid(row=0, column=2, rowspan=2, padx=(5, 0))
                entrybox_address.bind("<KP_Enter>", partial(controlSet, self.imager, entryvar_address, entryvar_value,
                                                            self.statusArea))
                entrybox_address.bind("<Return>", partial(controlSet, self.imager, entryvar_address, entryvar_value,
                                                          self.statusArea))
                entrybox_value.bind("<KP_Enter>", partial(controlSet, self.imager, entryvar_address, entryvar_value,
                                                          self.statusArea))
                entrybox_value.bind("<Return>", partial(controlSet, self.imager, entryvar_address, entryvar_value,
                                                        self.statusArea))

            elif (controlParams["type"] == "checkbutton_and_slider"):
                sreg = tkinter.DoubleVar()
                sreg.set(controlParams["slider_default"])
                s = tkinter.Scale(l, length=165, orient=tkinter.HORIZONTAL, variable=sreg, highlightthickness=0,
                                    troughcolor="#FECAB2")
                s.config(command=partial(controlSetSlider, self, sreg))
                s["from_"] = controlParams["min"]
                s["to"] = controlParams["max"]
                s["resolution"] = controlParams["step"]
                s.set(controlParams["slider_default"])
                s["state"] = controlParams["slider_default_state"]
                s.grid(row=0, column=1, padx=(2, 6))
                    
                sentry = tkinter.ttk.Label(l, textvariable=sreg, width=6)
                sentry.grid(row=0, column=2)

                checkvar = tkinter.BooleanVar()
                cb = tkinter.ttk.Checkbutton(l, variable=checkvar, style='Roundtoggle.Toolbutton',
                                         command=partial(controlSetCheckbutton, self, checkvar))
                cb["onvalue"] = controlParams["onvalue"]
                cb["offvalue"] = controlParams["offvalue"]
                cb.grid(row=0, column=0, padx=5)
                if controlParams["comment"]:
                    CreateToolTip(s, s, controlParams["comment"])
                if controlParams["comment"]:
                    CreateToolTip(cb, cb, controlParams["comment"])
                if controlParams["checkbutton_default"] == "on":
                    checkvar.set(bool("onvalue"))
                widget = [controlParams, sreg, s, partial(controlGetSlider, self, sreg), checkvar, cb, partial(controlGetCheckbutton, self, checkvar)]
                self.widgetList.append(widget)

            elif (controlParams["type"] == "two_checkbuttons"):
                checkvar1 = tkinter.BooleanVar()
                cb1 = tkinter.ttk.Checkbutton(l, variable=checkvar1, command=partial(controlSetCb1, self, checkvar1), style='Roundtoggle.Toolbutton')
                cb1["onvalue"] = controlParams["cb1_onvalue"]
                cb1["offvalue"] = controlParams["cb1_offvalue"]
                cb1.grid(row=0, column=1, padx=controlParams["cb1_xpad"])
                if controlParams["cb1_default"] == "on":
                    cb1.select()

                checkvar2 = tkinter.BooleanVar()
                cb2 = tkinter.ttk.Checkbutton(l, variable=checkvar2, command=partial(controlSetCb2, self, checkvar2), style='Roundtoggle.Toolbutton')
                cb2["onvalue"] = controlParams["cb2_onvalue"]
                cb2["offvalue"] = controlParams["cb2_offvalue"]
                cb2.grid(row=0, column=3, padx=controlParams["cb2_xpad"])
                if controlParams["cb2_default"] == "on":
                    cb2.select()

                cb1_label = Label(l, text=controlParams["cb1_label_text"])
                cb1_label.grid(row=0, column=0)

                cb2_label = Label(l, text=controlParams["cb2_label_text"])
                cb2_label.grid(row=0, column=2)
                widget = [controlParams, checkvar1, cb1, partial(controlGetCb1, self, checkvar1), checkvar2, cb2, partial(controlGetCb2, self, checkvar2)]
                self.widgetList.append(widget)

            elif (controlParams["type"] == "optionmenu"):
                nb_w = controlParams["nb_widgets"]
                for w_i in range(1, nb_w + 1):
                    omvar = tkinter.StringVar()
                    omvar.set(controlParams["default_" + str(w_i)])
                    om = tkinter.ttk.OptionMenu(l, omvar, controlParams["default_" + str(w_i)], 
                                            *controlParams["option_list_" + str(w_i)],
                                            command=partial(eval("controlSet_" + str(w_i)), self, omvar))
                    om.grid(row=0, column=w_i-1, padx=(0, 5))
                    if controlParams["comment"]:
                        CreateToolTip(om, om, controlParams["comment"])
                    widget = [controlParams, omvar, om, partial(eval("controlGet_" + str(w_i)), self, omvar)]
                    self.widgetList.append(widget)

            elif (controlParams["type"] == "label"):
                slvar = tkinter.StringVar()
                sl = Label(l, textvariable=slvar)
                slvar.set(controlParams["label_text"])
                sl.grid(row=0, column=0)
                if controlParams["comment"]:
                    CreateToolTip(sl, sl, controlParams["comment"])
                widget = [controlParams, slvar, sl, partial(controlGet, self, slvar)]
                if (("refresh" in controlParams) and (controlParams["refresh"] == True)):
                    self.widgetList.append(widget)
                if (("auto" in controlParams) and (controlParams["auto"] == True)):
                    self.widgetAutoUpdate.append(widget)

            else:
                self.statusAddLine("Undefined")

        # Prepare addition Batch scripts
        self.controlLabel3 = tkinter.LabelFrame(self.controlArea)
        self.controlLabel3["text"] = "Additional Batch scripts:"
        self.controlLabel3.pack()
        self.controlBatchList = list()
        for key in self.sensorConfig["Batch"]:
            self.controlBatchList.append(key)
            b = tkinter.ttk.Button(self.controlLabel3, command=partial(self.execBatch, key))
            b["text"] = key
            b.pack()
        # select the right tab
        self.controlBook.select(self.controlArea)
        # enable tools expand buttons
        self.histframe.toggle_button.config(state="normal")
        self.waveframe_h.toggle_button.config(state="normal")
        self.waveframe_v.toggle_button.config(state="normal")
        self.colprofileframe.toggle_button.config(state="normal")
        self.rowprofileframe.toggle_button.config(state="normal")
        # and finally init the Sensor


    def initSensor(self, sensFormat):
        self.statusAddLine("Sensor initialization started ({})".format(sensFormat))
        if (self.streaming == True):
            self.statusAddLine("Stopping live feed")
            self.streaming = False
            self.stopLive()
        # Execute sensor initialization script
        old_code = 0
        if old_code:
            fname = str(self.sensorConfig["Format"][sensFormat])
            fname = os.getcwd() + "/" + fname
            try:
                with open(fname, "r") as file:
                    eobj = compile(file.read(), fname, "exec")
                    exec(eobj, globals())

            except:
                self.statusAddLine("Error: Control file problem (not found or buggy {}".format(fname))
            # Execute all settings scripts
            self.root.config(cursor="clock") # show the clock cursor
            self.sensorInfo = getSensorInfo(self.imager)
            self.sensor_w = int(self.sensorInfo["width"])
            self.sensor_h = int(self.sensorInfo["height"])
            self.sensor_wdma = int(self.sensorInfo["widthDMA"])
            self.sensor_hdma = int(self.sensorInfo["heightDMA"])
            self.w = int(self.sensorInfo["widthDISP"])
            self.h = int(self.sensorInfo["heightDISP"])
            self.updateLiveDimensions()
            self.sensor_fps = int(self.sensorInfo["fps"])
            self.sensor_mode = int(self.sensorInfo["dtMode"])
            self.bpp = self.sensorInfo["bpp"]
            try:
                resetSensor(self.imager)
                initSensor(self.imager)
            except IOError:
                messagebox.showinfo("ERROR", "The image sensor is not reacting on I2C.\nPlease check for correct video interface selection and functional hardware.")
                self.endProgram()
        else:
            if self.dialog.selection == 'Mira050':
                self.sensor = Mira050(imagertools = self.imager)
            elif self.dialog.selection == 'Mira220':
                self.sensor = Mira220(imagertools = self.imager)
            elif self.dialog.selection == 'Mira130':
                self.sensor = Mira130(imagertools = self.imager)
            elif self.dialog.selection == 'Mira030':
                self.sensor = Mira030(imagertools = self.imager)
            else:
                raise NotImplementedError('sensor unknown')
            self.imager.disablePrint()
            try:
                sensor_NOK = self.sensor.cold_start()
            except IOError:
                messagebox.showinfo("ERROR", "The image sensor is not reacting on I2C.\nPlease check for correct video interface selection and functional hardware.")
                self.endProgram()

            if self.dialog.selection == 'Mira030':
                sensFormatParsed = sensFormat.split('_')
                nb_lanes = 1 if len(sensFormatParsed) == 4 else 2
                self.sensor.init_sensor(bit_mode=sensFormatParsed[2]+'it', 
                                        fps=int(sensFormatParsed[1].split('f')[0]), 
                                        w=int(sensFormatParsed[0].split('x')[0]), 
                                        h=int(sensFormatParsed[0].split('x')[1]), 
                                        nb_lanes=nb_lanes)
            else:
                if not(sensor_NOK):
                    self.sensor.init_sensor()
            self.imager.enablePrint()
            self.root.config(cursor="clock") # show the clock cursor
            self.sensorInfo = self.sensor.get_sensor_info()
            self.sensor_w = int(self.sensorInfo["width"])
            self.sensor_h = int(self.sensorInfo["height"])
            self.sensor_wdma = int(self.sensorInfo["widthDMA"])
            self.sensor_hdma = int(self.sensorInfo["heightDMA"])
            self.w = int(self.sensorInfo["width"])
            self.h = int(self.sensorInfo["height"])
            self.updateLiveDimensions()
            self.sensor_fps = int(self.sensorInfo["fps"])
            self.sensor_mode = int(self.sensorInfo["dtMode"])
            self.bpp = self.sensorInfo["bpp"]
        self.startLive()

    def startLive(self, record=False, fname="noname.mp4"):
        self.statusAddLine("Starting new Gstreamer Pipeline...")
        if(self.GEVactive.get() == True):
            self.startGEV()
            return

        # Stop live pipeline if it was already running
        try:
            if(self.gstpipe != None):
                self.gstpipe.set_state(Gst.State.NULL)
                self.gstpipe = None
        except:
            pass
        # Create new live pipeline
        self.gstpipe = Gst.Pipeline.new("Live")
        if(int(self.sensorInfo["bpp"]) == 8):
            # The nVidia ISP is not supporting RAW8!
            # So use testdata instead of live
            self.src = Gst.ElementFactory.make("videotestsrc", "src")
            self.src.set_property("pattern", 19)
        else:
            self.src = Gst.ElementFactory.make("nvarguscamerasrc", "src")

            self.src.set_property("sensor-id", self.port)
            self.setWBMODE(self.ispwbmode.get())
            self.setTNR(self.isptnr.get())
            self.setTNRSTRENGTH(self.isptnrstrength.get())
            self.setEE(self.ispee.get())
            self.setEESTRENGTH(self.ispeestrength.get())
            self.setDGAIN(self.ispdgain.get())

            self.src.set_property("sensor-mode", self.sensor_mode)
            if(self.sensorConfig["Sensor"]["gstPipe"] != "color"):
                self.src.set_property("saturation", 1.0)
            else:
                self.src.set_property("saturation", 0.0)

            caps1 = Gst.ElementFactory.make("capsfilter", "caps1")
            txt = f"video/x-raw(memory:NVMM), width=(int){self.sensor_w}, height=(int){self.sensor_h}, format=(string)NV12, framerate=(fraction){int(self.sensor_fps)}/1"
            txt = Gst.Caps.from_string(txt)
            caps1.set_property("caps", txt)
            self.gstpipe.add(caps1)
        self.filter1 = Gst.ElementFactory.make("nvvidconv", "filter1")
        self.filter1.set_property("flip-method", self.rot)

        self.sink = Gst.ElementFactory.make("xvimagesink", "sink")
        self.sink.set_property("enable-last-sample", True)
        self.sink.set_property("force-aspect-ratio", True)
        self.setCONTRAST(self.ispcontrast.get())
        self.setBRIGHTNESS(self.ispbrightness.get())
        
        self.gstpipe.add(self.src)
        self.gstpipe.add(self.filter1)
        self.gstpipe.add(self.sink)
        if (record == True):
            tee1 = Gst.ElementFactory.make("tee", "tee1")
            tee1_q1_pad = tee1.get_request_pad("src_%u")
            tee1_q2_pad = tee1.get_request_pad("src_%u")
            q1 = Gst.ElementFactory.make("queue", "q1")
            q2 = Gst.ElementFactory.make("queue", "q2")
            enc1 = Gst.ElementFactory.make("nvv4l2h264enc", "h264enc")
            enc2 = Gst.ElementFactory.make("h264parse", "h264parse")
            enc3 = Gst.ElementFactory.make("avimux", "avimux")
            sink2 = Gst.ElementFactory.make("filesink", "filesink")
            sink2.set_property("location", fname)
            self.gstpipe.add(tee1)
            self.gstpipe.add(q1)
            self.gstpipe.add(q2)
            self.gstpipe.add(enc1)
            self.gstpipe.add(enc2)
            self.gstpipe.add(enc3)
            self.gstpipe.add(sink2)
            self.src.link(caps1)
            caps1.link(tee1)
            dest = q1.get_static_pad("sink")
            tee1_q1_pad.link(dest)
            q1.link(self.filter1)
            self.filter1.link(self.sink)
            dest = q2.get_static_pad("sink")
            tee1_q2_pad.link(dest)
            q2.link(enc1)
            enc1.link(enc2)
            enc2.link(enc3)
            enc3.link(sink2)
        else:
            if(int(self.sensorInfo["bpp"]) == 8):
                self.src.link(self.filter1)
            else:
                self.src.link(caps1)
                caps1.link(self.filter1)
            self.filter1.link(self.sink)
        
        self.has_overlay = False
        self.wf_height = self.sensor_h // 2
        self.wf_width = self.sensor_w // 2

        # connect LiveUpdate callback
        bus = self.gstpipe.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        bus.connect("message", self.liveMessage)
        bus.connect("sync-message::element", self.liveView)
        self.v4l2 = False
        self.capt = False
        self.statusAddLine("Opening interface ({})".format(self.iface))
        self.streaming = True
        self.root.config(cursor="")
        self.imager.setformat(self.bpp, self.sensor_w, self.sensor_h, self.sensor_wdma, self.sensor_hdma, self.v4l2)
        self.root.after(2000, self.doWidgetAutoUpdate)
        self.imager.doWidgetUpdate()
        # Finally start the stream
        self.gstpipe.set_state(Gst.State.PLAYING)
        self.statusAddLine("Done starting new Gstreamer pipeline")
        self.root.after(200, self.liveUpdate)
        # And start also the GEV / Genicam interface
        self.statusAddLine("GEVactive = {}".format(self.GEVactive.get()))

    def pipelineOverlay(self):
        hist_active = bool(self.histframe.show.get())
        wave_h_active = bool(self.waveframe_h.show.get())
        wave_v_active = bool(self.waveframe_v.show.get())
        colprofile_active = bool(self.colprofileframe.show.get())
        rowprofile_active = bool(self.rowprofileframe.show.get())
        
        overlay_en = (not (hist_active or colprofile_active or rowprofile_active)) and (wave_h_active or wave_v_active)
        if self.has_overlay != overlay_en:
            if overlay_en == 1:
                #stop
                self.gstpipe.set_state(Gst.State.PAUSED)
                self.filter1.set_state(Gst.State.NULL)

                #unlink
                self.filter1.unlink(self.sink)
                
                #create
                self.overlay = Gst.ElementFactory.make('cairooverlay', 'overlay')
                self.adaptor = Gst.ElementFactory.make('videoconvert', 'adaptor')

                #add
                self.gstpipe.add(self.overlay)
                self.gstpipe.add(self.adaptor)

                #link
                self.filter1.link(self.overlay)
                self.overlay.link(self.adaptor)
                self.adaptor.link(self.sink)

                #play
                self.filter1.set_state(Gst.State.PLAYING)
                if self.video_mode == True:
                    self.gstpipe.set_state(Gst.State.PLAYING)

            else:
                #stop
                self.gstpipe.set_state(Gst.State.PAUSED)
                self.adaptor.set_state(Gst.State.NULL)
                self.overlay.set_state(Gst.State.NULL)
                self.filter1.set_state(Gst.State.NULL)

                #unlink
                self.filter1.unlink(self.overlay)
                self.overlay.unlink(self.adaptor)
                self.adaptor.unlink(self.sink)

                #remove
                self.gstpipe.remove(self.overlay)
                self.gstpipe.remove(self.adaptor)

                #delete
                del self.overlay
                del self.adaptor
                self.master.unbind("<Up>")
                self.master.unbind("<Down>")
                self.master.unbind("<Left>")
                self.master.unbind("<Right>")

                #link
                self.filter1.link(self.sink)

                #play
                self.filter1.set_state(Gst.State.PLAYING)
                if self.video_mode == True:
                    self.gstpipe.set_state(Gst.State.PLAYING)
        
        if overlay_en == 1:
            if (self.has_overlay == 1):
                    self.overlay.disconnect(self.draw_id)
            if (wave_h_active == 1) and (wave_v_active == 1):
                self.draw_id = self.overlay.connect('draw', self.on_overlay_draw_waveform_hv)
                self.master.bind("<Up>", self.wf_overlay_up)
                self.master.bind("<Down>", self.wf_overlay_down)
                self.master.bind("<Left>", self.wf_overlay_left)
                self.master.bind("<Right>", self.wf_overlay_right)
            elif (wave_h_active == 1) and (wave_v_active == 0):
                self.draw_id = self.overlay.connect('draw', self.on_overlay_draw_waveform_h)
                self.master.bind("<Up>", self.wf_overlay_up)
                self.master.bind("<Down>", self.wf_overlay_down)
                self.master.unbind("<Left>")
                self.master.unbind("<Right>")
            elif (wave_h_active == 0) and (wave_v_active == 1):
                self.draw_id = self.overlay.connect('draw', self.on_overlay_draw_waveform_v)
                self.master.bind("<Left>", self.wf_overlay_left)
                self.master.bind("<Right>", self.wf_overlay_right)
                self.master.unbind("<Up>")
                self.master.unbind("<Down>")
        self.has_overlay = overlay_en


    def on_overlay_draw_waveform_h(self, overlay, context, timestamp, duration):
        #todo: Move line faster if key is pressed long
        #      Increase line width when zooming in on image

        context.set_source_rgba(253/256, 80/256, 0.0, 1)
        context.set_line_width(2)
        
        context.move_to(0, self.wf_height - 1.0)
        context.line_to(self.sensor_w, self.wf_height - 1.0)
        context.move_to(0, self.wf_height + 2.0)
        context.line_to(self.sensor_w, self.wf_height + 2.0)
        context.stroke()

    def on_overlay_draw_waveform_v(self, overlay, context, timestamp, duration):
        context.set_source_rgba(253/256, 80/256, 0.0, 1)
        context.set_line_width(2)
        
        context.move_to(self.wf_width - 1.0, 0)
        context.line_to(self.wf_width - 1.0, self.sensor_h)
        context.move_to(self.wf_width + 2.0, 0)
        context.line_to(self.wf_width + 2.0, self.sensor_h)
        context.stroke()

    def on_overlay_draw_waveform_hv(self, overlay, context, timestamp, duration):
        context.set_source_rgba(253/256, 80/256, 0.0, 1)
        context.set_line_width(2)
        
        context.move_to(0, self.wf_height - 1.0)
        context.line_to(self.wf_width - 1.0, self.wf_height - 1.0)
        context.line_to(self.wf_width - 1.0, 0)

        context.move_to(self.wf_width + 2.0, 0)
        context.line_to(self.wf_width + 2.0, self.wf_height - 1.0)
        context.line_to(self.sensor_w, self.wf_height - 1.0)

        context.move_to(self.sensor_w, self.wf_height + 2.0)
        context.line_to(self.wf_width + 2.0, self.wf_height + 2.0)
        context.line_to(self.wf_width + 2.0, self.sensor_h)

        context.move_to(self.wf_width - 1.0, self.sensor_h)
        context.line_to(self.wf_width - 1.0, self.wf_height + 2.0)
        context.line_to(0, self.wf_height + 2.0)
        context.stroke()
    
    def wf_overlay_up(self, event):
        self.wf_height -= 10
        if self.wf_height < 0:
            self.wf_height += self.sensor_h
    
    def wf_overlay_down(self, event):
        self.wf_height += 10
        if self.wf_height >= self.sensor_h:
            self.wf_height -= self.sensor_h

    def wf_overlay_left(self, event):
        self.wf_width -= 10
        if self.wf_width < 0:
            self.wf_width += self.sensor_w
    
    def wf_overlay_right(self, event):
        self.wf_width += 10
        if self.wf_width >= self.sensor_w:
            self.wf_width -= self.sensor_w

    def getImageGEV(self, sink):
        sample = sink.emit("pull-sample")
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
            self.cvimage = np.left_shift(np.ndarray(shape=(height, width), dtype=np.uint16, buffer=map_info.data), shift)
        # send image also to GEV Genicam interface
        # Clean up the buffer mapping
        if (self.GEVrun == True):
            #print("Sending in {}".format(self.sensor_fps))
            GEVPython.setimage(self.cvimage)
        buffer.unmap(map_info)
        return False


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
        bus.connect("message", self.liveMessage)
        bus.connect("sync-message::element", self.liveView)
        self.sink.connect("new-sample", self.getImageGEV)
        self.v4l2 = False
        self.capt = False
        self.statusAddLine("Opening GEV interface ({})".format(self.iface))
        self.streaming = True
        self.root.config(cursor="")
        self.imager.setformat(self.bpp, self.sensor_w, self.sensor_h, self.sensor_wdma, self.sensor_hdma, self.v4l2)
        # Do a raw save to get it up and running
        self.imager.clearArgus()
        self.imager.saveTiff("/dev/null", count=1)
        self.root.after(2000, self.doWidgetAutoUpdate)
        self.imager.doWidgetUpdate()
        # Finally start the stream
        self.gstpipe.set_state(Gst.State.PLAYING)
        self.root.after(200, self.liveUpdate)
        # And start also the GEV / Genicam interface
        self.statusAddLine("Starting GEV streaming...")
        GEVPython.setparams(self.sensor_w, self.sensor_h, self.bpp)
        GEVPython.setip(self.ethIP)
        GEVPython.run(1)
        self.GEVrun = True
        self.statusAddLine("Done.")


    def stopGEV(self):
        self.statusAddLine("GEV streaming stopped")
        self.GEVrun = False
        GEVPython.run(0)
        result = self.gstpipe.set_state(Gst.State.PAUSED)
        if (result == Gst.StateChangeReturn.ASYNC):
            self.statusAddLine("Async change in stoplive")
        self.gstpipe.get_state(10)
        result = self.gstpipe.set_state(Gst.State.READY)
        if (result == Gst.StateChangeReturn.ASYNC):
            self.statusAddLine("Async change in stoplive")
        self.gstpipe.get_state(10)
        result = self.gstpipe.set_state(Gst.State.NULL)
        if (result == Gst.StateChangeReturn.ASYNC):
            self.statusAddLine("Async change in stoplive")
        self.gstpipe.get_state(10)

        del self.gstpipe

    def stopLive(self):
        if(self.GEVrun == True):
            self.stopGEV()
            return
        self.streaming = False
        result = self.gstpipe.set_state(Gst.State.PAUSED)
        if(result == Gst.StateChangeReturn.ASYNC):
            self.statusAddLine("Async change in stoplive")
        self.gstpipe.get_state(10)
        time.sleep(1)
        result = self.gstpipe.set_state(Gst.State.READY)
        if(result == Gst.StateChangeReturn.ASYNC):
            self.statusAddLine("Async change in stoplive")
        self.gstpipe.get_state(10)
        #result = self.gstpipe.set_state(Gst.State.NULL)
        if(result == Gst.StateChangeReturn.ASYNC):
            self.statusAddLine("Async change in stoplive")
        self.gstpipe.get_state(10)
        self.statusAddLine("Cleaning up Gstreamer Pipeline...")
        #self.gstpipe.unref()
        self.statusAddLine("Done.")
        return

#        time.sleep(1.5)


    def liveMessage(self, bus, message):
        t = message.type
        if (t == Gst.MessageType.EOS):
            self.gstpipe.set_state(Gst.State.NULL)
            self.gstpipe = None
            self.statusAddLine("Error: Gstreamer pipe is broken (.EOS) and must be restarted")
        elif (t == Gst.MessageType.ERROR):
            self.gstpipe.set_state(Gst.State.NULL)
            self.gstpipe = None
            self.statusAddLine("Error: Gstreamer pipe is broken (.ERROR) and must be restarted")

    def liveView(self, bus, message):
        window = self.liveCanvas.winfo_id()
        message_name = message.get_structure().get_name()
#        print("Live-View: {}".format(message_name))
        if (message_name == "prepare-window-handle"):
            message.src.set_window_handle(window)

        if (message_name == "prepare-xwindow-id"):
            imagesink = message.src
            imagesink.set_property("force-aspect-ratio", True)
            imagesink.set_xwindow_id(self.liveCanvas.winfo_id())

    def updateScaler(self):
#        self.statusAddLine("ScalerUpdate: Scale={}, posx={}, posy={}, w={}, h={}, Size={}".format(self.scale, self.posx, self.posy, self.disp_w, self.disp_h, self.factor))
        centerX = int(self.sensor_w * self.posx)
        centerY = int(self.sensor_h * self.posy)
        offsetX = int(self.sensor_w / (2.0 * self.scale))
        offsetY = int(self.sensor_h / (2.0 * self.scale))
        top = centerY - offsetY
        bottom = centerY + offsetY
        left = centerX - offsetX
        right = centerX + offsetX
        # some security checks
        if(top < 0):
            top = 0
        if(bottom >= self.sensor_h):
            bottom = self.sensor_h - 1
        if(left < 0):
            left = 0
        if(right >= self.sensor_w):
            right = self.sensor_w - 1
        try:
            self.filter1.set_property("top", top)
            self.filter1.set_property("bottom", bottom)
            self.filter1.set_property("left", left)
            self.filter1.set_property("right", right)
        except:
            # to avoid warnings if pipeline is not active
            pass


    def liveUpdate(self):
        if (self.streaming):

            sample = self.sink.get_last_sample()
            if (sample == None):
                self.root.after(200, self.liveUpdate)
                return
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
            if( (self.GEVrun == True) and (self.bpp == 8)):
                numbytes = 1
            else:
                numbytes = 2

            self.cvimage = np.ndarray(shape=(height, width, numbytes), dtype=np.uint8, buffer=map_info.data)
            # send image also to GEV Genicam interface
            # Clean up the buffer mapping
            buffer.unmap(map_info)

            try:
                if (self.controlBook.index(self.controlBook.select()) == 2) and (self.video_mode == True):
                    if (bool(self.histframe.show.get()) == True):
                        plotx = np.linspace(0, 255, 256)
                        ploty = cv2.calcHist([self.cvimage], [0], None, [256], [0, 256])
                        ploty = ploty / ploty.max()
                        self.updateHistPlot(plotx, ploty)
                    if (bool(self.waveframe_h.show.get()) == True):
                        hline = self.cvimage[self.wf_height, :, 0]
                        self.updateWaveHPlot(hline)
                    if (bool(self.waveframe_v.show.get()) == True):
                        vline = self.cvimage[:, self.wf_width, 0]
                        self.updateWaveVPlot(vline)
                    if (bool(self.colprofileframe.show.get()) == True):
                        hline = np.mean(self.cvimage[:, :, 0], axis=0)
                        self.updateColprofilePlot(hline)
                    if (bool(self.rowprofileframe.show.get()) == True):
                        vline = np.mean(self.cvimage[:, :, 0], axis=1)
                        self.updateRowprofilePlot(vline)
            except:
                raise

            self.liveStatUpdate("FPS sensor: {}".format(self.sensor_fps))
        if(self.imager.WidgetUpdatePending() == True):
            self.doWidgetUpdate()
#        self.root.update()
        self.root.after(200,self.liveUpdate)


    def doFlashEnable(self):
        self.imager.setSensorI2C(0x30)
        self.imager.type(0) # Reg=8bit, val=8bit
        self.imager.write(6,0xA)
        self.imager.setSensorI2C(0x32)
        self.imager.type(1) # reset to sensor

    def doWidgetUpdate(self):
        # Disable read and write information in status area
        self.imager.disablePrint()

        # loop through all registered widgets, execute the get functions and update the variables
        for widget in self.widgetList:
            try:
                controlParams = widget[0]
                var1 = widget[1]
                ctrl1 = widget[2]
                get1 = widget[3]
                if (len(widget) > 4):
                    var2 = widget[4]
                    ctrl2 = widget[5]
                    get2 = widget[6]
                get1() # call widgets get function to update widget variable and also automatically the widget itself
                if (controlParams["type"] == "checkbutton_and_slider"):
                    get2() # get actual checkbutton state
                    # disable slider if checkbutton is disabled
                    if(var2.get() == False):
                        ctrl1["state"] = "disabled"
                        ctrl1["bg"] = "#C7CCCF"
                    else:
                        ctrl1["state"] = "normal"
                        ctrl1["bg"] = "#FD5000"
                if (controlParams["type"] == "two_checkbuttons"):
                    get2()
            except Exception as e:
                print(f"{type(e).__name__} at line {e.__traceback__.tb_lineno} of {__file__}: {e}")

                self.statusAddLine("Error: Widget {} has some errors. Please correct them and restart the software".format(controlParams["name"]))
        # Disable read and write information in status area
        self.imager.enablePrint()


    def doWidgetAutoUpdate(self):

        # Disable read and write information in status area
        self.imager.disablePrint()

        # Update all hardware related stuff like power sensor
        if(self.pwrAvail == True):
            (result, pwr) = self.imager.ina260Check()
            if (result):
                self.Powerdisp["text"] = "Sensorboard power: {}W".format(pwr)
            else:
                self.Powerdisp["text"] = ""
                self.pwrAvail = False


        # loop through all registered widgets, execute the get functions and update the variables
        for widget in self.widgetAutoUpdate:
            try:
                controlParams = widget[0]
                var1 = widget[1]
                ctrl1 = widget[2]
                get1 = widget[3]
                if (len(widget) > 4):
                    var2 = widget[4]
                    ctrl2 = widget[5]
                    get2 = widget[6]
                get1() # call widgets get function to update widget variable and also automatically the widget itself
                if (controlParams["type"] == "checkbutton_and_slider"):
                    get2() # get actual checkbutton state
                    # disable slider if checkbutton is disabled
                    if(var2.get() == False):
                        ctrl1["state"] = "disabled"
                    else:
                        ctrl1["state"] = "enabled"
                if (controlParams["type"] == "two_checkbuttons"):
                    get2()
            except:
                self.statusAddLine("Error: Widget {} has some errors. Please correct them and restart the software".format(controlParams["name"]))
        # Disable read and write information in status area
        self.imager.enablePrint()
        if(self.streaming == True):
            self.root.after(1000,self.doWidgetAutoUpdate)

    def execBatch(self, event):
        self.statusAddLine("Executing{}".format(str(event)))
        fname = str(self.sensorConfig["Batch"][str(event)])
        fname = os.getcwd() + "/" + fname
        try:
            with open(fname, "r") as file:
                exec (file.read())
        except Exception as ex:
            print(ex)
            self.statusAddLine("Error: control file problem (not found or buggy {}".format(fname))
        execCmd(self.imager)

    def editSettings(self):
        # TODO:
        # Add Encoder and Recording settings 
        pass

    def saveSettings(self):
        fp = open("/tmp/gui_config.cfg", "w")
        self.config.write(fp)
        fp.close()
        os.system("echo {} | sudo -S cp /tmp/gui_config.cfg ./gui_config.cfg".format(self.rootPW))
        self.statusAddLine("Config file updated")

    def showDocumentation(self):
        # check if Chromium is installed
        # Open chromium Browser with Help URL
        try:
            self.help = os.popen(f"chromium-browser --no-sandbox --app=file://{os.path.dirname(os.path.dirname(os.getcwd()))}/doc/index.html")
        except:
            messagebox.showinfo("Documentation", "The documentation cannot be shown\nPlease check if Chromium webbrowser is installed")

    def showChanges(self):
        # check if Chromium is installed
        # Open chromium Browser with Help URL
        try:
            self.help = os.popen(f"chromium-browser --no-sandbox --app=file://{os.path.dirname(os.path.dirname(os.getcwd()))}/doc/Changes.html")
        except:
            messagebox.showinfo("Documentation", "The documentation cannot be shown\nPlease check if Chromium webbrowser is installed")

    def showAgreement(self):
        # check if Chromium is installed
        # Open chromium Browser with Help URL
        try:
            self.help = os.popen(f"chromium-browser --no-sandbox --app=file://{os.path.dirname(os.path.dirname(os.getcwd()))}/doc/LicenseAgreement.html")
        except:
            messagebox.showinfo("Documentation", "The documentation cannot be shown\nPlease check if Chromium webbrowser is installed")

    def showDocumentationOnline(self):
        # check if Chromium is installed
        # Open chromium Browser with Help URL
        try:
            self.help = os.popen("chromium-browser  --no-sandbox --app=https://ams.com/mira130")
        except:
            messagebox.showinfo("Documentation", "The documentation cannot be shown\nPlease check if Chromium webbrowser is installed")

    def showAbout(self):
        messagebox.showinfo("About", "JetCis Viewer by ams OSRAM in 2021 \nVersion {} \nFor updates, check the ams website.".format(self.version))

    def checkForUpdates(self):
        ''' Checks if there is new SW and HW available.
            Parse info:
                The software version in version_info.cfg should contain dots
                The software version on the ams website should contain dashes
        '''

        def connected(host):
            try:
                urllib.request.urlopen(host)
                return True
            except:
                return False

        # Check if an internet connection exists
        url = "https://ams.com/mira130-nvidia-jetson-nano-evalkit#tab/tools"
        if connected(url) == False:
            messagebox.showerror("No internet Connection", "The system is not connected to the internet to check for a software update. \
                                 \nPlease insert an ethernet cable or a USB-Wi-Fi-adapter to establish a connection and retry.")
        else:
            # There is an internet connection. Check if there is a new version available online
            # Get html info from ams website
            page = requests.get(url)
            soup = BeautifulSoup(page.content, "html.parser")

            results = soup.find(id="tab4")
            table = results.find('table', attrs={'class':'table table--technical-documents'})
            table_body = table.find('tbody')
            rows = table_body.find_all('tr')

            # Parse table
            versions_website = []
            for row in rows:
                cols = row.find_all('td')
                cols = [ele.text.strip() for ele in cols]
                version = [((ele.split('_')[-1]).split('.')[0]).split('v')[-1] for ele in cols if 'EvalSW' in ele]
                versions_website.append(version[0].replace('-','.'))
                
            # Sort available versions
            versions_website.sort(key=StrictVersion)

            # Parse installed version
            version_installed = self.version.split('-')[0] #remove rc


            if StrictVersion(version_installed) < StrictVersion(versions_website[-1]):
                messagebox.showinfo("Software version", "There is a newer version available on the ams website. Please update.")
            else:
                messagebox.showinfo("Software version", "Your software version is up to date.")

        # Check if HW is outdated
        dialog_product = ChoiceDialog(self, 'Check for hardware', items=['Mira030', 'Mira050', 'Mira130', 'Mira220'], 
                                    text="Which sensor product name is written on your sensor board below the ams logo?")
        product_selection = dialog_product.selection
        if product_selection == None:
            return

        pcb_version = self.version_info[product_selection]["pcb"]
        
        if pcb_version != '1.0':
            messagebox.showinfo("Check for hardware", f'Check the version written on your sensor board below the ams logo.\
                                \nPlease contact your local FAE to update when the version is lower than v{pcb_version}.')
        else:
            messagebox.showinfo("Check for hardware", 'Your hardware version is up to date.')


class ChoiceDialog(tkinter.simpledialog.Dialog):
    def __init__(self, parent, title, items, text=None):
        self.selection = None
        self._items = items
        self._text = text
        super().__init__(parent, title=title)

    def body(self, parent):
        self._message = tkinter.Message(parent, aspect=400)
        self._message.pack(expand=1, fill=tkinter.BOTH)
        if self._text != None:
            self._label = tkinter.Label(parent, text=self._text, justify=LEFT, wraplength=150, anchor=W)
            self._label.pack(expand=1, fill=tkinter.BOTH, side=tkinter.TOP)
        self._list = tkinter.Listbox(parent)
        self._list.pack(expand=1, fill=tkinter.BOTH, side=tkinter.TOP)
        for item in self._items:
            self._list.insert(tkinter.END, item)
        return self._list

    def validate(self):
        if not self._list.curselection():
            return 0
        return 1

    def apply(self):
        self.selection = self._items[self._list.curselection()[0]]


class ToggledFrame(tkinter.Frame):

    def __init__(self, parent, pipelineOverlay, text="", state=tkinter.DISABLED, *args, **options):
        tkinter.Frame.__init__(self, parent, *args, **options)
        self.pipelineOverlay = pipelineOverlay
        self.show = tkinter.IntVar()
        self.show.set(0)

        self.title_frame = tkinter.Frame(self)
        self.title_frame.pack(fill="x", expand=1)

        self.toggle_button = tkinter.ttk.Checkbutton(self.title_frame, width=2, text=" \u2303", command=self.toggle,
                                            variable=self.show, style='Toolbutton', state=state)
        self.toggle_button.pack(side="left")
        
        tkinter.ttk.Label(self.title_frame, text=" " + text, anchor='w').pack(side="left", fill="x", expand=1)

        self.sub_frame = tkinter.Frame(self, relief="sunken", borderwidth=1)

    def toggle(self):
        if bool(self.show.get()):
            self.sub_frame.pack(fill="x", expand=1)
            self.toggle_button.configure(text=" \u2304")
        else:
            self.sub_frame.forget()
            self.toggle_button.configure(text=" \u2303")
        self.pipelineOverlay()


class ScrollFrame(tkinter.Frame):
    def __init__(self, parent):
        super().__init__(parent) # create a frame (self)
        # Place canvas on self
        self.canvas = tkinter.Canvas(self, borderwidth=0, highlightthickness=0)
        # Place a frame on the canvas, this frame will hold the child widgets
        self.viewPort = tkinter.Frame(self.canvas)
        # Place a scrollbar on self
        self.vsb = tkinter.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        # Attach scrollbar action to scroll of canvas
        self.canvas.configure(yscrollcommand=self.vsb.set)

        # Pack scrollbar to right of self
        self.vsb.pack(side="right", fill="y")
        # Pack canvas to left of self and expand to fill
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas_window = self.canvas.create_window((0,0),
                                                 window=self.viewPort, anchor="nw",
                                                 tags="self.viewPort")

        # Bind an event whenever the size of the viewPort frame changes.
        self.viewPort.bind("<Configure>", self.onFrameConfigure)
        self.canvas.bind("<Configure>", self.onCanvasConfigure)  

        # Perform an initial stretch on render, otherwise the scroll region has a tiny border until the first resize
        self.onFrameConfigure(None)

    def onFrameConfigure(self, event):
        '''Reset the scroll region to encompass the inner frame'''
        #whenever the size of the frame changes, alter the scroll region respectively.
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def onCanvasConfigure(self, event):
        '''Reset the canvas window to encompass inner frame when required'''
        canvas_width = event.width
        #whenever the size of the canvas changes alter the window region respectively.
        self.canvas.itemconfig(self.canvas_window, width = canvas_width)


def run():
    #####################
    # MAIN
    #####################
    root = tkinter.Tk()
    root.title("JetCis viewer")
    root.style = Style(theme='jetcis')
    app = MainApp(master=root)
    app.mainloop()

