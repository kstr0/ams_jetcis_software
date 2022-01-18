# How to use this package

## Organization
the sw folder (root folder) contains all subpackages we need:
ams_jetcis, characterization, mira_xs_api and so on.
The setup.py and setup.cfg describe which pages we want to distribute.

## Create VENV
`python3 -m virtualenv env`

## Get build packages
`python3 -m pip install setuptools`
`python3 -m pip install build`

## Build for distribution:
`python3 -m build`
in the dist folder you will find a wheel file
install it with
`pip install *.whl`

## Build and install for testing:
`pip install --editable .`

### TBD
add console script to fully replace the install script
upload to pypi


## Install
First, to install, run in the shellinstaller folder.
You need a working internet connection to run it the first time. (only when there is no ams software on the kit yet)
`$ ./instal_0.sh`
the second time, if you are only upgrading, you can do 
`$ ./instal_0.sh nointernet`


## Run 
from the parent dir of ams_jetcis:

### for the GUI:
`python3 -m ams_jetcis`
### for SCRIPTS:
`python3 -m ams_jetcis.scripts`

You can also run the shell scripts

'$ gui.sh'

'$ scripts.sh'