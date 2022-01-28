[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![nVIDIA](https://img.shields.io/badge/nVIDIA-%2376B900.svg?style=for-the-badge&logo=nVIDIA&logoColor=white)
![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)
![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)

<a href="https://ams.com/area-scan-sensors">
<img src="https://upload.wikimedia.org/wikipedia/commons/3/32/Ams_AG_Logo.svg" alt="ams logo" width="200" title="ams logo" border="0"/>
</a>


# ams_jetcis_software for MIRA image sensors
Python code to evaluate ams image sensors for jetson nano evaluation kit.
To be more specific, the global shutter, NIR-enhanced MIPI sensors from ams.

https://ams.com/area-scan-sensors

This guide requires an nvidia jetson nano B01 with 4 GB ram. Other versions will NOT work.

Software: https://github.com/ams-sensors/ams_jetcis_software

Microcontroller: https://github.com/ams-sensors/ams_jetcis_microcontroller

Kernel: https://github.com/ams-sensors/ams_jetcis_kernel

Hardware: https://github.com/ams-sensors/ams_jetcis_hardware



# 1. Preparing the jetson nano

### Download image from
version: (make sure it is jetpack 4.6)

https://developer.nvidia.com/embedded/l4t/r32_release_v6.1/jeston_nano/jetson-nano-jp46-sd-card-image.zip

### Burn image to SD card.
Windows:
https://www.balena.io/etcher/

Linux:
use dd command

### Boot the kit
Boot the jetson nano by pluggin in the power connector.
During first install, we recommend to set location to United States.
Select for both user name and password:

`username: jetcis`

`password: jetcis`


This is needed since the software assumes this as your root password.

# 2. Installing ams software 

## Clone the software repo to the jetson nano.

After installation, open a terminal

`$ cd ~ `

`$ git clone  https://github.com/ams-sensors/ams_jetcis_software.git`

`$ cd ~/ams_jetcis_software `

`$ make all`

done.


# 3. Running the application:

## from terminal

`$ cd ~/ams_jetcis_software `

`$ make launch_gui`

`$ make launch_notebook`

## from desktop

click the desktop shortcut


