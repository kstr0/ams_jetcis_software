#!/bin/bash
echo "building installer archive"
echo "please do not commit this archive to svn"
version='2.4.0-rc5' #$(awk '/version/{print $NF}' ./ams_jetcis/config.cfg)
echo "version is $version"

filename='installer_'$version'.tar.gz'
echo $filename is building
sleep 1
tar -czvf $filename --exclude="*.tar.gz" --exclude="*.zip"  --exclude="*.vscode"  --exclude="*.egg-info"   --exclude="*.build" *
echo "done"
