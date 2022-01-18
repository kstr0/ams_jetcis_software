#!/bin/bash
HOME="$( cd ~  >/dev/null 2>&1 && pwd )"
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd $DIR
export PYTHONPATH=$PYTHONPATH:$DIR
echo "install Pleora eBUS applications"
#if python3 -c "import GEVPython" &> /dev/null; then
#    echo '... already installed, skipping installation.'
#else
cd ../Genicam/GEVPython/
python3 setup.py build
sudo python3 setup.py install
#fi

zenity --info --title "JetCis Installer 2" --text "Installation is done." --width=300
