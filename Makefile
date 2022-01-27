# Development management facilities
#
# This file specifies useful routines to soften development management.
# See https://www.gnu.org/software/make/.


# Tool configuration
SHELL := /bin/bash
GNUMAKEFLAGS += --no-print-directory

# File system record
REPO_ROOT ?= $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
SOURCE_ROOT ?= .
DIST_ROOT ?= dist
VENV_ROOT ?= venv

# Executables definition
PYTHON ?= $(VENV_ROOT)/bin/python3
PIP = $(PYTHON) -m pip
REMOVE = rm -fr


%: # Treat unrecognized targets
	@ echo "No rule to '$(*)'."
	echo "use 'make help' to check available ones."

help:: ## Show this help
	@ egrep -h '\s##\s' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[3	7;1m%-20s\033[0m %s\n", $$1, $$2}'


launch_gui::
	$(PYTHON) -m ams_jetcis 
launch_notebook::
	$(PYTHON) -m jupyter notebook 

all::
	make init
	make install_system
	make install_editable

init:: veryclean requirements.txt ## Configure development environment
	test -d $(VENV_ROOT) || python3 -m virtualenv $(VENV_ROOT) --system-site-packages
	$(PIP) install -r requirements.txt --upgrade
	$(PIP) freeze

lala::
	@ echo $(REPO_ROOT)

build:: clean ## Build package
	$(PYTHON) -m build 

install_editable:: clean ## Install ams package
	test -d $(VENV_ROOT) || make init
	$(PYTHON) -m pip install --editable . 

test:: clean ## Test code w unit tests
	$(PYTHON) -m pytest 

clean:: ## Delete all files created through build process
	$(REMOVE) dist/*
	$(REMOVE) **/*.egg-info
	$(REMOVE) build/

veryclean:: clean ## Delete all generated files
	$(REMOVE) $(VENV_ROOT)
	find $(SOURCE_ROOT) -iname "*.pyc" -iname "*.pyo" -delete
	find $(SOURCE_ROOT) -name "__pycache__" -type d -exec rm -rf {} +


	if [ -d "$HOME/JetCis" ]
	then
		echo "...remove old Application folder"
		sudo rm -rf ~/ams_jetcis
		rm ~/Desktop/JetCis.desktop
	fi
	if [ -d "$HOME/ams_jetcis" ]
	then
		echo "...remove old Application folder"
		sudo rm -rf ~/ams_jetcis
		rm ~/Desktop/JetCis.desktop
	fi
	if [ -d "$HOME/ams" ]
	then
		echo "...remove old Application folder"
		sudo rm -rf ~/ams
	fi
	
	if [ -f "/boot/sensor.conf" ]
	then
		sudo rm /boot/sensor.conf
	fi

install_system: ## install system packages
	echo "Update Repository"
	sudo apt-get update

	echo "Disable updates"
	sudo apt -y purge update-notifier-common
	sudo apt -y purge  unattended-upgrades

	echo "Install python packages"
	sudo apt-get -y install python3-pip
	sudo apt-get -y install python3-tk
	sudo apt-get -y install python3-pil.imagetk
	sudo apt-get -y install python3-matplotlib
	pip3 install v4l2

	echo "Install multimedia packages"
	sudo apt-get -y install build-essential cmake git pkg-config libgtk-3-dev
	sudo apt-get -y install libavcodec-dev libavformat-dev libswscale-dev libv4l-dev libxvidcore-dev libx264-dev
	sudo apt-get -y install libjpeg-dev libpng-dev libtiff-dev gfortran openexr libatlas-base-dev
	sudo apt-get -y install python3-dev python3-numpy libtbb2 libtbb-dev libdc1394-22-dev
	sudo apt-get -y install libgstreamer1.0-dev 
	sudo apt-get -y install libgstreamer-plugins-base1.0-dev
	sudo apt-get -y install v4l-utils

	echo "Install other useful packages"
	sudo apt-get -y install subversion
	sudo apt-get -y install nano
	sudo apt-get -y install lsof
	python3 -m pip install -U pip
	python3 -m pip install virtualenv

	python3 -m pip install ttkbootstrap==0.5.2
	sudo cp data/themes_custom.py ~/.local/lib/python3.6/site-packages/ttkbootstrap/themes_custom.py

	echo "Install jupyter notebook"
	sudo apt install libzmq3-dev
	sudo apt install jupyter-notebook
	sudo apt install libffi-dev
	python3 -m pip install ipywidgets --upgrade
	python3 -m pip install jupyterlab
	python3 -m pip install nbconvert==5.6.1
	sudo apt-get install libxml2-dev libxslt-dev python3-dev
	python3 -m pip install jupyter_contrib_nbextensions
	sudo jupyter nbextension install --user
	python3 -m pip install hide_code
	sudo jupyter nbextension install --py hide_code
	jupyter nbextension enable --py hide_code
	jupyter serverextension enable --py hide_code
	python3 -m pip install plotly==5.5.0
	python3 -m pip install tqdm
	python3 -m pip install openpyxl
	python3 -m pip install characterization_ams-1.0.4-py3-none-any.whl
	sudo apt install python3-h5py
	python3 -m pip install kaleido

	sudo data/install_fan.sh


	echo "Fix v4l2 python library issue"
	sudo cp data/v4l2.py /usr/local/lib/python3.6/dist-packages/v4l2.py
	sudo cp data/v4l2.py ~/.local/lib/python3.6/site-packages/v4l2.py

	sudo cp data/extlinux.conf /boot/extlinux/extlinux.conf

	nvidiaversion=$(dpkg-query --show nvidia-l4t-core)
	nvidiaversionparse=(${nvidiaversion//./ })
	if [[ ${nvidiaversionparse[2]} -eq 6 ]]
	then
		echo "Jetpack 4.6"
		sudo cp data/dtbnano_L4T_32_6_1.dtb /boot/dtbnano.dtb
		sudo cp data/kernelnano_L4T_32_6_1.img /boot/Image
	elif [[ ${nvidiaversionparse[2]} -eq 4 ]]
	then
		echo "Jetpack 4.4"
		sudo cp data/dtbnano.dtb /boot/dtbnano.dtb
		sudo cp data/kernelnano.img /boot/Image
	fi
		

	echo "turn off lens shading"
	sudo cp data/camera_overrides.isp /var/nvidia/nvcam/settings/camera_overrides.isp
	sudo chown root:root /var/nvidia/nvcam/settings/camera_overrides.isp
	sudo chmod 664 /var/nvidia/nvcam/settings/camera_overrides.isp

	echo "Set wallpaper"
	cp data/desktop-background-ams-OSRAM.jpg $HOME/Pictures
	gsettings set org.gnome.desktop.background picture-uri "file://$HOME/Pictures/desktop-background-ams-OSRAM.jpg"
	echo "installation done."
	#zenity --info --title "ams_jetcis Installer" --text "Simplified installation is done.\nPlease reboot the system to make sure,\nall changes are applied and then run install 1 and 2.sh if genicam is needed. (usually it is not)" --width=300

	#some aliases
	echo alias python=python3 > ~/.bash_aliases



	make launcher

launcher:: ## desktop shortcut
	echo "Create GUI Desktop Icon"
	echo "[Desktop Entry]" > ~/Desktop/ams_jetcis.desktop
	echo "Version=1.0" >> ~/Desktop/ams_jetcis.desktop
	echo "Type=Application" >> ~/Desktop/ams_jetcis.desktop
	echo "Terminal=true" >> ~/Desktop/ams_jetcis.desktop
	echo "Exec= make -C $(REPO_ROOT) launch_gui" >> ~/Desktop/ams_jetcis.desktop
	echo "Name=ams_osram_jetcis" >> ~/Desktop/ams_jetcis.desktop
	echo "Comment=ams_osram_jetcis" >> ~/Desktop/ams_jetcis.desktop
	echo "Icon=$(REPO_ROOT)/ams_jetcis/button_icons/desktop_icon.png" >> ~/Desktop/ams_jetcis.desktop
	echo "Set the script rights accordingly"
	gio set ~/Desktop/ams_jetcis.desktop "metadata::trusted" yes
	sudo chmod a+rwx ~/Desktop/ams_jetcis.desktop
	# sudo chmod a+rwx ~/ams/gui.sh

	echo "Create Jupyter Notebook Desktop Icon"
	echo "[Desktop Entry]" > ~/Desktop/jupyter_notebook.desktop
	echo "Version=1.0" >> ~/Desktop/jupyter_notebook.desktop
	echo "Type=Application" >> ~/Desktop/jupyter_notebook.desktop
	echo "Terminal=true" >> ~/Desktop/jupyter_notebook.desktop
	echo "Exec=make -C $(REPO_ROOT) launch_notebook" >> ~/Desktop/jupyter_notebook.desktop
	echo "Name=jupyter_notebook" >> ~/Desktop/jupyter_notebook.desktop
	echo "Comment=jupyter_notebook" >> ~/Desktop/jupyter_notebook.desktop
	echo "Icon=$(REPO_ROOT)/ams_jetcis/button_icons/jupyter_logo.png" >> ~/Desktop/jupyter_notebook.desktop
	gio set ~/Desktop/jupyter_notebook.desktop "metadata::trusted" yes
	sudo chmod a+rwx ~/Desktop/jupyter_notebook.desktop
	# sudo chmod a+rwx ~/ams/start_jupyter.sh





.EXPORT_ALL_VARIABLES:
.ONESHELL:
.PHONY: help init all build clean veryclean install test launch_gui launch_notebook install_editable