from distutils.core import setup, Extension
import numpy

modul = Extension(	
	"GEVPython", 
    
	sources=["GEVPython.cpp", "Utilities.cpp", "MyEventSink.cpp", "MyRegisterEventSink.cpp"],
	include_dirs=["/opt/pleora/ebus_sdk/linux-aarch64-arm/include/",
			"/usr/include/python3.6/numpy",
			numpy.get_include()],
	define_macros=[("_UNIX_" , "1" ), ("_LINUX_", "1")],
	library_dirs=[  "/opt/pleora/ebus_sdk/linux-aarch64-arm/lib/",
			"/opt/pleora/ebus_sdk/linux-aarch64-arm/lib/genicam/bin/Linux64_ARM"],
	libraries=["PvAppUtils", "PtConvertersLib", "PvBase", "PvBuffer", "PvGenICam", 
			"PvSystem", "PvStream", "PvDevice", "PvTransmitter", "PvVirtualDevice",
			"PvPersistence", "PvSerial", "PvCameraBridge", "PvGUI", "SimpleImagingLib"]
	)

setup(
	name= "GEVPython",
	version = "1.3",
	description = "Wrapper for eBUS SDK",
	ext_modules = [modul]
	)


