#!/bin/bash
HOME="$( cd ~  >/dev/null 2>&1 && pwd )"
cd $HOME

jupyter notebook --no-browser
