[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![nVIDIA](https://img.shields.io/badge/nVIDIA-%2376B900.svg?style=for-the-badge&logo=nVIDIA&logoColor=white)
![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)
![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)

<a href="https://ams.com/area-scan-sensors">
<img src="https://upload.wikimedia.org/wikipedia/commons/3/32/Ams_AG_Logo.svg" alt="ams logo" width="200" title="ams logo" border="0"/>
</a>


# ams_jetcis_software
Python code to evaluate ams image sensors for jetson nano evaluation kit.
To be more specific, the global shutter, NIR-enhanced MIPI sensors from ams.

https://ams.com/area-scan-sensors

This guide requires an nvidia jetson nano B01 with 4 GB ram. Other versions will NOT work.

Software: https://github.com/ams-sensors/ams_jetcis_software

Microcontroller: https://github.com/ams-sensors/ams_jetcis_microcontroller

Kernel: https://github.com/ams-sensors/ams_jetcis_kernel

Hardware: https://github.com/ams-sensors/ams_jetcis_hardware



# Preparing the jetson nano

### Download image from
version: (make sure it is jetpack 4.6)

https://developer.nvidia.com/embedded/l4t/r32_release_v6.1/jeston_nano/jetson-nano-jp46-sd-card-image.zip

### Burn image to SD card.
Windows:
https://www.balena.io/etcher/

Linux:
use dd command

### Clone the software repo to the jetson nano.
Boot the jetson nano by pluggin in the power connector.
During first install, we recommend to set location to United States.
Select for both user name and password:

`username: jetcis`

`password: jetcis`


This is needed since the software assumes this as your root password.

### Clone the software repo to the jetson nano.
After installation, open a terminal

`$ git clone https://github.com/ams-sensors/ams_jetcis_software.git`

Then, go to the ShellInstaller folder and run the following commands in a terminal with a working network connection.

`$ ./install_0.sh`

done.


# Running the application:

### for the GUI:

`$ python3 -m ams_jetcis`

### for SCRIPTS:

`$ python3 -m ams_jetcis.scripts`

### for Notebooks:

`$ python3 -m jupyter notebook`

You can also run the shell scripts

'$ gui.sh'

'$ scripts.sh'

# How to use this package (For developers)

## Organization
the sw folder (root folder) contains all subpackages we need:
ams_jetcis, characterization, mira_xs_api and so on.
The setup.py and setup.cfg describe which pages we want to distribute.

## Create VENV
`$ python3 -m virtualenv env`

### Get build packages
`$ python3 -m pip install setuptools`
`$ python3 -m pip install build`

### Build for distribution:
`$ python3 -m build`
in the dist folder you will find a wheel file
install it with
`$ pip install *.whl`

### Build and install for testing:
`$ pip install --editable .`

### TBD
add console script to fully replace the install script
upload to pypi
pytest

