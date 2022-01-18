#!/bin/bash
HOME="$( cd ~  >/dev/null 2>&1 && pwd )"
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd $DIR
export PYTHONPATH=$PYTHONPATH:$DIR

zenity --warning --title "JetCis Installer" --text "Make sure that all instances of JetCis viewer are closed\nand you are not within the JetCis folder.\nOtherwise installation might fail." --width=400

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
sudo apt-get -y install ubuntu-mate-desktop 

echo "Fix v4l2 python library issue"
sudo cp v4l2.py /usr/local/lib/python3.6/dist-packages/v4l2.py
sudo cp v4l2.py ~/.local/lib/python3.6/site-packages/v4l2.py

echo "Install GStreamer Patches"
if [ $(gst-inspect-1.0 v4l2src | egrep -o "bggr12|bggr10" | wc -l) == 2 ] ; then
    echo "...patches are already installed, skipping installation of Gstreamer Patches"
else
    cd ./gst-plugins-good-1.14.5_patched/
    sudo chmod +x autogen.sh
    ./autogen.sh --disable-gtk-doc  --prefix /usr/ --libdir /usr/lib/aarch64-linux-gnu
    make
    sudo make install
fi

cd $DIR
echo "install the Pleora eBUS SDK"
if [ -d "/opt/pleora/" ]; then
   echo "/opt/pleora/ already exists, skipping installation of Pleora eBUS SDK"
else
   sudo apt-get -y install qt5-default
    sudo dpkg -i ./sdk.deb
    sudo nvpmodel -m 0
    sudo jetson_clocks --store ../jetson_clock.bac
    sudo jetson_clocks
fi


echo "Install Application to $HOME/JetCis , user: $USER"

if [ -d "$HOME/JetCis" ]
then
	echo "...remove old Application folder"
	sudo rm -rf ~/JetCis
fi
cp -rf ../Jetcis/. ~/JetCis

echo "Prepare customized kernel infrastructure"
sudo cp ./extlinux.conf /boot/extlinux/extlinux.conf
sudo cp ./dtbnano.dtb /boot/dtbnano.dtb
sudo cp ./kernelnano.img /boot/Image
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

echo "Create Desktop Icon"
echo "[Desktop Entry]" > ~/Desktop/JetCis.desktop
echo "Version=1.0" >> ~/Desktop/JetCis.desktop
echo "Type=Application" >> ~/Desktop/JetCis.desktop
echo "Terminal=true" >> ~/Desktop/JetCis.desktop
echo "Exec=$HOME/JetCis/startPy.sh" >> ~/Desktop/JetCis.desktop
echo "Name=JetCis" >> ~/Desktop/JetCis.desktop
echo "Comment=JetCis" >> ~/Desktop/JetCis.desktop
echo "Icon=$HOME/JetCis/desktop_icon.png" >> ~/Desktop/JetCis.desktop
echo "Set the script rights accordingly"
sudo chmod +x ~/Desktop/JetCis.desktop
sudo chmod +x ~/JetCis/startPy.sh
sudo chmod +x ~/JetCis/start.sh
sudo chown -R $USER $HOME/JetCis
gio set ~/Desktop/JetCis.desktop "metadata::trusted" yes

zenity --info --title "JetCis Installer" --text "Installation is done.\nPlease reboot the system to make sure,\nall changes are applied and then run install2.sh." --width=300
