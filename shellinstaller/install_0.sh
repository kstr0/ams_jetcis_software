#!/bin/bash
HOME="$( cd ~  >/dev/null 2>&1 && pwd )"
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd $DIR

nointernet=0
extra=1

# while getopts i: flag
# do
#     case "${flag}" in
#         i) internet=${OPTARG};;
#     esac
# done
# echo "Internet: $internet";




if [[ $# -eq 0 ]] ; then
    echo "No arguments provided, will continue with online installation. Make sure to have working internet connection and make sure all apps are closed."
    # exit 1
else
	echo "provided arg is '$1'"
	if  [ "$1" == "nointernet" ] ; then
		nointernet=1
		echo "no internet value is $nointernet , proceeding with offline installation....................."
	fi
	if  [ "$1" == "extra" ] ; then
		extra=1
		echo "extra  value is $extra , proceeding with extra packages like jupyter installation....................."
	fi
fi


export PYTHONPATH=$PYTHONPATH:$DIR

# zenity --warning --title "ams_jetcis Installer" --text "Make sure that all instances of ams_jetcis viewer are closed\nand you are not within the ams_jetcis folder.\nOtherwise installation might fail." --width=400


if  [ $nointernet -eq 0 ] ; then

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
	sudo cp themes_custom.py ~/.local/lib/python3.6/site-packages/ttkbootstrap/themes_custom.py
	# sudo apt-get -y install ubuntu-mate-desktop 
	if  [ $extra -eq 1 ] ; then	
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
		sudo apt install python3-h5py
		python3 -m pip install kaleido
	fi
fi

sudo ./install_fan.sh


echo "Fix v4l2 python library issue"
sudo cp v4l2.py /usr/local/lib/python3.6/dist-packages/v4l2.py
sudo cp v4l2.py ~/.local/lib/python3.6/site-packages/v4l2.py

# echo "Install GStreamer Patches"
# if [ $(gst-inspect-1.0 v4l2src | egrep -o "bggr12|bggr10" | wc -l) == 2 ] ; then
#     echo "...patches are already installed, skipping installation of Gstreamer Patches"
# else
#     cd ./gst-plugins-good-1.14.5_patched/
#     sudo chmod +x autogen.sh
#     ./autogen.sh --disable-gtk-doc  --prefix /usr/ --libdir /usr/lib/aarch64-linux-gnu
#     make
#     sudo make install
# fi

# cd $DIR
# echo "install the Pleora eBUS SDK"
# if [ -d "/opt/pleora/" ]; then
#    echo "/opt/pleora/ already exists, skipping installation of Pleora eBUS SDK"
# else
#    sudo apt-get -y install qt5-default
#     sudo dpkg -i ./sdk.deb
#     sudo nvpmodel -m 0
#     sudo jetson_clocks --store ../jetson_clock.bac
#     sudo jetson_clocks
# fi


echo "Install Application to $HOME/ams_jetcis , user: $USER"

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

mkdir ~/ams
cp -rf ../ ~/ams/


echo "Prepare customized kernel infrastructure"
sudo cp ./extlinux.conf /boot/extlinux/extlinux.conf

nvidiaversion=$(dpkg-query --show nvidia-l4t-core)
nvidiaversionparse=(${nvidiaversion//./ })
if [[ ${nvidiaversionparse[2]} -eq 6 ]]
then
  	echo "Jetpack 4.6"
	sudo cp ./dtbnano_L4T_32_6_1.dtb /boot/dtbnano.dtb
	sudo cp ./kernelnano_L4T_32_6_1.img /boot/Image
elif [[ ${nvidiaversionparse[2]} -eq 4 ]]
then
  	echo "Jetpack 4.4"
  	sudo cp ./dtbnano.dtb /boot/dtbnano.dtb
	sudo cp ./kernelnano.img /boot/Image
fi

if [ -f "/boot/sensor.conf" ]
then
	sudo rm /boot/sensor.conf
fi

echo "Remove other temporary files"
if [ -f "/tmp/SyncServer.tmp" ]
then
	sudo rm /tmp/SyncServer.tmp
fi

echo "turn off lens shading"
sudo cp camera_overrides.isp /var/nvidia/nvcam/settings/camera_overrides.isp
sudo chown root:root /var/nvidia/nvcam/settings/camera_overrides.isp
sudo chmod 664 /var/nvidia/nvcam/settings/camera_overrides.isp

echo "Create GUI Desktop Icon"
echo "[Desktop Entry]" > ~/Desktop/ams_jetcis.desktop
echo "Version=1.0" >> ~/Desktop/ams_jetcis.desktop
echo "Type=Application" >> ~/Desktop/ams_jetcis.desktop
echo "Terminal=true" >> ~/Desktop/ams_jetcis.desktop
echo "Exec=$HOME/ams/gui.sh" >> ~/Desktop/ams_jetcis.desktop
echo "Name=ams_osram_jetcis" >> ~/Desktop/ams_jetcis.desktop
echo "Comment=ams_osram_jetcis" >> ~/Desktop/ams_jetcis.desktop
echo "Icon=$HOME/ams/ams_jetcis/button_icons/desktop_icon.png" >> ~/Desktop/ams_jetcis.desktop
echo "Set the script rights accordingly"
gio set ~/Desktop/ams_jetcis.desktop "metadata::trusted" yes
sudo chmod a+rwx ~/Desktop/ams_jetcis.desktop
sudo chmod a+rwx ~/ams/gui.sh

echo "Create Jupyter Notebook Desktop Icon"
echo "[Desktop Entry]" > ~/Desktop/jupyter_notebook.desktop
echo "Version=1.0" >> ~/Desktop/jupyter_notebook.desktop
echo "Type=Application" >> ~/Desktop/jupyter_notebook.desktop
echo "Terminal=true" >> ~/Desktop/jupyter_notebook.desktop
echo "Exec=$HOME/ams/start_jupyter.sh" >> ~/Desktop/jupyter_notebook.desktop
echo "Name=jupyter_notebook" >> ~/Desktop/jupyter_notebook.desktop
echo "Comment=jupyter_notebook" >> ~/Desktop/jupyter_notebook.desktop
echo "Icon=$HOME/ams/ams_jetcis/button_icons/jupyter_logo.png" >> ~/Desktop/jupyter_notebook.desktop
gio set ~/Desktop/jupyter_notebook.desktop "metadata::trusted" yes
sudo chmod a+rwx ~/Desktop/jupyter_notebook.desktop
sudo chmod a+rwx ~/ams/start_jupyter.sh

echo "Set wallpaper"
cp desktop-background-ams-OSRAM.jpg $HOME/Pictures
gsettings set org.gnome.desktop.background picture-uri "file://$HOME/Pictures/desktop-background-ams-OSRAM.jpg"
echo "installation done."
#zenity --info --title "ams_jetcis Installer" --text "Simplified installation is done.\nPlease reboot the system to make sure,\nall changes are applied and then run install 1 and 2.sh if genicam is needed. (usually it is not)" --width=300

#some aliases
echo alias python=python3 > ~/.bash_aliases
