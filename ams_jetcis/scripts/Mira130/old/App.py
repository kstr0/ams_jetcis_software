import tkinter
import tkinter.ttk
from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
from tkinter.ttk import *
import configparser
import sys
import os
import traceback
import cv2
import time
import PIL
import threading
import numpy as np
from PIL import ImageTk, Image
from functools import partial
from zoomcontroller import ZoomController
from live_area_controller import LiveAreaController
import driver_access
from datetime import datetime
import subprocess
from tooltip import CreateToolTip
from xmlrpc.client import ServerProxy

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure




class MainApp(tkinter.Frame):
    zoom_controller = None

    def __init__(self, master=None):
        # store master link
        self.root = master
        # Define important things
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
        # Load config File
        self.config = configparser.ConfigParser()
        self.config.read("./config.cfg")
        try:
            version = str(self.config["App"]["version"])
            print("INFO: config file loaded, version={}".format(version))
        except:
            print("ERROR: no or wrong config.cfg present. Program will be terminated")
            sys.exit()
        # And check file path
        try:
            self.config["File"]["path"]
        except:
            self.config["File"]["path"] = "~/Pictures"
        try:
            self.config["File"]["logpath"]
        except:
            self.config["File"]["logpath"] = "~/Documents"
        tkinter.Frame.__init__(self, master)
        self.pack()
        self.menuBar = tkinter.Menu(master)
        master.config(menu=self.menuBar)
        self.initMenuBar()
        self.initPopups()
        self.checkPlatform()
        self.initGUI()
        # Connect to SyncServer
        self.cli = ServerProxy("http://localhost:1337")
        try:
            print("Connected to SyncServer, Version {}".format(self.cli.getVersion()))
        except:
            messagebox.showinfo("ERROR",
                                  "SyncServer is not active. Please reboot the linux system")
            self.endProgram()
        # Start watchdog thread
        self.wd = threading.Thread(target=self.updateWd)
        self.wd.start()
        # Add keyboard functions
        self.master.bind("f", self.toggleFullscreen)
        self.master.bind("q", self.endProgram)
        self.master.bind("s", self.live_area_controller.save_image_callback)
        self.master.bind("r", self.live_area_controller.save_video_callback) # H264: comment out if not used
        self.master.bind("b", self.live_area_controller.save_raw_callback)
        self.master.bind("p", self.live_area_controller.play_pause_callback)
        self.master.bind("o", self.openSensorConfig)

    def updateWd(self):
        while(self.run):
            if (self.videoLocked == True):
                self.cli.lockVideo(self.port)
            time.sleep(1.0)

    def endProgram(self, event=None):
        self.run = False
        self.wd.join(2.0)
        try:
            self.cli.unlockVideo(self.port)
        except:
            pass # happens if SyncServer did not run
        try:
            if(self.cap is not None):
                self.cap.release()
                self.cap = None
        except:
            pass
        if (self.streaming):
            self.imager.stopstream()
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


    def initMenuBar(self):
        self.live_area_controller = LiveAreaController(self, self.config["File"]["path"], int(self.config["Record"]["rawburst"]))
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
        self.menuControl.add_command(label="Pause", command=self.live_area_controller.play_pause_callback,
                                     accelerator="P")
        self.live_area_controller.set_play_pause_menu(self.menuControl)
        self.menuControl.add_command(label="Save Image", command=self.live_area_controller.save_image_callback,
                                     accelerator="S")
        self.menuControl.add_command(label="Save Video(H.264)", command=self.live_area_controller.save_video_callback,
                                     accelerator="R") # H264: Disable with , state=tkinter.DISABLED
        self.menuControl.add_command(label="Save Video(RAW)", command=self.live_area_controller.save_raw_callback,
                                     accelerator="B")
        self.menuControl.add_command(label="Full Screen", command=self.toggleFullscreen, accelerator="F")
        self.menuBar.add_cascade(label="Control", menu=self.menuControl)
        # Help Menu
        self.menuHelp = tkinter.Menu(self.menuBar, tearoff=False)
        self.menuHelp.add_command(label="Open Installed Documentation", command=self.showDocumentation)
        self.menuHelp.add_command(label="Open Online Documentation", command=self.showDocumentationOnline)
        self.menuHelp.add_separator()
        self.menuHelp.add_command(label="About", command=self.showAbout)
        self.menuHelp.add_command(label="Changes", command=self.showChanges)
        self.menuHelp.add_command(label="License Agreement", command=self.showAgreement)
        self.menuBar.add_cascade(label="Help", menu=self.menuHelp)
        #self.menuHelp.entryconfig(1, state=DISABLED)

    def initPopups(self):
        # text area popup menu
        self.menuText = tkinter.Menu(self, tearoff=False)
#        self.menuText.add_separator()
        self.menuText.add_command(label="Clear", command=self.statusClear)
        self.menuText.add_command(label="Save", command=self.statusSave)

    def initGUI(self):
        ##################
        # only root can use the GUI
        ############################
        if(os.getuid() != 0):
            messagebox.showinfo("ERROR",
                                  "The Program is not started as root. Some hardware functions might fail")
            self.su = False
        else:
            self.su = True
        ##############################
        # check kernel and SDK version
        ##############################
        p = subprocess.Popen(["uname", "-r"], stdout=subprocess.PIPE)
        version = str(p.stdout.read())
        if(not re.search(r"4.9.140", version)): # SDK 4.3
            messagebox.showinfo("ERROR",
                                  "Kernel Version({}) is not supported by the software".format(version))
            exit(1)

        ##################
        # The ButtonArea
        ##################
        self.buttonArea = tkinter.Frame(self, bd=1, relief="raised")
        self.buttonArea.grid(row=0, column=0, rowspan=2, columnspan=20, sticky="ew")
        # Open config button
        img_openconfig = ImageTk.PhotoImage(Image.open("./button_icons/folder_out.png"))
        self.button_openconfig = tkinter.Button(self.buttonArea, image=img_openconfig, relief="flat",
                                                command=self.openSensorConfig)
        self.button_openconfig.image = img_openconfig
        self.button_openconfig.grid(row=0, column=0)
        self.button_openconfig_ttp = CreateToolTip(self.button_openconfig, self.buttonArea,
                                                   "Open a sensor configuration file")
        # Vertical line
        sep1 = Separator(self.buttonArea, orient="vertical")
        sep1.grid(row=0, column=1, padx=4, pady=4, sticky="ns")
        # Edit settings button
        img_opensettings = ImageTk.PhotoImage(Image.open("./button_icons/window_gear.png"))
        self.button_opensettings = tkinter.Button(self.buttonArea, image=img_opensettings, relief="flat",
                                                  command=self.editSettings)
        self.button_opensettings.image = img_opensettings
        self.button_opensettings.grid(row=0, column=2)
        self.button_opensettings_ttp = CreateToolTip(self.button_opensettings, self.buttonArea, "Open settings")
        # Save config button
        img_savesettings = ImageTk.PhotoImage(Image.open("./button_icons/folder_into.png"))
        self.button_savesettings = tkinter.Button(self.buttonArea, image=img_savesettings, relief="flat",
                                                  command=self.saveSettings)
        self.button_savesettings.image = img_savesettings
        self.button_savesettings.grid(row=0, column=3)
        self.button_savesettings_ttp = CreateToolTip(self.button_savesettings, self.buttonArea,
                                                     "Save the gui settings")
        # Vertical line
        sep2 = Separator(self.buttonArea, orient="vertical")
        sep2.grid(row=0, column=4, padx=4, pady=4, sticky="ns")
        # Play pause button
        self.img_pause = ImageTk.PhotoImage(Image.open("./button_icons/media_pause.png"))
        self.img_play = ImageTk.PhotoImage(Image.open("./button_icons/media_play.png"))
        self.button_playpause = tkinter.Button(self.buttonArea, image=self.img_pause, relief="flat",
                                               command=self.live_area_controller.play_pause_callback)
        self.button_playpause_ttp = CreateToolTip(self.button_playpause, self.buttonArea,
                                                  "Pause the live video stream (P)")
        self.live_area_controller.set_play_pause_param(self.button_playpause, self.img_pause, self.img_play,
                                                       self.button_playpause_ttp)
        self.button_playpause.grid(row=0, column=5)
        # Save image button
        img_saveimage = ImageTk.PhotoImage(Image.open("./button_icons/save_image.png"))
        self.button_saveimage = tkinter.Button(self.buttonArea, image=img_saveimage, relief="flat",
                                               command=self.live_area_controller.save_image_callback)
        self.button_saveimage.image = img_saveimage
        self.button_saveimage.grid(row=0, column=6)
        self.button_saveimage_ttp = CreateToolTip(self.button_saveimage, self.buttonArea,
                                                  "Save the presented image as TIFF (S)")
        # Save video button
        self.img_save264 = ImageTk.PhotoImage(Image.open("./button_icons/media_record_start.png"))
        self.img_save264stop = ImageTk.PhotoImage(Image.open("./button_icons/media_record_stop.png"))
        self.button_save264 = tkinter.Button(self.buttonArea, image=self.img_save264, relief="flat",
                                               command=self.live_area_controller.save_video_callback) # H264 disable with , state=tkinter.DISABLED
        self.button_save264.image = self.img_save264
        self.button_save264.grid(row=0, column=7)
        self.button_save264_ttp = CreateToolTip(self.button_save264, self.buttonArea,
                                                  "Save the presented video in H.264 (R)")
        # Save raw button
        img_saveraw = ImageTk.PhotoImage(Image.open("./button_icons/burst.png"))
        self.button_saveimage = tkinter.Button(self.buttonArea, image=img_saveraw, relief="flat",
                                               command=self.live_area_controller.save_raw_callback)
        self.button_saveimage.image = img_saveraw
        self.button_saveimage.grid(row=0, column=8)
        self.button_saveimage_ttp = CreateToolTip(self.button_saveimage, self.buttonArea,
                                                  "Save the presented video as RAW burst (B)")

        # Fullscreen button
        img_fullscreen = ImageTk.PhotoImage(Image.open("./button_icons/monitor_size.png"))
        self.button_fullscreen = tkinter.Button(self.buttonArea, image=img_fullscreen, relief="flat",
                                                command=self.toggleFullscreen)
        self.button_fullscreen.image = img_fullscreen
        self.button_fullscreen.grid(row=0, column=9)
        self.button_fullscreenm_ttp = CreateToolTip(self.button_fullscreen, self.buttonArea,
                                                    "Turn on full screen (F)")

        ##################
        # The LiveArea
        ##################
        self.liveArea = tkinter.LabelFrame(self)
        self.liveArea["text"] = "Image/Video"
        self.liveArea.grid(row=2, column=0, rowspan=10, columnspan=15)
        self.w = int(self.config["GUI"]["liveWidth"])
        self.h = int(self.config["GUI"]["liveHeight"])
        self.liveCanvas = tkinter.Canvas(self.liveArea, width=self.w, height=self.h)
        self.liveCanvas.bind("<Button-1>", self.liveCanvasScroll)
        self.liveCanvas.bind("<B1-Motion>", self.liveCanvasScroll)
        self.liveCanvas.bind("<ButtonRelease-1>", self.liveCanvasScrollStop)
        self.liveCanvas.bind("<Button-4>", self.liveCanvasScaleUp)
        self.liveCanvas.bind("<Button-5>", self.liveCanvasScaleDown)
        self.liveCanvas.pack()
        self.liveCanvas.create_rectangle(0,0,self.w,self.h, fill="blue")
        self.zoom_controller = ZoomController(self.w, self.h)

        ###################
        # The ControlArea
        ###################
        self.controlBook = Notebook(self)
        self.controlBook.grid(row=2, column=15, rowspan=16, columnspan=5, sticky="ns")
        self.controlArea = tkinter.Frame(self)
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
        self.statArea = tkinter.Frame(self)
        # FPS Sensor
        self.actFPS = tkinter.Label(self.statArea)
        self.actFPS["text"] = "FPS sensor: ???"
        self.actFPS.pack(side="top", anchor="w")
        lf = tkinter.LabelFrame(self.statArea)
        # FPS Display
        self.actFPSdisp = tkinter.Label(self.statArea)
        self.actFPSdisp["text"] = "FPS display: ???"
        self.actFPSdisp.pack(side="top", anchor="w")
        lf = tkinter.LabelFrame(self.statArea)
        # Resolution
        self.Resdisp = tkinter.Label(self.statArea)
        self.Resdisp["text"] = "Resolution: ??? x ???"
        self.Resdisp.pack(side="top", anchor="w")
        self.controlBook.add(self.statArea, text="Status")
        # Bits per Pixel
        self.BPPdisp = tkinter.Label(self.statArea)
        self.BPPdisp["text"] = "Bits per Pixel: ???"
        self.BPPdisp.pack(side="top", anchor="w")
        # Sensor Name
        self.Namedisp = tkinter.Label(self.statArea)
        self.Namedisp["text"] = "Sensor Name: ???"
        self.Namedisp.pack(side="top", anchor="w")
        # Sensor I2C
        self.I2Cdisp = tkinter.Label(self.statArea)
        self.I2Cdisp["text"] = "Sensor I2C address: ???"
        self.I2Cdisp.pack(side="top", anchor="w")
        # Sensor Color
        self.Colordisp = tkinter.Label(self.statArea)
        self.Colordisp["text"] = "Sensor Color: ???"
        self.Colordisp.pack(side="top", anchor="w")
        # System Type
        self.Systypedisp = tkinter.Label(self.statArea)
        self.Systypedisp["text"] = "System Type: nVidia Jetson {}".format(self.systype)
        self.Systypedisp.pack(side="top", anchor="w")
        # System Temperature
        self.Systempdisp = tkinter.Label(self.statArea)
        self.Systempdisp["text"] = "System Temperature: {}°C".format(self.temp)
        self.Systempdisp.pack(side="top", anchor="w")
        # Video Pipe
        self.Pipedisp = tkinter.Label(self.statArea)
        self.Pipedisp["text"] = "Video Pipeline: ???"
        self.Pipedisp.pack(side="top", anchor="w")
        # Board Type/Revision
        self.Revdisp = tkinter.Label(self.statArea)
        self.Revdisp["text"] = "Board Type/Revision: ???/???"
        self.Revdisp.pack(side="top", anchor="w")
        # Board Serial No.
        self.Serialdisp = tkinter.Label(self.statArea)
        self.Serialdisp["text"] = "Board Serial-No.: ??-??-??-??"
        self.Serialdisp.pack(side="top", anchor="w")
        # Add book
        self.controlBook.add(self.statArea, text="Status")
        ######################################
        # ISP controls
        ######################################
        self.ispArea = tkinter.Frame(self)
        self.controlBook.add(self.ispArea, text="ISP")
        lf = tkinter.LabelFrame(self.ispArea)
        lf["text"] = "Noise Reduction"
        lf.pack(side="top", anchor="w")
        self.tnrList = ["off", "fast", "HQ"]
        self.isptnr = tkinter.StringVar()
        self.isptnr.set(str(self.config["ISP"]["tnr"]))
        self.TNRispArea = tkinter.OptionMenu(lf, self.isptnr, *self.tnrList, command=self.setTNR)
        self.TNRispArea.pack()
        lf = tkinter.LabelFrame(self.ispArea)
        lf["text"] = "Edge Enhancement"
        lf.pack(side="top", anchor="w")
        self.eeList = ["off", "fast", "HQ"]
        self.ispee = tkinter.StringVar()
        self.ispee.set(str(self.config["ISP"]["ee"]))
        self.EEispArea = tkinter.OptionMenu(lf, self.ispee, *self.eeList, command=self.setEE)
        self.EEispArea.pack()
        lf = tkinter.LabelFrame(self.ispArea)
        lf["text"] = "Digital Gain (AGC)"
        lf.pack(side="top", anchor="w")
        self.dgainList = ["off", "on"]
        self.ispdgain = tkinter.StringVar()
        self.ispdgain.set(str(self.config["ISP"]["dgain"]))
        self.DGAINispArea = tkinter.OptionMenu(lf, self.ispdgain, *self.dgainList, command=self.setDGAIN)
        self.DGAINispArea.pack()
        #######################
        # tools area
        #######################
        self.toolsArea = tkinter.Frame(self)
        self.controlBook.add(self.toolsArea, text="Tools")
        lf = tkinter.LabelFrame(self.toolsArea)
        lf["text"] = "Histogram"
        lf.pack(side="top", anchor="w")
        f = Figure(figsize=(5,5), dpi=50)
        self.histplot = f.add_subplot(111)
        self.hplotdata, = self.histplot.plot([0,255], [0,0])
        self.histplot.set_xlabel('Pixel value')
        self.histplot.set_ylabel('Occurrence')
        self.histplot.set_xlim(left=0, right=256)
        self.histplot.set_ylim(bottom=0.0, top=1.0)
        self.histplot.set_facecolor("#b3b3b3")
        self.histcanvas = FigureCanvasTkAgg(f, lf)
        self.histcanvas.get_tk_widget().pack(side=tkinter.BOTTOM, fill=tkinter.BOTH, expand=False)
        self.histcanvas.show()
        toolbar = NavigationToolbar2TkAgg(self.histcanvas, lf)
        toolbar.update()
        self.histcanvas._tkcanvas.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=False)
        lf = tkinter.LabelFrame(self.toolsArea)
        lf["text"] = "Waveform"
        lf.pack(side="top", anchor="w")
        f = Figure(figsize=(5,5), dpi=50)
        self.waveplot = f.add_subplot(111)
        self.wplotdata, = self.waveplot.plot([0,255], [0,255])
        self.waveplot.set_xlabel('X-Position')
        self.waveplot.set_ylabel('Pixel value')
        self.waveplot.set_xlim(left=0, right=256)
        self.waveplot.set_ylim(bottom=0.0, top=256)
        self.waveplot.set_facecolor("#b3b3b3")
        self.wavecanvas = FigureCanvasTkAgg(f, lf)
        self.wavecanvas.get_tk_widget().pack(side=tkinter.BOTTOM, fill=tkinter.BOTH, expand=False)
        self.wavecanvas.show()
        toolbar = NavigationToolbar2TkAgg(self.wavecanvas, lf)
        toolbar.update()
        self.wavecanvas._tkcanvas.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=False)


        ###################
        # The StatusArea
        ###################
        self.statusArea = tkinter.LabelFrame(self)
        self.statusArea["text"] = "Status"
        self.statusArea.grid(row=12, column=0, rowspan=6, columnspan=15, sticky="s")
        self.statusScroll = tkinter.Scrollbar(self.statusArea)
        self.statusScroll.pack(side="right", fill="y")
        self.wTxt = int(self.config["GUI"]["statuswidth"])
        self.hTxt = int(self.config["GUI"]["statusheight"])
        self.statusText = tkinter.Text(self.statusArea, width=self.wTxt, height=self.hTxt)
        self.statusText.pack(side="left")
        self.statusScroll.config(command=self.statusText.yview)
        self.statusText.config(yscrollcommand=self.statusScroll.set)
        self.statusText.insert(tkinter.END, "Logging started\n")
        self.statusText.insert(tkinter.END, "Open sensor config to start\n")
        self.statusText.configure(state="disabled")
        self.statusText.bind("<Button-3>", self.TextPopup)

        ###################
        # The LogoArea
        ###################
        self.logoArea = tkinter.Frame(self, bd=1, bg="gray65")
        self.logoArea.grid(row=18, column=0, rowspan=1, columnspan=14, sticky="ew")
        ams_logo = Image.open("logo.png")  # original image is 320x88
        ams_logo = ams_logo.resize((80, 22), Image.ANTIALIAS)
        ams_logo_photo = ImageTk.PhotoImage(ams_logo)
        logo_label = Label(self.logoArea, image=ams_logo_photo, background="gray65")
        logo_label.image = ams_logo_photo
        logo_label.pack(side="left")
        self.videoSrc = tkinter.Frame(self, bd=1, bg="gray65")
        self.videoSrc.grid(row=18, column=14, rowspan=1, columnspan=12, sticky="ew")
        self.videorb2 = tkinter.Radiobutton(self.videoSrc)
        self.videorb2["text"] = "/dev/video1"
        self.videorb2["value"] = 1
        self.videorb2["variable"] = self.videoDevice
        self.videorb2["bg"] = "gray65"
#        self.videorb2["disabledforeground"] = self.videorb2["fg"]
        self.videorb2["disabledforeground"] = "blue"
        self.videorb2.pack(side="right")
        self.videorb1 = tkinter.Radiobutton(self.videoSrc)
        self.videorb1["text"] = "/dev/video0"
        self.videorb1["value"] = 0
        self.videorb1["variable"] = self.videoDevice
        self.videorb1["bg"] = "gray65"
#        self.videorb1["disabledforeground"] = self.videorb1["fg"]
        self.videorb1["disabledforeground"] = "blue"
        self.videorb1.pack(side="right")


    def videoSrcDisable(self):
        self.videorb1["state"] = "disabled"
        self.videorb2["state"] = "disabled"

    def videoSrcEnable(self):
        self.videorb1["state"] = "active"
        self.videorb2["state"] = "active"

    def videoSrcSet(self, port):
        self.videoDevice.set(int(port))


    def setTNR(self, text):
        self.config["ISP"]["tnr"] = self.isptnr.get()
        self.streaming = False
        self.startLive()

    def setEE(self, text):
        self.config["ISP"]["ee"] = self.ispee.get()
        self.streaming = False
        self.startLive()

    def setDGAIN(self, text):
        self.config["ISP"]["dgain"] = self.ispdgain.get()
        self.streaming = False
        self.startLive()


    def TextPopup(self, event):
        try:
            self.menuText.tk_popup(event.x_root, event.y_root, 0)
        finally:
#            self.menuText.grab_release()
            pass

    def updateLiveDimensions(self):
        self.liveCanvas.config(width=self.w, height=self.h)
        self.liveCanvas.pack()


    def toggleFullscreen(self, event=None):
        if self.fullscreen == True:
            self.fullscreen = False
            cv2.destroyWindow("Live") # the opencv way
#            self.root.attributes("-fullscreen", True) # the TK way
        else:
            self.fullscreen = True;
#            self.root.attributes("-fullscreen", False)  # the Tk way
            cv2.namedWindow("Live", cv2.WND_PROP_FULLSCREEN) # the opencv way
            cv2.setWindowProperty("Live", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN) # the opencv way
        self.statusAddLine("Fullscreen toggled")



    def updateHistPlot(self, xplot, yplot):
        self.hplotdata.set_xdata(xplot)
        self.hplotdata.set_ydata(yplot)
#        self.histplot.relim()
#        self.histplot.autoscale_view()
        self.histcanvas.draw()

    def updateWavePlot(self, wline):
        w, = wline.shape
        plotx = np.linspace(0, (w-1), w)
        self.waveplot.set_xlim(left=0, right=w)
        self.wplotdata.set_xdata(plotx)
        self.wplotdata.set_ydata(wline)
        #        self.waveplot.relim()
        #        self.waveplot.autoscale_view()
        self.wavecanvas.draw()

    def liveStatUpdate(self, fps, dispfps):
        self.actFPS["text"] = fps
        self.actFPSdisp["text"] = dispfps
        try:
            self.sensorConfig
            self.Pipedisp["text"] = "Video Pipeline: " + self.sensorConfig["Sensor"]["gstInterface"]
            self.Colordisp["text"] = "Sensor Color: " + self.sensorConfig["Sensor"]["gstPipe"]
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
            self.Revdisp["text"] = "Board Type/Revision: {}/{}".format(self.board_type, self.board_revision)
            self.Serialdisp["text"] = "Board Serial-No.: {}".format(self.serial_no)
        # Read also system temperatur
        try:
            self.temp = self.imager.getBoardTemp()
        except:
            pass
        self.Systempdisp["text"] = "System Temperature: {}°C".format(self.temp)
        self.update()

    def liveCanvasScaleDown(self, event):
        if self.zoom_controller is not None:
            self.zoom_controller.scale_down()

    def liveCanvasScaleUp(self, event):
        if self.zoom_controller is not None:
            self.zoom_controller.scale_up()

    def liveCanvasScroll(self, event):
        if self.zoom_controller is not None:
            self.zoom_controller.scroll(event.x, event.y)

    def liveCanvasScrollStop(self, event):
        if self.zoom_controller is not None:
            self.zoom_controller.stop_scrolling()

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
        self.root.update()

    def changeVideoSrc(self, port, oldport):
        self.cli.unlockVideo(oldport)
        result = self.cli.lockVideo(port)
        self.videoLocked = True
        return result


    def checkVideoSrc(self):
        ports = self.cli.getVideo()
        # check all options:
        if((ports[0] == False) and (ports[1] == False)):
            return 2
        elif((ports[0] == False) and (ports[1] == True)):
            return 0
        elif((ports[0] == True) and (ports[1] == False)):
            return 1
        else:
            return -1



    def openSensorConfig(self, event=None):
        self.sensorConfigFile = filedialog.askopenfilename(initialdir="./sensor", title="Open Sensor Configuration", filetypes=(("sensor configuration files", "*.sensor"),("all files", "*.*")))
        self.statusAddLine("INFO: opening sensor configuration ({})".format(self.sensorConfigFile))
        # Parse the sensor configuration
        self.sensorConfig = configparser.ConfigParser()
        self.sensorConfig.read(self.sensorConfigFile)
        try:
            name = str(self.sensorConfig["Description"]["Name"])
            self.statusAddLine("INFO: loading sensor configuration({})".format(name))
        except:
            self.statusAddLine("ERROR: no or wrong config.cfg p. Program will be terminated")
            return
        # Check for available video device
        if (self.port < 0):
            self.port = self.videoDevice.get()
        else:
            pass
        self.videoSrcDisable()
        if(self.sensLoaded):
            self.videoLocked = False
            time.sleep(1)
            self.cli.unlockVideo(self.port)
            time.sleep(1)
        self.sensLoaded = True
        oldport = self.port
        self.port = self.checkVideoSrc()
        if (self.port == 2):
            self.port = self.videoDevice.get()
            self.videoSrcSet(self.port)
            self.changeVideoSrc(self.port, oldport)
        elif (self.port == -1):
            # Error, there are already 2 instances open
            messagebox.showinfo("ERROR",
                                "Unable to open sensor interface /dev/video{}\nThere are already two program instances running.\nPlease close at least one instance before opening a new one.".format(self.port))
            self.endProgram()
        else:
            self.videoSrcSet(self.port)
            self.changeVideoSrc(self.port, oldport)
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
        except:
            self.i2c = 0
        if(self.i2c != 0):
            detected = False
            # check device tree
            try:
                fin = open("/boot/sensor.conf", "r")
                for line in fin:
                    if(re.match(r"(.*){}(.*)".format(name), line)):
                        self.statusAddLine("INFO: device tree is okay")
                        detected = True
            except:
                self.statusAddLine("ERROR: unable to check device tree")
            if((detected == False) or (self.systype == "Unknown")):
                if(messagebox.askyesno("INFO","The selected sensor is not supported by the actual kernel or devicetree\n Do you wish to change this?") != True):
                    return(0)
                if (os.getuid() != 0):
                    messagebox.showinfo("ERROR",
                                          "As kernel parts will be updated, only root user can do this.\nPlease restart the application as root.")
                    return(0)
                else:
                    # Adjust the kernel configuration
                    if(self.systype == "Nano"):
                        # program the new dtb
                        self.statusAddLine("INFO: reprogramming DTB image")
                        os.system("cp {} /boot/dtbnano.dtb".format(self.sensorConfig["Sensor"]["DevtreeImgNano"]))
                        # and also program the new kernel
                        self.statusAddLine("INFO: reprogramming kernel image")
                        os.system("cp {} /boot/Image".format(self.sensorConfig["Sensor"]["KernelImgNano"]))
                        # Update the sensor configuration
                        self.statusAddLine("INFO: updating sensor configuration")
                        os.system("echo \"{}\" > /boot/sensor.conf".format(name))
                        messagebox.showinfo("INFO","Done.\nPlease reboot the system and restart the Software.")
                        self.endProgram()
                    elif(self.systype == "TX2"):
                        # program the new dtb
                        self.statusAddLine("INFO: reprogramming DTB image")
                        os.system("dd if={} of=/dev/mmcblk0p30".format(self.sensorConfig["Sensor"]["DevtreeImg"]))
                        # and also program the new kernel
                        self.statusAddLine("INFO: reprogramming kernel image")
                        os.system("dd if={} of=/dev/mmcblk0p28".format(self.sensorConfig["Sensor"]["KernelImg"]))
                        # Update the sensor configuration
                        self.statusAddLine("INFO: updating sensor configuration")
                        os.system("echo \"{}\" > /boot/sensor.conf".format(name))
                        messagebox.showinfo("INFO","Done.\nPlease reboot the system and restart the Software.")
                        self.endProgram()
                    else:
                        messagebox.showinfo("ERROR","Unsupported nVidia Platform.")
                        self.endProgram()
                return(0)

        # Open v4l2 interface
        self.imager = driver_access.ImagerTools(self.statusAddLine, self.port, self.cli)
        self.imager.initStatusCallback(self.liveStatUpdate)
        self.imager.setSystype(self.systype)
        # read some important board info
        self.board_type = self.imager.getBoardType()
        self.board_revision = self.imager.getBoardRevision()
        self.serial_no = self.imager.getBoardSerialNo()
        # connect to live viewer
        self.live_area_controller.set_hw(self.imager)
        # Prepare Control panel
        self.controlArea.destroy()
        self.controlArea = tkinter.Frame(self)
        self.controlBook.add(self.controlArea, text="Sensor")
        # Prepare Sensor Format
        self.controlLabel1 = tkinter.LabelFrame(self.controlArea)
        self.controlLabel1["text"] = "Sensor Format:"
        self.controlLabel1.pack()
        self.controlFormat = tkinter.StringVar()
        self.controlFormat.set(self.sensorConfig["Sensor"]["defFormat"])
        self.controlFormatList = list()
        for key in self.sensorConfig["Format"]:
            self.controlFormatList.append(key)
        self.controlFormatSelect = tkinter.OptionMenu(self.controlLabel1, self.controlFormat, *self.controlFormatList, command=self.initSensor)
        self.controlFormatSelect.pack()
        # Prepare Sensor Controls
        self.controlLabel2 = tkinter.LabelFrame(self.controlArea)
        self.controlLabel2["text"] = "Control Elements:"
        self.controlLabel2.pack()
        self.widgetList = list()
        for key in self.sensorConfig["Control"]:
            fname = str(self.sensorConfig["Control"][key])
            fname = os.getcwd() + "/" + fname
            try:
                with open(fname, "r") as file:
                    eobj = compile(file.read(),fname, "exec")
                    exec(eobj, globals())
            except:
                self.statusAddLine("ERROR: control file problem (not found or buggy {}".format(fname))
            controlParams = controlInit()
            l = tkinter.LabelFrame(self.controlLabel2)
            l["text"] = controlParams["name"] + " ({})".format(controlParams["unit"])
            l.pack()
            if(controlParams["type"] == "slider"):
                sreg = tkinter.DoubleVar()
                sreg.set(controlParams["default"])
                s = tkinter.Scale(l, length=200, orient=tkinter.HORIZONTAL, variable=sreg)
                s.config(command=partial(controlSet, self, sreg))
                s["from_"] = controlParams["min"]
                s["to"] = controlParams["max"]
                s["resolution"] = controlParams["step"]
                s.set(controlParams["default"])
                s.pack()
                if controlParams["comment"]:
                    CreateToolTip(s, s, controlParams["comment"])
                widget = [controlParams, sreg, s, partial(controlGet, self, sreg)]
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
                s.pack()
                if controlParams["comment"]:
                    CreateToolTip(s, s, controlParams["comment"])
                widget = [controlParams, sreg, s, controlGet]
                self.widgetList.append(widget)

            elif (controlParams["type"] == "spinbox"):
                sreg = tkinter.DoubleVar()
                sreg.set(controlParams["default"])
                s = tkinter.Spinbox(l, width=12, textvariable=sreg, format="%.3f", command=partial(controlSet, self, sreg), validate='all')
                s["from_"] = controlParams["min"]
                s["to"] = controlParams["max"]
                s["increment"] = controlParams["step"]
                s.config(wrap=False)
                s.config(validatecommand=(s.register(partial(validate, s)), "%P"))
                s.grid(row=0, column=0, padx=(5, 85))
                s.bind("<Return>", partial(controlSet, self, sreg))
                s.bind("<KP_Enter>", partial(controlSet, self, sreg))
                s.bind("<FocusOut>", partial(setGuiValue, sreg, partial(controlGet, self, s)))
                if controlParams["comment"]:
                    CreateToolTip(s, s, controlParams["comment"])
                widget = [controlParams, sreg, s, partial(controlGet, self, s)]
                self.widgetList.append(widget)

            elif (controlParams["type"] == "checkbutton"):
                checkvar = tkinter.BooleanVar()
                cb = tkinter.Checkbutton(l, variable=checkvar, command=partial(controlSet, self, checkvar))
                cb["onvalue"] = controlParams["onvalue"]
                cb["offvalue"] = controlParams["offvalue"]
                cb["indicatoron"] = True
                cb.grid(row=0, column=0, padx=(5, 174))
                if controlParams["default"] == "on":
                    cb.select()
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
                entrybox.config(width=18)
                entrybox.bind("<KP_Enter>", partial(controlSet, self.imager, entryvar, self.statusArea))
                entrybox.bind("<Return>", partial(controlSet, self.imager, entryvar, self.statusArea))
                CreateToolTip(entrybox, entrybox, "Address, e.g. 3E01")
                entrybutton = tkinter.Button(l, command=partial(controlSet, self.imager, entryvar, self.statusArea))
                entrybutton["text"] = controlParams["buttontext"]
                if controlParams["comment"]:
                    CreateToolTip(entrybutton, entrybutton, controlParams["comment"])
                entrybutton.grid(row=1, column=1)

            elif (controlParams["type"] == "text_entry_write"):
                address_label = Label(l, text="Address:")
                address_label.grid(row=0, column=0)

                entryvar_address = tkinter.StringVar()
                entrybox_address = tkinter.Entry(l, textvariable=entryvar_address)
                entrybox_address.grid(row=0, column=1)
                entrybox_address.bind("<FocusIn>", partial(disableShortcuts, self.master))
                entrybox_address.bind("<FocusOut>", partial(enableShortcuts, self.master, self.toggleFullscreen))
                entrybox_address.config(width=18)
                CreateToolTip(entrybox_address, entrybox_address, "Address, e.g. 3E01")
                value_label = Label(l, text="Value:")
                value_label.grid(row=1, column=0, sticky=W)

                entryvar_value = tkinter.StringVar()
                entrybox_value = tkinter.Entry(l, textvariable=entryvar_value)
                entrybox_value.grid(row=1, column=1)
                entrybox_value.bind("<FocusIn>", partial(disableShortcuts, self.master))
                entrybox_value.bind("<FocusOut>", partial(enableShortcuts, self.master, self.toggleFullscreen))
                entrybox_value.config(width=18)
                CreateToolTip(entrybox_value, entrybox_value, "Value, e.g. 3C")
                entrybutton = tkinter.Button(l, command=partial(controlSet, self.imager, entryvar_address, entryvar_value,
                                                                self.statusArea))
                entrybutton["text"] = controlParams["buttontext"]
                entrybutton.grid(row=2, column=1)
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
                s = tkinter.Scale(l, length=165, orient=tkinter.HORIZONTAL, variable=sreg)
                s.config(command=partial(controlSetSlider, self, sreg))
                s["from_"] = controlParams["min"]
                s["to"] = controlParams["max"]
                s["resolution"] = controlParams["step"]
                s.set(controlParams["slider_default"])
                s["state"] = controlParams["slider_default_state"]
                s.grid(row=0, column=1)

                checkvar = tkinter.BooleanVar()
                cb = tkinter.Checkbutton(l, variable=checkvar,
                                         command=partial(controlSetCheckbutton, self, checkvar))
                cb["onvalue"] = controlParams["onvalue"]
                cb["offvalue"] = controlParams["offvalue"]
                cb["indicatoron"] = True
                cb.grid(row=0, column=0, padx=5)
                if controlParams["comment"]:
                    CreateToolTip(s, s, controlParams["comment"])
                if controlParams["comment"]:
                    CreateToolTip(cb, cb, controlParams["comment"])
                if controlParams["checkbutton_default"] == "on":
                    cb.select()
                widget = [controlParams, sreg, s, partial(controlGetSlider, self, sreg), checkvar, cb, partial(controlGetCheckbutton, self, checkvar)]
                self.widgetList.append(widget)

            elif (controlParams["type"] == "two_checkbuttons"):
                checkvar1 = tkinter.BooleanVar()
                cb1 = tkinter.Checkbutton(l, variable=checkvar1, command=partial(controlSetCb1, self.imager, checkvar1))
                cb1["onvalue"] = controlParams["cb1_onvalue"]
                cb1["offvalue"] = controlParams["cb1_offvalue"]
                cb1["indicatoron"] = True
                cb1.grid(row=0, column=1, padx=controlParams["cb1_xpad"])
                if controlParams["cb1_default"] == "on":
                    cb1.select()

                checkvar2 = tkinter.BooleanVar()
                cb2 = tkinter.Checkbutton(l, variable=checkvar2, command=partial(controlSetCb2, self.imager, checkvar2))
                cb2["onvalue"] = controlParams["cb2_onvalue"]
                cb2["offvalue"] = controlParams["cb2_offvalue"]
                cb2["indicatoron"] = True
                cb2.grid(row=0, column=3, padx=controlParams["cb2_xpad"])
                if controlParams["cb2_default"] == "on":
                    cb2.select()

                cb1_label = Label(l, text=controlParams["cb1_label_text"])
                cb1_label.grid(row=0, column=0)

                cb2_label = Label(l, text=controlParams["cb2_label_text"])
                cb2_label.grid(row=0, column=2)
                widget = [controlParams, checkvar1, cb1, partial(controlGetCb1, self.imager), checkvar2, cb2, partial(controlGetCb2, self.imager)]
                self.widgetList.append(widget)

            else:
                self.statusAddLine("Undefined")

        # Prepare addition Batch scripts
        self.controlLabel3 = tkinter.LabelFrame(self.controlArea)
        self.controlLabel3["text"] = "Additional Batch scripts:"
        self.controlLabel3.pack()
        self.controlBatchList = list()
        for key in self.sensorConfig["Batch"]:
            self.controlBatchList.append(key)
            b = tkinter.Button(self.controlLabel3, command=partial(self.execBatch, key))
            b["text"] = key
            b.pack()
        # select the right tab
        self.controlBook.select(self.controlArea)
        # and finally init the Sensor
        self.initSensor(self.sensorConfig["Sensor"]["defFormat"])


    def initSensor(self, sensFormat):
        self.statusAddLine("INFO: sensor initialization started ({})".format(sensFormat))
        self.streaming = False
        if(self.cap is not None):
            self.cap.release()
            self.cap = None
        # Execute sensor initialization script
        fname = str(self.sensorConfig["Format"][sensFormat])
        fname = os.getcwd() + "/" + fname
        try:
            with open(fname, "r") as file:
                eobj = compile(file.read(), fname, "exec")
                exec(eobj, globals())

        except:
            self.statusAddLine("ERROR: control file problem (not found or buggy {}".format(fname))
        # Stop streaming
        if(self.streaming == True):
            self.imager.stopstream()
            self.streaming = False
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
        self.startLive()

    def startLive(self, record=False):
        lp = 0
        self.ee = 0
        self.tnr = 0
        for entry in self.tnrList:
            if (entry == str(self.config["ISP"]["tnr"])):
                self.tnr = lp
            else:
                lp += 1
        lp = 0
        for entry in self.eeList:
            if (entry == str(self.config["ISP"]["ee"])):
                self.ee = lp
            else:
                lp += 1
        if(self.config["ISP"]["dgain"] == "off"):
            self.dgain = "1 1"
        else:
            self.dgain = "1 8"
        # Enable Live picture
        try:
            self.cap.release()
            del(self.cap)
        except:
            pass
        if(self.sensorConfig["Sensor"]["gstPipe"] != "color"):
            self.statusAddLine("INFO: GREY sensor, V4L2 pipeline")
            self.v4l2 = True
            if(self.noGst):
                self.cap = self.iface
            else:
                self.statusAddLine("ERROR: GREY sensor works only in V4L2 streaming mode. Please check gstInterface setting in sensor config")
        else:
            self.v4l2 = False
            self.iface =  "nvarguscamerasrc sensor-id={} wbmode=0  tnr-mode={} tnr-strength=0.5 ee-mode={} ee-strength=0.5 sensor-mode={} ".format(self.port, self.tnr, self.ee, self.sensor_mode)
            self.iface += "saturation=0.0 "
            self.iface += "ispdigitalgainrange=\"{}\" !".format(self.dgain)
            self.iface += " video/x-raw(memory:NVMM),width=(int){},height=(int){},format=(string)NV12,framerate=(fraction){}/1 !".format(self.sensor_w, self.sensor_h, self.sensor_fps)
#            if (record == False):
            self.iface += " nvvidconv ! video/x-raw ! appsink"
#            else:
#                self.iface += " tee name=t ! nvvidconv ! video/x-raw ! appsink t. !"
#                self.iface += " nvvidconv ! video/x-raw(memory:NVMM),format=(string)I420 !"
#                self.iface += " nvv4l2h264enc ! h264parse ! avimux ! filesink location=/run/test.avi"
#                self.iface += " video/x-h264, stream-format=(string)byte-stream ! h264parse !"
#                self.iface += " qtmux ! filesink location=test.mp4 t. ! nvvidconv ! video/x-raw ! appsink"
#                self.iface += " qtmux ! tee name=t ! filesink location=/run/test.mp4 t. ! appsink"
            print(self.iface)
            self.cap = cv2.VideoCapture(self.iface)
        self.statusAddLine("INFO: opening interface ({})".format(self.iface))
        self.streaming = True
        self.root.config(cursor="")
        self.imager.setformat(self.bpp, self.sensor_w, self.sensor_h, self.sensor_wdma, self.sensor_hdma, self.v4l2)
        self.imager.startstream()
        self.root.after(2000, self.doWidgetAutoUpdate)
        self.imager.doWidgetUpdate()
        self.liveUpdate()

    def stopLive(self):
        self.streaming = False
        time.sleep(0.1)
        self.cap.release()
        del(self.cap)

    def liveUpdate(self):
        while self.streaming:
            if (self.v4l2):
                self.statusAddLine("V4L2 live streaming is obsolete. Please correct the according setting in the resolution file")
            else:
                #self.doFlashEnable()
                # In case the sensor is a lot faster than display speed, we drop every second or third image
                if(self.temp > 65.0):
                    cnt = 3
                elif(self.temp > 55.0):
                    cnt = 2
                else:
                    cnt = 1
                for lp in range(0,cnt):
                    retval, frame = self.cap.read()
                    if retval == False:
                        time.sleep(0.01)
                    else:
                        cvimage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
            if retval == True:
                # dont read a new image if pause was pressed
                if self.live_area_controller.is_video_mode():
                    self.last_image = cvimage
                    self.last_frame = frame
                    cvimage = self.zoom_controller.calculate_current_image(cvimage)
                    # Update Histogram if focus is active
                    try:
                        if (self.controlBook.index(self.controlBook.select()) == 2):
                            plotx = np.linspace(0, 255, 256)
                            ploty = cv2.calcHist([cvimage], [0], None, [256], [0, 256])
                            ploty = ploty / ploty.max()
                            self.updateHistPlot(plotx, ploty)
                            h, w, ch = cvimage.shape
                            wline = cvimage[int(h/2), :, 0]
                            self.updateWavePlot(wline)
                            # TODO: Add a line to canvas object
                    except:
                        raise
                else:
                    cvimage = self.zoom_controller.calculate_current_image(self.last_image)
                h,w,ch = cvimage.shape
                if self.fullscreen == False:
                    cvimage = cv2.resize(cvimage, (self.w, self.h))
                    photo = ImageTk.PhotoImage(image=PIL.Image.fromarray(cvimage))
                    self.liveCanvas.create_image(0,0, image=photo, anchor=tkinter.NW)
                else:
                    cv2.imshow("Live", cvimage)
                    if(cv2.waitKey(1) & 0x7F == ord("f")):
                        cv2.destroyAllWindows()
                        self.fullscreen = False
                # do statistics
                try:
                    self.lasttime
                    self.acttime = time.time()
                    self.disp_freq = format(1.0 / (self.acttime - self.lasttime), ".2f")
                    self.disp_fps = "FPS display: {}".format((self.disp_freq))
                    self.lasttime = self.acttime
                except:
                    self.lasttime = time.time()
                    self.disp_fps = "FPS display: ???"
                self.liveStatUpdate("FPS sensor: {}".format(self.sensor_fps), self.disp_fps)
            if(self.imager.WidgetUpdatePending() == True):
                self.doWidgetUpdate()
            self.root.update()
            #self.doFlashEnable()

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
                        ctrl1["fg"] = "lightgrey"
                        ctrl1["troughcolor"] = "lightgrey"
                    else:
                        ctrl1["state"] = "normal"
                        ctrl1["fg"] = "black"
                        ctrl1["troughcolor"] = "#b3b3b3"
                if (controlParams["type"] == "two_checkbuttons"):
                    get2()
            except:
                self.statusAddLine("ERROR: Widget {} has some errors. Please correct them and restart the software".format(controlParams["name"]))
        # Disable read and write information in status area
        self.imager.enablePrint()


    def doWidgetAutoUpdate(self):
        # Disable read and write information in status area
        self.imager.disablePrint()

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
                self.statusAddLine("ERROR: Widget {} has some errors. Please correct them and restart the software".format(controlParams["name"]))
        # Disable read and write information in status area
        self.imager.enablePrint()


        if(self.streaming == True):
            self.root.after(1000,self.doWidgetAutoUpdate)

    def execBatch(self, event):
        self.statusAddLine("INFO: executing{}".format(str(event)))
        fname = str(self.sensorConfig["Batch"][str(event)])
        fname = os.getcwd() + "/" + fname
        try:
            with open(fname, "r") as file:
                exec (file.read())
        except:
            self.statusAddLine("ERROR: control file problem (not found or buggy {}".format(fname))
        execCmd(self.imager)

    def editSettings(self):
        # TODO:
        # Add Encoder and Recording settings
        pass

    def saveSettings(self):
        fp = open("./config.cfg", "w")
        self.config.write(fp)
        self.statusAddLine("INFO: config file updated")

    def showDocumentation(self):
        # check if Chromium is installed
        # Open chromium Browser with Help URL
        try:
            self.help = os.popen("chromium-browser --no-sandbox --app=file://{}/doc/index.html".format(os.getcwd()))
        except:
            messagebox.showinfo("Documentation", "The documentation cannot be shown\nPlease check if Chromium webbrowser is installed")

    def showChanges(self):
        # check if Chromium is installed
        # Open chromium Browser with Help URL
        try:
            self.help = os.popen("chromium-browser --no-sandbox --app=file://{}/doc/Changes.html".format(os.getcwd()))
        except:
            messagebox.showinfo("Documentation", "The documentation cannot be shown\nPlease check if Chromium webbrowser is installed")

    def showAgreement(self):
        # check if Chromium is installed
        # Open chromium Browser with Help URL
        try:
            self.help = os.popen("chromium-browser --no-sandbox --app=file://{}/doc/LicenseAgreement.html".format(os.getcwd()))
        except:
            messagebox.showinfo("Documentation", "The documentation cannot be shown\nPlease check if Chromium webbrowser is installed")

    def showDocumentationOnline(self):
        # check if Chromium is installed
        # Open chromium Browser with Help URL
        try:
            self.help = os.popen("chromium-browser  --no-sandbox --app=https://ams.com/cgss130".format(os.getcwd())) # TODO: replace by real webpage
        except:
            messagebox.showinfo("Documentation", "The documentation cannot be shown\nPlease check if Chromium webbrowser is installed")

    def showAbout(self):
        messagebox.showinfo("About", "JetCis Viewer by ams in 2020 \nVersion {} \nFor updates, check the ams website.".format(self.config["App"]["version"]))


#####################
# MAIN
#####################
root = tkinter.Tk()
root.title("JetCis viewer")
app = MainApp(master=root)
app.mainloop()
