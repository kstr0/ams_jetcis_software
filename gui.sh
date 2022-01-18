#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd $DIR
export PYTHONPATH=$PYTHONPATH:$DIR
#echo $DIR
python3 -m ams_jetcis